# Product Requirements Document

## Northstar FX

**Version:** 0.1  
**Status:** Draft for review  
**Product type:** Browser-based trading terminal prototype  
**Client location:** United States  
**End-user market:** To be confirmed; this draft assumes U.S. users only  
**Reference experience:** TradeWill-style market watch, chart, order ticket, and trade ledger. Northstar FX uses its own name and visual identity.

> **Current boundary:** The existing prototype is a paper-trading simulator. Its prices and fills are generated locally. It is not a broker, does not connect to an exchange, and cannot accept deposits or send live orders.

## 1. Product summary

Northstar FX is a beginner-friendly trading terminal for a U.S.-based client. The first release is a local, virtual-money simulator. A later live-trading release may connect to a broker API only after the instruments, end-user locations, the app's role, permissions, and applicable regulatory requirements are confirmed.

Northstar FX is intended to be a **client application for an existing regulated broker**, not a new brokerage business. The product must not present simulated quotes or paper fills as real market execution, or imply that the app itself is a regulated broker. A U.S.-based client does not by itself establish that the app serves only U.S. users; confirm user geography before live-trading scope is set.

## 2. Problem and opportunity

New traders see feature-rich broker terminals but often do not understand currency pairs, order sizes, pending orders, stop-loss, take-profit, margin, or trade history. Depositing money just to learn the interface creates avoidable financial risk. Users need a clear practice environment that resembles a trading terminal while clearly distinguishing simulated activity from real trading.

## 3. Goals

1. Let a beginner learn the core order workflow without depositing money.
2. Present market instruments, charts, order entry, account balance, positions, pending orders, and history in one responsive interface.
3. Make the data source and mode obvious at all times: simulated, broker demo, or live.
4. Keep the interface ready for a future authorized broker integration without embedding broker credentials in browser code.
5. Give users a clear path to review their practice trades and reset the virtual account.

## 4. Non-goals

- Becoming or operating as a broker, exchange, investment adviser, or payment provider.
- Accepting deposits, withdrawals, customer funds, or custody of assets.
- Launching live trading before the client, broker, instruments, customer locations, and regulatory roles have been reviewed by qualified counsel and the broker's compliance team.
- Providing guaranteed signals, investment recommendations, or profit claims.
- Treating a paper-trading result as evidence that a live strategy will be profitable.
- Building KYC, AML, settlement, clearing, or customer-support operations in the first release.

## 5. Users and primary use cases

### Primary user: beginner learning Forex

- Opens the terminal and understands that it is in paper mode.
- Selects a currency pair and changes chart timeframes.
- Uses chart indicators and drawing controls to study price movement.
- Places a simulated market or limit order with an optional stop-loss and take-profit.
- Reviews open positions, pending orders, and closed-trade history.
- Resets the virtual account without affecting real funds.

### Future user: existing eligible broker customer

- Authenticates through the broker's approved authorization flow.
- Views broker-provided instruments and market data.
- Reviews estimated charges, margin, and order details before confirming an order.
- Sees order status and positions from the broker, including rejected or partially filled orders.

## 6. Product modes

| Mode | Data | Funds | Order destination | Release status |
|---|---|---|---|---|
| Paper simulator | Locally generated sample data | Virtual | Local simulator only | Current prototype |
| Broker demo | Broker-provided demo feed, if supported | Virtual at broker | Broker sandbox/demo | Future; provider-specific |
| Live broker | Broker market feed | Broker account funds | Selected broker API | Blocked pending provider and eligibility review |

The app must display a persistent mode label. The user must never confuse sample data or a demo balance with a live account.

## 7. Functional requirements

### 7.1 Workspace and navigation

- **FR-01:** Show a terminal workspace with navigation rail, watchlist, chart, order panel, and positions panel.
- **FR-02:** Provide responsive desktop and mobile layouts.
- **FR-03:** Show broker connection status and current mode in the top navigation.
- **FR-04:** Keep all actions that could place orders clearly separate from data and chart controls.

