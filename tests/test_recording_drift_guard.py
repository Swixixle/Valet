from datetime import datetime, timezone

def fixed_id():
    return "fixed-session-id"

def fixed_now():
    return datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
from valet.recording.canonical import receipt_for_manifest
import pytest
import tempfile
import zipfile
import json
from pathlib import Path
from valet.recording.session_recorder import SessionRecorder
from valet.recording.snapshot import create_snapshot
from valet.recording.canonical import canonical_json
from valet.recording.crypto import sha256_hex
from valet.recording.signer import NoopSigner

def fixed_now():
    from datetime import datetime
    return datetime(2024, 1, 1, 12, 0, 0)

def test_transcript_hash_correctness():
    tmp_path = Path(tempfile.gettempdir())
    payloads = [
        {"cmd": "echo", "args": ["hello"]},
        {"result": "hello"}
    ]
    rec = SessionRecorder("machine-xyz", now_fn=fixed_now)
    rec.start()
    rec.record_event("command.request", payloads[0])
    rec.record_event("command.result", payloads[1])
    bundle_path, receipt = rec.stop_and_export(tmp_path)
    with zipfile.ZipFile(bundle_path, "r") as z:
        events_array = json.loads(z.read("events.json"))
    expected = sha256_hex(canonical_json(events_array))
    assert receipt["transcript_hash"] == expected

def test_event_hash_chain_correctness():
    tmp_path = Path(tempfile.gettempdir())
    payloads = [
        {"cmd": "echo", "args": ["hello"]},
        {"result": "hello"}
    ]
    rec = SessionRecorder("machine-xyz", now_fn=fixed_now)
    rec.start()
    rec.record_event("command.request", payloads[0])
    rec.record_event("command.result", payloads[1])
    bundle_path, receipt = rec.stop_and_export(tmp_path)
    with zipfile.ZipFile(bundle_path, "r") as z:
        events_array = json.loads(z.read("events.json"))
    for i, event in enumerate(events_array):
        if i == 0:
            assert event["prev_event_hash"] == "0"*64
        else:
            assert event["prev_event_hash"] == events_array[i-1]["event_hash"]
        event_body_for_hash = {
            "seq": event["seq"],
            "ts": event["ts"],
            "type": event["type"],
            "payload": event["payload"],
            "attachments": event["attachments"],
            "prev_event_hash": event["prev_event_hash"]
        }
        prev_event_hash_bytes = bytes.fromhex(event["prev_event_hash"])
        computed_event_hash = sha256_hex(canonical_json(event_body_for_hash) + prev_event_hash_bytes)
        assert event["event_hash"] == computed_event_hash

def test_bundle_hash_matches_bytes():
    tmp_path = Path(tempfile.gettempdir())
    payloads = [
        {"cmd": "echo", "args": ["hello"]},
        {"result": "hello"}
    ]
    rec = SessionRecorder("machine-xyz", now_fn=fixed_now)
    rec.start()
    rec.record_event("command.request", payloads[0])
    rec.record_event("command.result", payloads[1])
    bundle_path, receipt = rec.stop_and_export(tmp_path)
    with zipfile.ZipFile(bundle_path, "r") as z:
        manifest = json.loads(z.read("bundle_manifest.json"))
        manifest_bytes = canonical_json(manifest)
    expected_hash = sha256_hex(manifest_bytes)
    assert receipt["bundle_hash"] == expected_hash
    # Snapshot
    payload = {"text": "hello world"}
    bundle_path_snap, receipt_snap = create_snapshot(payload, tmp_path, "machine-xyz")
    with zipfile.ZipFile(bundle_path_snap, "r") as z:
        manifest_snap = json.loads(z.read("bundle_manifest.json"))
        manifest_snap_bytes = canonical_json(manifest_snap)
    expected_hash_snap = sha256_hex(manifest_snap_bytes)
    assert receipt_snap["bundle_hash"] == expected_hash_snap

