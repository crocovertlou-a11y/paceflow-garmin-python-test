"""Athlete-scoped encrypted Garmin sessions using garminconnect 0.3.19 Client.dumps/loads.
Never print credentials or tokens. No automatic password fallback from a saved session.
"""
import os
import urllib.parse
import json
import urllib.request
from cryptography.fernet import Fernet, InvalidToken

class SessionStoreError(Exception):
    pass

def _settings():
    url = os.environ.get('SUPABASE_URL', '').rstrip('/')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
    secret = os.environ.get('GARMIN_SESSION_FERNET_KEY', '')
    if not url.startswith('https://') or not key or not secret:
        raise SessionStoreError('Encrypted session store is not configured')
    try:
        cipher = Fernet(secret.encode())
    except (ValueError, TypeError):
        raise SessionStoreError('Invalid session encryption key') from None
    return url, key, cipher

def _request(method, path, payload=None):
    url, key, _ = _settings()
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url + '/rest/v1/' + path, method=method, data=data,
        headers={'apikey': key, 'Authorization': 'Bearer ' + key,
                 'Content-Type': 'application/json', 'Accept': 'application/json',
                 'Prefer': 'resolution=merge-duplicates,return=minimal'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.load(response) if method == 'GET' else None
    except Exception:
        raise SessionStoreError('Session storage unavailable') from None

def restore(athlete_id):
    _, _, cipher = _settings()
    query = urllib.parse.urlencode({'select': 'encrypted_tokens',
        'athlete_id': 'eq.' + str(athlete_id), 'limit': '1'})
    rows = _request('GET', 'paceflow_garmin_sessions?' + query)
    if not rows:
        return None
    try:
        token_json = cipher.decrypt(rows[0]['encrypted_tokens'].encode()).decode('utf-8')
        if not token_json.startswith('{') or len(token_json) > 200000:
            raise ValueError()
        if not isinstance(json.loads(token_json), dict):
            raise ValueError()
        return token_json
    except (InvalidToken, ValueError, TypeError, KeyError, UnicodeDecodeError):
        raise SessionStoreError('Stored Garmin session invalid') from None

def persist(athlete_id, token_json):
    _, _, cipher = _settings()
    if not isinstance(token_json, str) or not token_json.startswith('{'):
        raise SessionStoreError('Invalid Garmin session export')
    encrypted = cipher.encrypt(token_json.encode()).decode()
    _request('POST', 'paceflow_garmin_sessions?on_conflict=athlete_id',
        [{'athlete_id': str(athlete_id), 'encrypted_tokens': encrypted}])

def login_with_session(Garmin, athlete_id, email, password, prompt_mfa):
    """A saved token is restored without credentials, preventing hidden fallback logins."""
    token_json = restore(athlete_id)
    if token_json is not None:
        client = Garmin(prompt_mfa=prompt_mfa)
        try:
            client.login(tokenstore=token_json)
        except Exception:
            raise SessionStoreError('Saved Garmin session rejected; reconnect explicitly') from None
    else:
        client = Garmin(email, password, prompt_mfa=prompt_mfa)
        client.login()  # Garmin auth errors propagate to the caller
    try:
        exported = client.client.dumps()
        if not isinstance(exported, str):
            raise ValueError('non-text export')
        persist(athlete_id, exported)
    except Exception:
        raise SessionStoreError('Garmin session could not be saved securely') from None
    return client
