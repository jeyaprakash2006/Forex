const instruments = [
  { symbol: "EUR/USD", desc: "Euro / US Dollar", icon: "€", price: 1.08420, change: 0.18, spread: 1.2, low: 1.08108, high: 1.08714, digits: 5 },
  { symbol: "GBP/USD", desc: "British Pound / US Dollar", icon: "£", price: 1.27184, change: -0.24, spread: 1.5, low: 1.26820, high: 1.27608, digits: 5 },
  { symbol: "USD/JPY", desc: "US Dollar / Japanese Yen", icon: "¥", price: 149.620, change: 0.31, spread: 1.4, low: 149.180, high: 150.040, digits: 3 },
  { symbol: "USD/INR", desc: "US Dollar / Indian Rupee", icon: "₹", price: 83.4200, change: -0.08, spread: 2.0, low: 83.3100, high: 83.5800, digits: 4 },
  { symbol: "EUR/GBP", desc: "Euro / British Pound", icon: "€", price: 0.85264, change: 0.06, spread: 1.3, low: 0.85048, high: 0.85401, digits: 5 },
  { symbol: "AUD/USD", desc: "Australian Dollar / US Dollar", icon: "A$", price: 0.65841, change: -0.12, spread: 1.6, low: 0.65602, high: 0.66110, digits: 5 }
];

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const state = {
  instrument: instruments[0],
  timeframe: "15m",
  orderType: "market",
  activeTab: "positions",
  showMA: false,
  showMACD: true,
  balance: 10000,
  currentPrice: instruments[0].price,
  positions: [],
  pending: [],
  history: [],
  candles: []
};

const money = (n) => `$${Number(n).toLocaleString("en-US", {minimumFractionDigits:2, maximumFractionDigits:2})}`;
const fmtPrice = (n, item = state.instrument) => Number(n).toFixed(item.digits);
const pipSize = (item) => item.digits === 3 ? 0.01 : item.digits === 4 ? 0.0001 : 0.0001;
const escapeHtml = (value) => String(value).replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[char]));

function loadSavedState() {
  try {
    const saved = JSON.parse(localStorage.getItem("northstar-demo-state") || "null");
    if (saved && Number.isFinite(saved.balance) && Array.isArray(saved.positions) && Array.isArray(saved.history)) {
      state.balance = Math.max(0, saved.balance);
      const validTrade = item => item && typeof item.id === "string" && instruments.some(i=>i.symbol===item.symbol) && ["BUY","SELL"].includes(item.side) && Number.isFinite(item.lot) && item.lot>=.01 && item.lot<=5 && Number.isFinite(item.entry);
      state.positions = saved.positions.filter(validTrade);
      state.history = saved.history.filter(item=>validTrade(item)&&Number.isFinite(item.exit)&&Number.isFinite(item.pnl)).slice(0,50);
      state.pending = Array.isArray(saved.pending) ? saved.pending.filter(item=>validTrade({...item,entry:item.price})&&Number.isFinite(item.price)) : [];
    }
  } catch { /* Ignore damaged or unavailable browser storage. */ }
}

function saveState() {
  try {
    localStorage.setItem("northstar-demo-state", JSON.stringify({balance:state.balance,positions:state.positions,history:state.history,pending:state.pending}));
  } catch { showToast("Browser storage is unavailable; this session will not persist."); }
}

function renderWatchlist() {
  $("#marketList").innerHTML = instruments.map((item, index) => `
    <button class="market-row ${state.instrument.symbol === item.symbol ? "active" : ""}" data-market="${index}">
      <span class="pair-badge">${item.icon}</span><span class="pair-info"><b>${item.symbol}</b><small>${item.desc.split(" /")[0]}</small></span>
      <span class="pair-quote"><b>${fmtPrice(item.price,item)}</b><small class="${item.change >= 0 ? "positive" : "negative"}">${item.change >= 0 ? "+" : ""}${item.change.toFixed(2)}%</small></span>
    </button>`).join("");
  $$("[data-market]").forEach(button => button.addEventListener("click", () => selectInstrument(instruments[Number(button.dataset.market)])));
}

