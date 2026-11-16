# Northstar FX — Product Requirements Document

**Version:** 0.2  
**Updated:** 15 November 2026  
**Status:** Implementation planning baseline; provider and launch-market decisions open  
**Product:** Broker-connected trading web application, customer portal, and operations console  
**Reference:** TradeWill user experience; independent Northstar FX branding and implementation  
**First delivery:** Complete, backend-backed demo trading journey  
**Live delivery:** Conditional on broker capability, eligibility, data permissions, and launch review

## 1. Product direction

Build an end-to-end trading application with a professional terminal, persistent customer accounts, account management, reporting, support, and an administrative console. The intended operating model is a software application connected to an existing broker. The product is not currently scoped to become an independent brokerage, custodian, payment processor, or exchange.

The first release must complete the whole demo journey: sign up, create a virtual account, explore instruments, submit an order, manage positions, close a position, review history, and export a statement. A static visual replica does not satisfy this release.

Future live trading, funding, and verification must use the selected provider's approved capabilities. A feature visible on TradeWill is a reference requirement, not evidence that it is available through another broker or in the intended user's location.

## 2. Reference review and evidence boundaries

Reference inspected on 15 November 2026:

- Trading terminal: https://www.tradewill.com/chart/BTCUSD
- Initial reference: https://www.tradewill.com/chart/ETCUSD
- Account overview: https://www.tradewill.com/account-center/overview?activeName=tw
- Account management: https://www.tradewill.com/account-center/asset-center/tradeW
- Order reports: https://www.tradewill.com/account-center/order-details
- Profile/security: https://www.tradewill.com/account-center/safety

**Directly inspected:** market/limit ticket, lot presets, SL/TP fields and estimated outcomes, margin/fee/leverage display, demo/standard account selector, positions/pending/history tables, timeframe menu, searchable indicator dialog, chart layout, account dashboard, trading-account page, order-report filters, and security-setting categories.

**Entry points observed, complete workflows not validated:** deposit, withdrawal, internal transfer, verification, statements, referrals, task center, support, economic calendar, calculators, and education. No financial transaction or order was submitted during the review. Execution behavior, mobile-app behavior, and operational internals were not verified.

**Proposed for Northstar FX, not observed in TradeWill:** administration, internal architecture, reliability mechanisms, service targets, acceptance tests, and rollout plan below.

Do not copy proprietary code, branding, licensed assets, or assume access to the reference platform's APIs. Chart library selection and licensing require an independent decision.

## 3. Users and roles

| Role | Main responsibilities |
|---|---|
| Visitor | Explore product information and start registration |
| Demo trader | Learn and trade with virtual funds; review results |
| Eligible broker customer | Connect a permitted account and use supported live services |
| Support agent | View permitted account context and manage support requests |
| Operations reviewer | Review integration exceptions and provider workflow statuses |
| Administrator | Manage authorized configuration and staff access |

Staff permissions must be explicit and scoped. Support staff cannot submit trades, move funds, or access broker secrets. Administrative access does not imply authority to change financial records.

## 4. Scope and release boundaries

| Capability | R1: complete demo | R2: provider demo | R3: live launch | R4: expansion |
|---|---|---|---|---|
| Auth, customer dashboard, profile | Required | Extend | Harden | Extend |
| Terminal and order management | Internal simulator | Broker sandbox where available | Broker execution | Additional providers |
| History and statements | Required | Provider reconciliation | Provider-backed | Advanced analytics |
| Admin and support | Basic required | Integration operations | Production operations | Expanded workflows |
| Verification | Status model only; no document collection | Provider workflow evaluation | Approved provider flow | As supported |
| Deposit/withdrawal/transfer | Clearly unavailable | Sandbox only if supported | Provider-hosted or approved flow | As supported |
| News/calendar/calculators | Basic explanatory tools optional | Optional | Optional | Full resources |
| Referrals/rewards | Excluded | Excluded | Optional separately reviewed | Candidate |
| Native mobile apps / MT4 / MT5 bridges | Excluded | Excluded | Not implied | Separate scope |

Web application must work on desktop and mobile browsers from R1. Multi-asset support is an architectural capability; it does not require launching every category immediately.

## 5. Information architecture and screen inventory

### Customer application

1. Welcome, registration, login, email verification, password recovery.
2. First-run onboarding and demo account creation.
3. Dashboard: assets, selected account, positions, recent activity, connection status.
4. Markets: categories, search, favorites, instrument details and trading specifications.
5. Terminal: watchlist, chart, ticket, account summary, positions/pending/history.
6. Accounts: account list, demo/live distinction, provider connection, account detail.
7. Reports: open/closed orders, filters, trade detail, statement export.
8. Funds: provider availability, deposit/withdraw/transfer entry points and status history.
9. Verification: requirement explanation and provider-reported status.
10. Profile/security: profile, sessions, recovery, supported MFA and connected identities.
11. Notifications and support requests.
12. Later resources: calendar, education, calculators, referrals.

