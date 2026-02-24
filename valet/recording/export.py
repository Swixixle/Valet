"""
Export .halo zip bundles for HALO receipts.
"""
import io
import zipfile
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from .canonical import canonical_json

import copy
import io
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from zipfile import ZIP_DEFLATED

from .canonical import canonical_json, receipt_for_manifest
from .crypto import sha256_hex

def receipt_for_manifest(receipt: dict) -> dict:
    r = copy.deepcopy(receipt)
    r.pop("bundle_hash", None)
    r.pop("signatures", None)
    return r

def build_zip_bytes(entries: List[Tuple[str, bytes]], compression=ZIP_DEFLATED, compresslevel=6) -> bytes:
    zip_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_bytes, "w", compression=compression, compresslevel=compresslevel) as z:
        for fname, content in entries:
            zi = zipfile.ZipInfo(fname)
            zi.date_time = (1980, 1, 1, 0, 0, 0)
            zi.compress_type = compression
            zi.create_system = 0
            zi.external_attr = 0o644 << 16
            z.writestr(zi, content)
    zip_bytes.seek(0)
    return zip_bytes.getvalue()

def export_session_bundle(
    receipt: Dict[str, Any],
    events: List[Dict[str, Any]],
    output_dir: Path,
    source_url: Optional[str],
    machine_id: str,
    created_at: Optional[str] = None
) -> Tuple[Path, Dict[str, Any]]:
    meta = {
        "created_at": created_at or receipt["ended_at"],
        "source_url": source_url,
        "domain": None,
        "valet_version": "0.1",
        "mode": "record",
        "machine_id": machine_id
    }
    verification_log = {
        "steps": [
            "canonical_json",
            "payload_hash",
            "event_hash_chain",
            "transcript_hash",
            f"signing: {receipt['signatures'][0]['alg'] if receipt['signatures'] else 'none'}",
            "bundle_hash"
        ],
        "success": True
    }
    base_receipt = copy.deepcopy(receipt)
    base_receipt.pop("bundle_hash", None)
    base_receipt["bundle_manifest_schema"] = "halo.bundle_manifest.v1"
    receipt_bytes_no_bundle_hash = canonical_json(base_receipt)
    receipt_dict_no_bundle_hash = json.loads(receipt_bytes_no_bundle_hash.decode("utf-8"))
    receipt_sha256 = sha256_hex(canonical_json(receipt_for_manifest(receipt_dict_no_bundle_hash)))
    events_bytes = canonical_json(events)
    meta_bytes = canonical_json(meta)
    bundle_manifest = {
        "schema_version": "halo.bundle_manifest.v1",
        "mode": "record",
        "meta_sha256": sha256_hex(meta_bytes),
        "receipt_sha256": receipt_sha256,
        "events_sha256": sha256_hex(events_bytes),
        "raw_content_sha256": None,
        "attachments": []
    }
    bundle_manifest_bytes = canonical_json(bundle_manifest)
    bundle_hash = sha256_hex(bundle_manifest_bytes)
    final_receipt = copy.deepcopy(base_receipt)
    final_receipt["bundle_hash"] = bundle_hash
    receipt_bytes_final = canonical_json(final_receipt)
    entries = [
        ("meta.json", meta_bytes),
        ("bundle_manifest.json", bundle_manifest_bytes),
        ("session_receipt.json", receipt_bytes_final),
        ("events.json", events_bytes),
        ("verification_log.json", canonical_json(verification_log)),
    ]
    final_bytes = build_zip_bytes(entries)
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = output_dir / f"session_{final_receipt['session_id']}.halo"
    with open(bundle_path, "wb") as f:
        f.write(final_bytes)
    return bundle_path, json.loads(receipt_bytes_final.decode("utf-8"))

def export_snapshot_bundle(
    receipt: Dict[str, Any],
    payload: Dict[str, Any],
    output_dir: Path,
    raw_text: Optional[str],
    source_url: Optional[str],
    machine_id: str
) -> Tuple[Path, Dict[str, Any]]:
    meta = {
        "created_at": receipt["captured_at"],
        "source_url": source_url,
        "domain": None,
        "valet_version": "0.1",
        "mode": "snapshot",
        "machine_id": machine_id
    }
    verification_log = {
        "steps": [
            "canonical_json",
            "payload_hash",
            f"signing: {receipt['signatures'][0]['alg'] if receipt['signatures'] else 'none'}",
            "bundle_hash"
        ],
        "success": True
    }
    base_receipt = copy.deepcopy(receipt)
    base_receipt.pop("bundle_hash", None)
    base_receipt["bundle_manifest_schema"] = "halo.bundle_manifest.v1"
    receipt_bytes_no_bundle_hash = canonical_json(base_receipt)
    receipt_dict_no_bundle_hash = json.loads(receipt_bytes_no_bundle_hash.decode("utf-8"))
    receipt_sha256 = sha256_hex(canonical_json(receipt_for_manifest(receipt_dict_no_bundle_hash)))
    payload_bytes = canonical_json(payload)
    meta_bytes = canonical_json(meta)
    bundle_manifest = {
        "schema_version": "halo.bundle_manifest.v1",
        "mode": "snapshot",
        "meta_sha256": sha256_hex(meta_bytes),
        "receipt_sha256": receipt_sha256,
        "payload_sha256": sha256_hex(payload_bytes),
        "raw_content_sha256": sha256_hex(raw_text.encode("utf-8")) if raw_text else None,
        "attachments": []
    }
    bundle_manifest_bytes = canonical_json(bundle_manifest)
    bundle_hash = sha256_hex(bundle_manifest_bytes)
    final_receipt = copy.deepcopy(base_receipt)
    final_receipt["bundle_hash"] = bundle_hash
    receipt_bytes_final = canonical_json(final_receipt)
    entries = [
        ("meta.json", meta_bytes),
        ("bundle_manifest.json", bundle_manifest_bytes),
        ("snapshot_receipt.json", receipt_bytes_final),
        ("payload.json", payload_bytes),
    ]
    if raw_text:
        entries.append(("raw_content.txt", raw_text.encode("utf-8")))
    entries.append(("verification_log.json", canonical_json(verification_log)))
    final_bytes = build_zip_bytes(entries)
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = output_dir / f"snapshot_{final_receipt['snapshot_id']}.halo"
    with open(bundle_path, "wb") as f:
        f.write(final_bytes)
    return bundle_path, json.loads(receipt_bytes_final.decode("utf-8"))