function selectInstrument(item) {
  state.instrument = item;
  state.currentPrice = item.price;
  $("#pairName").textContent = item.symbol.replace("/", " / ");
  $("#pairDesc").textContent = item.desc;
  $("#pairIcon").textContent = item.icon;
  $("#mainPrice").textContent = fmtPrice(item.price,item);
  $("#mainChange").textContent = `${item.change >= 0 ? "+" : ""}${item.change.toFixed(2)}%`;
  $("#mainChange").className = item.change >= 0 ? "positive" : "negative";
  $("#dayHigh").textContent = fmtPrice(item.high,item);
  $("#dayLow").textContent = fmtPrice(item.low,item);
  $("#spread").textContent = `${item.spread.toFixed(1)} pips`;
  $("#sellAction").textContent = `Sell ${item.symbol}`;
  $("#buyAction").textContent = `Buy ${item.symbol}`;
  $("#sellQuote").textContent = fmtPrice(item.price - item.spread * pipSize(item),item);
  $("#buyQuote").textContent = fmtPrice(item.price,item);
  $("#limitPrice").value = fmtPrice(item.price - pipSize(item) * 8,item);
  $("#tpPrice").value = fmtPrice(item.price + pipSize(item) * 25,item);
  $("#slPrice").value = fmtPrice(item.price - pipSize(item) * 15,item);
  renderWatchlist();
  makeCandles();
  drawChart();
  updateEstimate();
  renderTable();
}

function makeCandles() {
  const seedBase = Math.round(state.instrument.price * (state.instrument.digits === 3 ? 100 : 10000));
  let seed = seedBase + state.timeframe.length * 203 + state.timeframe.charCodeAt(0) * 57;
  const random = () => { seed = (seed * 9301 + 49297) % 233280; return seed / 233280; };
  const count = 60;
  let price = state.instrument.price * (1 - (random() - .5) * .006);
  state.candles = Array.from({length:count},(_,i) => {
    const move = (random() - .48) * state.instrument.price * .0015;
    const open = price;
    const close = Math.max(state.instrument.price * .985, Math.min(state.instrument.price * 1.015, open + move));
    const high = Math.max(open,close) + random() * state.instrument.price * .00045;
    const low = Math.min(open,close) - random() * state.instrument.price * .00045;
    const volume = 18 + Math.round(random() * 76);
    price = close;
    return {open,high,low,close,volume,index:i};
  });
}

function drawChart() {
  const canvas = $("#priceChart");
  if (!canvas) return;
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.round(rect.width * dpr));
  canvas.height = Math.max(1, Math.round(rect.height * dpr));
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr,0,0,dpr,0,0);
  const w=rect.width,h=rect.height, pad={l:12,r:60,t:16,b:22};
  const macdH=state.showMACD?54:0, volumeH=25, chartH=h-pad.t-pad.b-macdH-volumeH-8;
  const values=state.candles.flatMap(c=>[c.high,c.low]);
  const max=Math.max(...values), min=Math.min(...values), range=max-min || 1;
  const x0=pad.l, x1=w-pad.r, y0=pad.t, y1=pad.t+chartH;
  const xAt=i=>x0+(i+.5)*(x1-x0)/state.candles.length;
  const yAt=v=>y1-(v-min)/range*chartH;
  ctx.clearRect(0,0,w,h);
  ctx.font="9px DM Sans"; ctx.lineWidth=1;
  for(let k=0;k<=5;k++){
    const y=y0+k*(chartH/5); const val=max-k*(range/5);
    ctx.strokeStyle="#1b2838";ctx.beginPath();ctx.moveTo(x0,y);ctx.lineTo(x1,y);ctx.stroke();
    ctx.fillStyle="#8290a4";ctx.fillText(fmtPrice(val),x1+9,y+3);
  }
  const candleW=Math.max(2,Math.min(7,(x1-x0)/state.candles.length*.58));
  state.candles.forEach((c,i)=>{
    const x=xAt(i), up=c.close>=c.open, color=up?"#37d5a0":"#f36f7c";
    ctx.strokeStyle=color;ctx.fillStyle=color;ctx.lineWidth=1;
    ctx.beginPath();ctx.moveTo(x,yAt(c.high));ctx.lineTo(x,yAt(c.low));ctx.stroke();
    const top=yAt(Math.max(c.open,c.close)), bottom=yAt(Math.min(c.open,c.close));
    ctx.fillRect(x-candleW/2,top,candleW,Math.max(1,bottom-top));
  });
  if(state.showMA){
    ctx.strokeStyle="#efc976";ctx.lineWidth=1.4;ctx.beginPath();
    state.candles.forEach((c,i)=>{const start=Math.max(0,i-8);const avg=state.candles.slice(start,i+1).reduce((s,x)=>s+x.close,0)/(i-start+1);i===0?ctx.moveTo(xAt(i),yAt(avg)):ctx.lineTo(xAt(i),yAt(avg));});ctx.stroke();
  }
  const price=state.currentPrice, py=yAt(price);
  ctx.setLineDash([4,4]);ctx.strokeStyle="#3ac99d88";ctx.beginPath();ctx.moveTo(x0,py);ctx.lineTo(x1,py);ctx.stroke();ctx.setLineDash([]);
  ctx.fillStyle="#168565";ctx.fillRect(x1+2,py-9,pad.r-3,18);ctx.fillStyle="#fff";ctx.font="600 9px Space Grotesk";ctx.fillText(fmtPrice(price),x1+7,py+3);
  const vY=y1+8, maxVol=Math.max(...state.candles.map(c=>c.volume));
  state.candles.forEach((c,i)=>{ctx.fillStyle=c.close>=c.open?"#28624f88":"#63354188";const bh=c.volume/maxVol*volumeH;ctx.fillRect(xAt(i)-candleW/2,vY+volumeH-bh,candleW,bh);});
  ctx.fillStyle="#8290a4";ctx.font="9px DM Sans";ctx.fillText("09:00",x0,y1+volumeH+19);ctx.fillText("12:00",x0+(x1-x0)*.31,y1+volumeH+19);ctx.fillText("15:00",x0+(x1-x0)*.62,y1+volumeH+19);ctx.fillText("18:00",x1-31,y1+volumeH+19);
  if(state.showMACD){
    const my=y1+volumeH+31,mh=macdH-5,mid=my+mh/2;
    ctx.strokeStyle="#1b2838";ctx.beginPath();ctx.moveTo(x0,mid);ctx.lineTo(x1,mid);ctx.stroke();
    for(let i=0;i<state.candles.length;i++){
      const c=state.candles[i], prev=state.candles[Math.max(0,i-1)], diff=(c.close-prev.close)/state.instrument.price*mh*15;
      const bh=Math.min(mh/2-1,Math.abs(diff));ctx.fillStyle=diff>=0?"#3cc99a":"#ef6f7b";ctx.fillRect(xAt(i)-candleW/2,diff>=0?mid-bh:mid,candleW,Math.max(1,bh));
    }
    ctx.fillStyle="#94a1b3";ctx.fillText("MACD · DEMO",x0+2,my+9);
  }
}

