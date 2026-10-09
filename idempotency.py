"""Durable send claim through a SECURITY DEFINER Supabase RPC.

Fail closed: if the database is unavailable, never contact Garmin.
"""
import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

class LedgerError(Exception):
    pass

class AlreadyClaimed(LedgerError):
    pass


def _rpc(name, payload):
    base = os.environ.get('SUPABASE_URL', '').rstrip('/')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
    if not base.startswith('https://') or not key:
        raise LedgerError('Ledger configuration unavailable')
    req = Request(base + '/rest/v1/rpc/' + name,
                  data=json.dumps(payload).encode(), method='POST',
                  headers={'apikey':key,'Authorization':'Bearer '+key,
                           'Content-Type':'application/json','Accept':'application/json'})
    try:
        with urlopen(req, timeout=12) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        raise LedgerError('Ledger unavailable') from exc


def claim(athlete_id, workout_id):
    result = _rpc('paceflow_garmin_claim', {'p_athlete':athlete_id,'p_workout':workout_id})
    if result is not True:
        raise AlreadyClaimed('Existing or uncertain send; check Garmin Connect')


def finish(athlete_id, workout_id, status, garmin_id=None):
    if status not in ('sent', 'partial', 'uncertain', 'auth_failed'):
        raise ValueError('Invalid send status')
    _rpc('paceflow_garmin_finish', {'p_athlete':athlete_id,'p_workout':workout_id,
                                   'p_status':status,'p_garmin_id':str(garmin_id) if garmin_id is not None else None})
