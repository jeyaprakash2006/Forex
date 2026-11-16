import concurrent.futures
import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from backend.engine import Engine
from backend.server import AppServer


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.engine=Engine(str(Path(self.tmp.name)/'api.db'))
        self.server=AppServer(('127.0.0.1',0),self.engine)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        status, headers, data=self.request('POST','/api/auth/register',{'name':'API Tester','email':'api@example.test','password':'test-password-123'})
        self.assertEqual(status,200)
        self.cookie=headers['Set-Cookie'].split(';')[0]

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.engine.db.close();self.tmp.cleanup()

    def request(self,method,path,data=None,headers=None):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        defaults={'Content-Type':'application/json','X-Northstar-Request':'1'}
        if hasattr(self,'cookie'):defaults['Cookie']=self.cookie
        defaults.update(headers or {})
        conn.request(method,path,json.dumps(data) if data is not None else None,defaults)
        response=conn.getresponse();payload=response.read();output=(response.status,dict(response.headers),payload)
        conn.close();return output

    def test_auth_static_allowlist_and_csrf(self):
        self.assertEqual(self.request('GET','/api/state',headers={'Cookie':''})[0],401)
        self.assertEqual(self.request('GET','/backend/engine.py')[0],404)
        self.assertEqual(self.request('GET','/data/northstar.sqlite3')[0],404)
        self.assertEqual(self.request('GET','/api/health',headers={'Host':'attacker.example'})[0],403)
        self.assertEqual(self.request('POST','/api/auth/logout',{},headers={'Origin':'https://attacker.example'})[0],403)
        self.assertEqual(self.request('POST','/api/auth/logout',{},headers={'X-Northstar-Request':''})[0],403)
        status,headers,body=self.request('GET','/')
        self.assertEqual(status,200);self.assertIn('Content-Security-Policy',headers);self.assertIn(b'northstar',body)

    def test_concurrent_order_deduplication_and_csv(self):
        account=json.loads(self.request('GET','/api/state')[2])['account']['id']
        self.engine.tick({'EURUSD':110000})
        payload={'account_id':account,'symbol':'EURUSD','side':'buy','kind':'market','lots':'.01'}
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results=list(pool.map(lambda _:self.request('POST','/api/orders',payload,{'Idempotency-Key':'same-concurrent-request'}),range(4)))
        self.assertTrue(all(r[0]==200 for r in results))
        ids={json.loads(r[2])['id'] for r in results};self.assertEqual(len(ids),1)
        state=json.loads(self.request('GET','/api/state')[2]);self.assertEqual(len(state['orders']),1)
        status,headers,csv=self.request('GET','/api/statement.csv')
        self.assertEqual(status,200);self.assertIn('attachment',headers['Content-Disposition']);self.assertIn(b'paper,generated',csv)

    def test_support_routes_authentication_and_staff_boundary(self):
        self.assertEqual(self.request('GET','/api/support',headers={'Cookie':''})[0],401)
        self.assertEqual(self.request('GET','/api/admin')[0],403)
        self.assertEqual(self.request('POST','/api/admin',{'status':'resolved'})[0],403)
        status, _, body = self.request('POST','/api/support',{'subject':'Test request','body':'Please inspect this local test request.'})
        self.assertEqual(status,200)
        self.assertEqual(len(json.loads(body)),1)
        self.assertEqual(len(json.loads(self.request('GET','/api/support')[2])),1)
        self.assertEqual(self.request('GET','/api/auth/sessions')[0],200)

    def test_invalid_json_and_live_route(self):
        self.assertEqual(self.request('POST','/api/orders',[],{'Idempotency-Key':'invalid-payload-123'})[0],400)
        self.assertEqual(self.request('POST','/api/live/orders',{})[0],404)
        self.assertEqual(self.request('GET','/api/candles?interval=banana')[0],400)
        self.assertEqual(self.request('GET','/api/history?account=missing')[0],404)


if __name__=='__main__':unittest.main()
