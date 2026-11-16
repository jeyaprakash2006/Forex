# Implementation baseline — 15 November 2026

## Delivered increment

The current implementation replaces authoritative browser-local balances with a backend-controlled local multi-user demo application. This is a working slice of PRD milestones 1 and 2, not completion of the entire v0.2 specification.

### Architecture

- Vanilla HTML/CSS/JavaScript frontend retains the lightweight no-build development workflow.
- Python 3.13 standard-library backend exposes JSON routes and serves only three allowlisted frontend files.
- SQLite WAL database persists users, sessions, accounts, orders, ledger entries, idempotency results, price candles, and account events.
- One in-process execution worker ticks every second. The UI polls account state every 1.5 seconds and refreshes charts from server candles.
- A reentrant lock and explicit `BEGIN IMMEDIATE` transactions serialize ledger-changing operations. Decimal arithmetic stores economic values as decimal strings.
- Run one server process per database. Multi-process coordination, pagination, and production scale are future work.

### Data model

- `users`: id, name, normalized unique email, salt, scrypt hash, creation time.
- `sessions`: hashed bearer value, owner, expiry; browser receives an HttpOnly cookie.
- `accounts`: owner, balance, creation/archive time; unique active account per user.
- `orders`: account, symbol, side, order type, size, limit/SL/TP, lifecycle state, execution prices, realized result, margin, timestamps, close reason.
- `ledger`: initial allocation and realized events; records are appended, not modified during normal execution.
- `requests`: owner + idempotency key + request fingerprint + committed result.
- `quotes`, `candles`: authoritative generated price series and shared timeframe source.
- `events`: user-visible practice-account activity.

Separate-position order modeling is used: a filled order remains `open` until closed. There is no separate execution/fill table yet because the simulator only performs full fills. Provider integration will need that richer event model.

### HTTP contract

All mutations require JSON, `X-Northstar-Request: 1`, same-origin requests, and the allowed loopback host. Trading mutations also require `Idempotency-Key` and the current `account_id`.

| Method | Route | Input / output |
|---|---|---|
| POST | `/api/auth/register` | name, email, password → session cookie and one demo account |
| POST | `/api/auth/login` | email, password → expiring session cookie |
| POST | `/api/auth/logout` | empty object → current session revoked |
| GET | `/api/state` | authenticated snapshot of user, active account, totals, orders, markets, activity, archive references |
| GET | `/api/candles?symbol=EURUSD&interval=15` | ordered generated bid OHLC array; interval in 1/5/15/60/240 minutes |
| POST | `/api/orders` | account_id, symbol, side, kind, lots, optional limit_price/sl/tp → durable order result |
| POST | `/api/orders/cancel` | account_id, id → acknowledged pending-order cancellation |
| POST | `/api/positions/close` | account_id, id → close result and realized P&L |
| POST | `/api/positions/risk` | account_id, id, sl, tp → protection updated; null removes a level |
| POST | `/api/accounts/reset` | account_id → old account archived, one new allocation |
| GET | `/api/history?account=ID` | owned current/archived account orders |
| GET | `/api/statement.csv?account=ID` | complete account order export; USD and UTC fields |
| GET | `/api/health` | local service health and simulated-mode label |

No live or funding API exists. Browser `success` state never credits an account. Changing the displayed mode cannot enable live execution.

### Financial defaults

EUR/USD and GBP/USD only; USD account; 100,000 base units per lot; size 0.01–1.00 in increments of 0.01; simulated 1:20 leverage; spread 1.2 and 1.5 pips respectively; zero fee/swap; initial USD 10,000.

Buy fills at ask and marks/closes at bid; sell fills at bid and marks/closes at ask. Limit fills occur only at a qualifying executable quote. Pending margin is reserved; funds are rechecked at fill. SL/TP are evaluated per server tick, with a 0.00020 minimum placement distance. Gap exits use the available quote. Equity at or below 50% of used margin triggers pending cancellation, re-evaluation, and loss-ordered closure as needed.

A deterministic illustrative series seeds initial candle history. Restarts recover durable state and process the next current quote, without replaying imagined fills during an outage. The simulator is explicitly not a liquidity model or a strategy backtesting engine.

### Acceptance progress

| PRD scenarios | Current evidence |
|---|---|
| AC-01 | Account allocation/deduplication covered; verified-email signup remains open |
| AC-02–06 | Core isolation, calculations, retry, validation, limit/cancel cases covered by tests |
| AC-07–08 | Engine runs independently of browser; tick-trigger tests and restart recovery covered |
| AC-09–10 | Close ledger/CSV and reset/archive covered; report UI smoke-tested |
| AC-11–12 | Stale quote and stale-account validation covered; multi-account switching UI not implemented |
| AC-13 | Staff/admin role model not implemented |
| AC-14 | Responsive checks and focus-preserving updates implemented; formal keyboard/accessibility audit remains |
| AC-15–16 | Provider integration not implemented |
| AC-17 | Unavailable live endpoints verified |

### Next development sequence

1. Introduce maintained identity service for verified email/recovery, staff MFA, revocable session management, and role boundaries.
2. Add basic staff console, support workflow, audit events, backup/restore verification, and deployment transport.
3. Complete chart tools/preferences, pending amendments, report pagination/date filters, accessibility review, and measured load targets.
4. Select broker and launch geography; implement provider capability contract, sandbox authorization, and order reconciliation.
5. Proceed through documented live/funding readiness gates.

No provider credentials or production secrets are present. Original static sources are preserved in `docs/prototype-v0/`; original PRD in `docs/PRD-v0.1.md`.
