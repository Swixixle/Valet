"""
Crypto primitives for HALO recording.
"""
import hashlib
import base64
from typing import Any

def sha256_bytes(data: bytes) -> bytes:
    """
    Compute SHA-256 hash of bytes.
    """
    return hashlib.sha256(data).digest()

def sha256_hex(data: bytes) -> str:
    """
    Compute SHA-256 hash of bytes and return as lowercase hex string.
    """
    return hashlib.sha256(data).hexdigest()

def b64url_encode(data: bytes) -> str:
    """
    URL-safe base64 encode, strip '=' padding.
    """
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

def b64url_decode(s: str) -> bytes:
    """
    Decode URL-safe base64 string, restoring padding.
    """
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)