### Operations console

1. Staff login with MFA and role-based navigation.
2. User/account search with minimum necessary data.
3. Provider connection health and reconciliation exceptions.
4. Instrument configuration and trading availability.
5. Verification/funding status review where provider permissions allow.
6. Support queue, administrative audit events, incident controls.

## 6. Core user journeys

### J1 — First practice trade

Register → verify email → onboarding → create demo account → select instrument → inspect specifications → enter side/size → preview costs and SL/TP → confirm → see accepted/filled state → view position → close → inspect history and statement.

### J2 — Pending order

Choose limit order → validate limit/size/SL/TP → confirm → see pending order → amend or cancel → receive acknowledged state. If the price reaches the limit first, show the resulting fill and reject any invalid late cancellation clearly.

### J3 — Return to the application

Authenticate → retrieve server state → show activity since last visit → reconnect price stream → reconcile order/position state. Reloads and different devices must show the same account ledger.

### J4 — Broker connection and live trading

Check eligibility → provider-approved authorization → select account → retrieve permissions/instruments → explicit live-mode entry → quote/cost review → confirm → receive broker acknowledgment → reconcile execution events → show actual broker result.

### J5 — Funding and verification

Show supported provider workflow → user completes provider-authorized steps → show pending status → receive/reconcile provider confirmation → update status. Returning from a redirect alone is not proof of success.

## 7. Functional requirements

### Identity and onboarding

- **AUTH-01 / R1:** Support registration, verified email login, logout, password reset, and session expiry through a maintained identity solution. Google sign-in is optional for R1.
- **AUTH-02 / R1:** Explain simulated prices, virtual funds, account currency, and execution assumptions before first demo use.
- **AUTH-03 / R1:** Display and revoke active sessions; enforce access ownership on every account API.
- **AUTH-04 / R1:** Require MFA for staff. Live customer MFA/step-up requirements must follow the approved identity/provider design.

### Markets and charts

- **MKT-01 / R1:** Search a configured instrument catalog; filter categories and persist favorites per user.
- **MKT-02 / R1:** Show bid, ask, spread, change, source, market state, and last update time. Define daily change against the previous UTC daily close in the simulator.
- **MKT-03 / R1:** Show contract size, price precision, lot increment, minimum/maximum size, margin assumptions, and session schedule per instrument.
- **CHT-01 / R1:** Provide candles and 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M views from the same underlying series.
- **CHT-02 / R1:** Support MA, EMA, MACD, RSI, horizontal line, trend line, zoom, pan, and fullscreen. Persist supported chart preferences.
- **CHT-03 / R1:** Label candle price basis and simulated history. Mark stale feeds; never silently substitute sample data for broker prices.
- **CHT-04 / R2:** Adopt a charting solution with verified distribution/data permissions. Reference-platform library access is not assumed.

### Order entry and lifecycle

- **ORD-01 / R1:** Support market and limit buy/sell orders, size presets, manual quantity, and optional SL/TP.
- **ORD-02 / R1:** Validate precision, lot steps, price direction, available margin, trading availability, and permitted instrument before acceptance.
- **ORD-03 / R1:** Show account, mode, side, size, notional, margin, spread, fees, and projected SL/TP outcome before confirmation.
- **ORD-04 / R1:** Return a durable order identifier and distinguish submitted, accepted, rejected, filled, cancelled, and uncertain states.
- **ORD-05 / R1:** Support pending-order amendment/cancellation, SL/TP amendment, and full position closure with acknowledgment. Partial position closure is deferred unless required by the selected broker.
- **ORD-06 / R1:** Prevent duplicate submissions with idempotency keys. A timeout must trigger status lookup, not blind resubmission.
- **ORD-07 / R2:** Handle partial fills, expiry, delayed acknowledgment, cancellation races, and out-of-order provider events.
- **ORD-08 / R3:** Require explicit live review and confirmation; show unavailable cost estimates as unavailable rather than zero.

### Accounts, reporting, and support

