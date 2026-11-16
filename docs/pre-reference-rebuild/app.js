'use strict';
const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money = v => Number(v || 0).toLocaleString('en-US',{style:'currency',currency:'USD'});
const price = v => v === null || v === undefined ? '—' : Number(v).toFixed(5);
const date = v => v ? new Date(v * 1000).toLocaleString([], {month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}) : '—';
const signed = v => `${Number(v) >= 0 ? '+' : '−'}${money(Math.abs(Number(v)))}`;
const tone = v => Number(v) >= 0 ? 'positive' : 'negative';
const state = {data:null, symbol:'EURUSD', interval:15, candles:[], page:'terminal', side:'buy', kind:'market',
  ledger:'open', ma:true, macd:false, authMode:'login', busy:false, polling:false, connected:false, chartSequence:0,
  favorites:[], filter:'all', reportOrders:null, reportAccount:'', dialogAction:null};
try { state.favorites = JSON.parse(localStorage.getItem('northstar-favorites') || '[]'); if (!Array.isArray(state.favorites)) state.favorites=[]; } catch {}

async function api(path, data, key) {
  let response;
  try {
    response = await fetch(path, {credentials:'same-origin', headers:data ? {'Content-Type':'application/json','X-Northstar-Request':'1', ...(key ? {'Idempotency-Key':key} : {})} : {},
      method:data ? 'POST' : 'GET', body:data ? JSON.stringify(data) : undefined, signal:AbortSignal.timeout(10000)});
  } catch {
    const e = new Error(data ? 'Connection interrupted. Retry this same action to safely check its result.' : 'Cannot reach the local server. Check that it is running.');
    e.network = true; throw e;
  }
  const result = await response.json();
  if (!response.ok) {
    if (response.status === 401 && state.data) showAuth();
    const error = new Error(result.error || 'Request failed.'); error.status=response.status; throw error;
  }
  return result;
}
function toast(text,error=false){const el=$('#toast');el.textContent=text;el.classList.toggle('error',error);el.hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>el.hidden=true,5500);}
function showAuth(){state.reportOrders=null;state.reportAccount='';state.data=null;state.connected=false;$('#appScreen').hidden=true;$('#authScreen').hidden=false;$('#actionDialog').close();}
function authMode(mode){state.authMode=mode;$('#nameField').hidden=mode==='login';$('#authName').required=mode==='register';$('#loginTab').classList.toggle('selected',mode==='login');$('#registerTab').classList.toggle('selected',mode==='register');$('#authTitle').textContent=mode==='login'?'Welcome back.':'Make room to learn.';$('#authDescription').textContent=mode==='login'?'Sign in to your practice workspace.':'Start with $10,000 in virtual funds.';$('#authSubmit').textContent=mode==='login'?'Sign in →':'Create practice account →';$('#authPassword').autocomplete=mode==='login'?'current-password':'new-password';$('#authError').textContent='';}
$('#loginTab').onclick=()=>authMode('login');$('#registerTab').onclick=()=>authMode('register');
$('#authForm').onsubmit=async event=>{event.preventDefault();const button=$('#authSubmit');button.disabled=true;$('#authError').textContent='';try{await api(`/api/auth/${state.authMode}`,{name:$('#authName').value,email:$('#authEmail').value,password:$('#authPassword').value});$('#authPassword').value='';await refresh(true);navigate('terminal');}catch(e){$('#authError').textContent=e.message;}finally{button.disabled=false;}};

