"""
SessionRecorder for HALO multi-event recording.
"""
from pathlib import Path
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List, Tuple
from .models import BaseEvent, SessionReceipt, EventSummary, SignatureBlock
from .canonical import canonical_json
from .crypto import sha256_hex
from .signer import get_signer_from_env, Signer
from .export import export_session_bundle

class SessionRecorder:
    def __init__(
        self,
        machine_id: str,
        subject_meta: Optional[Dict[str, Any]] = None,
        signer: Optional[Signer] = None,
        now_fn: Optional[Callable[[], datetime]] = None,
        id_fn: Optional[Callable[[], str]] = None
    ):
        self.machine_id = machine_id
        self.subject_meta = subject_meta or {}
        self.signer = signer or get_signer_from_env()
        self.now_fn = now_fn or (lambda: datetime.utcnow())
        self.id_fn = id_fn or (lambda: str(uuid4()))
        self._events: List[BaseEvent] = []
        self._recording = False
        self._session_id = None
        self._started_at = None
        self._ended_at = None
    @property
    def is_recording(self) -> bool:
        return self._recording
    def start(self, session_meta: Optional[Dict[str, Any]] = None) -> None:
        if self._recording:
            raise RuntimeError("Session already started")
        self._session_id = self.id_fn()
        self._started_at = self.now_fn().isoformat(timespec="seconds") + "Z"
        self._recording = True
        self._session_meta = session_meta or {}
    def record_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        attachments: Optional[List[Path]] = None,
        ts: Optional[str] = None
    ) -> None:
        if not self._recording:
            raise RuntimeError("Session not started")
        seq = len(self._events) + 1
        ts = ts or self.now_fn().isoformat(timespec="seconds") + "Z"
        prev_event_hash = self._events[-1]["event_hash"] if self._events else "0"*64
        prev_event_hash_bytes = bytes.fromhex(prev_event_hash)
        payload_hash = sha256_hex(canonical_json(payload))
        attachments_list = []
        # Attachments handling is stubbed for now
        event_body_for_hash = {
            "seq": seq,
            "ts": ts,
            "type": event_type,
            "payload": payload,
            "attachments": attachments_list,
            "prev_event_hash": prev_event_hash
        }
        event_hash = sha256_hex(canonical_json(event_body_for_hash) + prev_event_hash_bytes)
        event = {
            "seq": seq,
            "ts": ts,
            "type": event_type,
            "payload": payload,
            "attachments": attachments_list,
            "prev_event_hash": prev_event_hash,
            "event_hash": event_hash,
            "payload_hash": payload_hash
        }
        self._events.append(event)
    def stop_and_export(
        self,
        output_dir: Path,
        source_url: Optional[str] = None
    ) -> Tuple[Path, Dict[str, Any]]:
        if not self._recording:
            raise RuntimeError("Session not started")
        self._ended_at = self.now_fn().isoformat(timespec="seconds") + "Z"
        self._recording = False
        issuer = {"service": "valet", "key_id": self.signer.key_id}
        subject = {"machine_id": self.machine_id}
        if self.subject_meta:
            subject.update(self.subject_meta)
        events_summary = [
            {
                "seq": e["seq"],
                "ts": e["ts"],
                "type": e["type"],
                "payload_hash": e["payload_hash"],
                "event_hash": e["event_hash"]
            } for e in self._events
        ]
        transcript_hash = sha256_hex(canonical_json(self._events))
        receipt = {
            "schema_version": "halo.session.v1",
            "session_id": self._session_id,
            "started_at": self._started_at,
            "ended_at": self._ended_at,
            "issuer": issuer,
            "subject": subject,
            "events": events_summary,
            "transcript_hash": transcript_hash,
            "bundle_hash": "",
            "signatures": []
        }
        payload_bytes = canonical_json({k: v for k, v in receipt.items() if k != "signatures" and k != "bundle_hash"})
        sig = self.signer.sign(payload_bytes)
        if sig:
            receipt["signatures"] = [sig]
        bundle_path, receipt_out = export_session_bundle(
            receipt, self._events, output_dir, source_url, self.machine_id, created_at=self._ended_at
        )
        return bundle_path, receipt_out
    def __enter__(self):
        self.start()
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.is_recording:
            self.stop_and_export(Path("."))
