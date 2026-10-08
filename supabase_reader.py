"""Read-only Supabase REST reader. Uses athlete-scoped RLS JWT; no service-role keys."""
import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from uuid import UUID


def validate_uuid(value):
    return str(UUID(value))


def fetch_workout(base_url, anon_key, user_jwt, workout_id, athlete_id):
    if not base_url.startswith('https://'):
        raise ValueError('SUPABASE_URL must use HTTPS')
    if not anon_key or not user_jwt:
        raise ValueError('SUPABASE_ANON_KEY and SUPABASE_USER_JWT are required')
    query = urllib.parse.urlencode({
        'select': 'id,athlete_id,title,scheduled_date,status,structured_workout',
        'id': 'eq.' + validate_uuid(workout_id),
        'athlete_id': 'eq.' + validate_uuid(athlete_id),
        'limit': '1',
    })
    url = base_url.rstrip('/') + '/rest/v1/workouts?' + query
    request = urllib.request.Request(url, headers={
        'apikey': anon_key, 'Authorization': 'Bearer ' + user_jwt,
        'Accept': 'application/json',
    }, method='GET')
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            rows = json.load(response)
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            raise RuntimeError('Access denied by Supabase RLS; no service-role fallback') from None
        raise RuntimeError('Supabase request failed (HTTP %d)' % e.code) from None
    if not isinstance(rows, list) or len(rows) != 1:
        raise LookupError('No authorized workout found for this athlete')
    row = rows[0]
    if row.get('id') != workout_id or row.get('athlete_id') != athlete_id:
        raise ValueError('Returned workout identity mismatch')
    return row


def main():
    parser = argparse.ArgumentParser(description='PaceFlow read-only Supabase POC')
    parser.add_argument('--workout-id', required=True)
    parser.add_argument('--athlete-id', required=True)
    parser.add_argument('--preview', action='store_true', help='Show metadata only; never prints tokens')
    args = parser.parse_args()
    row = fetch_workout(os.environ.get('SUPABASE_URL',''),
                        os.environ.get('SUPABASE_ANON_KEY',''),
                        os.environ.get('SUPABASE_USER_JWT',''),
                        args.workout_id, args.athlete_id)
    print(json.dumps({'id': row['id'], 'athlete_id': row['athlete_id'],
                      'title': row.get('title'), 'scheduled_date': row.get('scheduled_date'),
                      'has_structured_workout': bool(row.get('structured_workout'))}, indent=2))
    print('READ ONLY: no Garmin call and no Supabase mutation')

if __name__ == '__main__':
    main()
