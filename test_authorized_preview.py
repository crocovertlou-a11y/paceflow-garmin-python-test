import unittest
from authorized_preview import preview_workout, AccessError

UID='11111111-1111-4111-8111-111111111111'
AID='22222222-2222-4222-8222-222222222222'
WID='33333333-3333-4333-8333-333333333333'
CID='44444444-4444-4444-8444-444444444444'
ENV={'SUPABASE_URL':'https://test.supabase.co','SUPABASE_ANON_KEY':'anon','SUPABASE_SERVICE_ROLE_KEY':'server-only'}

class TestPreview(unittest.TestCase):
    def fake(self, owner=UID):
        def fetch(url,key,bearer):
            if url.endswith('/auth/v1/user'):
                assert bearer == 'valid-jwt'
                return {'id':UID}
            if '/athlete_profiles?' in url:
                return [{'id':AID,'user_id':owner,'owner_coach_id':CID}]
            if '/coaches?' in url: return []
            if '/workouts?' in url:
                return [{'id':WID,'athlete_id':AID,'title':'Test', 'scheduled_date':'2026-10-09',
                         'structured_workout':{'valid':True,'blocks':[{'kind':'warmup','duration':{'value':10,'unit':'min'}}]}}]
            raise AssertionError(url)
        return fetch

    def test_athlete_can_preview(self):
        result=preview_workout('valid-jwt',WID,AID,env=ENV,fetch=self.fake())
        self.assertFalse(result['garmin_sent'])
        self.assertEqual(result['scheduled_date'],'2026-10-09')
        self.assertIn('garmin_workout',result)

    def test_other_athlete_denied(self):
        with self.assertRaises(AccessError):
            preview_workout('valid-jwt',WID,AID,env=ENV,fetch=self.fake(owner=CID))

    def test_invalid_id_denied(self):
        with self.assertRaises(ValueError):
            preview_workout('valid-jwt','not-uuid',AID,env=ENV,fetch=self.fake())

    def test_missing_config_denied(self):
        with self.assertRaises(RuntimeError):
            preview_workout('valid-jwt',WID,AID,env={},fetch=self.fake())

if __name__ == '__main__': unittest.main()
