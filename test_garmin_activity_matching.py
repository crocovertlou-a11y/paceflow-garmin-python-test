import unittest
from datetime import date
from garmin_activity_matching import normalize_candidates
class Tests(unittest.TestCase):
 def test_dedup(self):
  r=normalize_candidates([{'activityId':7,'startTimeLocal':'2026-10-18 09:00:00'},{'activityId':8,'startTimeLocal':'2026-10-16 09:00:00'},{'activityId':8}],date(2026,10,16))
  self.assertEqual([x['activity_id'] for x in r],['8','7'])
  self.assertTrue(all(x['requires_athlete_confirmation'] for x in r))
 def test_metrics(self):
  r=normalize_candidates([{'activityId':1,'distance':-2,'duration':float('nan')}],date(2026,10,16))
  self.assertIsNone(r[0]['distance_m'])
  self.assertIsNone(r[0]['duration_s'])
