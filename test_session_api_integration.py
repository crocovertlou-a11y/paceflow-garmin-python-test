"""Offline regression tests of the real PaceFlow API with session feature enabled."""
import unittest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from api import GarminSendRequest, GarminActivityCandidatesRequest, send_canonical_workout, garmin_activity_candidates
from garmin_session_auth import ReconnectRequired
from garmin_session_store import SessionStoreError

CANON={'scheduled_date':'2026-10-09','athlete_id':'11111111-1111-4111-8111-111111111111','garmin_workout':{'workoutName':'Run'}}

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        import api
        api._garmin_cooldown_until=0
        self.send=GarminSendRequest(workout_id='w',athlete_id=CANON['athlete_id'],email='a@example.com')
        self.candidates=GarminActivityCandidatesRequest(workout_id='w',athlete_id=CANON['athlete_id'],email='a@example.com')

    @patch('api.preview_workout',return_value=CANON)
    @patch('idempotency.claim')
    @patch('idempotency.finish')
    @patch('api.session_login',side_effect=ReconnectRequired('no session'))
    def test_send_requires_reconnect_without_upload(self,login,finish,claim,preview):
        with self.assertRaises(HTTPException) as err:send_canonical_workout(self.send,'Bearer token')
        self.assertEqual(err.exception.status_code,428)
        finish.assert_called_once_with(CANON['athlete_id'],'w','auth_failed',None)

    @patch('api.preview_workout',return_value=CANON)
    @patch('idempotency.claim')
    @patch('idempotency.finish')
    @patch('api.session_login',side_effect=SessionStoreError('private'))
    def test_store_unavailable_prevents_send(self,login,finish,claim,preview):
        with self.assertRaises(HTTPException) as err:send_canonical_workout(self.send,'Bearer token')
        self.assertEqual(err.exception.status_code,503)
        self.assertNotIn('private',err.exception.detail)

    @patch('api.preview_workout',return_value=CANON)
    @patch('idempotency.claim')
    @patch('idempotency.finish')
    @patch('api.session_login',return_value=(MagicMock(),object()))
    @patch('api.session_persist',side_effect=SessionStoreError('private'))
    @patch('garmin_sender.send_workout',return_value={'workout_id':321})
    def test_success_remains_success_after_persist_failure(self,send,persist,login,finish,claim,preview):
        result=send_canonical_workout(self.send,'Bearer token')
        self.assertEqual(result['workoutId'],321)
        finish.assert_called_once_with(CANON['athlete_id'],'w','sent',321)

    @patch('api.preview_workout',return_value=CANON)
    @patch('api.session_login',return_value=(MagicMock(get_activities_by_date=MagicMock(return_value=[])),object()))
    @patch('api.session_persist',return_value=None)
    @patch('garmin_activity_matching.normalize_candidates',return_value=[])
    def test_candidates_without_password(self,normalize,persist,login,preview):
        result=garmin_activity_candidates(self.candidates,'Bearer token')
        self.assertFalse(result['confirmed'])
        self.assertFalse(result['saved'])
        login.assert_called_once()

if __name__=='__main__':unittest.main()
