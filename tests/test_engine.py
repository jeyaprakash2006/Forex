import tempfile
import time
import unittest
from decimal import Decimal as D
from pathlib import Path
from backend.engine import Engine, DomainError


class TradingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tmp.name) / 'test.db')
        self.engine = Engine(self.path)
        token = self.engine.register({'name':'Test Trader','email':'trader@example.test','password':'test-password-123'})
        self.user = self.engine.authenticate(token)
        self.account = self.engine.state(self.user)['account']['id']
        self.engine.tick({'EURUSD':110000,'GBPUSD':130000})
        self.seq = 0

    def tearDown(self):
        self.engine.db.close()
        self.tmp.cleanup()

    def action(self, op='order', **data):
        self.seq += 1
        return self.engine.mutation(self.user, f'test-request-{self.seq:08}', op, {'account_id':self.account,**data})

    def buy(self, **extra):
        return self.action(symbol='EURUSD',side='buy',kind='market',lots='0.10',**extra)

    def test_support_isolation_staff_reply_and_revocation(self):
        from backend.manage import set_staff
        token = self.engine.register({'name':'Other User','email':'other@example.test','password':'test-password-456'})
        other = self.engine.authenticate(token)
        ticket = self.engine.support(self.user, {'subject':'Chart issue','body':'The chart does not display my drawing.'})[0]
        self.assertEqual(self.engine.support(other), [])
        with self.assertRaises(DomainError) as denied:
            self.engine.admin(other)
        self.assertEqual(denied.exception.status, 403)
        set_staff(self.engine, 'other@example.test', True)
        self.assertTrue(self.engine.state(other)['is_staff'])
        result = self.engine.admin(other, {'id':ticket['id'],'reply':'Please choose the saved instrument.','status':'resolved'})
        self.assertEqual(len(result['audit']), 2)
        self.assertNotIn('password', result['users'][0])
        own = self.engine.support(self.user)[0]
        self.assertEqual(own['status'], 'resolved')
        self.assertEqual(len(own['replies']), 1)
        set_staff(self.engine, 'other@example.test', False)
        with self.assertRaises(DomainError):
            self.engine.admin(other, {'id':ticket['id'],'status':'open'})
        self.assertEqual(self.engine.support(self.user)[0]['status'], 'resolved')

    def test_support_validation_leaves_no_partial_writes(self):
        with self.assertRaises(DomainError):
            self.engine.support(self.user, {'subject':'x','body':'short'})
        self.assertEqual(self.engine.support(self.user), [])

    def test_bid_ask_pnl_margin_and_ledger(self):
        result = self.buy()
        s = self.engine.state(self.user)
        self.assertEqual(D(result['entry']), D('1.10012'))
        self.assertEqual(D(s['totals']['unrealized']), D('-1.20'))
        self.assertEqual(D(s['totals']['used_margin']), D('550.06'))
        self.engine.tick({'EURUSD':110100,'GBPUSD':130000})
        result = self.action('close', id=result['id'])
        self.assertEqual(D(result['pnl']), D('8.80'))
        s = self.engine.state(self.user)
        self.assertEqual(D(s['totals']['balance']), D('10008.80'))
        amounts = self.engine.db.execute('SELECT amount FROM ledger WHERE account_id=?', (self.account,))
        self.assertEqual(sum(D(r[0]) for r in amounts), D(s['totals']['balance']))

    def test_sell_marks_at_ask(self):
        self.action(symbol='GBPUSD',side='sell',kind='market',lots='0.10')
        s = self.engine.state(self.user)
        self.assertEqual(D(s['totals']['unrealized']), D('-1.5'))

    def test_limit_trigger_reservation_cancel_race(self):
        order = self.action(symbol='EURUSD',side='buy',kind='limit',lots='0.10',limit_price='1.09900')
        self.assertEqual(order['status'],'pending')
        self.assertEqual(D(self.engine.state(self.user)['totals']['used_margin']),D('549.5'))
        self.engine.tick({'EURUSD':109900,'GBPUSD':130000})  # ask still above limit
        self.assertEqual(self.engine.state(self.user)['orders'][0]['status'],'pending')
        self.engine.tick({'EURUSD':109880,'GBPUSD':130000})
        o = self.engine.state(self.user)['orders'][0]
        self.assertEqual(o['status'],'open')
        self.assertLessEqual(D(o['entry']),D('1.09900'))
        with self.assertRaises(DomainError):
            self.action('cancel',id=o['id'])

    def test_cancel_never_fills(self):
        order = self.action(symbol='EURUSD',side='sell',kind='limit',lots='.1',limit_price='1.10100')
        self.action('cancel',id=order['id'])
        self.engine.tick({'EURUSD':110200,'GBPUSD':130000})
        self.assertEqual(self.engine.state(self.user)['orders'][0]['status'],'cancelled')
        self.assertEqual(D(self.engine.state(self.user)['totals']['used_margin']),0)

    def test_stop_loss_gap_and_take_profit(self):
        self.buy(sl='1.09900')
        self.engine.tick({'EURUSD':109800,'GBPUSD':130000})
        o = self.engine.state(self.user)['orders'][0]
        self.assertEqual(o['status'],'closed')
        self.assertEqual(o['reason'],'stop_loss')
        self.assertEqual(D(o['exit']),D('1.098'))
        self.buy(tp='1.10000')
        self.engine.tick({'EURUSD':110050,'GBPUSD':130000})
        self.assertEqual(self.engine.state(self.user)['orders'][0]['reason'],'take_profit')

    def test_validation_and_margin_rollback(self):
        for invalid in [{'lots':'NaN'},{'lots':'0.001'},{'lots':'1.01'},{'sl':'1.2'}, {'tp':'1.0'}, {'symbol':['EURUSD']}]:
            payload=dict(symbol='EURUSD',side='buy',kind='market',lots='.1')
            payload.update(invalid)
            with self.assertRaises(DomainError):
                self.action(**payload)
        self.assertEqual(self.engine.state(self.user)['orders'],[])
        self.action(symbol='EURUSD',side='buy',kind='market',lots='1')
        with self.assertRaises(DomainError):
            self.action(symbol='EURUSD',side='buy',kind='market',lots='1')
        self.assertEqual(len(self.engine.state(self.user)['orders']),1)

    def test_idempotency_and_conflicting_payload(self):
        payload={'account_id':self.account,'symbol':'EURUSD','side':'buy','kind':'market','lots':'.1'}
        first=self.engine.mutation(self.user,'repeat-request-123','order',payload)
        second=self.engine.mutation(self.user,'repeat-request-123','order',payload)
        self.assertEqual(first,second)
        self.assertEqual(len(self.engine.state(self.user)['orders']),1)
        with self.assertRaises(DomainError):
            self.engine.mutation(self.user,'repeat-request-123','order',{**payload,'lots':'.2'})

    def test_ownership_and_archived_account_isolation(self):
        other=self.engine.authenticate(self.engine.register({'name':'Other Trader','email':'other@example.test','password':'test-password-123'}))
        order=self.buy()
        other_account=self.engine.state(other)['account']['id']
        with self.assertRaises(DomainError):
            self.engine.mutation(other,'wrong-owner-123456','close',{'account_id':other_account,'id':order['id']})
        with self.assertRaises(DomainError):
            self.engine.statement(other,self.account)
        self.assertEqual(self.engine.state(other)['orders'],[])

    def test_reset_is_idempotent_preserves_archive(self):
        self.buy()
        payload={'account_id':self.account}
        r1=self.engine.mutation(self.user,'reset-request-123','reset',payload)
        r2=self.engine.mutation(self.user,'reset-request-123','reset',payload)
        self.assertEqual(r1,r2)
        s=self.engine.state(self.user)
        self.assertEqual(D(s['totals']['balance']),10000)
        self.assertEqual(len(s['archives']),1)
        self.assertEqual(s['orders'],[])
        self.assertEqual(self.engine.statement(self.user,self.account)[1][0]['reason'],'reset')
        with self.assertRaises(DomainError):
            self.buy()

    def test_restart_keeps_account_and_orders(self):
        self.buy()
        self.engine.db.close()
        self.engine=Engine(self.path)
        s=self.engine.state(self.user)
        self.assertEqual(s['account']['id'],self.account)
        self.assertEqual(len(s['orders']),1)
        self.assertEqual(D(s['totals']['balance']),10000)

    def test_stale_feed_rejects_new_order(self):
        self.engine.db.execute('UPDATE quotes SET updated=?',(time.time()-10,))
        with self.assertRaises(DomainError):
            self.buy()
        self.assertEqual(self.engine.state(self.user)['orders'],[])

    def test_chart_timeframes_aggregate_same_data(self):
        one=self.engine.candles('EURUSD',1)
        five=self.engine.candles('EURUSD',5)
        last=five[-1]
        relevant=[c for c in one if c['time']>=last['time']]
        self.assertEqual(last['high'],max(c['high'] for c in relevant))
        self.assertEqual(last['low'],min(c['low'] for c in relevant))
        self.assertEqual(last['close'],relevant[-1]['close'])

    def test_stop_out_closes_losing_position(self):
        self.action(symbol='EURUSD',side='buy',kind='market',lots='1')
        self.engine.tick({'EURUSD':100000,'GBPUSD':130000})
        self.assertEqual(self.engine.state(self.user)['orders'][0]['reason'],'stop_out')
        self.assertEqual(D(self.engine.state(self.user)['totals']['used_margin']),0)

    def test_pending_amend_preserves_id_and_rolls_back_invalid_change(self):
        order=self.action(symbol='EURUSD',side='buy',kind='limit',lots='.1',limit_price='1.09')
        self.action('amend',id=order['id'],lots='.2',limit_price='1.08',sl=None,tp=None)
        o=self.engine.state(self.user)['orders'][0]
        self.assertEqual(o['id'],order['id'])
        self.assertEqual(D(o['margin']),D('1080'))
        with self.assertRaises(DomainError):
            self.action('amend',id=order['id'],lots='1',limit_price='2',sl=None,tp=None)
        o=self.engine.state(self.user)['orders'][0]
        self.assertEqual(o['status'],'pending')
        self.assertEqual(D(o['lots']),D('.2'))
        self.assertEqual(len(self.engine.state(self.user)['orders']),1)

    def test_password_change_revokes_other_sessions(self):
        token=self.engine.login({'email':'trader@example.test','password':'test-password-123'})
        other=self.engine.login({'email':'trader@example.test','password':'test-password-123'})
        with self.assertRaises(DomainError):
            self.engine.change_password(self.user,token,{'current_password':'wrong','new_password':'replacement-secret-123'})
        self.assertEqual(self.engine.authenticate(other),self.user)
        self.engine.change_password(self.user,token,{'current_password':'test-password-123','new_password':'replacement-secret-123'})
        self.assertEqual(self.engine.authenticate(token),self.user)
        with self.assertRaises(DomainError): self.engine.authenticate(other)
        with self.assertRaises(DomainError): self.engine.login({'email':'trader@example.test','password':'test-password-123'})
        self.assertTrue(self.engine.login({'email':'trader@example.test','password':'replacement-secret-123'}))

    def test_session_revocation_owner_and_profile_validation(self):
        token=self.engine.login({'email':'trader@example.test','password':'test-password-123'})
        sessions=self.engine.session_list(self.user,token)
        current=next(s for s in sessions if s['current'])
        other=self.engine.authenticate(self.engine.register({'name':'Other','email':'other@example.test','password':'test-password-123'}))
        with self.assertRaises(DomainError): self.engine.revoke_session(other,current['id'])
        self.assertEqual(self.engine.authenticate(token),self.user)
        self.engine.revoke_session(self.user,current['id'])
        with self.assertRaises(DomainError): self.engine.authenticate(token)
        with self.assertRaises(DomainError): self.engine.profile_update(self.user,{'name':''})
        self.engine.profile_update(self.user,{'name':'Updated Name'})
        self.assertEqual(self.engine.state(self.user)['user']['name'],'Updated Name')

    def test_crypto_contract_and_precision(self):
        self.engine.tick({'BTCUSD':6400000000,'ETCUSD':570000})
        btc=self.action(symbol='BTCUSD',side='buy',kind='market',lots='1')
        self.assertEqual(D(btc['entry']),D('64010.1'))
        o=next(o for o in self.engine.state(self.user)['orders'] if o['id']==btc['id'])
        self.assertEqual(D(o['unrealized']),D('-10.1'))
        self.assertEqual(D(o['margin']),D('3200.505'))
        etc=self.action(symbol='ETCUSD',side='buy',kind='market',lots='1')
        o=next(o for o in self.engine.state(self.user)['orders'] if o['id']==etc['id'])
        self.assertEqual(D(o['unrealized']),D('-1.1'))
        with self.assertRaises(DomainError):
            self.action(symbol='BTCUSD',side='buy',kind='limit',lots='.01',limit_price='63000.001')

    def test_authentication_logout_and_duplicate_user(self):
        with self.assertRaises(DomainError):
            self.engine.login({'email':'trader@example.test','password':'wrong'})
        token=self.engine.login({'email':'trader@example.test','password':'test-password-123'})
        self.assertEqual(self.engine.authenticate(token),self.user)
        self.engine.logout(token)
        with self.assertRaises(DomainError):
            self.engine.authenticate(token)
        with self.assertRaises(DomainError):
            self.engine.register({'name':'Test Trader','email':'trader@example.test','password':'test-password-123'})
        self.assertEqual(self.engine.db.execute('SELECT count(*) FROM accounts').fetchone()[0],1)

    def test_risk_update_and_clear(self):
        order=self.buy()
        self.action('risk',id=order['id'],sl='1.099',tp='1.102')
        self.assertEqual(self.engine.state(self.user)['orders'][0]['sl'],'1.099')
        self.action('risk',id=order['id'],sl=None,tp=None)
        self.assertIsNone(self.engine.state(self.user)['orders'][0]['sl'])


if __name__=='__main__':
    unittest.main()