function updateEstimate() {
  const lot=Math.max(0,Number($("#lotSize").value)||0);
  const notional=lot*100000*state.currentPrice;
  $("#estimatedValue").textContent=money(notional);
  $("#estimatedMargin").textContent=money(notional/50);
  $("#sellQuote").textContent=fmtPrice(state.currentPrice-state.instrument.spread*pipSize(state.instrument));
  $("#buyQuote").textContent=fmtPrice(state.currentPrice);
}

function updateBalances() {
  const floating=state.positions.reduce((sum,p)=>sum+positionPnl(p),0);
  $("#balanceValue").textContent=money(state.balance);
  $("#equityValue").textContent=money(state.balance+floating);
  $("#positionCount").textContent=state.positions.length;
  $("#pendingCount").textContent=state.pending.length;
}

function positionPnl(position) {
  const item=instruments.find(i=>i.symbol===position.symbol)||state.instrument;
  const current=state.instrument.symbol===position.symbol?state.currentPrice:item.price;
  const diff=position.side==="BUY"?current-position.entry:position.entry-current;
  return diff*position.lot*100000;
}

function renderTable() {
  const headers={
    positions:["PAIR","OPENED","SIDE","SIZE","ENTRY","CURRENT","STOP / TARGET","P&L","ACTION"],
    pending:["PAIR","CREATED","SIDE","SIZE","LIMIT PRICE","STATUS","ACTION"],
    history:["PAIR","CLOSED","SIDE","SIZE","ENTRY","EXIT","RESULT","TYPE"]
  };
  $("#tableHeader").innerHTML=headers[state.activeTab].map(x=>`<th>${x}</th>`).join("");
  let rows=[];
  if(state.activeTab==="positions") rows=state.positions.map(p=>{const pnl=positionPnl(p), item=instruments.find(i=>i.symbol===p.symbol)||state.instrument;return `<tr><td><b>${escapeHtml(p.symbol)}</b></td><td>${escapeHtml(p.opened)}</td><td class="${p.side==="BUY"?"positive":"negative"}">${p.side}</td><td>${p.lot.toFixed(2)}</td><td>${fmtPrice(p.entry,item)}</td><td>${fmtPrice(state.instrument.symbol===p.symbol?state.currentPrice:item.price,item)}</td><td>${p.sl?fmtPrice(p.sl,item):"—"} / ${p.tp?fmtPrice(p.tp,item):"—"}</td><td class="${pnl>=0?"positive":"negative"}">${money(pnl)}</td><td><button class="close-trade" data-close="${escapeHtml(p.id)}">Close</button></td></tr>`;});
  if(state.activeTab==="pending") rows=state.pending.map(p=>{const item=instruments.find(i=>i.symbol===p.symbol)||state.instrument;return `<tr><td><b>${escapeHtml(p.symbol)}</b></td><td>${escapeHtml(p.opened)}</td><td class="${p.side==="BUY"?"positive":"negative"}">${p.side}</td><td>${p.lot.toFixed(2)}</td><td>${fmtPrice(p.price,item)}</td><td>Waiting</td><td><button class="close-trade" data-cancel="${escapeHtml(p.id)}">Cancel</button></td></tr>`;});
  if(state.activeTab==="history") rows=state.history.map(p=>{const item=instruments.find(i=>i.symbol===p.symbol)||state.instrument;return `<tr><td><b>${escapeHtml(p.symbol)}</b></td><td>${escapeHtml(p.closed)}</td><td class="${p.side==="BUY"?"positive":"negative"}">${p.side}</td><td>${p.lot.toFixed(2)}</td><td>${fmtPrice(p.entry,item)}</td><td>${fmtPrice(p.exit,item)}</td><td class="${p.pnl>=0?"positive":"negative"}">${money(p.pnl)}</td><td>Paper</td></tr>`;});
  $("#tableBody").innerHTML=rows.join("");
  $("#emptyState").hidden=rows.length>0;
  $("#emptyTitle").textContent=state.activeTab==="positions"?"No open positions":state.activeTab==="pending"?"No pending orders":"No completed trades yet";
  $("#emptyState span").textContent=state.activeTab==="history"?"Closed practice trades will show here.":"Your practice trades will show here.";
  $$('[data-close]').forEach(b=>b.addEventListener("click",()=>closePosition(b.dataset.close)));
  $$('[data-cancel]').forEach(b=>b.addEventListener("click",()=>cancelPending(b.dataset.cancel)));
  updateBalances();
}

