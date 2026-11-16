from docx import Document
from docx.shared import Inches,Pt,RGBColor
from pathlib import Path
import re
root=Path(__file__).parent
d=Document(); sec=d.sections[0]; sec.top_margin=sec.bottom_margin=Inches(.7)
for n in ['Normal','Title','Heading 1','Heading 2']:
 s=d.styles[n]; s.font.name='Arial'; s.font.color.rgb=RGBColor(0,0,0)
d.styles['Normal'].font.size=Pt(10)
d.add_paragraph('TradeWill Application Functional Documentation','Title')
d.add_paragraph('Browser inspection record and screen reference • 16 November 2026')
d.add_paragraph('This manual documents the Trade W website and signed-in account screens inspected during this session. It provides navigation, visible controls, form fields, account workflows and screenshot evidence. Values reflect the inspected account and region at capture time and may change.')
d.add_heading('Coverage and verification status',1)
d.add_paragraph('The captured evidence covers account overview, MT5, Trade W real and demo accounts, investment, internal transfer, deposits, bank and cryptocurrency withdrawals, identity verification, questionnaire, settings, orders, referrals, tasks, downloads and the principal public navigation pages. The appendices preserve the distinct visible labels and controls for each captured screen.')
d.add_paragraph('Coverage is not certified as 100 percent. Successful deposits, withdrawals, transfers, live orders, account opening, identity submission, password changes, account deletion, every historical article, all FAQ content across every page and every regional or account-specific state were not executed or exhaustively inspected. MT4 account and all five history tabs now have retained captures. Trusted device selection produced no confirmed distinct view. The points rules capture repeats the task screen; the linked help article is recorded separately.')
d.add_heading('Observed account journeys',1)
flows=[('Account access','Open the account overview. Review total assets and the balances of MT4, MT5, Trade W and Investment. Desktop navigation additionally exposes Order, Invite Friends, Task Center and Downloads.'),('Verification','Open Verification. The page separates Questionnaire, Identity Verification and Address proof. Questionnaire asks date of birth, email, phone, address, US tax citizenship and politically exposed person questions. Identity upload requests country or region and front and back document images in JPG, JPEG, PNG or PDF up to 10 MB. Later steps require user documents and were not completed.'),('Funding','Deposit opens account selection with Trade W, MT4 and MT5 tabs and regional payment channels. QRIS, BRI, BNI, PermataBank, E-Wallet, TRX, Bitcoin and Tether networks were displayed. Next Step and downstream payment completion were not tested.'),('Withdrawals','Bank withdrawal displays account, amount, receiving bank card, fees, actual receipt, exchange calculation and Confirm. The loaded screen showed ID verification required, a 5 to 1500 USD range and a 1 USD fee in its instructions. Crypto withdrawal displays currency, network, address and amount; the captured USDT state showed an 11 USD minimum and zero account withdrawal limit. These are captured UI values, not independently verified financial terms.'),('Internal transfers','Select source and destination accounts, enter amount or All, then review Confirm. The inspected empty form had a disabled Confirm. No transfer was submitted.'),('Trading','Web Trader provides market categories, symbol search, quote data, TradingView chart, account selector, positions, pending orders and history. Market and Limit tabs expose buy or sell, lots, lot presets, optional take profit and stop loss, margin and fee. Limit adds a limit price. Entering through the Demo page unexpectedly displayed Standard with zero real balance; account mode must be verified before any order. No order was placed.'),('Orders','MT4 and MT5 account tabs provide open and closed positions. Trade W provides Position, Pending order and History. Captured history states that only seven days are displayed and offers Transaction Details for full history.'),('Rewards and referrals','Invite Friends provides code, link, QR, invitation table, activity rules and reward rules. Task Center provides points, check-in, tasks and redemption choices. Visiting Task Center automatically displayed Check-in Successful plus one and a balance of 101 points. No Collect, Exchange, referral withdrawal or prize draw was intentionally executed.'),('Settings','Personal information includes picture, nickname, gender and age. Security includes login account, password, security code, phone, email, Google and Facebook authorization, trusted devices and irreversible account deletion. These settings were inspected without editing credentials or deleting the account.')]
for title,body in flows:d.add_heading(title,2);d.add_paragraph(body)
d.add_heading('Screen evidence and detailed control inventory',1)
d.add_paragraph('Each section below identifies the captured page URL and lists distinct accessible headings, fields, tabs, buttons and visible text. Shared headers, footers and support widgets are removed where a clear boundary exists. Screenshots show the viewport captured, while the inventory may include content below the fold. Marketing, regulatory and yield statements remain site claims; this manual does not independently validate them.')
for f in sorted((root/'evidence').glob('*.txt')):
 if f.stem in ['points-rules','trusted-devices']:continue
 text=f.read_text();text=text.split('container Footer navigation')[0];text=re.split(r'\n\s*\d+ container\n\s*\d+ container\n\s*\d+ image logo',text)[0]
 d.add_heading(f.stem.replace('-',' ').title(),2)
 url=re.search(r'URL: "([^"]+)"',text)
 if url:d.add_paragraph(url.group(1))
 seen=set();items=[]
 for line in text.splitlines():
  m=re.search(r'\d+ (text|heading|button|tab |combo box|text field|stepper|switch|radio button|link Description:)(.*)',line)
  if not m:continue
  val=(m.group(1)+m.group(2)).strip();val=re.sub(r', ID:.*','',val);val=re.sub(r', Secondary Actions:.*','',val)
  if val in seen:continue
  seen.add(val)
  if len(val)>1500:val=val[:1500]+' [long page text abbreviated in this inventory]'
  items.append(val)
 if f.stem=='public-tradingGlossary':
  d.add_paragraph('Glossary contains category filters and an alphabetical accordion index. Individual definitions were not all expanded. The retained evidence file includes the full captured term index.')
  items=items[:35]
 for val in items:d.add_paragraph(val,style='List Bullet')
 img=f.with_suffix('.png')
 if img.exists():
  from PIL import Image
  w,h=Image.open(img).size
  d.add_picture(str(img),width=Inches(min(6.7,5.8*w/h)))
  d.add_paragraph('Captured viewport for '+f.stem.replace('-',' '))
d.save(root/'TradeWill_Application_Documentation.docx')
print('Created',root/'TradeWill_Application_Documentation.docx')
