import unittest
from unittest.mock import patch
import garmin_session_store as store

class FakeClient:
    def dumps(self): return '{"access_token":"simulated"}'
class FakeGarmin:
    calls=[]
    def __init__(self,email=None,password=None,prompt_mfa=None):
        self.email=email;self.password=password;self.client=FakeClient()
    def login(self,tokenstore=None):
        self.calls.append((self.email,self.password,tokenstore))
class SessionTests(unittest.TestCase):
    def setUp(self): FakeGarmin.calls=[]
    def test_first_login_persists(self):
        with patch.object(store,'restore',return_value=None),patch.object(store,'persist') as p:
            store.login_with_session(FakeGarmin,'athlete','mail','pass',None)
            self.assertEqual(FakeGarmin.calls,[('mail','pass',None)])
            p.assert_called_once_with('athlete','{"access_token":"simulated"}')
    def test_saved_login_never_supplies_password(self):
        with patch.object(store,'restore',return_value='{"token":"saved"}'),patch.object(store,'persist') as p:
            store.login_with_session(FakeGarmin,'athlete','mail','pass',None)
            self.assertEqual(FakeGarmin.calls,[(None,None,'{"token":"saved"}')])
            p.assert_called_once()
    def test_saved_rejection_does_not_fallback(self):
        class Reject(FakeGarmin):
            def login(self,tokenstore=None):
                self.calls.append((self.email,self.password,tokenstore))
                raise RuntimeError('rejected')
        with patch.object(store,'restore',return_value='{"token":"saved"}'):
            with self.assertRaises(store.SessionStoreError):
                store.login_with_session(Reject,'athlete','mail','pass',None)
            self.assertEqual(FakeGarmin.calls,[(None,None,'{"token":"saved"}')])
if __name__=='__main__': unittest.main()