function market(){return state.data?.markets.find(m=>m.id===state.symbol);}
function healthy(){return state.connected && market() && Date.now()/1000-market().updated<5;}
function connection(){const ok=healthy();$('#connectionText').textContent=ok?'Simulator connected':'Connection unavailable · trading paused';$('#connectionDot').classList.toggle('offline',!ok);$('#reviewOrder').disabled=!ok||state.busy;}
async function refresh(initial=false){
  if(state.polling)return;state.polling=true;
  try {
    const data=await api('/api/state');const previous=state.data?.account.id;state.data=data;state.connected=true;
    $('#authScreen').hidden=true;$('#appScreen').hidden=false;
    if(previous&&previous!==data.account.id){clearTicket();if($('#actionDialog').open)$('#actionDialog').close();toast('Account changed. Your order ticket has been cleared.');}
    render();
    if(initial||!state.candles.length)await loadChart();
    else if(state.page==='terminal')await loadChart(false);
  }catch(e){state.connected=false;if(e.status===401)showAuth();else if(initial)throw e;}
  finally{state.polling=false;if(state.data)connection();}
}
function navigate(page){if(!['terminal','dashboard','reports','account'].includes(page))page='terminal';state.page=page;for(const p of ['terminal','dashboard','reports','account'])$(`#${p}Page`).hidden=p!==page;$$('[data-page]').forEach(b=>b.classList.toggle('active',b.dataset.page===page));history.replaceState(null,'',`#${page}`);if(page==='terminal'){requestAnimationFrame(drawChart);loadChart();}if(page==='reports')loadReport();}
$$('[data-page]').forEach(b=>b.onclick=()=>navigate(b.dataset.page));$('#profileButton').onclick=()=>navigate('account');$('.topbar .brand').onclick=e=>{e.preventDefault();navigate('terminal');};
function clearTicket(){state.side='buy';state.kind='market';$('#lots').value='0.01';$('#useSL').checked=false;$('#useTP').checked=false;$('#stopLoss').hidden=true;$('#takeProfit').hidden=true;$('#stopLoss').value='';$('#takeProfit').value='';$('#limitPrice').value='';renderTicket();}
function render(){
  const {data}=state;const {totals:t,user,account}=data;const m=market();
  $('#profileButton').textContent=user.name.slice(0,1).toUpperCase();$('#ticketAccount').textContent=`#${account.id.slice(0,8).toUpperCase()}`;
  $('#pairName').textContent=m.symbol;$('#pairDescription').textContent=m.name;$('#pairIcon').textContent=m.icon;$('#mainPrice').textContent=price(m.bid);$('#mainChange').textContent=`${m.change>=0?'+':''}${m.change.toFixed(2)}% today`;$('#mainChange').className=tone(m.change);
  for(const [id,value] of Object.entries({balanceValue:t.balance,equityValue:t.equity,pnlValue:t.unrealized,usedMarginValue:t.used_margin,freeMarginValue:t.free_margin,dashboardBalance:t.balance}))$('#'+id).textContent=money(value);
  $('#pnlValue').className=tone(t.unrealized);$('#serverClock').textContent=new Date(data.server_time*1000).toLocaleTimeString('en-GB',{timeZone:'UTC'})+' UTC';
  $('#openCount').textContent=data.orders.filter(o=>o.status==='open').length;$('#pendingCount').textContent=data.orders.filter(o=>o.status==='pending').length;
  renderMarkets();renderTicket();renderLedger();renderDashboard();renderAccount();
  if(state.page==='reports'&&!state.reportAccount)renderReport();connection();
}
function patchHTML(target, markup) {
  const template=document.createElement('template');template.innerHTML=markup;
  function sync(parent, source) {
    const desired=[...source.childNodes];
    desired.forEach((next,index)=>{
      const current=parent.childNodes[index];
      if(!current){parent.append(next.cloneNode(true));return;}
      if(current.nodeType!==next.nodeType || current.nodeName!==next.nodeName){current.replaceWith(next.cloneNode(true));return;}
      if(current.nodeType===Node.TEXT_NODE){if(current.nodeValue!==next.nodeValue)current.nodeValue=next.nodeValue;return;}
      if(current.nodeType===Node.ELEMENT_NODE){
        for(const attr of [...current.attributes])if(!next.hasAttribute(attr.name))current.removeAttribute(attr.name);
        for(const attr of [...next.attributes])if(current.getAttribute(attr.name)!==attr.value)current.setAttribute(attr.name,attr.value);
        sync(current,next);
      }
    });
    while(parent.childNodes.length>desired.length)parent.lastChild.remove();
  }
  sync(target,template.content);
}
function renderMarkets(){
  const search=$('#marketSearch').value.toLowerCase();const items=state.data.markets.filter(m=>(m.symbol+' '+m.name).toLowerCase().includes(search)&&(state.filter!=='favorites'||state.favorites.includes(m.id)));
  patchHTML($('#marketList'),items.map(m=>`<div class="market-row ${m.id===state.symbol?'active':''}"><button class="favorite-button ${state.favorites.includes(m.id)?'starred':''}" data-favorite="${m.id}" aria-label="${state.favorites.includes(m.id)?'Remove':'Add'} ${m.symbol} ${state.favorites.includes(m.id)?'from':'to'} favorites">${state.favorites.includes(m.id)?'★':'☆'}</button><button class="market-select" data-symbol="${m.id}"><span><b>${m.symbol}</b><small>${m.name.split(' /')[0]}</small></span><span class="market-price"><b>${price(m.bid)}</b><small class="${tone(m.change)}">${m.change>=0?'+':''}${m.change.toFixed(2)}%</small></span></button></div>`).join('')||'<div class="empty-state">No matching instruments.</div>');
}
$('#marketSearch').oninput=renderMarkets;
$('#marketList').onclick=e=>{const favorite=e.target.closest('[data-favorite]');if(favorite){const id=favorite.dataset.favorite;state.favorites=state.favorites.includes(id)?state.favorites.filter(x=>x!==id):[...state.favorites,id];try{localStorage.setItem('northstar-favorites',JSON.stringify(state.favorites));}catch{}renderMarkets();return;}const b=e.target.closest('[data-symbol]');if(b){state.symbol=b.dataset.symbol;clearTicket();state.candles=[];render();loadChart();}};
$$('[data-filter]').forEach(b=>b.onclick=()=>{state.filter=b.dataset.filter;$$('[data-filter]').forEach(x=>x.classList.toggle('selected',x===b));renderMarkets();});