### 7.2 Watchlist and instruments

- **FR-05:** Show a watchlist of currency pairs with symbol, indicative price, and daily movement.
- **FR-06:** Selecting a pair updates the chart and order ticket.
- **FR-07:** Each instrument must show its product type and data source. Future live instruments must come from the connected broker's permitted instrument master.
- **FR-08:** Do not show a simulated instrument as an available live instrument.

### 7.3 Charts and analysis

- **FR-09:** Provide candlestick charts, timeframe selection, price axis, and a visible simulated-data label in paper mode.
- **FR-10:** Support basic chart tools and indicators, including a moving-average overlay and MACD panel in the prototype.
- **FR-11:** Clearly distinguish chart history generated for practice from exchange or broker history.
- **FR-12:** A future live feed must show its source and last-update time; stale or disconnected data must be visibly marked.

### 7.4 Order entry

- **FR-13:** In paper mode, support simulated Buy/Sell market orders and limit orders.
- **FR-14:** Let the user set a bounded virtual order size and optionally set stop-loss and take-profit levels.
- **FR-15:** Show estimated notional and margin with the assumptions used by the simulator.
- **FR-16:** Validate size and price inputs before accepting a simulated order.
- **FR-17:** Show a clear confirmation state after an order is submitted, cancelled, or closed.
- **FR-18:** Live mode must require an explicit order review and confirmation. No live order may be sent by a background action, chart refresh, or one-click control enabled by default.
- **FR-19:** The live order ticket must display broker fees, applicable taxes, margin requirement, and product-specific warnings when available from verified sources.

### 7.5 Account, positions, and history

- **FR-20:** Show virtual balance, estimated equity, and open simulated positions.
- **FR-21:** Show pending limit orders and allow the user to cancel them in paper mode.
- **FR-22:** Let the user close a paper position and record its simulated result in history.
- **FR-23:** Store paper state locally and provide a reset action that clearly explains what will be cleared.
- **FR-24:** In live mode, display broker-reported balances, positions, order statuses, and trade history; do not infer execution from a successful HTTP request alone.

### 7.6 Alerts and journaling (later phase)

- **FR-25:** Add user-configured price alerts only after a reliable data source is selected.
- **FR-26:** Allow users to add notes and review outcomes for practice trades.

## 8. U.S. regulatory scope and market boundary

The first release is a paper simulator. It must not accept customer money or send live orders. This PRD assumes U.S.-only end users for planning, but the assumption must be confirmed with the client. The client being based in the United States does not determine where the app may offer services; user location, instruments, execution model, compensation, and the app's role all matter.

- Before live release, qualified U.S. counsel and the selected broker's compliance team must determine whether the product is only a software interface for a regulated broker or whether its activities could create registration, intermediary, solicitation, advisory, or other obligations.
- For retail off-exchange leveraged forex, assess applicable CFTC/NFA rules and the broker/counterparty's required registrations. For securities, assess SEC, FINRA, and applicable state requirements. The correct path depends on the exact instruments and activities; this PRD is not a legal determination.
- Verify the broker and relevant firm/person registrations using the appropriate regulator or self-regulatory organization before enabling live links.
- If Indian residents or Indian operations are included, add a separate India-specific legal review for RBI/FEMA, SEBI, exchange, tax, privacy, and other applicable requirements. Do not treat the U.S. review as covering India.
- This PRD is a software product specification, not legal or investment advice.

## 9. Data and calculation requirements

### Prototype

- Store only paper balance, simulated positions, pending orders, and history in browser `localStorage`.
- Mark all generated prices as illustrative; do not call them live or real-time quotes.
- Label estimated P&L and margin as simulator estimates, and show assumptions beside them.
- Do not collect account credentials, payment details, identity documents, or broker tokens.

### Live integration phase

