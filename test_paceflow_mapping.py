import unittest
from paceflow_mapping import convert_paceflow

class MappingTests(unittest.TestCase):
    def setUp(self):
        self.w = {'title':'4x2km', 'structured_workout':{'valid':True,'blocks':[
            {'kind':'warmup','duration':{'value':2,'unit':'km'}},
            {'kind':'repeat','repeat':4,'children':[
                {'kind':'work','duration':{'value':2,'unit':'km'},'target':{'type':'pace_range','min':'4:30','max':'4:45'}},
                {'kind':'recovery','duration':{'value':1,'unit':'min'}}]},
            {'kind':'cooldown','duration':{'value':2,'unit':'km'}}]}}
    def test_ten_steps(self):
        steps=convert_paceflow(self.w)['workoutSegments'][0]['workoutSteps']
        self.assertEqual(len(steps),10)
        self.assertEqual([s['endConditionValue'] for s in steps],[2000,2000,60,2000,60,2000,60,2000,60,2000])
        self.assertAlmostEqual(steps[1]['targetValueOne'],1000/285)
        self.assertAlmostEqual(steps[1]['targetValueTwo'],1000/270)
    def test_unvalidated_rejected(self):
        self.w['structured_workout']['valid']=False
        with self.assertRaises(ValueError): convert_paceflow(self.w)
    def test_unsupported_hr_rejected(self):
        self.w['structured_workout']['blocks'][1]['children'][0]['target']={'type':'heart_rate','value':155}
        with self.assertRaises(ValueError): convert_paceflow(self.w)
if __name__=='__main__':unittest.main()
