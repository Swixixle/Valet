"""
HALO event and receipt models.
"""
from typing import TypedDict, List, Optional, Dict, Any
from dataclasses import dataclass, field

class Attachment(TypedDict):
    name: str
    sha256: str
    size_bytes: int
    mime: Optional[str]
    path_in_bundle: str

class BaseEvent(TypedDict):
    seq: int
    ts: str
    type: str
    payload: Dict[str, Any]
    attachments: List[Attachment]
    prev_event_hash: str
    event_hash: str
    payload_hash: str

class EventSummary(TypedDict):
    seq: int
    ts: str
    type: str
    payload_hash: str
    event_hash: str

class SignatureBlock(TypedDict):
    alg: str
    key_id: str
    sig: str
    signed_payload: str
    payload_hash: str

class SessionReceipt(TypedDict):
    schema_version: str
    session_id: str
    started_at: str
    ended_at: str
    issuer: Dict[str, Any]
    subject: Dict[str, Any]
    events: List[EventSummary]
    transcript_hash: str
    bundle_hash: str
    signatures: List[SignatureBlock]

class SnapshotReceipt(TypedDict):
    schema_version: str
    snapshot_id: str
    captured_at: str
    issuer: Dict[str, Any]
    subject: Dict[str, Any]
    type: str
    payload: Dict[str, Any]
    payload_hash: str
    signatures: List[SignatureBlock]
    bundle_hash: str