function reference(){const m=market();return state.kind==='limit'?Number($('#limitPrice').value):Number(state.side==='buy'?m?.ask:m?.bid);}
function renderTicket(){
  if(!state.data)return;const m=market();$('#sellQuote').textContent=price(m.bid);$('#buyQuote').textContent=price(m.ask);$('#spreadValue').textContent=(m.spread/10).toFixed(1);
  $('#sellQuoteButton').classList.toggle('selected',state.side==='sell');$('#buyQuoteButton').classList.toggle('selected',state.side==='buy');
  $$('[data-kind]').forEach(b=>b.classList.toggle('selected',b.dataset.kind===state.kind));$('#limitField').hidden=state.kind!=='limit';$('#limitPrice').required=state.kind==='limit';
  const lots=Number($('#lots').value),entry=reference(),notional=entry*lots*100000;
  $('#notionalValue').textContent=Number.isFinite(notional)?money(notional):'—';$('#marginValue').textContent=Number.isFinite(notional)?money(notional/20):'—';
  $('#reviewOrder').textContent=`Review ${state.side} order →`;$('#reviewOrder').classList.toggle('sell',state.side==='sell');
  const parts=[];for(const [checked,input,label]of [['useSL','stopLoss','SL'],['useTP','takeProfit','TP']]){if($('#'+checked).checked&&Number($('#'+input).value)>0){const pnl=(Number($('#'+input).value)-entry)*lots*100000*(state.side==='buy'?1:-1);parts.push(`${label}: ${signed(pnl)}`);}}
  $('#riskPreview').textContent=parts.join(' · ');
}
function selectSide(side){state.side=side;defaultProtection();renderTicket();}
function defaultProtection(){const entry=reference();if(!entry)return;const sign=state.side==='buy'?1:-1;if($('#useSL').checked)$('#stopLoss').value=price(entry-.0015*sign);if($('#useTP').checked)$('#takeProfit').value=price(entry+.0025*sign);}
$('#sellQuoteButton').onclick=()=>selectSide('sell');$('#buyQuoteButton').onclick=()=>selectSide('buy');
$$('[data-kind]').forEach(b=>b.onclick=()=>{state.kind=b.dataset.kind;if(state.kind==='limit'){const m=market();$('#limitPrice').value=price(Number(state.side==='buy'?m.ask:m.bid)+(state.side==='buy'?-.001:.001));}defaultProtection();renderTicket();});
$$('[data-size]').forEach(b=>b.onclick=()=>{$('#lots').value=b.dataset.size;renderTicket();});
for(const id of ['lots','limitPrice','stopLoss','takeProfit'])$('#'+id).oninput=renderTicket;
for(const [id,target]of [['useSL','stopLoss'],['useTP','takeProfit']])$('#'+id).onchange=()=>{$('#'+target).hidden=!$('#'+id).checked;$('#'+target).required=$('#'+id).checked;defaultProtection();renderTicket();};
function dialog(title,body,action,label='Confirm'){state.dialogAction=action;$('#dialogTitle').textContent=title;$('#dialogBody').innerHTML=body;$('#dialogError').textContent='';$('#dialogConfirm').textContent=label;$('#dialogConfirm').hidden=!action;$('#dialogCancel').textContent=action?'Cancel':'Close';$('#dialogConfirm').disabled=false;$('#actionDialog').showModal();}
$('#dialogCancel').onclick=()=>$('#actionDialog').close();
$('#dialogConfirm').onclick=async()=>{const button=$('#dialogConfirm');if(!state.dialogAction||state.busy)return;state.busy=true;button.disabled=true;$('#dialogError').textContent='';try{await state.dialogAction();$('#actionDialog').close();await refresh();}catch(e){$('#dialogError').textContent=e.message;}finally{state.busy=false;button.disabled=false;connection();}};
function mutation(path,payload,message){const key=crypto.randomUUID();return async()=>{const result=await api(path,payload,key);toast(message);return result;};}
$('#orderForm').onsubmit=e=>{e.preventDefault();if(!healthy())return toast('Wait for the simulator to reconnect.',true);const m=market();const payload={account_id:state.data.account.id,symbol:state.symbol,side:state.side,kind:state.kind,lots:$('#lots').value,limit_price:state.kind==='limit'?$('#limitPrice').value:null,sl:$('#useSL').checked?$('#stopLoss').value:null,tp:$('#useTP').checked?$('#takeProfit').value:null};
  if(!reference())return toast('Enter a valid price.',true);
  dialog(`${state.side==='buy'?'Buy':'Sell'} ${m.symbol}`,`<p>Review your simulated order. Market execution uses the current server quote when confirmed.</p><dl><dt>Account</dt><dd>Paper #${state.data.account.id.slice(0,8)}</dd><dt>Order</dt><dd>${state.kind==='market'?'Market':'Limit'} · ${esc(payload.lots)} lots</dd><dt>${state.kind==='market'?'Indicative price':'Limit price'}</dt><dd>${price(reference())}</dd><dt>Estimated margin</dt><dd>${money(reference()*Number(payload.lots)*100000/20)}</dd><dt>Stop loss / take profit</dt><dd>${price(payload.sl)} / ${price(payload.tp)}</dd><dt>Fees / swap</dt><dd>$0.00 simulated</dd></dl><p>1:20 practice leverage. Prices and fills are generated; no real order will be sent.</p>`,mutation('/api/orders',payload,'Practice order accepted.'),'Confirm paper order');};
