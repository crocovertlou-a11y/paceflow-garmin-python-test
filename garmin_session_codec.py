"""Version-gated adapter for garminconnect tokenstore, without live login.

Explicitly accepts only a validated implementation supplied by the caller.
The default is fail-closed until the installed library contract is verified.
"""
from dataclasses import dataclass
import json

class UnsupportedTokenstore(RuntimeError):
    pass

@dataclass(frozen=True)
class TokenstoreContract:
    library_version: str
    exporter: object
    restorer: object

    def __post_init__(self):
        if not self.library_version or not callable(self.exporter) or not callable(self.restorer):
            raise ValueError('Validated tokenstore implementation required')

class GarminTokenCodec:
    MAX_BYTES = 65536

    def __init__(self, contract: TokenstoreContract | None = None):
        if contract is None:
            raise UnsupportedTokenstore('Tokenstore API has not been validated')
        self.contract = contract

    def export(self, client) -> bytes:
        raw = self.contract.exporter(client)
        if not isinstance(raw, bytes) or not raw or len(raw) > self.MAX_BYTES:
            raise UnsupportedTokenstore('Invalid tokenstore export')
        return json.dumps({'v': 1, 'library': self.contract.library_version,
                           'token_hex': raw.hex()}, separators=(',', ':')).encode()

    def restore(self, blob: bytes):
        if not isinstance(blob, bytes) or len(blob) > self.MAX_BYTES * 3:
            raise UnsupportedTokenstore('Invalid tokenstore envelope')
        try:
            envelope = json.loads(blob)
            if not isinstance(envelope, dict) or set(envelope) != {'v','library','token_hex'}:
                raise ValueError()
            if envelope['v'] != 1 or envelope['library'] != self.contract.library_version:
                raise ValueError()
            raw = bytes.fromhex(envelope['token_hex'])
            if not raw or len(raw) > self.MAX_BYTES:
                raise ValueError()
        except (ValueError, TypeError, KeyError):
            raise UnsupportedTokenstore('Invalid or incompatible tokenstore') from None
        return self.contract.restorer(raw)