- **ACC-01 / R1:** Persist demo accounts, selected account, balance, equity, used/free margin, and trade history server-side.
- **ACC-02 / R1:** Display demo, broker demo, and live modes distinctly throughout navigation, ticket, reports, and confirmations.
- **ACC-03 / R1:** Account switching clears the unsent ticket and refreshes account-specific state; no order may use a stale account context.
- **REP-01 / R1:** Provide position, pending-order, and closed-trade views with symbol, timestamps, side, size, prices, SL/TP, fees, swap, realized and net P&L as applicable.
- **REP-02 / R1:** Filter reports by account, instrument, status, and time; export CSV with timezone, mode, source, and calculation assumptions.
- **REP-03 / R1:** Reset demo only after confirmation. Close the old demo session and start a new session; preserve prior ledger/history as an archive.
- **SUP-01 / R1:** Provide in-app notifications and support tickets with status tracking; sanitize content and restrict attachments.

### Provider-dependent customer services

- **FUN-01 / R3:** Expose only supported deposit, withdrawal, and transfer workflows. Display fees/limits/statuses from the provider when available.
- **FUN-02 / R3:** Reconcile provider transaction references and status events; deduplicate callbacks. Never credit balances from a browser success screen.
- **VER-01 / R3:** Prefer provider-hosted verification and retain status/reference identifiers; collecting identity documents requires a separately approved data-handling design.
- **SEC-01 / R1:** Profile edits, sensitive account changes, session management, and recovery must have appropriate authentication and audit coverage.

### Administration

- **ADM-01 / R1:** Enforce staff roles on the server; log actor, action, target, timestamp, reason, and correlation ID for administrative changes.
- **ADM-02 / R1:** Provide user/account lookup, support handling, simulator health, and instrument configuration.
- **ADM-03 / R2:** Add provider health, event delivery status, order reconciliation exceptions, and recovery tooling.
- **ADM-04 / R3:** Allow authorized operators to disable new submissions while preserving visibility and provider-supported risk-reducing actions. Define provider outage behavior in an incident runbook.
- **ADM-05 / All:** No silent editing of balances or executed trades. Any authorized correction requires a traceable compensating ledger event.

## 8. Simulator specification — R1 defaults

These are product defaults for practice, not claims about actual market terms.

| Setting | R1 decision |
|---|---|
| Account | USD base currency; initial virtual balance USD 10,000 |
| Initial catalog | EUR/USD and GBP/USD; add other currencies/assets only with contract and conversion rules |
| Contract | 100,000 base units per lot for these two demo instruments |
| Size | 0.01 minimum/step; 1.00 maximum per order; account margin checks still apply |
| Margin | Configured 1:20 simulated leverage; label as a practice assumption |
| Spread | Configured per-instrument bid/ask spread, visible in ticket and specifications |
| Fees/swap | Zero in R1 simulator, explicitly labeled; never imply equivalence to broker costs |
| Price source | Server-generated deterministic, seedable series; visibly simulated |
| Position model | Separate position per filled order in R1; broker netting/hedging handled by adapter later |
| Execution | Server-side sequential processing per account; append-only financial ledger |
| Background behavior | Orders and SL/TP continue while server runs, even with browser closed |

### Calculation and fill rules

- Units = lots × contract size. For the initial USD-quoted catalog, USD notional = units × fill price.
- Required initial margin = USD notional / configured leverage; reserve margin for pending orders to prevent overcommitment. Reserved pending margin is included in used margin.
- Market buy fills at ask; market sell fills at bid on the first valid server tick after acceptance.
- Buy limit must be below current ask and triggers when ask is at or below limit. Sell limit must be above current bid and triggers when bid is at or above limit. Fill at the qualifying quote or better; never worse than the limit.
- Long positions mark/close at bid; short positions mark/close at ask. Gross P&L = signed units × (close/mark price − entry price). Net realized P&L subtracts explicitly configured fees and swap.
- Balance = initial capital + realized net P&L + authorized ledger adjustments. Equity = balance + unrealized net P&L. Free margin = equity − used margin.
- Long SL below entry and TP above entry; short SL above entry and TP below entry. Enforce configured minimum distance and price precision.
- SL/TP are evaluated against executable bid/ask on ordered ticks. Gaps fill at the next eligible quote, which can differ from the trigger. Do not infer both SL and TP from the same historical candle.
- Use decimal-safe arithmetic. Store price/quantity at instrument precision; round displayed USD amounts to two decimals without accumulating display-rounding errors in the ledger.
- If equity / used margin falls to 50% or below, cancel pending reservations, re-evaluate, then close positions from greatest loss until above the threshold. Show this as a simulator-specific rule; skip the ratio when used margin is zero.
- On engine restart, recover account/order state before resuming ticks. Do not invent fills during an unobserved outage. Record the outage interval and apply the next valid quote normally.
- Extend instruments only after defining currency conversion, session rules, contract multiplier, margin, fees, and rounding for that product.