function empty(title,description){return `<div class="empty-state"><span class="empty-icon">↗</span><b>${title}</b><span>${description}</span></div>`;}
function table(orders,actions=false){if(!orders.length)return empty('A fresh perspective','Your trades will appear here. Start with a small practice order.');return `<table><thead><tr><th>INSTRUMENT / TIME</th><th>SIDE / LOTS</th><th>ENTRY / LIMIT</th><th>MARK / EXIT</th><th>SL / TP</th><th>P&L (USD)</th><th>STATUS</th>${actions?'<th>ACTION</th>':''}</tr></thead><tbody>${orders.map(o=>`<tr><td><b>${o.symbol==='EURUSD'?'EUR/USD':'GBP/USD'}</b><span class="small muted">${date(o.closed||o.opened||o.created)}</span></td><td><span class="${o.side==='buy'?'positive':'negative'}">${o.side.toUpperCase()}</span><span class="small muted">${Number(o.lots).toFixed(2)} lots</span></td><td>${price(o.entry||o.limit_price)}</td><td>${price(o.exit||o.mark)}</td><td>${price(o.sl)}<span class="small muted">${price(o.tp)}</span></td><td class="${tone(o.pnl||o.unrealized||0)}">${o.status==='closed'||o.status==='open'?signed(o.pnl||o.unrealized||0):'—'}</td><td>${o.status}<span class="small muted">${esc(o.reason||o.kind)}</span></td>${actions?`<td>${o.status==='open'?`<button class="row-action" data-risk="${o.id}">SL/TP</button><button class="row-action" data-close="${o.id}">Close</button>`:o.status==='pending'?`<button class="row-action" data-cancel="${o.id}">Cancel</button>`:'—'}</td>`:''}</tr>`).join('')}</tbody></table>`;}
function renderLedger(){const items=state.data.orders.filter(o=>state.ledger==='history'?['closed','cancelled','rejected'].includes(o.status):o.status===state.ledger);patchHTML($('#tradeTable'),table(items,true));}
$$('[data-ledger]').forEach(b=>b.onclick=()=>{state.ledger=b.dataset.ledger;$$('[data-ledger]').forEach(x=>x.classList.toggle('active',x===b));renderLedger();});
$('#tradeTable').onclick=e=>{const b=e.target.closest('[data-close],[data-cancel],[data-risk]');if(!b)return;const id=b.dataset.close||b.dataset.cancel||b.dataset.risk;const o=state.data.orders.find(x=>x.id===id);if(!o)return;const base={account_id:state.data.account.id,id};
  if(b.dataset.risk){const key=crypto.randomUUID();let pendingPayload=null;dialog('Position protection',`<p>Levels use the current closing quote as reference. Minimum distance: 0.00020. Leave blank to remove a level.</p><label for="editSL">Stop loss</label><input id="editSL" type="number" step="0.00001" value="${esc(o.sl||'')}"><label for="editTP">Take profit</label><input id="editTP" type="number" step="0.00001" value="${esc(o.tp||'')}">`,async()=>{pendingPayload=pendingPayload||{...base,sl:$('#editSL').value||null,tp:$('#editTP').value||null};try{await api('/api/positions/risk',pendingPayload,key);toast('Position protection updated.');}catch(err){if(!err.network)pendingPayload=null;throw err;}},'Save protection');
  }else{const closing=!!b.dataset.close;dialog(closing?'Close practice position?':'Cancel pending order?',`<p>${o.side.toUpperCase()} ${esc(o.lots)} lots · ${o.symbol==='EURUSD'?'EUR/USD':'GBP/USD'}</p><dl><dt>${closing?'Current estimated P&L':'Order status'}</dt><dd>${closing?signed(o.unrealized):'Pending'}</dd></dl><p>${closing?'The server will close at the next available executable quote. Your actual result may change.':'If the order fills before cancellation is processed, the server will report the new status.'}</p>`,mutation(closing?'/api/positions/close':'/api/orders/cancel',base,closing?'Position closed.':'Pending order cancelled.'),closing?'Close position':'Cancel order');}};

