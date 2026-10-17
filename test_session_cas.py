import unittest
from garmin_session_supabase import SupabaseSessionBackend, SessionBackendUnavailable

A='11111111-1111-4111-8111-111111111111'
class FakeBackend(SupabaseSessionBackend):
    rows = {}
    def _request(self, method, path, payload=None, prefer=None):
        if method == 'GET':
            row = self.rows.get(A)
            return [row.copy()] if row else []
        if path == 'rpc/pf_garmin_session_cas':
            old = self.rows.get(A)
            expected = payload['p_expected_revision']
            if (old['revision'] if old else 0) != expected:
                return None
            new = expected+1
            self.rows[A]={'ciphertext':payload['p_ciphertext'],'revision':new}
            return new
        raise AssertionError(path)

class CasTests(unittest.TestCase):
    def setUp(self):
        FakeBackend.rows={}
    def backend(self):
        return FakeBackend('https://example.supabase.co','server-key')
    def test_insert_and_update(self):
        b=self.backend()
        self.assertIsNone(b.get(A))
        b.put(A,b'first')
        self.assertEqual(b.get(A),b'first')
        b.put(A,b'second')
        self.assertEqual(b.get(A),b'second')
    def test_concurrent_writer_rejected(self):
        a,b=self.backend(),self.backend()
        a.get(A); b.get(A)
        a.put(A,b'new')
        with self.assertRaises(SessionBackendUnavailable): b.put(A,b'stale')
        self.assertEqual(a.get(A),b'new')
    def test_unread_write_rejected(self):
        with self.assertRaises(SessionBackendUnavailable): self.backend().put(A,b'no')

if __name__=='__main__': unittest.main()
