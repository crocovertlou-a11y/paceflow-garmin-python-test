"""Opt-in Garmin session authentication; never silently retries a rejected session."""
import os
from garmin_session_auth import SessionAuthenticator, ReconnectRequired
from garmin_session_store import GarminSessionStore, SessionNotFound, SessionStoreError
from garmin_session_supabase import SupabaseSessionBackend
from garmin_tokenstore_0319 import build_codec


def enabled():
    return os.getenv('PACEFLOW_GARMIN_SESSION_MODE') == 'enabled'


def authenticator():
    key = os.environ['PACEFLOW_GARMIN_SESSION_FERNET_KEY'].encode('ascii')
    backend = SupabaseSessionBackend(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE_KEY'])
    return SessionAuthenticator(GarminSessionStore(backend, key), build_codec(), enabled=True)


def login(athlete_id, email=None, password=None, prompt_mfa=None):
    from garminconnect import Garmin
    if not enabled():
        if not email or not password:
            raise ReconnectRequired('Identifiants Garmin requis')
        client = Garmin(email, password, prompt_mfa=prompt_mfa)
        client.login()
        return client, None
    auth = authenticator()
    try:
        blob = auth.store.load(athlete_id)
    except SessionNotFound:
        blob = None
    # Never mask storage errors by initiating a fresh SSO login.
    if blob is not None:
        try:
            client = auth.codec.restore(blob)
        except Exception:
            # A cached session may be expired. Only attempt a new SSO login
            # when the athlete explicitly provided fresh credentials.
            if not email or not password:
                raise ReconnectRequired('Session Garmin expirée : reconnexion nécessaire') from None
            client = Garmin(email, password, prompt_mfa=prompt_mfa)
            client.login()
    else:
        if not email or not password:
            raise ReconnectRequired('Connexion initiale Garmin requise')
        client = Garmin(email, password, prompt_mfa=prompt_mfa)
        client.login()
    # Initial login must be persisted before any upload; otherwise fail closed.
    auth.persist(athlete_id, client)
    return client, auth


def persist(auth, athlete_id, client):
    if auth is not None:
        auth.persist(athlete_id, client)
