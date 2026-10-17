"""PaceFlow: encrypted per-athlete Garmin token storage building block.

This module does not perform Garmin logins or alter workout sending.
It requires a durable backend supplied by the application. Never store tokens in logs.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID
from cryptography.fernet import Fernet, InvalidToken


class SessionStoreError(RuntimeError):
    pass


class SessionNotFound(SessionStoreError):
    pass


class EncryptedBackend(Protocol):
    def get(self, athlete_id: str) -> bytes | None: ...
    def put(self, athlete_id: str, encrypted_data: bytes) -> None: ...
    def delete(self, athlete_id: str) -> None: ...


def canonical_athlete_id(value: str) -> str:
    try:
        return str(UUID(value))
    except (ValueError, AttributeError, TypeError) as exc:
        raise ValueError('Invalid athlete UUID') from exc


@dataclass
class GarminSessionStore:
    backend: EncryptedBackend
    encryption_key: bytes

    def __post_init__(self):
        self._cipher = Fernet(self.encryption_key)

    def save(self, athlete_id: str, token_blob: bytes) -> None:
        athlete_id = canonical_athlete_id(athlete_id)
        if not isinstance(token_blob, bytes) or not token_blob or len(token_blob) > 65536:
            raise ValueError('Invalid token blob')
        # Bind ciphertext to athlete ID to prevent cross-athlete token swapping.
        payload = athlete_id.encode('ascii') + b'\n' + token_blob
        self.backend.put(athlete_id, self._cipher.encrypt(payload))

    def load(self, athlete_id: str) -> bytes:
        athlete_id = canonical_athlete_id(athlete_id)
        encrypted = self.backend.get(athlete_id)
        if encrypted is None:
            raise SessionNotFound('Garmin session not connected')
        try:
            payload = self._cipher.decrypt(encrypted)
        except (InvalidToken, TypeError, ValueError) as exc:
            raise SessionStoreError('Garmin session cannot be decrypted') from exc
        prefix = athlete_id.encode('ascii') + b'\n'
        if not payload.startswith(prefix):
            raise SessionStoreError('Garmin session athlete mismatch')
        return payload[len(prefix):]

    def revoke(self, athlete_id: str) -> None:
        self.backend.delete(canonical_athlete_id(athlete_id))
