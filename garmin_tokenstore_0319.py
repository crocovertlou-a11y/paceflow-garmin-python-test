"""Explicit adapter for garminconnect 0.3.19 tokenstore JSON.

No network or credentials are accessed during export. Restoring does invoke Garmin
login to validate tokens; callers must enforce authorization and rate limits.
"""
from __future__ import annotations
import importlib.metadata
import json
from garmin_session_codec import GarminTokenCodec, TokenstoreContract

EXPECTED_VERSION = '0.3.19'

class GarminVersionMismatch(RuntimeError):
    pass


def _assert_version():
    if importlib.metadata.version('garminconnect') != EXPECTED_VERSION:
        raise GarminVersionMismatch('Unverified garminconnect version')


def export_token_json(client) -> bytes:
    """Export the currently active session, including refreshed tokens."""
    _assert_version()
    session = getattr(client, 'client', None)
    if session is None or not callable(getattr(session, 'dumps', None)):
        raise GarminVersionMismatch('Token JSON export API not verified')
    value = session.dumps()
    if isinstance(value, str):
        value = value.encode('utf-8')
    if not isinstance(value, bytes):
        raise GarminVersionMismatch('Unexpected token export type')
    decoded = json.loads(value)
    if not isinstance(decoded, dict):
        raise GarminVersionMismatch('Invalid token JSON')
    return value


def restore_token_json(raw: bytes):
    """Restore a saved session without supplying credentials.

    If Garmin rejects the cached tokens, this fails; it cannot fall back to
    password authentication because none is supplied.
    """
    _assert_version()
    from garminconnect import Garmin
    token_json = raw.decode('utf-8')
    if not isinstance(json.loads(token_json), dict):
        raise ValueError('Invalid token JSON')
    client = Garmin()
    client.login(tokenstore=token_json)
    return client


def build_codec() -> GarminTokenCodec:
    _assert_version()
    return GarminTokenCodec(TokenstoreContract(
        library_version=EXPECTED_VERSION,
        exporter=export_token_json,
        restorer=restore_token_json,
    ))