function renderDashboard(){const d=state.data,t=d.totals,closed=d.orders.filter(o=>o.status==='closed'),realized=closed.reduce((s,o)=>s+Number(o.pnl),0);$('#greeting').textContent=`Good to see you, ${d.user.name.split(' ')[0]}.`;$('#dashboardStats').innerHTML=[['Account equity',money(t.equity),'Balance + unrealized P&L'],['Unrealized P&L',signed(t.unrealized),'Current open positions',tone(t.unrealized)],['Realized P&L',signed(realized),`${closed.length} completed trades`,tone(realized)],['Free margin',money(t.free_margin),'Available for new orders']].map(([label,value,detail,cls])=>`<div class="stat-card"><span>${label}</span><b class="${cls||''}">${value}</b><small>${detail}</small></div>`).join('');$('#activityList').innerHTML=d.events.slice(0,6).map(e=>`<div class="activity-item"><span>↗</span><div><p>${esc(e.message)}</p><small>${date(e.created)}</small></div></div>`).join('');}
function renderAccount(){const d=state.data;$('#profileDetails').innerHTML=`<dt>Name</dt><dd>${esc(d.user.name)}</dd><dt>Email</dt><dd>${esc(d.user.email)}</dd><dt>Verification</dt><dd>Local / unverified</dd><dt>Session lifetime</dt><dd>7 days</dd>`;$('#accountDetails').innerHTML=`<dt>Account</dt><dd>#${d.account.id.slice(0,8).toUpperCase()}</dd><dt>Mode</dt><dd>Paper Standard</dd><dt>Currency</dt><dd>USD</dd><dt>Balance</dt><dd>${money(d.totals.balance)}</dd><dt>Archived accounts</dt><dd>${d.archives.length}</dd>`;
  const select=$('#reportAccount');const wanted=state.reportAccount;const options=[{id:'',name:'Current practice account'},...d.archives.map((a,i)=>({id:a.id,name:`Archived ${date(a.archived)} · #${a.id.slice(0,6)}`}))];const signature=options.map(o=>o.id).join(',');if(select.dataset.signature!==signature){select.innerHTML=options.map(o=>`<option value="${o.id}">${esc(o.name)}</option>`).join('');select.dataset.signature=signature;select.value=wanted;}}
