"""Authoritative demo execution engine. Decimal amounts are stored as text."""
import hashlib
import json
import math
import re
import secrets
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
from pathlib import Path

D = Decimal
CATALOG = {
    'EURUSD': {'symbol': 'EUR/USD', 'name': 'Euro / US Dollar', 'icon': '€', 'base': 108420, 'spread': 12, 'category': 'Forex', 'digits': 5, 'contract': 100000, 'max_lots': 1},
    'GBPUSD': {'symbol': 'GBP/USD', 'name': 'British Pound / US Dollar', 'icon': '£', 'base': 127180, 'spread': 15, 'category': 'Forex', 'digits': 5, 'contract': 100000, 'max_lots': 1},
    'BTCUSD': {'symbol': 'BTC/USDT', 'name': 'Bitcoin / Tether · USD-settled demo', 'icon': '₿', 'base': 6400000000, 'spread': 1010000, 'category': 'Crypto', 'digits': 2, 'contract': 1, 'max_lots': 5},
    'ETCUSD': {'symbol': 'ETC/USDT', 'name': 'Ethereum Classic / Tether · USD-settled demo', 'icon': '⟠', 'base': 570000, 'spread': 1100, 'category': 'Crypto', 'digits': 3, 'contract': 100, 'max_lots': 5},
    'ETHUSD': {'symbol': 'ETH/USDT', 'name': 'Ethereum / Tether · USD-settled demo', 'icon': 'Ξ', 'base': 175000000, 'spread': 150000, 'category': 'Crypto', 'digits': 2, 'contract': 1, 'max_lots': 5},
    'SOLUSD': {'symbol': 'SOL/USDT', 'name': 'Solana / Tether · USD-settled demo', 'icon': '◎', 'base': 6900000, 'spread': 8000, 'category': 'Crypto', 'digits': 3, 'contract': 10, 'max_lots': 5},
    'XAUUSD': {'symbol': 'XAUUSD', 'name': 'Gold / US Dollar', 'icon': 'Au', 'base': 387700000, 'spread': 35000, 'category': 'Metals', 'digits': 2, 'contract': 100, 'max_lots': 1},
}



class DomainError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def identifier():
    return uuid.uuid4().hex


def decimal(value, label, optional=False):
    if optional and value in (None, ''):
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float)) or len(str(value)) > 32:
        raise DomainError(f'Enter a valid {label}.')
    try:
        result = D(str(value))
    except InvalidOperation:
        raise DomainError(f'Enter a valid {label}.')
    if not result.is_finite() or result <= 0 or result > 1000000:
        raise DomainError(f'Enter a positive, finite {label}.')
    return result


