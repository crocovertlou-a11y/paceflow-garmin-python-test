"""Authorized, read-only PaceFlow workout preview. No Garmin network operations.

Requires SUPABASE_URL, SUPABASE_ANON_KEY and SUPABASE_SERVICE_ROLE_KEY on
Render (never in the browser or repository). Uses a user JWT only to identify
its holder; all relationship checks are explicit server-side.
"""
import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from uuid import UUID

from paceflow_mapping import convert_paceflow


class AccessError(Exception):
    pass


def _uuid(value):
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError('Invalid identifier') from exc


def _request(url, key, bearer, *, timeout=12):
    req = Request(url, headers={'apikey': key, 'Authorization': 'Bearer ' + bearer,
                                'Accept': 'application/json'}, method='GET')
    try:
        with urlopen(req, timeout=timeout) as res:
            return json.load(res)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise AccessError('Supabase authorization unavailable') from exc


def preview_workout(user_jwt, workout_id, athlete_id, *, env=None, fetch=None, athlete_only=False):
    env = os.environ if env is None else env
    base = env.get('SUPABASE_URL', '').rstrip('/')
    anon = env.get('SUPABASE_ANON_KEY', '')
    service = env.get('SUPABASE_SERVICE_ROLE_KEY', '')
    if not base.startswith('https://') or not anon or not service:
        raise RuntimeError('Supabase preview configuration missing')
    if not user_jwt or len(user_jwt) > 8192:
        raise AccessError('Authentication required')
    wid, aid = _uuid(workout_id), _uuid(athlete_id)
    get = fetch or _request
    user = get(base + '/auth/v1/user', anon, user_jwt)
    uid = _uuid(user.get('id')) if isinstance(user, dict) else None
    if not uid:
        raise AccessError('Invalid session')

    def rows(table, select, **filters):
        query = {'select': select, 'limit': '2'}
        query.update({k: 'eq.' + str(v) for k, v in filters.items()})
        result = get(base + '/rest/v1/' + table + '?' + urlencode(query), service, service)
        if not isinstance(result, list):
            raise AccessError('Unexpected Supabase response')
        return result

    athlete = rows('athlete_profiles', 'id,user_id,owner_coach_id', id=aid)
    if len(athlete) != 1:
        raise AccessError('Athlete not found')
    a = athlete[0]
    allowed = a.get('user_id') == uid
    if not allowed and not athlete_only:
        coaches = rows('coaches', 'id', user_id=uid)
        coach_ids = [c['id'] for c in coaches]
        for coach_id in coach_ids:
            if a.get('owner_coach_id') == coach_id or rows('coach_athlete_assignments', 'id', coach_id=coach_id, athlete_id=aid):
                allowed = True
                break
    if not allowed:
        raise AccessError('Not authorized for this athlete')
    workouts = rows('workouts', 'id,athlete_id,title,scheduled_date,structured_workout', id=wid, athlete_id=aid)
    if len(workouts) != 1:
        raise AccessError('Workout not found')
    w = workouts[0]
    date = w.get('scheduled_date')
    if not isinstance(date, str) or len(date) != 10:
        raise ValueError('Workout has no valid scheduled date')
    converted = convert_paceflow(w)
    return {'status': 'preview', 'garmin_sent': False, 'workout_id': wid,
            'athlete_id': aid, 'scheduled_date': date, 'garmin_workout': converted}
