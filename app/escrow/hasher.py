from __future__ import annotations

import hashlib
import json


def sha256_hash(data: str | bytes | dict) -> str:
    """Return the SHA-256 hex digest of *data*.

    Accepts a raw string, bytes, or a JSON-serialisable dict
    (serialised with sorted keys for determinism).
    """
    if isinstance(data, dict):
        raw = json.dumps(data, sort_keys=True, ensure_ascii=False).encode()
    elif isinstance(data, str):
        raw = data.encode()
    else:
        raw = data
    return hashlib.sha256(raw).hexdigest()
