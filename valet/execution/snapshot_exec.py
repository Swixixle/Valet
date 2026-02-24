from pathlib import Path
from typing import Sequence, Optional
from valet.recording.snapshot import create_snapshot
from .command_runner import run_command

def snapshot_command(
    cmd: Sequence[str] | str,
    *,
    cwd: str | Path | None = None,
    env_allowlist: Sequence[str] | None = None,
    stdin: str | None = None,
    timeout_s: int | None = None,
    machine_id: str,
    output_dir: Path,
    raw_text: Optional[str] = None,
    rationale: Optional[str] = None,
) -> tuple[Path, dict]:
    result = run_command(
        cmd,
        cwd=cwd,
        env_allowlist=env_allowlist,
        stdin=stdin,
        timeout_s=timeout_s,
    )
    payload = {
        "kind": "command",
        "cmd": result.cmd,
        "cwd": result.cwd,
        "exit_code": result.exit_code,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "duration_ms": result.duration_ms
    }
    bundle_path, receipt = create_snapshot(
        payload=payload,
        output_dir=output_dir,
        raw_text=raw_text,
        machine_id=machine_id
    )
    return bundle_path, receipt
