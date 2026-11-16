"""Read-only public Kraken spot data. Never feeds the simulation ledger."""
import json
import math
import threading
import time
import urllib.request
from urllib.parse import urlencode
from backend.engine import DomainError

PAIRS = {'BTCUSD':('XBTUSD','XXBTZUSD'), 'ETHUSD':('ETHUSD','XETHZUSD'),
         'ETCUSD':('ETCUSD','XETCZUSD'), 'SOLUSD':('SOLUSD','SOLUSD')}


def number(value):
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError('Invalid price')
    return result


class MarketData:
    def __init__(self):
        self.lock = threading.Lock()
        self.cache = {}
        self.retry_after = {}

    def fetch(self, endpoint, params, ttl):
        key = (endpoint, urlencode(params))
        with self.lock:
            now = time.time()
            cached = self.cache.get(key)
            if cached and now - cached[0] < ttl:
                return cached
            if now < self.retry_after.get(key, 0):
                raise DomainError('Live provider unavailable. Retry shortly.', 503)
            try:
                req = urllib.request.Request('https://api.kraken.com/0/public/'+endpoint+'?'+key[1], headers={'User-Agent':'Northstar-local/0.2'})
                with urllib.request.urlopen(req, timeout=6) as response:
                    payload = json.loads(response.read(2_000_000))
                if payload.get('error') or not isinstance(payload.get('result'), dict):
                    raise ValueError('Provider rejected request')
                result = (time.time(), payload['result'])
                self.cache[key] = result
                return result
            except Exception as exc:
                self.retry_after[key] = time.time() + 15
                raise DomainError('Live provider unavailable. No simulated fallback is used.', 503) from exc

    def quotes(self):
        received, data = self.fetch('Ticker', {'pair':','.join(p[0] for p in PAIRS.values())}, 5)
        try:
            markets = []
            for symbol, (_, key) in PAIRS.items():
                row = data[key]
                bid, ask = number(row['b'][0]), number(row['a'][0])
                if ask < bid: raise ValueError('Crossed quote')
                markets.append({'id':symbol, 'symbol':symbol[:-3]+'/USD', 'bid':bid, 'ask':ask,
                                'last':number(row['c'][0]), 'high':number(row['h'][1]), 'low':number(row['l'][1])})
            return {'source':'Kraken spot', 'received_at':received, 'poll_seconds':5, 'markets':markets}
        except (ValueError, KeyError, TypeError, IndexError) as exc:
            raise DomainError('Invalid live quote response.', 503) from exc

    def candles(self, symbol, interval):
        if symbol not in PAIRS or interval not in (1,5,15,30,60,240,1440,10080):
            raise DomainError('Unsupported live symbol or interval.')
        pair, key = PAIRS[symbol]
        received, data = self.fetch('OHLC', {'pair':pair,'interval':interval}, 15)
        try:
            candles=[]
            for row in data[key][-720:]:
                candle={'time':int(row[0]), **{k:number(row[i]) for i,k in enumerate(('open','high','low','close'),1)}}
                if candle['low']>min(candle['open'],candle['close']) or candle['high']<max(candle['open'],candle['close']):
                    raise ValueError('Invalid candle')
                if candles and candle['time']<=candles[-1]['time']: raise ValueError('Unordered candles')
                candles.append(candle)
            if not candles: raise ValueError('Empty candles')
            return {'source':'Kraken trade OHLC', 'received_at':received, 'candles':candles,
                    'current_candle_provisional':True}
        except (ValueError, KeyError, TypeError, IndexError) as exc:
            raise DomainError('Invalid live candle response.', 503) from exc
