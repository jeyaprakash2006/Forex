# TradeWill Exploration — New Chat Handoff

**Updated:** 15 November 2026  
**Project folder:** `/Users/jeyaprakash/PROJECTS/Forex`

## Goal

Build a browser-based trading terminal for a U.S.-based client, using TradeWill’s visible Web Trader experience as a product reference. The user wants a thorough, screen-by-screen exploration of TradeWill and a detailed document describing what it contains, how each feature works, and what the new app should implement.

## Current project status

- A static **paper-trading prototype** exists in `index.html`, `styles.css`, and `app.js`.
- The prototype uses generated/sample prices. It has no real market-data feed, broker API, deposits, or live orders.
- `PRD.md` was updated to say the client is U.S.-based and that end-user geography still needs confirmation.
- `TRADEWILL_EXPLORATION.md` records publicly visible TradeWill features, the screenshots already supplied, observed trading workflow, public account/resource lists, inconsistencies, and a checklist of authenticated screens still to inspect.
- The user says the in-app browser is open at `https://www.tradewill.com/account-center/overview?activeName=tw` and intends to log in so the app can be explored.

## Important exploration constraint

The current tool session did **not** expose browser-control/UI automation. The public web fetch for the authenticated Account Center URL failed, so the logged-in tab contents could not be inspected. Do not claim the private app has been explored or that the review is 100% complete. Continue when browser-control is available or when the user supplies screenshots/screen recordings from the logged-in demo account.

Do not request or accept the user’s password, API token, recovery code, identity documents, or unredacted private account details. Ask for sanitized screenshots/recordings only. Do not initiate deposits, withdrawals, or real trades while exploring.

## Findings already captured

- Screenshots show a dark Web Trader terminal with an instrument header and quote statistics, candlestick chart, `1m` timeframe, indicator/drawing controls, MACD, market/limit order tabs, buy/sell controls, lot-size field, take-profit/stop-loss toggles, Transfer/Deposit buttons, and Position/Pending order/History tabs.
- The screenshot’s instrument is `ETC/USDT`; the visible balance is `$0.00` and the order ticket reports insufficient balance. A screenshot does not prove that quotes are live.
- Public pages describe supported markets as Forex, metals, indices, stocks, and crypto CFDs; platforms as Trade W App, Web Trader, MT4/MT5 and mobile versions; and resources such as news, economic calendar, TradingView, profit/margin calculators, glossary, and beginner tutorials.
- Public chart onboarding describes choosing a product, reviewing quote data, choosing direction/lot size, optionally setting SL/TP, and viewing positions, pending orders, and history.
- Public account pages show conditions that differ across pages/account versions. Verify the client’s exact entity, region, instrument, and account before copying fees or leverage.
- TradeWill’s public FAQ says its entities do not offer service to U.S. residents. Confirm whether the U.S. reference is only the client’s location or also the target users’ location before using its brokerage model as a template.

## Next steps in the new chat

1. Check whether browser-control tools are available in the new session. If available, use the user’s already-open tab only after reading that tool’s instructions; do not ask the user to share login credentials.
2. Explore the account in **demo mode** and capture the initial view plus success/error states for each section in `TRADEWILL_EXPLORATION.md` §8.
3. If browser control is still unavailable, ask the user to upload redacted screenshots or a recording of each menu and feature flow.
4. Update `TRADEWILL_EXPLORATION.md` with date-stamped, evidence-based observations; mark each item as “observed in app”, “public-site claim”, or “not verified”.
5. Compare observed flows against the current `PRD.md` and list implementation requirements for the Northstar FX prototype. Keep all orders paper-only until the client confirms broker, API authorization, instruments, target-user countries, and compliance scope.

## Suggested first message in the new chat

“Continue the Forex project from `TRADEWILL_NEW_CHAT_HANDOFF.md`. The goal is to explore the logged-in TradeWill demo account screen by screen and update `TRADEWILL_EXPLORATION.md`. First check if browser-control is available. If it is not, ask me for redacted screenshots/recording. Do not claim 100% exploration until each checklist item has evidence.”
