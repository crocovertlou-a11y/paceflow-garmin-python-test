"""Server-only Supabase REST backend for encrypted Garmin sessions.

Pass only encrypted ciphertext from GarminSessionStore. Do not use an anon key.
No athlete authorization occurs here: the caller MUST verify ownership first.
"""
from __future__ import annotations
import base64
import json
from dataclasses import dataclass
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from garmin_session_store import canonical_athlete_id, SessionStoreError


class SessionBackendUnavailable(SessionStoreError):
    pass


@dataclass
class SupabaseSessionBackend:
    url: str
    service_role_key: str
    timeout: float = 8.0
    _revisions: dict | None = None

    def __post_init__(self):
        if not self.url.startswith('https://') or not self.service_role_key:
            raise ValueError('HTTPS Supabase URL and server-only key required')
        self.url = self.url.rstrip('/')
        self._revisions = {}

    def _request(self, method, path, payload=None, prefer=None):
        headers = {
            'apikey': self.service_role_key,
            'Authorization': 'Bearer ' + self.service_role_key,
            'Accept': 'application/json',
        }
        if payload is not None:
            headers['Content-Type'] = 'application/json'
        if prefer:
            headers['Prefer'] = prefer
        request = Request(self.url + '/rest/v1/' + path,
                          data=json.dumps(payload).encode('utf-8') if payload is not None else None,
                          headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read(131073)
                if len(body) > 131072:
                    raise SessionBackendUnavailable('Oversized session response')
                return json.loads(body) if body else None
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            # Deliberately do not expose provider errors, URL, credentials, or body.
            raise SessionBackendUnavailable('Garmin session storage unavailable') from None

    def get(self, athlete_id: str) -> bytes | None:
        athlete_id = canonical_athlete_id(athlete_id)
        result = self._request('GET', 'pf_garmin_sessions?athlete_id=eq.' + quote(athlete_id) + '&select=ciphertext,revision&limit=1')
        if not isinstance(result, list):
            raise SessionBackendUnavailable('Invalid session storage response')
        if not result:
            self._revisions[athlete_id] = 0
            return None
        if len(result) != 1 or not isinstance(result[0].get('ciphertext'), str):
            raise SessionBackendUnavailable('Invalid session storage response')
        revision = result[0].get('revision')
        if not isinstance(revision, int) or revision < 1:
            raise SessionBackendUnavailable('Invalid session revision')
        self._revisions[athlete_id] = revision
        try:
            return base64.b64decode(result[0]['ciphertext'], validate=True)
        except (ValueError, TypeError) as exc:
            raise SessionBackendUnavailable('Invalid encrypted session encoding') from None

    def put(self, athlete_id: str, encrypted_data: bytes) -> None:
        athlete_id = canonical_athlete_id(athlete_id)
        if not isinstance(encrypted_data, bytes) or len(encrypted_data) > 131072:
            raise ValueError('Invalid encrypted session')
        if athlete_id not in self._revisions:
            raise SessionBackendUnavailable('Session must be read before update')
        expected = self._revisions[athlete_id]
        result = self._request('POST', 'rpc/pf_garmin_session_cas',
                      {'p_athlete': athlete_id, 'p_expected_revision': expected,
                       'p_ciphertext': base64.b64encode(encrypted_data).decode('ascii')})
        if not isinstance(result, int) or result != expected + 1:
            raise SessionBackendUnavailable('Concurrent session update; retry after reload')
        self._revisions[athlete_id] = result

    def delete(self, athlete_id: str) -> None:
        athlete_id = canonical_athlete_id(athlete_id)
        self._request('DELETE', 'pf_garmin_sessions?athlete_id=eq.' + quote(athlete_id), prefer='return=minimal')