class Engine:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.db = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
        PRAGMA journal_mode=WAL;
        PRAGMA foreign_keys=ON;
        CREATE TABLE IF NOT EXISTS users (
          id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
          salt TEXT NOT NULL, password TEXT NOT NULL, created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions (
          hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS accounts (
          id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), balance TEXT NOT NULL,
          created REAL NOT NULL, archived REAL);
        CREATE UNIQUE INDEX IF NOT EXISTS active_account ON accounts(user_id) WHERE archived IS NULL;
        CREATE TABLE IF NOT EXISTS orders (
          id TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id), symbol TEXT NOT NULL,
          side TEXT NOT NULL, kind TEXT NOT NULL, lots TEXT NOT NULL, limit_price TEXT,
          sl TEXT, tp TEXT, status TEXT NOT NULL, entry TEXT, exit TEXT, pnl TEXT,
          margin TEXT NOT NULL, created REAL NOT NULL, opened REAL, closed REAL, reason TEXT);
        CREATE TABLE IF NOT EXISTS ledger (
          id TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id), order_id TEXT,
          amount TEXT NOT NULL, kind TEXT NOT NULL, created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS requests (
          user_id TEXT NOT NULL, key TEXT NOT NULL, fingerprint TEXT NOT NULL, result TEXT NOT NULL,
          PRIMARY KEY(user_id,key));
        CREATE TABLE IF NOT EXISTS quotes (symbol TEXT PRIMARY KEY, bid INTEGER NOT NULL, updated REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS candles (
          symbol TEXT NOT NULL, minute INTEGER NOT NULL, open INTEGER, high INTEGER, low INTEGER, close INTEGER,
          PRIMARY KEY(symbol, minute));
        CREATE TABLE IF NOT EXISTS staff (user_id TEXT PRIMARY KEY REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS tickets (id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),subject TEXT NOT NULL,body TEXT NOT NULL,status TEXT NOT NULL,created REAL NOT NULL,updated REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS replies (id TEXT PRIMARY KEY,ticket_id TEXT NOT NULL REFERENCES tickets(id),actor TEXT NOT NULL,body TEXT NOT NULL,created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS admin_audit (id TEXT PRIMARY KEY,actor TEXT NOT NULL,action TEXT NOT NULL,target TEXT NOT NULL,created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS events (
          id TEXT PRIMARY KEY, account_id TEXT NOT NULL, message TEXT NOT NULL, created REAL NOT NULL);
        ''')
        # Fresh install gets explicitly illustrative history; restarts do not replay missed executions.
        with self.transaction():
            for symbol in CATALOG:
                if not self.db.execute('SELECT 1 FROM quotes WHERE symbol=?', (symbol,)).fetchone():
                    end = int(time.time() // 60)
                    for minute in range(end - 2880, end + 1):
                        samples = [self.price(symbol, min(minute * 60 + i, time.time())) for i in (0, 15, 30, 45, 59)]
                        self.db.execute('INSERT INTO candles VALUES(?,?,?,?,?,?)',
                                        (symbol, minute, samples[0], max(samples), min(samples), samples[-1]))
                    self.db.execute('INSERT INTO quotes VALUES(?,?,?)', (symbol, self.price(symbol, time.time()), 0))
            self.db.execute('DELETE FROM sessions WHERE expires<?', (time.time(),))
        self.tick()

    @contextmanager
    def transaction(self):
        with self.lock:
            self.db.execute('BEGIN IMMEDIATE')
            try:
                yield
                self.db.execute('COMMIT')
            except Exception:
                self.db.execute('ROLLBACK')
                raise

    @staticmethod
    def price(symbol, stamp):
        base = CATALOG[symbol]['base']
        phase = 0 if symbol == 'EURUSD' else 2.4
        scale = 1 if symbol in ('EURUSD', 'GBPUSD') else base / 108420
        raw = base + round(scale * (160 * math.sin(stamp / 1500 + phase) +
                            70 * math.sin(stamp / 180 + phase) + 14 * math.sin(stamp / 14)))
        step = 10 ** (5 - CATALOG[symbol]['digits'])
        return round(raw / step) * step

    def quote(self, symbol):
        row = self.db.execute('SELECT * FROM quotes WHERE symbol=?', (symbol,)).fetchone()
        if not row:
            raise DomainError('Instrument is not available.')
        return D(row['bid']) / 100000, D(row['bid'] + CATALOG[symbol]['spread']) / 100000, row['updated']

    def ensure_fresh(self, symbol):
        if time.time() - self.quote(symbol)[2] > 5:
            raise DomainError('Price feed is stale. Try again when the simulator reconnects.', 409)

    def event(self, account_id, message):
        self.db.execute('INSERT INTO events VALUES(?,?,?,?)', (identifier(), account_id, message, time.time()))

    def new_account(self, user_id):
        account_id = identifier()
        self.db.execute('INSERT INTO accounts VALUES(?,?,?,?,NULL)', (account_id, user_id, '10000', time.time()))
        self.db.execute('INSERT INTO ledger VALUES(?,?,?,?,?,?)',
                        (identifier(), account_id, None, '10000', 'initial_allocation', time.time()))
        self.event(account_id, 'Practice account opened with $10,000 virtual funds.')
        return account_id

    def register(self, data):
        name = data.get('name', '')
        email = data.get('email', '')
        password = data.get('password', '')
        if not isinstance(name, str) or not 2 <= len(name.strip()) <= 60:
            raise DomainError('Name must contain 2–60 characters.')
        if not isinstance(email, str) or len(email) > 254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
            raise DomainError('Enter a valid email address.')
        if not isinstance(password, str) or not 10 <= len(password) <= 128:
            raise DomainError('Use a password with 10–128 characters.')
        salt = secrets.token_hex(16)
        hashed = self.hash_password(password, salt)
        with self.transaction():
            user_id = identifier()
            try:
                self.db.execute('INSERT INTO users VALUES(?,?,?,?,?,?)',
                                (user_id, name.strip(), email.strip().lower(), salt, hashed, time.time()))
            except sqlite3.IntegrityError:
                raise DomainError('Unable to register with these details. Try signing in.', 409)
            self.new_account(user_id)
            return self.new_session(user_id)

    @staticmethod
    def hash_password(password, salt):
        return hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1, dklen=64).hex()

    def new_session(self, user_id):
        token = secrets.token_urlsafe(32)
        self.db.execute('INSERT INTO sessions VALUES(?,?,?)',
                        (hashlib.sha256(token.encode()).hexdigest(), user_id, time.time() + 86400 * 7))
        return token

    def login(self, data):
        email, password = data.get('email', ''), data.get('password', '')
        if not isinstance(email, str) or not isinstance(password, str) or len(password) > 128 or len(email) > 254:
            raise DomainError('Invalid email or password.', 401)
        with self.lock:
            user = self.db.execute('SELECT * FROM users WHERE email=?', (email.strip().lower(),)).fetchone()
        candidate = self.hash_password(password, user['salt'] if user else '0' * 32)
        if not user or not secrets.compare_digest(candidate, user['password']):
            raise DomainError('Invalid email or password.', 401)
        with self.transaction():
            return self.new_session(user['id'])

    def authenticate(self, token):
        with self.lock:
            row = self.db.execute('SELECT user_id FROM sessions WHERE hash=? AND expires>?',
                                  (hashlib.sha256(token.encode()).hexdigest(), time.time())).fetchone()
            if not row:
                raise DomainError('Please sign in to continue.', 401)
            return row['user_id']

    def logout(self, token):
        with self.transaction():
            self.db.execute('DELETE FROM sessions WHERE hash=?', (hashlib.sha256(token.encode()).hexdigest(),))

    def is_staff(self, user_id):
        return bool(self.db.execute('SELECT 1 FROM staff WHERE user_id=?',(user_id,)).fetchone())

    def support(self, user_id, data=None):
        with self.transaction():
            if data is not None:
                subject, body = data.get('subject'), data.get('body')
                if not isinstance(subject,str) or not 3<=len(subject.strip())<=120 or not isinstance(body,str) or not 10<=len(body.strip())<=4000:
                    raise DomainError('Use a subject of 3–120 characters and a message of 10–4,000 characters.')
                now=time.time()
                self.db.execute('INSERT INTO tickets VALUES(?,?,?,?,?,?,?)',(identifier(),user_id,subject.strip(),body.strip(),'open',now,now))
            rows=[dict(r) for r in self.db.execute('SELECT * FROM tickets WHERE user_id=? ORDER BY updated DESC LIMIT 100',(user_id,))]
            for row in rows:
                row['replies']=[dict(r) for r in self.db.execute('SELECT body,created FROM replies WHERE ticket_id=? ORDER BY created',(row['id'],))]
            return rows

    def admin(self, user_id, data=None):
        with self.transaction():
            if not self.is_staff(user_id):
                raise DomainError('Staff access required.',403)
            if data is not None:
                ticket_id, reply, status=data.get('id'),data.get('reply',''),data.get('status')
                if not isinstance(ticket_id,str) or not isinstance(reply,str) or len(reply)>4000 or status not in ('open','in_progress','resolved'):
                    raise DomainError('Invalid ticket update.')
                ticket=self.db.execute('SELECT * FROM tickets WHERE id=?',(ticket_id,)).fetchone()
                if not ticket: raise DomainError('Ticket not found.',404)
                if reply.strip():
                    self.db.execute('INSERT INTO replies VALUES(?,?,?,?,?)',(identifier(),ticket_id,user_id,reply.strip(),time.time()))
                self.db.execute('UPDATE tickets SET status=?,updated=? WHERE id=?',(status,time.time(),ticket_id))
                self.db.execute('INSERT INTO admin_audit VALUES(?,?,?,?,?)',(identifier(),user_id,'ticket_update',ticket_id,time.time()))
                self.event(self.active_account(ticket['user_id'])['id'],f"Support request updated: {ticket['subject']}")
            return {'tickets':[dict(r) for r in self.db.execute('SELECT t.*,u.name,u.email FROM tickets t JOIN users u ON u.id=t.user_id ORDER BY t.updated DESC LIMIT 100')],
                    'users':[dict(r) for r in self.db.execute('SELECT id,name,email,created FROM users ORDER BY created DESC LIMIT 100')],
                    'audit':[dict(r) for r in self.db.execute('SELECT * FROM admin_audit ORDER BY created DESC LIMIT 100')]}

    def profile_update(self, user_id, data):
        name = data.get('name')
        if not isinstance(name, str) or not 2 <= len(name.strip()) <= 60:
            raise DomainError('Name must contain 2–60 characters.')
        with self.transaction():
            self.db.execute('UPDATE users SET name=? WHERE id=?', (name.strip(), user_id))
            self.event(self.active_account(user_id)['id'], 'Profile name updated.')
        return {'ok': True}

    def session_list(self, user_id, token):
        current = hashlib.sha256(token.encode()).hexdigest()
        with self.lock:
            rows = self.db.execute('SELECT hash,expires FROM sessions WHERE user_id=? AND expires>? ORDER BY expires DESC', (user_id,time.time())).fetchall()
            return [{'id': hashlib.sha256((r['hash'] + ':public').encode()).hexdigest(),
                     'expires': r['expires'], 'current': r['hash'] == current} for r in rows]

    def revoke_session(self, user_id, session_id):
        if not isinstance(session_id, str):
            raise DomainError('Invalid session.')
        with self.transaction():
            rows = self.db.execute('SELECT hash FROM sessions WHERE user_id=?', (user_id,)).fetchall()
            for r in rows:
                if hashlib.sha256((r['hash'] + ':public').encode()).hexdigest() == session_id:
                    self.db.execute('DELETE FROM sessions WHERE hash=? AND user_id=?', (r['hash'],user_id))
                    return {'ok': True}
            raise DomainError('Session not found.', 404)

    def change_password(self, user_id, token, data):
        old, new = data.get('current_password'), data.get('new_password')
        if not isinstance(old, str) or len(old)>128 or not isinstance(new,str) or not 10<=len(new)<=128:
            raise DomainError('Enter your current password and a new password with 10–128 characters.')
        with self.transaction():
            user = self.db.execute('SELECT salt,password FROM users WHERE id=?',(user_id,)).fetchone()
            if not secrets.compare_digest(self.hash_password(old,user['salt']),user['password']):
                raise DomainError('Current password is incorrect.',403)
            salt = secrets.token_hex(16)
            self.db.execute('UPDATE users SET salt=?,password=? WHERE id=?',(salt,self.hash_password(new,salt),user_id))
            self.db.execute('DELETE FROM sessions WHERE user_id=? AND hash<>?',(user_id,hashlib.sha256(token.encode()).hexdigest()))
            self.event(self.active_account(user_id)['id'],'Password changed; other sessions revoked.')
        return {'ok': True}

    def active_account(self, user_id, expected=None):
        row = self.db.execute('SELECT * FROM accounts WHERE user_id=? AND archived IS NULL', (user_id,)).fetchone()
        if not row or (expected is not None and expected != row['id']):
            raise DomainError('Account changed. Refresh before continuing.', 409)
        return row

    def orders(self, account_id):
        return [dict(r) for r in self.db.execute('SELECT * FROM orders WHERE account_id=? ORDER BY created DESC,id', (account_id,))]

    def pnl(self, order):
        bid, ask, _ = self.quote(order['symbol'])
        mark = bid if order['side'] == 'buy' else ask
        result = (mark - D(order['entry'])) * D(order['lots']) * CATALOG[order['symbol']]['contract'] * (1 if order['side'] == 'buy' else -1)
        return result, mark

    def totals(self, account):
        orders = self.orders(account['id'])
        floating = sum((self.pnl(o)[0] for o in orders if o['status'] == 'open'), D(0))
        used = sum((D(o['margin']) for o in orders if o['status'] in ('open', 'pending')), D(0))
        balance = D(account['balance'])
        return {'balance': str(balance), 'equity': str(balance + floating), 'unrealized': str(floating),
                'used_margin': str(used), 'free_margin': str(balance + floating - used)}

    def state(self, user_id):
        with self.lock:
            user = dict(self.db.execute('SELECT id,name,email FROM users WHERE id=?', (user_id,)).fetchone())
            account = self.active_account(user_id)
            orders = self.orders(account['id'])
            for o in orders:
                if o['status'] == 'open':
                    pnl, mark = self.pnl(o)
                    o.update(unrealized=str(pnl), mark=str(mark))
            markets = []
            for key, meta in CATALOG.items():
                bid, ask, updated = self.quote(key)
                baseline = D(self.price(key, int(time.time() // 86400) * 86400 - 1)) / 100000
                day = self.db.execute('SELECT MAX(high), MIN(low) FROM candles WHERE symbol=? AND minute>=?', (key, int(time.time()//60)-1440)).fetchone()
                markets.append(dict(meta, high=str(D(day[0] or 0)/100000), low=str(D(day[1] or 0)/100000), id=key, bid=str(bid), ask=str(ask), updated=updated,
                                    change=float((bid / baseline - 1) * 100)))
            return {'user': user, 'account': dict(account), 'totals': self.totals(account), 'orders': orders,
                    'markets': markets, 'server_time': time.time(), 'mode': 'simulated', 'is_staff': self.is_staff(user_id),
                    'events': [dict(r) for r in self.db.execute('SELECT * FROM events WHERE account_id=? ORDER BY created DESC LIMIT 20', (account['id'],))],
                    'archives': [dict(r) for r in self.db.execute('SELECT id,balance,created,archived FROM accounts WHERE user_id=? AND archived IS NOT NULL ORDER BY archived DESC', (user_id,))]}

    def candles(self, symbol, interval):
        if symbol not in CATALOG or interval not in (1, 5, 15, 30, 60, 240, 1440, 10080, 43200):
            raise DomainError('Unsupported chart interval or instrument.')
        with self.lock:
            rows = self.db.execute('SELECT * FROM candles WHERE symbol=? ORDER BY minute DESC LIMIT ?',
                                   (symbol, interval * 600)).fetchall()[::-1]
        groups = {}
        for row in rows:
            bucket = row['minute'] // interval * interval * 60
            if bucket not in groups:
                groups[bucket] = {'time': bucket, **{k: row[k] / 100000 for k in ('open', 'high', 'low', 'close')}}
            else:
                c = groups[bucket]
                c.update(high=max(c['high'], row['high'] / 100000), low=min(c['low'], row['low'] / 100000), close=row['close'] / 100000)
        return list(groups.values())[-600:]

    def mutation(self, user_id, key, operation, data):
        if not isinstance(key, str) or not re.fullmatch(r'[\w-]{16,100}', key):
            raise DomainError('A valid request ID is required.')
        fingerprint = json.dumps([operation, data], sort_keys=True, separators=(',', ':'))
        with self.transaction():
            prior = self.db.execute('SELECT * FROM requests WHERE user_id=? AND key=?', (user_id, key)).fetchone()
            if prior:
                if prior['fingerprint'] != fingerprint:
                    raise DomainError('Request ID was already used for another action.', 409)
                return json.loads(prior['result'])
            account = self.active_account(user_id, data.get('account_id', ''))
            if operation == 'order':
                result = self.place(account, data)
            elif operation == 'close':
                o = self.owned_order(account, data.get('id'), 'open')
                self.ensure_fresh(o['symbol'])
                result = self.close(o, 'manual')
            elif operation == 'cancel':
                o = self.owned_order(account, data.get('id'), 'pending')
                self.db.execute("UPDATE orders SET status='cancelled',closed=?,reason='manual' WHERE id=?", (time.time(), o['id']))
                self.event(account['id'], f"{CATALOG[o['symbol']]['symbol']} pending order cancelled.")
                result = {'id': o['id'], 'status': 'cancelled'}
            elif operation == 'amend':
                o = self.owned_order(account, data.get('id'), 'pending')
                # Release its reservation within the same transaction; validation failure rolls everything back.
                self.db.execute("UPDATE orders SET status='amending' WHERE id=?", (o['id'],))
                payload = dict(symbol=o['symbol'],side=o['side'],kind='limit',lots=data.get('lots'),
                               limit_price=data.get('limit_price'),sl=data.get('sl'),tp=data.get('tp'))
                replacement = self.place(account, payload, emit_event=False)
                row = self.db.execute('SELECT * FROM orders WHERE id=?',(replacement['id'],)).fetchone()
                self.db.execute("UPDATE orders SET lots=?,limit_price=?,sl=?,tp=?,margin=?,status='pending' WHERE id=?",
                                (row['lots'],row['limit_price'],row['sl'],row['tp'],row['margin'],o['id']))
                self.db.execute('DELETE FROM orders WHERE id=?',(replacement['id'],))
                self.event(account['id'],f"{CATALOG[o['symbol']]['symbol']} pending order amended.")
                result = {'id':o['id'],'status':'pending'}
            elif operation == 'risk':
                o = self.owned_order(account, data.get('id'), 'open')
                self.ensure_fresh(o['symbol'])
                _, mark = self.pnl(o)
                sl, tp = self.risk(data, o['side'], mark, o['symbol'])
                self.db.execute('UPDATE orders SET sl=?,tp=? WHERE id=?', (sl, tp, o['id']))
                self.event(account['id'], f"{CATALOG[o['symbol']]['symbol']} protection updated.")
                result = {'id': o['id'], 'status': 'updated'}
            elif operation == 'reset':
                for o in self.orders(account['id']):
                    if o['status'] == 'open':
                        self.ensure_fresh(o['symbol'])
                        self.close(o, 'reset')
                self.db.execute("UPDATE orders SET status='cancelled',closed=?,reason='reset' WHERE account_id=? AND status='pending'", (time.time(), account['id']))
                self.db.execute('UPDATE accounts SET archived=? WHERE id=?', (time.time(), account['id']))
                result = {'account_id': self.new_account(user_id), 'status': 'reset'}
            else:
                raise DomainError('Unknown operation.', 404)
            self.db.execute('INSERT INTO requests VALUES(?,?,?,?)', (user_id, key, fingerprint, json.dumps(result)))
            return result

    def owned_order(self, account, order_id, status):
        if not isinstance(order_id, str) or len(order_id) != 32:
            raise DomainError('Order not found.', 404)
        row = self.db.execute('SELECT * FROM orders WHERE id=? AND account_id=?', (order_id, account['id'])).fetchone()
        if not row:
            raise DomainError('Order not found.', 404)
        if row['status'] != status:
            raise DomainError('Order status changed. Refresh and try again.', 409)
        return dict(row)

    def risk(self, data, side, reference, symbol='EURUSD'):
        sl = decimal(data.get('sl'), 'stop loss', True)
        tp = decimal(data.get('tp'), 'take profit', True)
        for v in (sl, tp):
            if v is not None and v != v.quantize(D(10) ** -CATALOG[symbol]['digits']):
                raise DomainError(f"Prices support at most {CATALOG[symbol]['digits']} decimal places.")
        distance = max(D(CATALOG[symbol]['spread']) / 100000, D(10) ** -CATALOG[symbol]['digits'] * 20)
        if side == 'buy':
            valid = (sl is None or sl <= reference - distance) and (tp is None or tp >= reference + distance)
        else:
            valid = (sl is None or sl >= reference + distance) and (tp is None or tp <= reference - distance)
        if not valid:
            raise DomainError(f'SL/TP must be on the correct side, at least {distance} from the reference price.')
        return (str(sl) if sl is not None else None, str(tp) if tp is not None else None)

    def place(self, account, data, emit_event=True):
        symbol, side, kind = data.get('symbol'), data.get('side'), data.get('kind')
        if not isinstance(symbol, str) or symbol not in CATALOG or side not in ('buy', 'sell') or kind not in ('market', 'limit'):
            raise DomainError('Select an available instrument, side and order type.')
        self.ensure_fresh(symbol)
        lots = decimal(data.get('lots'), 'lot size')
        if not D('.01') <= lots <= CATALOG[symbol]['max_lots'] or lots != lots.quantize(D('.01')):
            raise DomainError(f"Size must be 0.01–{CATALOG[symbol]['max_lots']:.2f} lots in steps of 0.01.")
        bid, ask, _ = self.quote(symbol)
        price = ask if side == 'buy' else bid
        limit_price = None
        if kind == 'limit':
            price = decimal(data.get('limit_price'), 'limit price')
            if price != price.quantize(D(10) ** -CATALOG[symbol]['digits']) or (side == 'buy' and price >= ask) or (side == 'sell' and price <= bid):
                raise DomainError('Buy limits must be below ask; sell limits above bid. Use at most five decimals.')
            limit_price = str(price)
        sl, tp = self.risk(data, side, price, symbol)
        margin = lots * CATALOG[symbol]['contract'] * price / 20
        spread_cost = lots * CATALOG[symbol]['contract'] * (ask - bid) if kind == 'market' else D(0)
        if margin + spread_cost > D(self.totals(account)['free_margin']):
            raise DomainError('Insufficient free margin for this order.', 409)
        if len([o for o in self.orders(account['id']) if o['status'] in ('open', 'pending')]) >= 100:
            raise DomainError('Maximum 100 active demo orders reached.', 409)
        order_id, now = identifier(), time.time()
        status = 'open' if kind == 'market' else 'pending'
        self.db.execute('''INSERT INTO orders VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                        (order_id, account['id'], symbol, side, kind, str(lots), limit_price, sl, tp, status,
                         str(price) if status == 'open' else None, None, None, str(margin), now,
                         now if status == 'open' else None, None, None))
        if emit_event:
            self.event(account['id'], f"{side.title()} {lots} {CATALOG[symbol]['symbol']} — {'filled' if status == 'open' else 'pending'}.")
        return {'id': order_id, 'status': status, 'entry': str(price) if status == 'open' else None}

    def close(self, order, reason):
        pnl, mark = self.pnl(order)
        account = self.db.execute('SELECT balance FROM accounts WHERE id=?', (order['account_id'],)).fetchone()
        self.db.execute('UPDATE accounts SET balance=? WHERE id=?', (str(D(account['balance']) + pnl), order['account_id']))
        self.db.execute("UPDATE orders SET status='closed',exit=?,pnl=?,closed=?,reason=? WHERE id=?", (str(mark), str(pnl), time.time(), reason, order['id']))
        self.db.execute('INSERT INTO ledger VALUES(?,?,?,?,?,?)',
                        (identifier(), order['account_id'], order['id'], str(pnl), reason, time.time()))
        self.event(order['account_id'], f"{CATALOG[order['symbol']]['symbol']} closed ({reason}) · ${pnl:.2f}.")
        return {'id': order['id'], 'status': 'closed', 'pnl': str(pnl)}

    def tick(self, overrides=None, now=None):
        stamp = now or time.time()
        with self.transaction():
            for symbol in CATALOG:
                price = overrides[symbol] if overrides and symbol in overrides else self.price(symbol, stamp)
                self.db.execute('UPDATE quotes SET bid=?,updated=? WHERE symbol=?', (price, stamp, symbol))
                self.db.execute('''INSERT INTO candles VALUES(?,?,?,?,?,?) ON CONFLICT(symbol,minute)
                  DO UPDATE SET high=MAX(high,excluded.high),low=MIN(low,excluded.low),close=excluded.close''',
                                (symbol, int(stamp // 60), price, price, price, price))
            for row in self.db.execute("SELECT * FROM orders WHERE status='pending' ORDER BY created,id").fetchall():
                o = dict(row)
                bid, ask, _ = self.quote(o['symbol'])
                fill = ask if o['side'] == 'buy' else bid
                if (o['side'] == 'buy' and fill <= D(o['limit_price'])) or (o['side'] == 'sell' and fill >= D(o['limit_price'])):
                    margin = D(o['lots']) * CATALOG[o['symbol']]['contract'] * fill / 20
                    acc = self.db.execute('SELECT * FROM accounts WHERE id=?', (o['account_id'],)).fetchone()
                    available = D(self.totals(acc)['free_margin']) + D(o['margin'])
                    if margin + D(o['lots']) * CATALOG[o['symbol']]['contract'] * (ask - bid) > available:
                        self.db.execute("UPDATE orders SET status='rejected',closed=?,reason='margin_at_fill' WHERE id=?", (stamp, o['id']))
                        self.event(o['account_id'], 'Pending order rejected: insufficient margin at fill.')
                        continue
                    self.db.execute("UPDATE orders SET status='open',entry=?,margin=?,opened=? WHERE id=?", (str(fill), str(margin), stamp, o['id']))
                    self.event(o['account_id'], f"{CATALOG[o['symbol']]['symbol']} limit order filled.")
            for row in self.db.execute("SELECT * FROM orders WHERE status='open' ORDER BY created,id").fetchall():
                o = dict(row)
                _, mark = self.pnl(o)
                sl, tp = D(o['sl']) if o['sl'] else None, D(o['tp']) if o['tp'] else None
                stop = sl is not None and (mark <= sl if o['side'] == 'buy' else mark >= sl)
                target = tp is not None and (mark >= tp if o['side'] == 'buy' else mark <= tp)
                if stop or target:
                    self.close(o, 'stop_loss' if stop else 'take_profit')
            for acc in self.db.execute('SELECT * FROM accounts WHERE archived IS NULL').fetchall():
                totals = self.totals(acc)
                if D(totals['used_margin']) > 0 and D(totals['equity']) <= D(totals['used_margin']) / 2:
                    self.db.execute("UPDATE orders SET status='cancelled',closed=?,reason='stop_out' WHERE account_id=? AND status='pending'", (stamp, acc['id']))
                    open_orders = sorted([o for o in self.orders(acc['id']) if o['status'] == 'open'], key=lambda o: self.pnl(o)[0])
                    for o in open_orders:
                        latest = self.db.execute('SELECT * FROM accounts WHERE id=?', (acc['id'],)).fetchone()
                        totals = self.totals(latest)
                        if D(totals['used_margin']) == 0 or D(totals['equity']) > D(totals['used_margin']) / 2:
                            break
                        self.close(o, 'stop_out')
            self.db.execute('DELETE FROM candles WHERE minute<?', (int(stamp // 60) - 10080,))

    def statement(self, user_id, account_id=None):
        with self.lock:
            account = self.active_account(user_id) if not account_id else self.db.execute('SELECT * FROM accounts WHERE id=? AND user_id=?', (account_id, user_id)).fetchone()
            if not account:
                raise DomainError('Account not found.', 404)
            return dict(account), self.orders(account['id'])