$('#signOut').onclick=async()=>{try{await api('/api/auth/logout',{});showAuth();toast('Signed out. Your practice account is saved.');}catch(e){toast(e.message,true);}};
$('#resetAccount').onclick=()=>dialog('Start a fresh account?',`<p>Your open positions will close at current simulated prices and pending orders will be cancelled. This account and its history will be archived in Reports.</p><dl><dt>New virtual balance</dt><dd>$10,000.00</dd><dt>Real funds affected</dt><dd>None</dd></dl>`,mutation('/api/accounts/reset',{account_id:state.data.account.id},'New practice account created.'),'Archive & start fresh');
async function loadReport(){const requested=state.reportAccount;$('#reportExport').href='/api/statement.csv'+(requested?'?account='+encodeURIComponent(requested):'');if(requested){try{const result=await api('/api/history?account='+encodeURIComponent(requested));if(requested!==state.reportAccount)return;state.reportOrders=result.orders;}catch(e){toast(e.message,true);return;}}else state.reportOrders=null;renderReport();}
function renderReport(){const orders=(state.reportOrders||state.data.orders).filter(o=>($('#reportSymbol').value==='all'||o.symbol===$('#reportSymbol').value)&&($('#reportStatus').value==='all'||o.status===$('#reportStatus').value));const net=orders.reduce((s,o)=>s+Number(o.pnl||0),0);$('#reportSummary').textContent=`${orders.length} orders · Realized net P&L ${signed(net)} · USD · ${Intl.DateTimeFormat().resolvedOptions().timeZone} display time · CSV timestamps in UTC`;patchHTML($('#reportTable'),table(orders));}
$('#reportAccount').onchange=()=>{state.reportAccount=$('#reportAccount').value;loadReport();};$('#reportSymbol').onchange=renderReport;$('#reportStatus').onchange=renderReport;
$('#specButton').onclick=()=>{const m=market();dialog(`${m.symbol} specifications`,`<p>${m.name} · Generated practice prices</p><dl><dt>Contract size</dt><dd>100,000 base units / lot</dd><dt>Order size</dt><dd>0.01–1.00 lots</dd><dt>Size increment</dt><dd>0.01 lot</dd><dt>Spread</dt><dd>${m.spread/10} pips</dd><dt>Leverage</dt><dd>1:20 simulated</dd><dt>SL/TP min. distance</dt><dd>0.00020</dd><dt>Fees / swap</dt><dd>$0.00</dd><dt>Margin stop-out</dt><dd>50% of used margin</dd></dl><p>Long positions open at ask and close at bid. Short positions open at bid and close at ask. This simulator runs continuously while the local server is running.</p>`,null);};

