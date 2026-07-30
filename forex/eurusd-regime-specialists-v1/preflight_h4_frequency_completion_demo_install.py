from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.h4_frequency_completion_demo_bundle import (
    plan_shadow_install,
)


def discover_running_terminals() -> tuple[list[Path], bool]:
    command = (
        "Get-CimInstance Win32_Process -Filter \"Name='terminal64.exe'\" "
        "| ForEach-Object {$_.ExecutablePath}"
    )
    completed = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            command,
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    if completed.returncode != 0:
        return [], False
    paths = [
        Path(line.strip())
        for line in completed.stdout.splitlines()
        if line.strip()
    ]
    return paths, True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only preflight for the EURUSD frequency-completion "
            "disarmed shadow package. This command never installs files."
        )
    )
    parser.add_argument("--target-root", type=Path, required=True)
    args = parser.parse_args(argv)
    running, discovery_ok = discover_running_terminals()
    plan = plan_shadow_install(
        ROOT
        / "config"
        / "frozen_h4_frequency_completion_demo_bundle_v1.json",
        args.target_root,
        running_terminal_executables=running,
        process_discovery_ok=discovery_ok,
    )
    print(json.dumps(plan.as_dict(), indent=2, allow_nan=False))
    return 0 if plan.status == "READY_NO_WRITES" else 2


if __name__ == "__main__":
    raise SystemExit(main())