## 9. Architecture and data model

Recommended starting architecture: a modular application backend, relational database, background execution worker, and authenticated price/event streaming. Avoid unnecessary microservices in the first release.

- **Web client:** responsive terminal, customer portal, and separately protected staff interface.
- **Identity layer:** sessions, recovery, verified identities, and staff MFA.
- **Trading service:** validation, idempotency, account serialization, orders, positions, and ledger.
- **Price service:** generated series initially; provider feeds behind an explicit adapter later.
- **Provider adapter:** capabilities, authorization, instruments, quotes, order submission/cancellation, positions, balances, event reconciliation.
- **Operations worker:** notifications, exports, provider callbacks, scheduled reconciliation, and exception handling.
- **Database:** users, roles, sessions, accounts, instrument specifications, quotes/candles, orders, execution events, positions, ledger entries, provider connections, workflow statuses, support tickets, and audit events.

Every financial record carries account ID, mode, source, timestamps, and correlation/reference identifiers. Enforce account ownership and mode boundaries on the server. Demo code must not fall through to live provider endpoints.

Browser storage may cache non-sensitive preferences; it is not the authoritative account ledger. Provider secrets remain server-side in appropriate secret storage. Technology/library versions are selected during implementation and recorded separately.

## 10. Order/event consistency requirements

Internal order lifecycle: draft → submitted → accepted → pending/partially-filled/filled, or rejected/cancelled/expired. Market orders can move directly from accepted to filled. Connection uncertainty is a reconciliation condition, not proof of rejection or fill.

- Persist request identity before external submission; retries use the same idempotency identity.
- Deduplicate execution events by provider/event identifiers and validate allowed state transitions.
- Reconcile broker orders, fills, positions, and balances after reconnect and on a provider-appropriate schedule.
- A successful HTTP response is not execution confirmation.
- A cancellation request is not cancellation until acknowledged; fills may win the race.
- Replay/recovery must produce the same ledger and positions without duplicate economic effects.
- Use UTC timestamps internally and clearly labeled display timezones in UI and exports.

## 11. UX and non-functional acceptance targets

- Desktop: watchlist, chart, ticket, and ledger visible together where space permits; allow resizing/collapsing.
- Mobile: Markets / Chart / Trade / Positions / Account navigation; preserve instrument context and unsent input within the same account.
- Verify 360px, 768px, and 1440px layouts. Primary actions must remain usable without page-level horizontal scrolling; wide tables may scroll within their own region.
- Keyboard access, visible focus, accessible names, adequate contrast, non-color status indicators, and text alternatives for critical chart/account values.
- Loading, empty, invalid, rejected, offline, stale, unauthorized, and uncertain-order states must be designed, not left as generic errors.
- Proposed R1 test envelope: 100 concurrent demo sessions; p95 internal order acknowledgment under 1 second, excluding broker latency; account ledger correctness is mandatory under retries and reconnects.
- Quotes older than the configured source threshold must be marked stale; default simulator threshold 5 seconds. Block new simulator orders while price source is unhealthy.
- Log service failures and correlation IDs without secrets or unnecessary personal data. Add health checks, backups, and a verified restore exercise before hosted beta.
- Rate-limit auth and order endpoints; validate server-side; protect session cookies, use HTTPS, restrict staff access, and verify account isolation.

## 12. Release acceptance scenarios

| ID | Scenario and required outcome |
|---|---|
| AC-01 | New user completes verified signup and receives exactly one initial demo allocation despite retries |
| AC-02 | Two sessions see the same account state; neither can access another user's account |
| AC-03 | Buy fills at ask, marks at bid; independently calculated P&L and margin match ledger values |
| AC-04 | Repeated submit with one idempotency key produces one order and one economic effect |
| AC-05 | Invalid size, price, SL/TP, or insufficient margin produces a specific rejection with no ledger mutation |
| AC-06 | Limit order fills only at an eligible quote; cancel/fill race leaves one coherent final outcome |
| AC-07 | SL/TP continues after browser close; reopening shows fills that occurred while disconnected |
| AC-08 | Engine restart recovers pending/open state without duplicate fills or invented outage ticks |
| AC-09 | Position close updates balance/equity/history; CSV totals agree with the ledger |
| AC-10 | Demo reset archives the previous session and initializes a new one once after confirmation |
| AC-11 | Stale/disconnected data is visible and blocks invalid submissions; recovery refreshes authoritative state |
| AC-12 | Account switching clears unsent orders and cannot send an order to the previous account |
| AC-13 | Staff access obeys role boundaries; administrative actions are auditable |
| AC-14 | Core signup/order/close/history journey works at all target viewport widths and with keyboard navigation |
| AC-15 | Provider sandbox tests reject, partial fill, duplicate callback, timeout, out-of-order event, and reconnect cases |
| AC-16 | Live/funding states change only from authenticated, reconciled provider evidence; redirects alone cannot credit funds |
| AC-17 | Disabled live capability cannot be reached by changing client state or directly calling an API |

