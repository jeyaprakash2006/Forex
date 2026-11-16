from backend.market_data import MarketData
"""Loopback-only development HTTP server; production transport is a later milestone."""
import csv
import io
import json
import logging
import os
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from .engine import DomainError, Engine

ROOT = Path(__file__).resolve().parents[1]
STATIC = {'/': ('index.html', 'text/html'), '/app.js': ('app.js', 'text/javascript'),
          '/styles.css': ('styles.css', 'text/css'), '/chart.js': ('chart.js', 'text/javascript'),
          '/assets/avatar.svg': ('assets/avatar.svg', 'image/svg+xml'),
          '/assets/fonts/tasa-orbiter-regular.ttf': ('assets/fonts/tasa-orbiter-regular.ttf', 'font/ttf'),
          '/assets/fonts/tasa-orbiter-semibold.ttf': ('assets/fonts/tasa-orbiter-semibold.ttf', 'font/ttf')}


class AppServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, engine):
        self.engine = engine
        self.market_data = MarketData()
        self.rates = defaultdict(deque)
        self.rate_lock = threading.Lock()
        super().__init__(address, Handler)
        self.origin_hosts = {f'localhost:{self.server_port}', f'127.0.0.1:{self.server_port}'}

    def rate_limit(self, address, group, limit):
        with self.rate_lock:
            bucket = self.rates[(address, group)]
            now = time.time()
            while bucket and bucket[0] < now - 60:
                bucket.popleft()
            if len(bucket) >= limit:
                raise DomainError('Too many requests. Please wait a minute.', 429)
            bucket.append(now)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Never include cookies, request bodies, or query parameters in access logs.
        logging.info('%s %s', self.command, urlsplit(self.path).path)

    def response(self, status, value, content_type='application/json', cookie=None, filename=None):
        raw = json.dumps(value).encode() if content_type == 'application/json' else value
        self.send_response(status)
        self.send_header('Content-Type', content_type + '; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if cookie is not None:
            self.send_header('Set-Cookie', f'ns_session={cookie}; HttpOnly; SameSite=Strict; Path=/; Max-Age={604800 if cookie else 0}')
        if filename:
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(raw)

    def token(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get('Cookie', ''))
            return cookie['ns_session'].value if 'ns_session' in cookie else ''
        except Exception:
            return ''

    def validate_host(self):
        if self.headers.get('Host') not in self.server.origin_hosts:
            raise DomainError('Invalid host.', 403)

    def payload(self):
        if self.headers.get('X-Northstar-Request') != '1':
            raise DomainError('Missing request protection header.', 403)
        origin = self.headers.get('Origin')
        if origin and origin not in {f'http://{h}' for h in self.server.origin_hosts}:
            raise DomainError('Cross-origin request blocked.', 403)
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            raise DomainError('JSON request required.', 415)
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            raise DomainError('Invalid request length.')
        if not 0 < length <= 8192:
            raise DomainError('Request is too large or empty.', 413)
        self.connection.settimeout(5)
        try:
            data = json.loads(self.rfile.read(length))
        except (ValueError, TimeoutError):
            raise DomainError('Invalid JSON request.')
        if not isinstance(data, dict):
            raise DomainError('JSON object required.')
        return data

    def do_GET(self):
        self.dispatch(False)

    def do_POST(self):
        self.dispatch(True)

    def dispatch(self, mutation):
        try:
            self.validate_host()
            url = urlsplit(self.path)
            path, query = url.path, parse_qs(url.query)
            engine = self.server.engine
            if not mutation and path in STATIC:
                file, mime = STATIC[path]
                return self.response(200, (ROOT / file).read_bytes(), mime)
            if not mutation and path == '/api/health':
                return self.response(200, {'status': 'ok', 'mode': 'simulated'})
            if not path.startswith('/api/'):
                raise DomainError('Not found.', 404)
            data = self.payload() if mutation else None
            if mutation and path in ('/api/auth/register', '/api/auth/login'):
                self.server.rate_limit(self.client_address[0], 'auth', 15)
                token = engine.register(data) if path.endswith('register') else engine.login(data)
                return self.response(200, {'ok': True}, cookie=token)
            token = self.token()
            user_id = engine.authenticate(token)
            if not mutation and path == '/api/live/quotes':
                return self.response(200, self.server.market_data.quotes())
            if not mutation and path == '/api/live/candles':
                try:
                    interval = int(query.get('interval', ['1'])[0])
                except ValueError:
                    raise DomainError('Invalid live interval.')
                return self.response(200, self.server.market_data.candles(query.get('symbol',['ETCUSD'])[0], interval))
            if mutation:
                self.server.rate_limit(user_id, 'write', 90)
                if path == '/api/auth/logout':
                    engine.logout(token)
                    return self.response(200, {'ok': True}, cookie='')
                if path == '/api/support':
                    return self.response(200,engine.support(user_id,data))
                if path == '/api/admin':
                    return self.response(200,engine.admin(user_id,data))
                if path == '/api/profile':
                    return self.response(200, engine.profile_update(user_id,data))
                if path == '/api/auth/password':
                    self.server.rate_limit(user_id,'password',5)
                    return self.response(200,engine.change_password(user_id,token,data))
                if path == '/api/auth/sessions/revoke':
                    return self.response(200,engine.revoke_session(user_id,data.get('id')))
                operations = {'/api/orders/amend': 'amend', '/api/orders': 'order', '/api/orders/cancel': 'cancel', '/api/positions/close': 'close',
                              '/api/positions/risk': 'risk', '/api/accounts/reset': 'reset'}
                if path not in operations:
                    raise DomainError('Action unavailable in this demo build.', 404)
                result = engine.mutation(user_id, self.headers.get('Idempotency-Key'), operations[path], data)
                return self.response(200, result)
            if path == '/api/support':
                return self.response(200,engine.support(user_id))
            if path == '/api/admin':
                return self.response(200,engine.admin(user_id))
            if path == '/api/auth/sessions':
                return self.response(200,engine.session_list(user_id,token))
            if path == '/api/state':
                return self.response(200, engine.state(user_id))
            if path == '/api/candles':
                try:
                    interval = int(query.get('interval', ['1'])[0])
                except ValueError:
                    raise DomainError('Invalid interval.')
                return self.response(200, engine.candles(query.get('symbol', ['EURUSD'])[0], interval))
            if path == '/api/history':
                account, orders = engine.statement(user_id, query.get('account', [None])[0])
                return self.response(200, {'account': account, 'orders': orders})
            if path == '/api/statement.csv':
                account, orders = engine.statement(user_id, query.get('account', [None])[0])
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(['account', 'mode', 'source', 'order_id', 'symbol', 'side', 'lots', 'type', 'status',
                                 'entry', 'exit', 'net_pnl_usd', 'opened_utc', 'closed_utc', 'reason', 'leverage', 'fees_usd', 'swap_usd'])
                for o in orders:
                    dates = [datetime.fromtimestamp(o[k], timezone.utc).isoformat() if o[k] else '' for k in ('opened', 'closed')]
                    writer.writerow([account['id'], 'paper', 'generated', o['id'], o['symbol'], o['side'], o['lots'], o['kind'], o['status'],
                                     o['entry'], o['exit'], o['pnl'], *dates, o['reason'], '1:20', '0', '0'])
                return self.response(200, output.getvalue().encode(), 'text/csv', filename='northstar-demo-statement.csv')
            raise DomainError('Not found.', 404)
        except DomainError as exc:
            self.response(exc.status, {'error': str(exc)})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            logging.exception('Request failed')
            self.response(500, {'error': 'Something went wrong. Refresh to reconcile your account before retrying.'})


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    engine = Engine(os.environ.get('NORTHSTAR_DB', str(ROOT / 'data' / 'northstar.sqlite3')))
    server = AppServer(('127.0.0.1', int(os.environ.get('NORTHSTAR_PORT', '8000'))), engine)
    stop = threading.Event()

    def worker():
        while not stop.wait(1):
            try:
                engine.tick()
            except Exception:
                logging.exception('Simulator tick failed; stale-feed protection will block orders')

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    print(f'Northstar FX → http://127.0.0.1:{server.server_port} (local demo only)', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        thread.join(timeout=5)
        server.server_close()
        engine.db.close()


if __name__ == '__main__':
    main()
