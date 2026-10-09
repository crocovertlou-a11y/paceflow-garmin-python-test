import unittest
from garmin_sender import send_workout, GarminPartialSendError
class TestPartialSend(unittest.TestCase):
    def test_scheduling_failure_preserves_workout_id(self):
        class Client:
            def upload_workout(self, payload): return {'workoutId': 987}
            def schedule_workout(self, workout_id, date): raise RuntimeError('failure')
        with self.assertRaises(GarminPartialSendError) as ctx:
            send_workout(Client(), {'workoutName':'Test'}, '2026-10-10')
        self.assertEqual(ctx.exception.workout_id, 987)
        self.assertEqual(ctx.exception.step, 'scheduling')
    def test_missing_id_never_schedules(self):
        class Client:
            def upload_workout(self, payload): return {}
            def schedule_workout(self, workout_id, date): raise AssertionError('must not schedule')
        with self.assertRaises(RuntimeError):
            send_workout(Client(), {}, '2026-10-10')
