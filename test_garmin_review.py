import unittest
from garmin_activity_matching import assess_candidate

class ReviewTests(unittest.TestCase):
    def test_same_day_run(self):
        x = assess_candidate({'date_difference_days': 0, 'sport': 'running', 'distance_m': 10000}, expected_sport='running', expected_distance_m=10000)
        self.assertEqual(x['checks']['distance'], 'close')
        self.assertFalse(x['automatic_match'])
    def test_different_sport_and_distance(self):
        x = assess_candidate({'date_difference_days': 1, 'sport': 'cycling', 'distance_m': 2000}, expected_sport='running', expected_distance_m=10000)
        self.assertEqual(x['checks']['sport'], 'different')
        self.assertEqual(x['checks']['distance'], 'large_difference')
        self.assertEqual(len(x['review_reasons']), 3)
    def test_missing_fields(self):
        x = assess_candidate({'date_difference_days': None, 'sport': None, 'distance_m': None}, expected_sport='running', expected_distance_m=10000)
        self.assertEqual(len(x['review_reasons']), 3)
    def test_invalid_expected_distance(self):
        with self.assertRaises(ValueError):
            assess_candidate({}, expected_distance_m=0)
