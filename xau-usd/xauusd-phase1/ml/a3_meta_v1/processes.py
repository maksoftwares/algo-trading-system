from __future__ import annotations

import json
import os
import subprocess
from typing import Any

from .terminal_verification import RunningProcess


class ProcessEnumerationError(RuntimeError):
    """Raised when running process paths cannot be enumerated safely."""


def list_running_processes() -> list[RunningProcess]:
    if os.name != "nt":
        return []
    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        (
            "Get-CimInstance Win32_Process | "
            "Select-Object ProcessId,ExecutablePath | "
            "ConvertTo-Json -Compress"
        ),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise ProcessEnumerationError((completed.stderr or completed.stdout or "process enumeration failed").strip())
    text = completed.stdout.strip()
    if not text:
        return []
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProcessEnumerationError(f"process enumeration returned invalid JSON: {exc}") from exc
    return _coerce_processes(payload)


def _coerce_processes(payload: Any) -> list[RunningProcess]:
    rows = payload if isinstance(payload, list) else [payload]
    processes: list[RunningProcess] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        exe = row.get("ExecutablePath")
        pid = row.get("ProcessId")
        if not exe or pid is None:
            continue
        try:
            processes.append(RunningProcess(pid=int(pid), exe=str(exe)))
        except (TypeError, ValueError):
            continue
    return processes
