# TradeWill App Exploration Report

**Prepared:** 15 November 2026  
**Purpose:** Record what TradeWill appears to contain, how the visible Web Trader flows work, what has been inspected so far, and what remains to inspect before using it as a product reference for Northstar FX.  
**Evidence used:** User-provided screenshots of the signed-in Web Trader, TradeWill public website pages, public FAQ/help pages.  
**Scope note:** This is not a claim that every authenticated feature has been explored. Private account areas cannot be verified from public pages and screenshots alone.

## 1. Executive summary

TradeWill (marketed on the site as “Trade W”) combines a customer account portal, proprietary Web Trader and mobile app, MetaTrader 4/5 access, CFD instrument pages, learning/market resources, account funding, and customer support. The signed-in screenshot shows a terminal with a chart and an order ticket sharing the screen.

The visible chart screen includes instrument selection, quote summary, chart timeframes, TradingView-style chart controls, technical indicators and drawing tools, market/limit order tabs, buy/sell quote buttons, lot sizing, optional take-profit/stop-loss, transfer/deposit controls, and Position/Pending order/History tabs.

**Important client-market finding:** TradeWill’s public FAQ says its named entities do not offer services to U.S. residents. If the American client is building for U.S. residents, TradeWill can only be a visual/functional reference; its broker, CFD, account, and funding model cannot be assumed to fit that market. Confirm whether “American client” means the client/owner is American or the app’s users will be U.S. residents.

## 2. What was inspected

### Directly visible in user-provided screenshots

- Main navigation: Markets, Platforms, Account, Resources, Company, Partnership, and Web Trader.
- Instrument shown: `ETC/USDT`; quote area displays current price, approximate account-currency value, 24-hour change, high, and low.
- Chart: candlesticks, `1m` timeframe selector, chart type control, Indicators menu, undo/redo, full-screen control, left-side drawing tools, and a MACD panel. The screenshot also contains a trend line and Fibonacci retracement/extension drawing.
- Order panel: account selector (`#Standard`), Market Order and Limit Order tabs, Sell and Buy quote buttons, lot input and quick-size buttons, Take Profit and Stop Loss toggles, Transfer and Deposit buttons, total/margin fields, and an insufficient-balance message.
- Trade ledger: Position, Pending order, and History tabs; the supplied screen shows “No records.”
- The screenshot shows a zero account balance. It does not prove that the displayed prices are live market data or that any order was submitted.
- Public Markets menu screenshot lists Forex CFDs, Stock CFDs, Crypto CFDs, Indices CFDs, and Metals CFDs.

### Confirmed from public TradeWill pages

- Web Trader marketing page describes chart drawing/indicators, supported tradable instruments, web/app order synchronization, and encrypted transaction data.
- Public chart page exposes a guided demo overlay: choose a trading product, switch product varieties, review a quote, select direction and lot size, optionally set stop-loss/take-profit, and view positions, pending orders, and history. The public page asks the visitor to log in or sign up for account-specific features.
- Public pages list Trade W App, Web Trader, MT4/MT4 Mobile, MT5/MT5 Mobile, and partnership program.
- Public pages list market resources: market insights/analysis, trading news, economic calendar, profit and margin calculators, TradingView, glossary, and beginner tutorial.
- The Help Center categories include Getting Started, Deposits & Withdrawals, Account Security, Trading Terminal, FAQs, and Recent Questions.
- Public FAQ describes demo accounts using virtual USD, multiple platform access, possible bank/card/e-wallet/local payment methods, support, and educational resources.

## 3. Main areas and what each appears to do

| Area | What it contains | User purpose |
|---|---|---|
| Markets | Markets overview and Forex/Stock/Crypto/Indices/Metals CFD pages | Browse available products and their specifications |
| Platforms | Web Trader, Trade W app, MT4, MT5, mobile versions | Choose where to view prices and manage trades |
| Account | Classic/Professional account series and Demo account | Open or select an account type |
| Web Trader | Watchlist/product chooser, chart, order ticket, account/trade tabs | Analyze a product and place/manage a trade |
| Resources | Analysis, news, calendar, calculators, TradingView, glossary, beginner tutorial | Research and estimate trading details |
| Funding | Deposit, withdraw, transfer (shown in portal/terminal) | Move funds between supported account/payment flows |
| Support | Help Center, FAQ, feedback, contact options | Resolve account, funding, and platform questions |
| Company/legal | About, announcements, privacy, AML, legal statement, partnership | Review operator, policies, and business information |

## 4. Visible Web Trader workflow

### A. Select a product

1. Open the product chooser/search.
2. Select an instrument, or use the visible Favorite/Hot categories on the public chart page.
3. Review the quote summary: last price, 24-hour change, high/low, and instrument rules.

### B. Read the chart

1. Choose a timeframe (the supplied screenshot shows `1m`).
2. Change chart style or expand the chart if needed.
3. Add indicators from the Indicators menu (MACD is visible in the screenshot).
4. Use drawing tools such as trend lines and Fibonacci tools. Drawings in the supplied screenshot are user annotations; they do not indicate TradeWill-generated signals.

### C. Prepare an order

1. Select Market Order or Limit Order.
2. Choose Buy or Sell and enter the lot size.
3. Optionally enable Take Profit and Stop Loss and enter values.
4. Review total cost/margin and available balance before submitting.
5. Use a demo account for practice. The public demo copy says virtual funds are used; a screenshot of an order ticket alone does not confirm the selected account is demo.

### D. Review/manage trades

- Position: inspect open positions and their current status/P&L.
- Pending order: inspect orders waiting for trigger/placement and, if the authenticated app permits, edit/cancel them.
- History: inspect completed/cancelled/rejected orders or trade records. Exact status filters and detail screens remain unverified.

