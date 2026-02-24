from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Mapping, Callable
import subprocess, time, os

@dataclass(frozen=True)
class CommandResult:
    cmd: list[str]
    cwd: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int

def run_command(
    cmd: Sequence[str] | str,
    *,
    cwd: str | Path | None = None,
    env_allowlist: Sequence[str] | None = None,
    stdin: str | None = None,
    timeout_s: int | None = None,
    recorder: "SessionRecorder | None" = None,
    rationale: str | None = None,
) -> CommandResult:
    """
    Canonical command execution primitive.
    - Uses subprocess.run
    - Captures stdout/stderr as text (utf-8, errors='replace')
    - Does NOT raise on non-zero exit (returns exit_code)
    - If recorder is provided and recorder.is_recording, emits:
        command.request + command.result
    """
    if isinstance(cmd, str):
        cmd_as_list = [cmd]
    else:
        cmd_as_list = list(cmd)
    resolved_cwd = str(cwd) if cwd else os.getcwd()
    env = None
    if env_allowlist:
        env = {k: os.environ.get(k, "") for k in env_allowlist if k in os.environ}
    start = time.time()
    result = subprocess.run(
        cmd_as_list,
        cwd=resolved_cwd,
        input=stdin.encode("utf-8") if stdin else None,
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout_s,
        errors="replace"
    )
    duration_ms = int((time.time() - start) * 1000)
    payload_request = {
        "cmd": cmd_as_list,
        "cwd": resolved_cwd,
        "env_allowlist": env_allowlist or [],
        "stdin_present": stdin is not None,
    }
    if rationale:
        payload_request["rationale"] = rationale
    payload_result = {
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "duration_ms": duration_ms
    }
    if recorder and getattr(recorder, "is_recording", False):
        recorder.record_event("command.request", payload_request)
        recorder.record_event("command.result", payload_result)
    return CommandResult(
        cmd=cmd_as_list,
        cwd=resolved_cwd,
        exit_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
        duration_ms=duration_ms
    )