R1 must pass AC-01 through AC-14 and the disabled-live portion of AC-17. R2 adds sandbox/provider cases. R3 requires all relevant live scenarios and operational launch review.

## 13. Delivery plan and dependencies

### Milestone 0 — Scope and design baseline

Deliver screen map, prioritized backlog, instrument assumptions, roles, data model, provider capability questionnaire, and interactive UX specification. Audit existing prototype behavior before reusing code. Resolve launch geography before choosing a live provider.

### Milestone 1 — Identity and durable demo account

Implement authentication, database, account ownership, onboarding, account ledger, customer dashboard, and basic staff access. Exit: signup, login, recovery, and cross-session persistence verified.

### Milestone 2 — Complete trading journey

Implement deterministic price/candle engine, market catalog, chart, ticket, execution worker, pending orders, SL/TP, positions, history, reset/archive, and CSV statements. Exit: AC-01 through AC-12 pass where applicable.

### Milestone 3 — Demo product beta

Complete mobile/accessibility states, support/notifications, operations tools, load checks, backup recovery, and usability testing. Exit: all R1 acceptance criteria pass; four of five beginner testers complete the main practice journey unaided and all identify simulated mode correctly.

### Milestone 4 — Provider feasibility and sandbox

Select provider; confirm user/instrument permissions, data rights, auth flow, capabilities, and order model. Integrate sandbox/demo if available, reconcile events, and validate failure handling. No assumption that MT4/MT5 integrations are included.

### Milestone 5 — Controlled live release

Complete broker-required review, applicable legal review, security assessment, operational runbooks, customer support ownership, live confirmations, and monitoring. Enable supported funding/verification flows only after their separate readiness checks.

### Milestone 6 — Optional expansion

Additional markets/providers, richer analytics, calendar/news, education, referrals, and native apps based on demonstrated demand and provider support.

No fixed delivery dates are committed until team capacity, stack, provider, and integration access are known.

## 14. Open decisions and implementation blockers

| Decision | Current assumption / required resolution | Blocks |
|---|---|---|
| Product role | Broker-connected customer app with own portal/admin; confirm commercial model | Live scope |
| Geography | Unconfirmed. v0.1 assumes U.S.; current README refers to India/Dhan | Provider and live launch |
| Provider | Not selected; README's Dhan note is historical workspace context, not verified current eligibility | R2/R3 |
| Instruments | R1 generated EUR/USD and GBP/USD; live catalog from permitted provider | Additional asset classes |
| Live position model | Adapter must declare netting/hedging and supported close/amend semantics | R2 |
| Funding and verification | Prefer provider-hosted workflows; capability unknown | R3 funding/KYC |
| Charting | Select component after validating features, licenses, and data terms | Chart implementation |
| Identity/hosting | Choose maintained auth and hosting appropriate for launch/data location | Hosted beta |
| Language | English UI initially; Tamil localization after string extraction | Localization only |
| Retention/support | Assign retention policy, incident ownership, and support coverage | Production launch |

These unresolved items do not prevent building the documented internal demo application. Do not infer provider availability or legal eligibility from the reference platform.

## 15. Current implementation and migration

The existing workspace is documented as a static prototype using `index.html`, `styles.css`, and `app.js`, with locally generated prices and browser persistence. This PRD update does not establish that its existing calculations or workflows have been tested.

- Retain useful layout and interaction patterns after code review.
- Replace local authoritative trading state with backend services and a database.
- Keep legacy local practice history separate; any import must be explicit, labeled, and must never create live balances or trades.
- Update README when implementation scope changes; remove contradictory market/provider assumptions through the decision process above.
- Preserve v0.1 as historical scope. Canonical user-requested document: `/Users/jeyaprakash/PROJECTS/PRD.md`; workspace copy: `/Users/jeyaprakash/PROJECTS/Forex/PRD.md`. Keep both copies synchronized until consolidated deliberately.

## 16. Definition of done

A milestone is done when its working user journeys, failure states, server authorization, data consistency, required acceptance scenarios, and operational documentation are complete. UI placeholders do not count as implemented integrations. Mark each unavailable provider feature explicitly. The complete live product requires customer workflows, broker-backed execution/data, and operational readiness together.
