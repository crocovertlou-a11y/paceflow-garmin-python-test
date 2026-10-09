"""Offline contract checks for the real Garmin send endpoint; no Garmin credentials used."""
import unittest
import sys, types
try:
    import garminconnect
except ImportError:
    sys.modules["garminconnect"] = types.SimpleNamespace(Garmin=object)
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from api import GarminSendRequest, send_canonical_workout

CANON = {'scheduled_date':'2026-10-09','athlete_id':'a','garmin_workout':{'workoutName':'Test'}}

class SendContract(unittest.TestCase):
    def setUp(self):
        self.req=GarminSendRequest(workout_id='w',athlete_id='a',email='test@example.com',password='secret')
        self.claim_patch=patch('idempotency.claim')
        self.finish_patch=patch('idempotency.finish')
        self.claim_mock=self.claim_patch.start()
        self.finish_mock=self.finish_patch.start()
        self.addCleanup(self.claim_patch.stop)
        self.addCleanup(self.finish_patch.stop)
    def test_no_auth(self):
        with self.assertRaises(HTTPException) as c: send_canonical_workout(self.req,None)
        self.assertEqual(c.exception.status_code,401)
    @patch('authorized_preview.preview_workout')
    def test_forbidden(self,unused):
        from authorized_preview import AccessError
        with patch('api.preview_workout',side_effect=AccessError()):
            with self.assertRaises(HTTPException) as c: send_canonical_workout(self.req,'Bearer token')
        self.assertEqual(c.exception.status_code,403)
    @patch('api.preview_workout',return_value=CANON)
    @patch('garminconnect.Garmin')
    @patch('garmin_sender.send_workout',return_value={'workout_id':123})
    def test_success(self,send,Garmin,preview):
        result=send_canonical_workout(self.req,'Bearer token')
        self.assertEqual(result['provider'],'python')
        self.assertTrue(result['scheduled'])
        preview.assert_called_once_with('token','w','a',athlete_only=True)
        send.assert_called_once()
    @patch('api.preview_workout',return_value=CANON)
    @patch('garminconnect.Garmin')
    def test_mfa_required_explicit(self, Garmin, preview):
        def login():
            Garmin.call_args.kwargs['prompt_mfa']()
        Garmin.return_value.login.side_effect=login
        with self.assertRaises(HTTPException) as c:
            send_canonical_workout(self.req, 'Bearer token')
        self.assertEqual(c.exception.status_code, 428)

    @patch('api.preview_workout',return_value=CANON)
    @patch('garminconnect.Garmin')
    @patch('garmin_sender.send_workout',return_value={'workout_id': 9})
    def test_mfa_code_passed_to_callback(self, send, Garmin, preview):
        self.req.mfa_code = ' 123456 '
        def login():
            self.assertEqual(Garmin.call_args.kwargs['prompt_mfa'](), '123456')
        Garmin.return_value.login.side_effect=login
        self.assertTrue(send_canonical_workout(self.req, 'Bearer token')['ok'])

    @patch('api.preview_workout',return_value=CANON)
    @patch('garminconnect.Garmin')
    def test_login_failure_no_upload(self,Garmin,preview):
        Garmin.return_value.login.side_effect=Exception('sensitive detail')
        with self.assertRaises(HTTPException) as c: send_canonical_workout(self.req,'Bearer token')
        self.assertEqual(c.exception.status_code,502)
        self.assertNotIn('sensitive detail',c.exception.detail)
    @patch('api.preview_workout',return_value=CANON)
    @patch('garminconnect.Garmin')
    def test_rate_limit_does_not_upload_or_leak(self, Garmin, preview):
        Garmin.return_value.login.side_effect=Exception('Rate limited by Garmin at /oauth/preauthorized secret')
        with self.assertRaises(HTTPException) as c:
            send_canonical_workout(self.req, 'Bearer token')
        self.assertEqual(c.exception.status_code,429)
        self.assertNotIn('secret',c.exception.detail)
        Garmin.return_value.upload_workout.assert_not_called()

    @patch('api.preview_workout',return_value=CANON)
    @patch('garminconnect.Garmin')
    @patch('garmin_sender.send_workout',side_effect=RuntimeError('schedule failed'))
    def test_uncertain_send(self,send,Garmin,preview):
        with self.assertRaises(HTTPException) as c: send_canonical_workout(self.req,'Bearer token')
        self.assertIn('incertain',c.exception.detail)

    @patch('api.preview_workout',return_value=CANON)
    @patch('garminconnect.Garmin')
    def test_claim_conflict_prevents_login(self, Garmin, preview):
        from idempotency import AlreadyClaimed
        self.claim_mock.side_effect=AlreadyClaimed()
        with self.assertRaises(HTTPException) as c:
            send_canonical_workout(self.req,'Bearer token')
        self.assertEqual(c.exception.status_code,409)
        Garmin.assert_not_called()

    @patch('api.preview_workout',return_value=CANON)
    @patch('garminconnect.Garmin')
    def test_ledger_unavailable_prevents_login(self, Garmin, preview):
        from idempotency import LedgerError
        self.claim_mock.side_effect=LedgerError()
        with self.assertRaises(HTTPException) as c:
            send_canonical_workout(self.req,'Bearer token')
        self.assertEqual(c.exception.status_code,503)
        Garmin.assert_not_called()

if __name__=='__main__': unittest.main()
