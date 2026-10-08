"""Convert PaceFlow v0.10.12 structured_workout into normalized bridge DTO.
No I/O or network calls. Fail closed for unsupported targets.
"""
from adapter import convert


def _duration(d):
    if not isinstance(d, dict):
        raise ValueError('Missing duration')
    v, unit = d.get('value'), d.get('unit')
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:
        raise ValueError('Invalid duration')
    if unit not in ('km', 'm', 'min', 'sec'):
        raise ValueError('Unsupported duration unit')
    key = 'distance_m' if unit in ('km', 'm') else 'seconds'
    mult = {'km': 1000, 'm': 1, 'min': 60, 'sec': 1}[unit]
    amount = round(v * mult)
    if amount < 1 or abs(amount - v * mult) > 1e-6:
        raise ValueError('Duration cannot be represented precisely')
    return {key: amount}


def _step(b):
    kinds = {'warmup': 'warmup', 'work': 'interval', 'recovery': 'recovery', 'cooldown': 'cooldown'}
    kind = kinds.get(b.get('kind'))
    if not kind:
        raise ValueError('Unsupported step kind')
    out = {'kind': kind, **_duration(b.get('duration'))}
    t = b.get('target')
    if t:
        if t.get('type') == 'pace_range':
            out['pace'] = {'slow': t['max'], 'fast': t['min']}
        elif t.get('type') == 'pace':
            out['pace'] = {'slow': t['value'], 'fast': t['value']}
        else:
            raise ValueError('Unsupported target: ' + str(t.get('type')))
    return out


def normalize(w):
    if not isinstance(w, dict) or not w.get('structured_workout', {}).get('valid'):
        raise ValueError('PaceFlow workout not validated')
    blocks = []
    for b in w['structured_workout'].get('blocks', []):
        if b.get('kind') == 'repeat':
            blocks.append({'repeat': b.get('repeat'), 'steps': [_step(c) for c in b.get('children', [])]})
        else:
            blocks.append({'steps': [_step(b)]})
    return {'name': w.get('title'), 'sport': 'running', 'blocks': blocks}


def convert_paceflow(w):
    return convert(normalize(w))
