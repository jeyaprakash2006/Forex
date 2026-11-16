# Northstar FX — Full-stack practice terminal

A runnable local development increment of the v0.2 PRD: a customer dashboard, trading terminal, reports, and account screen backed by an authoritative SQLite demo ledger.

Prices are generated and funds are virtual. No broker is connected. There are no deposit, withdrawal, or live execution endpoints.

## Current reference rebuild

The UI now follows the inspected TradeWill terminal/account-center structure. See [reference parity status](docs/REFERENCE-PARITY.md) for implemented controls and remaining gaps. This supersedes the initial increment details below where noted: seven demo instruments, five indicators, drawing tools, and expanded timeframes are now present. **Exact end-to-end parity is not complete.**

## Run

Requires **Python 3.13+ with OpenSSL/scrypt**. There are no third-party Python or JavaScript dependencies and no build step.

```sh
cd /Users/jeyaprakash/PROJECTS/Forex
python3.13 -m backend.server
```

Open [Northstar FX](http://127.0.0.1:8000). Choose **Create account** to create a local practice account with $10,000 virtual funds. Existing local accounts can sign in. Email addresses are identifiers only; this build does not send or verify email.

If `python3` on your machine is Python 3.13 or newer with scrypt support, it can be used instead. On the development machine, system `python3` is older; `python3.13` is the correct executable.

Optional Node convenience commands:

```sh
npm start
npm test
npm run check
```

No `npm install` is required. Stop the server with Ctrl+C. Restarting preserves accounts, sessions, orders, and history. Orders process while the server runs, including when the browser is closed. Stopping the server stops simulated execution; restart does not backfill fills during downtime.

## Implemented in this increment

- Registration, salted scrypt password hashes, expiring HttpOnly/SameSite sessions, sign-in, logout, account ownership checks.
- Separate customer accounts with SQLite persistence; initial allocation recorded once.
- Seven demo instruments with instrument-specific contracts and precision, generated bid/ask feeds, and server-owned candles.
- 1m, 5m, 15m, 1h, 4h chart aggregation; MA(9), MACD(12,26,9), OHLC hover, fullscreen.
- Market and limit buy/sell orders; explicit review before submission; idempotent mutations.
- Lot and price validation; free-margin checks; pending margin reservation; fill-time margin revalidation.
- Executable bid/ask P&L, SL/TP triggering, position protection editing, close, cancellation, and margin stop-out.
- Open/pending/history tables, overview balances and activity, instrument/status report filters, full-account CSV exports.
- Confirmed demo reset closes/cancels current activity and archives the old account. Archived reports/CSV remain available to their owner.
- Market search, browser-local favorites, responsive desktop/tablet/mobile layout, keyboard focus preservation during polling.
- Stale-feed order blocking, basic request throttling, same-origin mutation protections, CSP, static-file allowlist.

## Code map

```text
Forex/
├── index.html                 Customer screens and accessible form structure
├── styles.css                 Responsive terminal and portal styling
├── app.js                     UI, chart rendering, API integration
├── backend/
│   ├── engine.py              Auth, SQLite, Decimal ledger, simulation/execution
│   └── server.py              Loopback HTTP API, worker, security boundaries
├── tests/
│   ├── test_engine.py         Financial rules, persistence, isolation, idempotency
│   └── test_http.py           HTTP access/CSRF/static boundaries and concurrency
├── docs/
│   ├── IMPLEMENTATION.md      Architecture, route contract, milestone status
│   ├── PRD-v0.1.md            Original specification
│   └── prototype-v0/          Original static prototype source
├── data/                      Runtime SQLite database (ignored)
├── .env.example               Optional environment settings
├── requirements.txt           Standard-library-only runtime requirement
└── PRD.md                     Full product roadmap, not all implemented yet
```

## Configuration

No secrets or external services are required for this local increment. Environment variables are read directly from the shell; `.env` is not loaded automatically.

| Variable | Default | Purpose |
|---|---|---|
| `NORTHSTAR_PORT` | `8000` | Loopback HTTP port |
| `NORTHSTAR_DB` | `data/northstar.sqlite3` under this project | Persistent SQLite file |

Example:

```sh
NORTHSTAR_PORT=8001 NORTHSTAR_DB=/tmp/northstar-development.sqlite3 python3.13 -m backend.server
```

Never delete the database to reset a user's account; use the account screen so prior history remains accessible. For local backup, stop the server cleanly and copy the `data` directory. Formal backup/restore automation is not implemented yet.

## Tests and observed verification

```sh
python3.13 -m unittest discover -s tests -v
node --check app.js
```

19 backend and 3 indicator tests passed on 15 November 2026. Coverage includes exact bid/ask results, long/short P&L, margin, limit triggers, cancellation races, SL/TP gap fills, stop-out, stale quotes, account isolation, duplicate requests, concurrent HTTP submissions, reset archival, restart persistence, session revocation, CSV delivery, host/origin validation, and blocked private-file access.

Browser smoke testing also completed registration → market-order review/submit → close → realized report; limit submit → cancel; dashboard and report rendering; server restart with retained session/balance. Screens were inspected at 360px, 768px, and 1440px. Mobile and tablet DOM checks showed no page-level horizontal overflow. No browser error logs were returned in the final inspected session. This is not a full accessibility audit or a load benchmark.

A local `demo-review@example.test` test account and its small virtual-trade history were created for browser verification. The preview remains signed into that account; sign out and create your own account if desired.

## Scope remaining

This is a **local development build**, not the finished R1 or a production/live release. In particular:

- Email verification, recovery, MFA, device/session-management UI, and production identity-provider integration.
- Staff/admin console, support tickets, external notifications, operational runbooks, monitored backup/restore.
- Full reference indicator/tool coverage and long-range historical data; current independent chart supports MA/EMA/MACD/RSI/Bollinger Bands, drawing tools, zoom/pan, and browser-local preferences.
- Pending-order amendment (cancel/recreate is currently available), partial closes/fills, provider-specific lifecycle reconciliation.
- Server-side favorites, multiple simultaneous active accounts, richer report/date filters, pagination/retention policies.
- Broker APIs, live quotes/orders, verification, funding, transfers, payment services.
- Public hosting, production transport, horizontal scale, and the PRD's 100-session performance target.

The server deliberately binds to `127.0.0.1`. Python's built-in HTTP server is used for local development only; replace it with a production application transport, HTTPS, and hardened identity before hosted beta. See [Python HTTP server documentation](https://docs.python.org/3.13/library/http.server.html).

The PRD's launch-market/provider questions remain open. No U.S., India, or Dhan eligibility is assumed by the code.

### Account settings and local support

Settings now supports profile editing, password changes and session revocation. Pending limits can be modified from the terminal; Reports includes date filters. Customer Service saves local requests; authorized staff can reply and update their status with audit records.

To assign a registered local operator explicitly:

```sh
python3.13 -m backend.manage grant-staff operator@example.test
python3.13 -m backend.manage revoke-staff operator@example.test
```

Use the actual registered operator email. No staff role is granted automatically. `NORTHSTAR_DB` or `--db` selects the database. Refresh the app to see Operations in the profile menu. This is a local development console, not a production brokerage administration system. Staff MFA, support submission idempotency and queue pagination remain outstanding.

Latest validation: 25 Python tests + 3 JavaScript tests pass; JavaScript syntax checks pass. See `docs/REFERENCE-PARITY.md` for the complete remaining scope.
