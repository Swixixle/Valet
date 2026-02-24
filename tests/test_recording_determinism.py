import pytest
from pathlib import Path
from valet.recording.session_recorder import SessionRecorder
from valet.recording.snapshot import create_snapshot
import tempfile

def fixed_now():
    from datetime import datetime
    return datetime(2024, 1, 1, 12, 0, 0)

def test_session_determinism():
    from valet.recording.canonical import canonical_json
    from valet.recording.crypto import sha256_hex
    import json
    import tempfile
    tmp_path = Path(tempfile.gettempdir())
    payloads = [
        {"cmd": "echo", "args": ["hello"]},
        {"result": "hello"}
    ]
    # First run
    rec1 = SessionRecorder("machine-xyz", now_fn=fixed_now)
    rec1.start()
    rec1.record_event("command.request", payloads[0])
    rec1.record_event("command.result", payloads[1])
    bundle_path1, receipt1 = rec1.stop_and_export(tmp_path)
    assert receipt1["schema_version"] == "halo.session.v1"
    assert len(receipt1["events"]) == 2
    # Read events.json from bundle
    import zipfile
    with zipfile.ZipFile(bundle_path1, "r") as z:
        events_array = json.loads(z.read("events.json"))
    expected_transcript_hash = sha256_hex(canonical_json(events_array))
    assert receipt1["transcript_hash"] == expected_transcript_hash
    # Second run, same inputs
    rec2 = SessionRecorder("machine-xyz", now_fn=fixed_now)
    rec2.start()
    rec2.record_event("command.request", payloads[0])
    rec2.record_event("command.result", payloads[1])
    bundle_path2, receipt2 = rec2.stop_and_export(tmp_path)
    with zipfile.ZipFile(bundle_path2, "r") as z:
        events_array2 = json.loads(z.read("events.json"))
    expected_transcript_hash2 = sha256_hex(canonical_json(events_array2))
    assert receipt2["transcript_hash"] == expected_transcript_hash2
    assert expected_transcript_hash == expected_transcript_hash2
    # Per-event hash chain checks
    for i, event in enumerate(events_array):
        if i == 0:
            assert event["prev_event_hash"] == "0"*64
        else:
            assert event["prev_event_hash"] == events_array[i-1]["event_hash"]
        # Recompute event_hash
        from valet.recording.models import BaseEvent
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

def test_snapshot_determinism():
    payload = {"text": "hello world"}
    bundle_path, receipt = create_snapshot(payload, Path(tempfile.gettempdir()), "machine-xyz")
    assert receipt["schema_version"] == "halo.snapshot.v1"
    assert receipt["payload_hash"] == receipt["signatures"][0]["payload_hash"] if receipt["signatures"] else receipt["payload_hash"]
