import unittest
from unittest.mock import patch, MagicMock
from backend.market_data import MarketData, PAIRS
from backend.engine import DomainError

class MarketDataTests(unittest.TestCase):
    def test_quote_mapping_and_crossed_quote_rejection(self):
        feed=MarketData()
        row={'a':['11'],'b':['10'],'c':['10.5'],'h':['12','13'],'l':['9','8']}
        with patch.object(feed,'fetch',return_value=(100,{p[1]:row for p in PAIRS.values()})):
            result=feed.quotes()
            self.assertEqual(len(result['markets']),4)
            self.assertEqual(result['markets'][0]['symbol'],'BTC/USD')
            self.assertEqual(result['markets'][0]['high'],13)
            row['a']=['9']
            with self.assertRaises(DomainError):feed.quotes()

    def test_candle_validation_and_symbol_allowlist(self):
        feed=MarketData()
        with self.assertRaises(DomainError):feed.candles('EURUSD',1)
        with self.assertRaises(DomainError):feed.candles('ETCUSD',43200)
        with patch.object(feed,'fetch',return_value=(100,{'XETCZUSD':[[60,'10','12','9','11']]})):
            self.assertEqual(feed.candles('ETCUSD',1)['candles'][0]['close'],11)
        with patch.object(feed,'fetch',return_value=(100,{'XETCZUSD':[[60,'10','8','9','11']]})):
            with self.assertRaises(DomainError):feed.candles('ETCUSD',1)

    def test_provider_cache_and_failure_backoff(self):
        feed=MarketData()
        response=MagicMock();response.__enter__.return_value.read.return_value=b'{"error":[],"result":{"ok":true}}'
        with patch('backend.market_data.urllib.request.urlopen',return_value=response) as request:
            feed.fetch('Ticker',{},5);feed.fetch('Ticker',{},5)
            self.assertEqual(request.call_count,1)
        feed.cache.clear()
        with patch('backend.market_data.urllib.request.urlopen',side_effect=OSError) as request:
            for _ in range(2):
                with self.assertRaises(DomainError) as error:feed.fetch('Ticker',{},5)
                self.assertEqual(error.exception.status,503)
            self.assertEqual(request.call_count,1)