def test_zip_determinism_same_inputs_same_bytes():
    tmp_path = Path(tempfile.gettempdir())
    payloads = [
        {"cmd": "echo", "args": ["hello"]},
        {"result": "hello"}
    ]
    rec1 = SessionRecorder("machine-xyz", now_fn=fixed_now, signer=NoopSigner(), subject_meta={"meta": "fixed"}, id_fn=fixed_id)
    rec1.start()
    rec1.record_event("command.request", payloads[0])
    rec1.record_event("command.result", payloads[1])
    bundle_path1, receipt1 = rec1.stop_and_export(tmp_path)
    rec2 = SessionRecorder("machine-xyz", now_fn=fixed_now, signer=NoopSigner(), subject_meta={"meta": "fixed"}, id_fn=fixed_id)
    rec2.start()
    rec2.record_event("command.request", payloads[0])
    rec2.record_event("command.result", payloads[1])
    bundle_path2, receipt2 = rec2.stop_and_export(tmp_path)
    with open(bundle_path1, "rb") as f1, open(bundle_path2, "rb") as f2:
        bytes1 = f1.read()
        bytes2 = f2.read()
    assert bytes1 == bytes2
    rec1 = SessionRecorder("machine-xyz", now_fn=fixed_now, signer=NoopSigner(), subject_meta={"meta": "fixed"}, id_fn=fixed_id)
    rec1.start()
    rec1.record_event("command.request", payloads[0])
    rec1.record_event("command.result", payloads[1])
    bundle_path1, receipt1 = rec1.stop_and_export(tmp_path)
    rec2 = SessionRecorder("machine-xyz", now_fn=fixed_now, signer=NoopSigner(), subject_meta={"meta": "fixed"}, id_fn=fixed_id)
    rec2.start()
    rec2.record_event("command.request", payloads[0])
    rec2.record_event("command.result", payloads[1])
    bundle_path2, receipt2 = rec2.stop_and_export(tmp_path)
    with zipfile.ZipFile(bundle_path1, "r") as z1, zipfile.ZipFile(bundle_path2, "r") as z2:
        manifest1 = json.loads(z1.read("bundle_manifest.json"))
        manifest2 = json.loads(z2.read("bundle_manifest.json"))
        assert canonical_json(manifest1) == canonical_json(manifest2)
def test_manifest_fields_match_zip_contents():
    tmp_path = Path(tempfile.gettempdir())
    payloads = [
        {"cmd": "echo", "args": ["hello"]},
        {"result": "hello"}
    ]
    rec = SessionRecorder("machine-xyz", now_fn=fixed_now)
    rec.start()
    rec.record_event("command.request", payloads[0])
    rec.record_event("command.result", payloads[1])
    bundle_path, receipt = rec.stop_and_export(tmp_path)
    with zipfile.ZipFile(bundle_path, "r") as z:
        manifest = json.loads(z.read("bundle_manifest.json"))
        meta_bytes = z.read("meta.json")
        events_bytes = z.read("events.json")
        receipt_bytes = z.read("session_receipt.json")
        assert manifest["meta_sha256"] == sha256_hex(meta_bytes)
        assert manifest["events_sha256"] == sha256_hex(events_bytes)
        receipt_dict = json.loads(receipt_bytes)
        receipt_manifest = receipt_for_manifest(receipt_dict)
        assert manifest["receipt_sha256"] == sha256_hex(canonical_json(receipt_manifest))
        assert manifest["raw_content_sha256"] is None
        assert manifest["attachments"] == []

def test_noop_signer_signature_empty():
    tmp_path = Path(tempfile.gettempdir())
    payloads = [
        {"cmd": "echo", "args": ["hello"]},
        {"result": "hello"}
    ]
    rec = SessionRecorder("machine-xyz", signer=NoopSigner(), now_fn=fixed_now)
    rec.start()
    rec.record_event("command.request", payloads[0])
    rec.record_event("command.result", payloads[1])
    bundle_path, receipt = rec.stop_and_export(tmp_path)
    assert receipt["signatures"] == []