- Broker credentials and access tokens must remain server-side or within the broker-approved secure flow; never store secrets in browser JavaScript or local storage.
- Consume the broker's official instrument master, quotes, and order endpoints only within the API terms and permissions.
- Record timestamps, source, stale-data state, order request identifiers, broker order identifiers, and final order status.
- Handle rejected, cancelled, partially-filled, delayed, and duplicate order responses safely.
- Calculate margin and P&L from broker/exchange contract specifications, not a fixed generic leverage assumption.

## 10. Non-functional requirements

- **Safety:** Paper/live mode must be unmistakable; no deposits or real orders exist in the paper build.
- **Security:** No secrets in frontend code; validate all inputs; encode user-controlled output; use HTTPS and access control before deployment.
- **Reliability:** Broker disconnections and API errors must fail closed; never show an order as filled without broker confirmation.
- **Usability:** Core order actions should be understandable on a laptop and phone, with visible size, side, instrument, order type, and risk controls.
- **Accessibility:** Keyboard-operable controls, visible focus, readable contrast, and labels for inputs and chart modes.
- **Maintainability:** Keep data providers behind an adapter boundary so the practice simulator cannot accidentally call a live broker.
- **Auditability:** A future live build must retain a user-visible order history and server-side audit trail consistent with provider and legal requirements.

## 11. MVP acceptance criteria

The paper-trading MVP is acceptable when:

1. It loads locally in a browser at desktop and mobile widths.
2. The app visibly says Paper Mode, Demo Feed, and Broker Not Connected.
3. Users can switch between listed pairs and timeframes.
4. Users can place virtual market and limit orders, set optional SL/TP, and view positions/pending/history.
5. Closing or cancelling a paper trade updates the demo ledger and virtual equity.
6. Resetting the demo asks for confirmation and clears only local practice data.
7. The UI and README state that generated prices are not live market data.
8. No route or control can transfer funds or submit a real order.

## 12. Current prototype status

The workspace contains a static responsive prototype in `index.html`, `styles.css`, and `app.js`. It currently includes a simulated quote watchlist, generated candlestick data, timeframe controls, MA/MACD display toggles, simulated market/limit order entry, virtual positions and history, and local browser persistence. It has no live market feed, authentication, server, broker API, KYC, or payment integration.

## 13. Dependencies and open decisions

1. **Client and users:** Is the American client the owner/customer, and which countries will the app's end users reside in?
2. **Instruments:** Retail spot FX, futures/options, securities, crypto, or another product?
3. **Broker/provider:** Which broker and official API will be used, and which registrations/permissions cover the intended flow?
4. **Product role:** Is Northstar FX only a software interface, or will it solicit users, route/execute orders, provide recommendations, or earn transaction-based compensation?
5. **Market data:** What official feed is available, what are its latency and licensing terms, and are fees passed to the user?
6. **User model:** Personal single-user tool, or a multi-user customer product with authentication and support?
7. **Platform/localization:** Web-only first release or mobile too? English-only, or English and Tamil?

## 14. Suggested delivery phases

### Phase 1 — Learning terminal

Polish and validate the current virtual-money app; make data labels and simulator assumptions explicit; add a practice journal and basic reset/export controls.

### Phase 2 — Broker feasibility

Choose an eligible provider, verify product availability and current rules, obtain API access, review terms and data licensing, and document authentication and order flows.

### Phase 3 — Broker demo integration

Connect only to an official demo/sandbox if the provider offers one. Validate order lifecycle, disconnections, rejected orders, account data, and auditability.

### Phase 4 — Live release review

Complete compliance, security, operational, and broker approval reviews; deploy with explicit live-mode confirmations, monitoring, incident handling, and support processes.

## 15. Success measures

- New users can explain the difference between sample prices, paper orders, and live broker orders after using the terminal.
- Users can complete a practice market order, limit order, stop-loss, take-profit, and close flow without help.
- Paper order and history records remain consistent across reloads until the user resets them.
- Before any live integration, the selected broker confirms the instrument and API permissions, and compliance review approves the intended release scope.

