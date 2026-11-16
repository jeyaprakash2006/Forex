# TradeWill reference parity — ongoing

Updated 15 November 2026. The user's target is matching the reference experience end to end; this is not a claim of completed parity. Broker selection remains open, as confirmed by the user.

## Implemented reference rebuild

- Full-bleed dark terminal with chart on left, fixed right ticket, bottom ledger, dropdown instrument selector, profile navigation.
- Separate light customer center with sidebar, profile banner, asset cards, positions, order reports, account settings, assets view.
- Seven configured demo instruments: EUR/USD, GBP/USD, BTC/USDT, ETC/USDT, ETH/USDT, SOL/USDT, XAUUSD. Crypto instruments settle in virtual USD; labels do not represent a real token balance.
- Per-instrument contract sizes, spread, price precision and maximum size; practice leverage remains 1:20.
- Independent canvas chart with candles/bars/line, zoom/pan, MA, EMA, MACD, RSI, Bollinger Bands; searchable indicator chooser.
- Horizontal/trend lines, rectangles, Fibonacci retracement, text annotations, movement measurement, undo/redo and drawing visibility.
- Chart drawing/indicator settings stored per user/instrument in browser storage.
- Expanded timeframe aggregation menu; available history is limited to retained server candles. Weekly/monthly views do not imply long historical coverage.
- Working profile menu, account summary dialog, calculator and activity notifications.

## Still incomplete

- Pixel-exact visual equivalence and all reference interactions have not been verified.
- The reference uses TradingView charting; this independent chart is not that licensed library and supports only the listed indicators/tools.
- Full market catalog, native apps, MT4/MT5 bridges, multiple active account types, provider permissions, live market data and execution.
- Email verification/recovery, MFA, complete brokerage staff operations, partner/referral/reward systems. Basic local support operations are implemented below.
- Funding and identity screens are explicit unavailable-service states, not working payment/KYC integrations. Several ancillary menu entries explain unimplemented capabilities.
- Login page remains the original Northstar layout; not yet reference-matched.
- Mobile layout is responsive but not claimed identical to TradeWill's mobile experience.

## Verification of this rebuild

25 Python tests and 3 JavaScript indicator tests pass. Added coverage for BTC/ETC contract sizing, spread P&L and BTC tick precision. Browser inspection confirmed terminal rendering, indicator selection (RSI), and light account center. Mobile 360px DOM width check: content 345px, viewport 360px, no page-level overflow. Browser error-log query returned no errors. Existing core trade lifecycle tests continue to pass.

The original development UI is preserved in `docs/pre-reference-rebuild/`. Runtime is still local-only; see README for launch steps.

## Gap closure: account settings and support

- Profile name editing with server validation.
- Password change requiring the current password; all other sessions revoked.
- Active session list, owner-scoped revocation and current-session sign-out.
- Pending limit-order amendment retaining the order ID, revalidating margin/SL/TP, and rolling back invalid edits; idempotent trading mutation.
- Report date range filters (browser local dates).
- Persistent support requests; users see only their own requests and staff replies.
- Explicit staff-only queue, reply/status updates, minimal user directory and administrative audit. Staff roles are provisioned/revoked by a local operator CLI, never self-assigned through the website.

Verification: tests cover password/session isolation, amendment rollback, support ownership, unauthorized staff rejection, staff reply and role revocation, HTTP authentication boundaries. Browser verified settings controls, active session rendering and support form. No console errors observed. Staff console UI has not been browser-tested; backend permissions and replies are tested. Support submissions are not yet idempotent and the queue is limited to the latest 100 records. This remains a local development service, without production email delivery, staff MFA, or a connected external support team.

## Measured UI alignment — 15 November 2026

Compared the signed-in TradeWill terminal at 1280×720 with the local terminal before edits. Corrected the local 740px minimum workspace height that caused desktop page scrolling; aligned the 316px ticket, 76px header, 56px instrument strip, chart/ledger split, quote controls, lot presets, protection toggles and ledger typography. Added locally served TASA Orbiter fonts (OFL license in assets/fonts/OFL.txt), matched the green palette, replaced the initial avatar with an original SVG, and expanded the profile menu to the observed 408px layout. Responsive rules preserve stacked mobile content and a scrollable menu.

The reference chart remained loading and its account overview rendered blank during this inspection. Browser access became unavailable before the updated local screen could be visually verified. Consequently these changes are implemented, but exact pixel parity, updated mobile rendering, account-center parity and login parity remain unverified. Branding and truthful simulated-account labels remain application-specific.

## Advanced chart controls

Added Heikin Ashi alongside candles, OHLC bars and close-line rendering; configurable MA/EMA/RSI/Bollinger/MACD periods and Bollinger deviations; persistent per-user/per-instrument chart style and parameters; crosshair UTC timestamp and price-axis labels; and a jump-to-latest control that preserves zoom. Instrument switching now restores defaults before applying that instrument's saved preferences. Indicator panes adapt to compact chart heights. Heikin Ashi is explicitly labelled synthetic; quote-based execution is unchanged.

Validation: 25 Python + 6 JavaScript tests pass, including recursive Heikin Ashi OHLC, configurable band widths, and invalid stored parameter handling. Syntax checks pass. Browser rendering verification remains pending because browser access was unavailable in this chat. This is the independent chart implementation, not full TradingView parity; long historical coverage, a complete indicator catalog, and provider data remain outstanding.

## Live spot market data

Added authenticated `/api/live/quotes` and `/api/live/candles`, backed by Kraken public REST endpoints, plus a separate Live Markets screen. Supported USD pairs: BTC, ETH, ETC, SOL. Quotes poll every 5 seconds and OHLC every 15 seconds, with server-side caching, provider timeout/backoff, schema validation, received timestamps and stale/error messaging. Up to 720 trade candles; latest candle is provisional. This is polled exchange data, not a streaming WebSocket feed. Received timestamps denote server receipt, not exchange quote timestamps.

Live data is intentionally separate from the existing simulated execution ledger: no existing demo positions are repriced against the new feed. Forex/gold live data and live-data-driven paper execution remain outstanding. Verified real provider responses for all four quotes and 720 ETC candles. 28 Python and 6 JavaScript tests pass. Browser verification of the new page remains pending.

Sources: https://docs.kraken.com/api-reference/market-data/get-ticker-information and https://docs.kraken.com/api-reference/market-data/get-ohlc-data . Public deployment/distribution terms must be assessed for the intended deployment.