async function loadChart(showLoading=true){if(!state.data)return;const sequence=++state.chartSequence;const symbol=state.symbol,interval=state.interval;try{const candles=await api(`/api/candles?symbol=${symbol}&interval=${interval}`);if(sequence!==state.chartSequence)return;state.candles=candles;$('#chartMessage').hidden=true;drawChart();}catch(e){if(sequence!==state.chartSequence)return;if(showLoading){$('#chartMessage').textContent='Chart unavailable. Reconnecting…';$('#chartMessage').hidden=false;}}}
$$('[data-interval]').forEach(b=>b.onclick=()=>{state.interval=Number(b.dataset.interval);$$('[data-interval]').forEach(x=>x.classList.toggle('selected',x===b));state.candles=[];drawChart();loadChart();});
for(const [id,field]of [['maToggle','ma'],['macdToggle','macd']])$('#'+id).onclick=()=>{state[field]=!state[field];$('#'+id).classList.toggle('selected',state[field]);$('#'+id).setAttribute('aria-pressed',String(state[field]));drawChart();};
$('#fullscreenButton').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await $('.chart-card').requestFullscreen();}catch{toast('Fullscreen is unavailable in this browser.',true);}};
function ema(values,period){const alpha=2/(period+1);let prev=values[0];return values.map(v=>(prev=alpha*v+(1-alpha)*prev));}
function drawChart(){
  if(state.page!=='terminal'||!state.data)return;const canvas=$('#priceChart'),rect=canvas.getBoundingClientRect();if(!rect.width||!rect.height)return;const dpr=devicePixelRatio||1;canvas.width=Math.round(rect.width*dpr);canvas.height=Math.round(rect.height*dpr);const ctx=canvas.getContext('2d');ctx.scale(dpr,dpr);const w=rect.width,h=rect.height;ctx.clearRect(0,0,w,h);const candles=state.candles;if(!candles.length)return;
  const pad={l:12,r:62,t:18,b:28},macdHeight=state.macd?75:0,chartHeight=h-pad.t-pad.b-macdHeight;const rawMin=Math.min(...candles.map(c=>c.low)),rawMax=Math.max(...candles.map(c=>c.high));const extra=Math.max((rawMax-rawMin)*.12,.0001),min=rawMin-extra,max=rawMax+extra;const plotW=w-pad.l-pad.r,step=plotW/candles.length;const x=i=>pad.l+(i+.5)*step,y=v=>pad.t+(max-v)/(max-min)*chartHeight;
  ctx.font='9px -apple-system, sans-serif';ctx.lineWidth=1;for(let i=0;i<=5;i++){const val=max-(max-min)*i/5,yy=y(val);ctx.strokeStyle='#21303b';ctx.beginPath();ctx.moveTo(pad.l,yy);ctx.lineTo(w-pad.r,yy);ctx.stroke();ctx.fillStyle='#7c8d9d';ctx.fillText(price(val),w-pad.r+8,yy+3);}
  candles.forEach((c,i)=>{ctx.strokeStyle=ctx.fillStyle=c.close>=c.open?'#56c9a6':'#de7885';ctx.beginPath();ctx.moveTo(x(i),y(c.high));ctx.lineTo(x(i),y(c.low));ctx.stroke();ctx.fillRect(x(i)-Math.max(1,step*.3),y(Math.max(c.open,c.close)),Math.max(1,step*.6),Math.max(1,Math.abs(y(c.close)-y(c.open))));});
  if(state.ma){ctx.strokeStyle='#e0bc75';ctx.lineWidth=1.25;ctx.beginPath();candles.forEach((c,i)=>{const avg=candles.slice(Math.max(0,i-8),i+1).reduce((s,v)=>s+v.close,0)/Math.min(i+1,9);i?ctx.lineTo(x(i),y(avg)):ctx.moveTo(x(i),y(avg));});ctx.stroke();}
  const last=candles[candles.length-1];ctx.setLineDash([3,4]);ctx.strokeStyle='#56d6b088';ctx.beginPath();ctx.moveTo(pad.l,y(last.close));ctx.lineTo(w-pad.r,y(last.close));ctx.stroke();ctx.setLineDash([]);ctx.fillStyle='#266e59';ctx.fillRect(w-pad.r,y(last.close)-9,60,18);ctx.fillStyle='#d7fff1';ctx.fillText(price(last.close),w-pad.r+6,y(last.close)+3);
  for(let i=0;i<5;i++){const index=Math.floor(i*(candles.length-1)/4);ctx.fillStyle='#7c8d9d';ctx.fillText(new Date(candles[index].time*1000).toLocaleTimeString('en-GB',{timeZone:'UTC',hour:'2-digit',minute:'2-digit'}),Math.min(w-pad.r-30,Math.max(12,x(index)-15)),h-9);}
  if(state.macd){const closes=candles.map(c=>c.close),fast=ema(closes,12),slow=ema(closes,26),macd=fast.map((v,i)=>v-slow[i]),signal=ema(macd,9),hist=macd.map((v,i)=>v-signal[i]),extent=Math.max(...macd.map(Math.abs),...signal.map(Math.abs),.00001),mid=h-pad.b-macdHeight/2;ctx.strokeStyle='#21303b';ctx.beginPath();ctx.moveTo(pad.l,mid);ctx.lineTo(w-pad.r,mid);ctx.stroke();hist.forEach((v,i)=>{ctx.fillStyle=v>=0?'#419e85':'#ab5f6d';const height=v/extent*(macdHeight/2-10);ctx.fillRect(x(i)-step*.3,Math.min(mid,mid-height),Math.max(1,step*.6),Math.max(1,Math.abs(height)));});for(const [values,color]of [[macd,'#d9bd78'],[signal,'#87b9e7']]){ctx.strokeStyle=color;ctx.beginPath();values.forEach((v,i)=>i?ctx.lineTo(x(i),mid-v/extent*(macdHeight/2-10)):ctx.moveTo(x(i),mid-v/extent*(macdHeight/2-10)));ctx.stroke();}ctx.fillStyle='#8195a8';ctx.fillText('MACD 12 26 9',16,h-pad.b-macdHeight+10);}
  $('#chartOHLC').textContent=`O ${price(last.open)}  H ${price(last.high)}  L ${price(last.low)}  C ${price(last.close)}`;$('#candleTime').textContent=`${state.interval} MIN · UTC`;
}
$('#priceChart').onpointermove=e=>{if(!state.candles.length)return;const r=e.currentTarget.getBoundingClientRect(),index=Math.max(0,Math.min(state.candles.length-1,Math.floor((e.clientX-r.left-12)/(r.width-74)*state.candles.length))),c=state.candles[index];$('#chartOHLC').textContent=`O ${price(c.open)}  H ${price(c.high)}  L ${price(c.low)}  C ${price(c.close)}`;};
new ResizeObserver(()=>requestAnimationFrame(drawChart)).observe($('.canvas-wrap'));
setInterval(()=>{if(state.data)refresh();},1500);
setInterval(()=>{if(state.data)connection();},1000);
refresh(true).then(()=>{if(state.data)navigate(location.hash.slice(1)||'terminal');}).catch(e=>{$('#authError').textContent=e.message;});
