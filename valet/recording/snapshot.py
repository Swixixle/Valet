"""
SnapshotRecorder for HALO one-off event capture.
"""
from pathlib import Path
from uuid import uuid4
from datetime import datetime, UTC
from typing import Dict, Any, Optional, Tuple
from .models import SnapshotReceipt, SignatureBlock
from .canonical import canonical_json
from .crypto import sha256_hex
from .signer import get_signer_from_env, Signer
from .export import export_snapshot_bundle

def create_snapshot(
    payload: Dict[str, Any],
    output_dir: Path,
    machine_id: str,
    subject_meta: Optional[Dict[str, Any]] = None,
    signer: Optional[Signer] = None,
    raw_text: Optional[str] = None,
    source_url: Optional[str] = None
) -> Tuple[Path, Dict[str, Any]]:
    now_fn = locals().get("now_fn") or globals().get("now_fn")
    id_fn = locals().get("id_fn") or globals().get("id_fn")
    now = now_fn().isoformat(timespec="seconds") + "Z" if now_fn else datetime.now(UTC).isoformat(timespec="seconds") + "Z"
    snapshot_id = id_fn() if id_fn else str(uuid4())
    issuer = {"service": "valet", "key_id": signer.key_id if signer else "noop"}
    subject = {"machine_id": machine_id}
    if subject_meta:
        subject.update(subject_meta)
    payload_hash = sha256_hex(canonical_json(payload))
    receipt = {
        "schema_version": "halo.snapshot.v1",
        "snapshot_id": snapshot_id,
        "captured_at": now,
        "issuer": issuer,
        "subject": subject,
        "type": "ai.snapshot",
        "payload": payload,
        "payload_hash": payload_hash,
        "signatures": [],
        "bundle_hash": ""
    }
    signer = signer or get_signer_from_env()
    payload_bytes = canonical_json({k: v for k, v in receipt.items() if k != "signatures" and k != "bundle_hash"})
    sig = signer.sign(payload_bytes)
    if sig:
        receipt["signatures"] = [sig]
    bundle_path, receipt_out = export_snapshot_bundle(
        receipt, payload, output_dir, raw_text, source_url, machine_id
    )
    return bundle_path, receipt_out
