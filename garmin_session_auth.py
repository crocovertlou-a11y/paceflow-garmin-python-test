"""Opt-in Garmin token restoration. No password storage or automatic retry.

NOT wired into api.py until the garminconnect tokenstore contract is validated.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Protocol
from garmin_session_store import GarminSessionStore, SessionNotFound, SessionStoreError


class ReconnectRequired(RuntimeError):
    """Existing session cannot be restored; ask athlete to reconnect."""


class TokenCodec(Protocol):
    def restore(self, blob: bytes): ...
    def export(self, client) -> bytes: ...


@dataclass
class SessionAuthenticator:
    store: GarminSessionStore
    codec: TokenCodec
    enabled: bool = False

    def restore(self, athlete_id: str):
        if not self.enabled:
            raise ReconnectRequired('Garmin session feature disabled')
        try:
            blob = self.store.load(athlete_id)
        except SessionNotFound:
            raise ReconnectRequired('Connect Garmin account') from None
        # Fail closed on storage errors: never silently fall back to password login.
        # Codec must be vetted against the installed garminconnect version.
        try:
            return self.codec.restore(blob)
        except Exception:
            # Do not log exception: third-party libraries can include token data.
            raise ReconnectRequired('Reconnect Garmin account') from None

    def persist(self, athlete_id: str, client) -> None:
        if not self.enabled:
            return
        try:
            blob = self.codec.export(client)
            self.store.save(athlete_id, blob)
        except Exception:
            # Explicit failure; callers must not claim persistent login worked.
            raise SessionStoreError('Could not persist Garmin session') from None

    def disconnect(self, athlete_id: str) -> None:
        if not self.enabled:
            raise ReconnectRequired('Garmin session feature disabled')
        self.store.revoke(athlete_id)
