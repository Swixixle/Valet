import pytest
from pathlib import Path
from valet.recording.session_recorder import SessionRecorder
from valet.recording.snapshot import create_snapshot
import tempfile
import zipfile
import json

def test_session_bundle_contents():
    rec = SessionRecorder("machine-xyz")
    rec.start()
    rec.record_event("command.request", {"cmd": "echo", "args": ["hello"]})
    rec.record_event("command.result", {"result": "hello"})
    bundle_path, receipt = rec.stop_and_export(Path(tempfile.gettempdir()))
    assert bundle_path.exists()
    with zipfile.ZipFile(bundle_path, "r") as z:
        files = z.namelist()
        assert "meta.json" in files
        assert "session_receipt.json" in files
        assert "events.json" in files
        assert "verification_log.json" in files
        meta = json.loads(z.read("meta.json"))
        assert meta["mode"] == "record"
        receipt_json = json.loads(z.read("session_receipt.json"))
        assert receipt_json["schema_version"] == "halo.session.v1"
        assert len(receipt_json["bundle_hash"]) == 64

def test_snapshot_bundle_contents():
    payload = {"text": "hello world"}
    bundle_path, receipt = create_snapshot(payload, Path(tempfile.gettempdir()), "machine-xyz")
    assert bundle_path.exists()
    with zipfile.ZipFile(bundle_path, "r") as z:
        files = z.namelist()
        assert "meta.json" in files
        assert "snapshot_receipt.json" in files
        assert "payload.json" in files
        assert "verification_log.json" in files
        meta = json.loads(z.read("meta.json"))
        assert meta["mode"] == "snapshot"
        receipt_json = json.loads(z.read("snapshot_receipt.json"))
        assert receipt_json["schema_version"] == "halo.snapshot.v1"
        assert len(receipt_json["bundle_hash"]) == 64