### E. Funding controls

- Deposit, Withdraw, and Transfer appear in the account experience.
- The actual funding providers, fees, limits, status steps, withdrawal checks, and inter-account transfer behavior were not tested. Do not infer those from button labels or marketing copy.

## 5. Publicly described account/instrument information

- Public account pages list Standard and Cent accounts, and other pages/menus also refer to Pro/Professional and Demo accounts.
- The account page opened during this review says Standard minimum deposit `$3`, spread from `0` pips, maximum leverage `1:800`, commission `$15/lot`, USD account value, and Web/App/MT4/MT5 access. Cent is shown as a live, real-money account displayed in cents.
- Other public pages show different conditions (for example maximum leverage `1:500`, a commission range of `$10–$15/lot`, and older deposit amounts). The margin-calculator page describes per-product commissions and a Pro account with no commission but wider minimum spreads.
- Therefore account pricing is **not settled by this exploration**. Pull the current specification for the user’s exact entity, country, account type, instrument, and platform before implementing fees/leverage.
- Categories publicly advertised include Forex, metals, indices, stocks, and crypto CFDs. Product availability varies by account type and region.

## 6. Important U.S.-client compatibility check

TradeWill’s public FAQ states that its entities do not offer services to residents of the United States (as well as certain other jurisdictions). The website also describes CFDs and offshore entities. Consequently:

- If the client is U.S.-based but the app serves a different eligible market, confirm the target-user countries and provider entity before designing the live account/funding flow.
- If the target users are U.S. residents, do not copy TradeWill’s CFD offering or assume its broker can be integrated. The product scope and broker must be selected for the intended U.S. users and instruments.
- The existing Northstar FX project remains a paper simulator; it is not connected to TradeWill, another broker, or a live price feed.

## 7. What has not been explored yet

The following require authenticated access, a live/demo account, or user-supplied sanitized screenshots/video. They are not claimed as verified:

- Account registration, email/phone verification, KYC/identity review, password reset, 2FA, sessions, and account recovery.
- Account creation/selection, demo balance reset/replenishment, account currency, leverage settings, and trading permissions.
- Every instrument’s contract rules, lot units, minimum/maximum size, tick size/value, trading hours, swap/financing, and margin calculation.
- Full chart behavior: symbol search results, all timeframes, chart history loading, refresh/reconnect, alerts, indicator settings, saved layouts, drawing persistence, and mobile layout.
- Order behavior: validation, confirmation, execution, requotes/slippage, rejected/partial fills, edit/cancel, pending trigger rules, stop-out/liquidation, and trade close workflow.
- Exact Position/Pending/History detail screens, filters, export/statement, realized/unrealized P&L, fees, and audit trail.
- Deposit/withdrawal/transfer steps, payment processors, verification, fee display, processing statuses, failure/refund states, and limits.
- App notifications, support chat, device linking, app/web synchronization, security controls, privacy/data settings, and accessibility.
- API access, broker-side order routing, data vendor/licensing, server architecture, and third-party integration terms.

## 8. Full exploration checklist

To complete the authenticated audit, inspect each item using a **demo account**, redact personal data and balances, and capture the initial screen plus every success/error state.

### Account and navigation

- [ ] Logged-out pages, signup/login, account selector, logout, password recovery
- [ ] Profile, verification/KYC status, security/2FA, devices/sessions, notification settings
- [ ] Demo vs live account labels and safeguards
- [ ] Web/app account and order synchronization

### Markets and product rules

- [ ] Search, favorites, hot list, categories, instrument details/rules
- [ ] Contract size, lot min/step/max, tick/pip value, trading hours, leverage/margin, swap/fees
- [ ] Product availability by account type and region

### Charts and analysis

- [ ] All timeframes, chart types, zoom/scroll, historical range, refresh/reconnect
- [ ] Indicators and editable parameters; drawing tools; save/clear layouts
- [ ] Alerts/news/calendars and any chart-to-order interaction
- [ ] Narrow/mobile screen behavior and keyboard/accessibility

### Orders and positions

- [ ] Market/limit and any stop/stop-limit order types
- [ ] Quantity/lot validation, SL/TP validation, risk/margin preview, confirmation dialog
- [ ] Successful, rejected, partially filled, delayed, cancelled, and duplicate submission states
- [ ] Edit/cancel pending orders; close/partial-close positions; fees and P&L breakdown
- [ ] Position, Pending, and History tables/details/filters/export

### Funds and service

- [ ] Deposit, withdrawal, transfer: available methods, fees, limits, verification, states/errors
- [ ] Statements, transaction ledger, notification/email receipts
- [ ] Help center, contact/live chat, support ticket, complaint route

## 9. Evidence and source links

Public content was reviewed on 15 November 2026. Marketing statements and account conditions may change; the logged-in app may differ by account, region, and product.

- [Trade W Web Trader page](https://www.tradewill.com/download-web-trader)
- [Public chart/demo onboarding page](https://www.tradewill.com/CHART)
- [Account overview](https://tradewill.com/in_en/account-overview)
- [Trade W FAQ](https://tradewill.com/faq/)
- [Trade W Help Center](https://help.tradewill.com/)
- [Margin Calculator](https://tradewill.com/margincalculator)

## 10. What is needed to finish the private-app exploration

Please share sanitized screenshots or a short screen recording of the checklist sections above while using a demo account. Hide email, phone, account IDs, personal documents, payment details, and any private balances. Do not send a password, API token, recovery code, or identity document. With that evidence, this report can be completed screen-by-screen without treating unknown private behavior as fact.
