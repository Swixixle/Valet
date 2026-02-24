"""
Canonical JSON encoding for HALO receipts and events.
"""
import json
from typing import Any

def canonical_json(obj: Any) -> bytes:
    """
    Deterministically encode a JSON object as canonical bytes.
    Args:
        obj: Any JSON-serializable object.
    Returns:
        Canonical UTF-8 encoded JSON bytes.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

import copy

def receipt_for_manifest(receipt: dict) -> dict:
    """
    Returns the exact receipt object used for receipt_sha256 in bundle_manifest.
    Removes 'signatures' and 'bundle_hash', keeps all other fields.
    """
    r = copy.deepcopy(receipt)
    r.pop("bundle_hash", None)
    r.pop("signatures", None)
    return r
