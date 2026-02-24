import tempfile
from pathlib import Path
from valet.recording.session_recorder import SessionRecorder
from valet.execution.command_runner import run_command

def fixed_now():
    return __import__("datetime").datetime(2024, 1, 1, 12, 0, 0)

def fixed_id():
    return "test-session-001"

def test_command_recording_and_bundle():
    tmp_path = Path(tempfile.gettempdir())
    recorder = SessionRecorder("machine-xyz", now_fn=fixed_now, id_fn=fixed_id)
    recorder.start()
    result = run_command([
        "python", "-c", "print('hi')"
    ], recorder=recorder)
    assert result.exit_code == 0
    assert "hi" in result.stdout
    bundle_path, receipt = recorder.stop_and_export(tmp_path)
    # Open bundle zip and check events
    import zipfile, json
    with zipfile.ZipFile(bundle_path, "r") as z:
        events = json.loads(z.read("events.json").decode("utf-8"))
    event_types = [e["type"] for e in events]
    assert event_types == ["command.request", "command.result"]
    payloads = [e["payload"] for e in events]
    assert payloads[0]["cmd"] == ["python", "-c", "print('hi')"]
    assert payloads[1]["exit_code"] == 0
    assert "hi" in payloads[1]["stdout"]
