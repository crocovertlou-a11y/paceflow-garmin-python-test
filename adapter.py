"""Isolated Garmin workout DTO adapter. No network calls, secrets or athlete data."""
import json
from pathlib import Path

KINDS = {'warmup': (1, 'warmup'), 'interval': (3, 'interval'), 'recovery': (4, 'recovery'), 'cooldown': (2, 'cooldown')}

def _pace_to_mps(pace):
    if not isinstance(pace, str) or ':' not in pace:
        raise ValueError('pace must be MM:SS per km')
    mm, ss = map(int, pace.split(':'))
    seconds = mm * 60 + ss
    if not (120 <= seconds <= 1200 and 0 <= ss < 60):
        raise ValueError('invalid pace')
    return 1000 / seconds

def convert(workout):
    if workout.get('sport') != 'running':
        raise ValueError('Only running supported by this prototype')
    name = workout.get('name')
    if not isinstance(name, str) or not 1 <= len(name) <= 100:
        raise ValueError('name required (1-100 chars)')
    steps = []
    for block in workout.get('blocks', []):
        repeats = block.get('repeat', 1)
        if type(repeats) is not int or not 1 <= repeats <= 30:
            raise ValueError('repeat must be 1..30')
        for _ in range(repeats):
            for source in block.get('steps', []):
                kind = source.get('kind')
                if kind not in KINDS:
                    raise ValueError('unknown step kind')
                has_distance = 'distance_m' in source
                has_time = 'seconds' in source
                if has_distance == has_time:
                    raise ValueError('exactly one of distance_m or seconds required')
                value = source['distance_m'] if has_distance else source['seconds']
                if type(value) is not int or not 1 <= value <= 100000:
                    raise ValueError('invalid step duration/distance')
                step_id, step_key = KINDS[kind]
                entry = {'type': 'ExecutableStepDTO', 'stepOrder': len(steps)+1,
                         'stepType': {'stepTypeId': step_id, 'stepTypeKey': step_key},
                         'endCondition': {'conditionTypeId': 3 if has_distance else 2,
                                          'conditionTypeKey': 'distance' if has_distance else 'time'},
                         'endConditionValue': value}
                if 'pace' in source:
                    p = source['pace']
                    slow, fast = _pace_to_mps(p['slow']), _pace_to_mps(p['fast'])
                    if slow > fast:
                        raise ValueError('slow pace must be slower than fast pace')
                    entry.update({'targetType': {'workoutTargetTypeId': 6, 'workoutTargetTypeKey': 'pace.zone'},
                                  'targetValueOne': slow, 'targetValueTwo': fast})
                steps.append(entry)
    if not 1 <= len(steps) <= 200:
        raise ValueError('workout must contain 1..200 steps')
    sport = {'sportTypeId': 1, 'sportTypeKey': 'running'}
    return {'workoutName': name, 'sportType': sport,
            'workoutSegments': [{'segmentOrder': 1, 'sportType': sport, 'workoutSteps': steps}]}

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='PaceFlow to Garmin DTO preview only; never sends data')
    parser.add_argument('file', help='Normalized PaceFlow workout JSON')
    args = parser.parse_args()
    workout = json.loads(Path(args.file).read_text(encoding='utf-8'))
    print(json.dumps(convert(workout), ensure_ascii=False, indent=2))
