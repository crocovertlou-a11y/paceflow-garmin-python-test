import json
import unittest
from pathlib import Path
from adapter import convert

class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.source = json.loads(Path(__file__).with_name('example_workout.json').read_text())
    def test_ten_steps_and_targets(self):
        steps = convert(self.source)['workoutSegments'][0]['workoutSteps']
        self.assertEqual(len(steps), 10)
        self.assertEqual([s['stepType']['stepTypeKey'] for s in steps],
                         ['warmup'] + ['interval', 'recovery']*4 + ['cooldown'])
        self.assertAlmostEqual(steps[1]['targetValueOne'], 1000/285)
        self.assertAlmostEqual(steps[1]['targetValueTwo'], 1000/270)
    def test_reject_bad_input(self):
        self.source['blocks'][0]['steps'][0]['distance_m'] = -2
        with self.assertRaises(ValueError): convert(self.source)

if __name__ == '__main__': unittest.main()
