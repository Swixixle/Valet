from __future__ import annotations

import copy
import hashlib
import hmac
import json
import os
from typing import Any


_ALGORITHM = "hmac-sha256"


def _canonical_json_bytes(data: dict[str, Any]) -> bytes:
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )


def _resolve_signing_key(key: str | None = None) -> str:
    resolved = key or os.environ.get("RECEIPT_SIGNING_KEY", "")
    if not resolved:
        raise OSError("RECEIPT_SIGNING_KEY is not set.")
    return resolved


def _unsigned_receipt_payload(receipt: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(receipt)
    payload.pop("signature", None)
    return payload


def sign_receipt(receipt: dict[str, Any], key: str | None = None) -> dict[str, Any]:
    payload = _unsigned_receipt_payload(receipt)
    payload_bytes = _canonical_json_bytes(payload)
    signing_key = _resolve_signing_key(key)
    signature = hmac.new(signing_key.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    payload_hash = hashlib.sha256(payload_bytes).hexdigest()

    signed = copy.deepcopy(payload)
    signed["signature"] = {
        "algorithm": _ALGORITHM,
        "payload_hash": payload_hash,
        "value": signature,
    }
    return signed


def verify_receipt_signature(receipt: dict[str, Any], key: str | None = None) -> bool:
    signature_block = receipt.get("signature")
    if not isinstance(signature_block, dict):
        return False
    if signature_block.get("algorithm") != _ALGORITHM:
        return False

    payload = _unsigned_receipt_payload(receipt)
    payload_bytes = _canonical_json_bytes(payload)
    expected_hash = hashlib.sha256(payload_bytes).hexdigest()
    actual_hash = signature_block.get("payload_hash")
    if not isinstance(actual_hash, str) or not hmac.compare_digest(expected_hash, actual_hash):
        return False

    signing_key = _resolve_signing_key(key)
    expected_signature = hmac.new(
        signing_key.encode("utf-8"), payload_bytes, hashlib.sha256
    ).hexdigest()
    actual_signature = signature_block.get("value")
    return isinstance(actual_signature, str) and hmac.compare_digest(
        expected_signature, actual_signature
    )
