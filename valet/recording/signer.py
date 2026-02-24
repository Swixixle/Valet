"""
Signer interface and implementations for HALO receipts.
"""
from typing import Protocol, Optional
from .models import SignatureBlock

class Signer(Protocol):
    key_id: str
    alg: str
    def sign(self, payload: bytes) -> SignatureBlock: ...

class NoopSigner:
    key_id = "noop"
    alg = "none"
    def sign(self, payload: bytes) -> Optional[SignatureBlock]:
        return None

try:
    import nacl.signing
    import nacl.encoding
except ImportError:
    nacl = None

import os
from .crypto import b64url_encode, sha256_hex

class Ed25519Signer:
    alg = "ed25519"
    def __init__(self, key_id: str, private_key_b64: str):
        if nacl is None:
            raise ImportError("pynacl is required for Ed25519Signer")
        self.key_id = key_id
        seed = b64url_decode(private_key_b64)
        if len(seed) == 64:
            seed = seed[:32]
        if len(seed) != 32:
            raise ValueError("Ed25519 seed must be 32 bytes")
        self._signer = nacl.signing.SigningKey(seed)
    def sign(self, payload: bytes) -> SignatureBlock:
        sig_bytes = self._signer.sign(payload).signature
        return {
            "alg": self.alg,
            "key_id": self.key_id,
            "sig": b64url_encode(sig_bytes),
            "signed_payload": b64url_encode(payload),
            "payload_hash": sha256_hex(payload)
        }

def get_signer_from_env() -> Signer:
    key_id = os.environ.get("HALO_KEY_ID")
    priv = os.environ.get("HALO_ED25519_PRIVATE_KEY_B64")
    if key_id and priv and nacl:
        return Ed25519Signer(key_id, priv)
    return NoopSigner()