function createOrder(side) {
  const lot=Number($("#lotSize").value);
  if(!Number.isFinite(lot)||lot<.01||lot>5){showToast("Choose a demo size from 0.01 to 5 lots.");return;}
  const item=state.instrument;
  const entry=side==="BUY"?state.currentPrice:state.currentPrice-item.spread*pipSize(item);
  const tp=$("#tpEnabled").checked?Number($("#tpPrice").value):null;
  const sl=$("#slEnabled").checked?Number($("#slPrice").value):null;
  const now=new Date().toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"});
  if(state.orderType==="limit"){
    const price=Number($("#limitPrice").value);
    if(!Number.isFinite(price)||price<=0){showToast("Enter a valid limit price.");return;}
    state.pending.unshift({id:crypto.randomUUID(),symbol:item.symbol,side,lot,price,opened:now,tp,sl});
    state.activeTab="pending";showToast(`${side} limit order added to demo pending orders.`);
  }else{
    state.positions.unshift({id:crypto.randomUUID(),symbol:item.symbol,side,lot,entry,opened:now,tp,sl});
    state.activeTab="positions";showToast(`${side} ${item.symbol} opened in paper mode.`);
  }
  saveState();renderTabs();renderTable();
}

function closePosition(id) {
  const index=state.positions.findIndex(p=>p.id===id);if(index<0)return;
  const p=state.positions[index], exit=state.instrument.symbol===p.symbol?state.currentPrice:(instruments.find(i=>i.symbol===p.symbol)?.price||p.entry);
  const pnl=positionPnl(p);state.balance+=pnl;state.positions.splice(index,1);state.history.unshift({...p,exit,pnl,closed:new Date().toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"})});
  saveState();renderTable();showToast(`Position closed. Demo result: ${pnl>=0?"+":""}${money(pnl)}.`);
}

function cancelPending(id) {state.pending=state.pending.filter(p=>p.id!==id);saveState();renderTable();showToast("Demo order cancelled.");}
function showToast(message){const toast=$("#toast");toast.textContent=message;toast.classList.add("show");clearTimeout(showToast.timer);showToast.timer=setTimeout(()=>toast.classList.remove("show"),2600);}

function renderTabs(){
  $$(".bottom-tabs button[data-tab]").forEach(button=>{button.classList.toggle("active",button.dataset.tab===state.activeTab);button.onclick=()=>{state.activeTab=button.dataset.tab;renderTabs();renderTable();};});
}

function bindControls(){
  $$("#timeframes button").forEach(button=>button.addEventListener("click",()=>{$$("#timeframes button").forEach(b=>b.classList.remove("selected"));button.classList.add("selected");state.timeframe=button.textContent;makeCandles();drawChart();}));
  $$(".order-tabs button").forEach(button=>button.addEventListener("click",()=>{$$(".order-tabs button").forEach(b=>b.classList.remove("selected"));button.classList.add("selected");state.orderType=button.dataset.order;$("#limitPriceWrap").hidden=state.orderType!=="limit";}));
  $$(".quick-sizes button").forEach(button=>button.addEventListener("click",()=>{$$(".quick-sizes button").forEach(b=>b.classList.remove("active"));button.classList.add("active");$("#lotSize").value=button.dataset.size;updateEstimate();}));
  $("#lotSize").addEventListener("input",updateEstimate);
  $("#lotDown").addEventListener("click",()=>{const input=$("#lotSize");input.value=Math.max(.01,(Number(input.value)||.01)-.01).toFixed(2);updateEstimate();});
  $("#lotUp").addEventListener("click",()=>{const input=$("#lotSize");input.value=Math.min(5,(Number(input.value)||.01)+.01).toFixed(2);updateEstimate();});
  [["tpEnabled","tpPriceWrap"],["slEnabled","slPriceWrap"]].forEach(([check,wrap])=>$("#"+check).addEventListener("change",e=>$("#"+wrap).hidden=!e.target.checked));
  $("#buyButton").addEventListener("click",()=>createOrder("BUY"));$("#buyAction").addEventListener("click",()=>createOrder("BUY"));
  $("#sellButton").addEventListener("click",()=>createOrder("SELL"));$("#sellAction").addEventListener("click",()=>createOrder("SELL"));
  $("#maToggle").addEventListener("click",()=>{state.showMA=!state.showMA;$("#maToggle").classList.toggle("active",state.showMA);drawChart();});
  $("#macdToggle").addEventListener("click",()=>{state.showMACD=!state.showMACD;$("#macdToggle").classList.toggle("active",state.showMACD);drawChart();});
  $("#fullscreenToggle").addEventListener("click",()=>$(".chart-card").requestFullscreen?.());
  $("#dismissNotice").addEventListener("click",()=>$(".notice-bar").remove());
  $("#resetDemo").addEventListener("click",()=>{if(!window.confirm("Reset the virtual balance, positions, pending orders, and history?"))return;state.balance=10000;state.positions=[];state.pending=[];state.history=[];saveState();renderTable();showToast("Demo account reset to $10,000.");});
  $("#chartTooltip").textContent="Illustrative price series · no live feed";
  $("#priceChart").addEventListener("pointermove",e=>{
    const rect=e.currentTarget.getBoundingClientRect(), i=Math.max(0,Math.min(state.candles.length-1,Math.floor((e.clientX-rect.left)/rect.width*state.candles.length))),c=state.candles[i];
    $("#chartTooltip").textContent=`O ${fmtPrice(c.open)}  H ${fmtPrice(c.high)}  L ${fmtPrice(c.low)}  C ${fmtPrice(c.close)}`;
  });
  $("#priceChart").addEventListener("pointerleave",()=>$("#chartTooltip").textContent="Illustrative price series · no live feed");
  window.addEventListener("resize",drawChart);
}

loadSavedState();renderWatchlist();renderTabs();bindControls();makeCandles();drawChart();updateEstimate();renderTable();

// A visible demo ticker makes the simulator interactive; it is deliberately not market data.
setInterval(()=>{
  const step=(Math.random()-.49)*state.instrument.price*.000035;
  state.currentPrice=Math.max(.00001,state.currentPrice+step);
  $("#mainPrice").textContent=fmtPrice(state.currentPrice);
  state.candles[state.candles.length-1].close=state.currentPrice;
  state.candles[state.candles.length-1].high=Math.max(state.candles[state.candles.length-1].high,state.currentPrice);
  state.candles[state.candles.length-1].low=Math.min(state.candles[state.candles.length-1].low,state.currentPrice);
  drawChart();updateEstimate();updateBalances();
  if(state.positions.length)renderTable();
},2200);
