from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from attach_phase2_shadow_fix_observers import (
    DEFAULT_METAEDITOR_EXE,
    DEFAULT_PORTABLE_ROOT,
    attach_phase2_shadow_fix_observers,
)


DEFAULT_INSTALL_ROOT = Path("C:/Program Files/MetaTrader 5")
DEFAULT_SOURCE_DATA_DIR = Path(
    "C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075"
)
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "PHASE2_SHADOW_FIX_OBSERVER_TERMINAL.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "PHASE2_SHADOW_FIX_OBSERVER_TERMINAL.md"


def setup_phase2_shadow_fix_observer_terminal(
    phase1_root: Path,
    install_root: Path = DEFAULT_INSTALL_ROOT,
    source_data_dir: Path = DEFAULT_SOURCE_DATA_DIR,
    portable_root: Path = DEFAULT_PORTABLE_ROOT,
    output_json: Path | None = None,
    prepare: bool = False,
    attach: bool = False,
    launch: bool = False,
    wait_seconds: int = 60,
) -> Path:
    phase1_root = phase1_root.resolve()
    install_root = install_root.resolve()
    source_data_dir = source_data_dir.resolve()
    portable_root = portable_root.resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_OUTPUT_JSON.name else phase1_root / DEFAULT_OUTPUT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    copied = _prepare_portable_root(install_root, source_data_dir, portable_root) if prepare else []
    attachment_report = "not_requested"
    attachment_count = 0
    if attach:
        attachment = attach_phase2_shadow_fix_observers(
            phase1_root=phase1_root,
            terminal_data_dir=portable_root,
            terminal_exe=portable_root / "terminal64.exe",
            metaeditor_exe=DEFAULT_METAEDITOR_EXE,
            output_json=phase1_root / "outputs" / "reports" / "PHASE2_SHADOW_FIX_OBSERVER_ATTACHMENTS.json",
            launch=launch,
        )
        attachment_report = str(attachment.markdown_path)
        attachment_count = attachment.attachment_count
    elif launch:
        subprocess.Popen([str(portable_root / "terminal64.exe"), "/portable"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    launch_started = launch
    if launch_started:
        deadline = time.time() + wait_seconds
        while time.time() < deadline:
            state = _log_state(portable_root)
            if state["startup_log_count"] > 0 or state["signal_log_count"] > 0:
                break
            time.sleep(1)

    logs = _log_state(portable_root)
    if launch_started and logs["startup_log_count"] > 0:
        status = "SHADOW_FIX_OBSERVER_TERMINAL_RUNNING"
    elif attach:
        status = "SHADOW_FIX_OBSERVER_TERMINAL_PREPARED"
    else:
        status = "REPORT_ONLY"

    payload: dict[str, Any] = {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": (
            "Isolated observer-only terminal for Phase 2 shadow-fix measurement. It does not touch the standard "
            "Capital.com demo trading terminal, its profile, charts, orders, or executor EAs."
        ),
        "portable_root": str(portable_root),
        "source_install_root": str(install_root),
        "source_demo_data_dir": str(source_data_dir),
        "prepare_attempted": prepare,
        "attach_attempted": attach,
        "launch_started": launch_started,
        "attachment_report": attachment_report,
        "attachment_count": attachment_count,
        "terminal_exe": str(portable_root / "terminal64.exe"),
        "copied_paths": copied,
        "logs": logs,
        "standard_demo_terminal_touched": False,
        "standard_demo_terminal_closed_or_restarted": False,
        "trading_eas_touched": False,
        "broker_action_allowed": False,
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return output_json


def _prepare_portable_root(install_root: Path, source_data_dir: Path, portable_root: Path) -> list[str]:
    portable_root.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for name in ("terminal64.exe", "MetaEditor64.exe", "metatester64.exe", "Terminal.ico"):
        copied.append(_copy_one(install_root / name, portable_root / name))
    for name in ("Bases", "Profiles", "Sounds"):
        source = install_root / name
        target = portable_root / name
        if source.exists() and not target.exists():
            shutil.copytree(source, target)
            copied.append(str(target))
    _copy_config(source_data_dir / "config", portable_root / "Config", copied)
    (portable_root / "MQL5" / "Files").mkdir(parents=True, exist_ok=True)
    return copied


def _copy_config(source: Path, target: Path, copied: list[str]) -> None:
    target.mkdir(parents=True, exist_ok=True)
    if not source.exists():
        raise FileNotFoundError(source)
    for item in source.iterdir():
        destination = target / item.name
        if item.is_dir():
            if destination.exists():
                continue
            shutil.copytree(item, destination)
            copied.append(str(destination))
        elif item.name in {
            "accounts.dat",
            "servers.dat",
            "common.ini",
            "terminal.ini",
            "settings.ini",
            "agents.dat",
            "dnsperf.dat",
            "hotkeys.ini",
        }:
            copied.append(_copy_one(item, destination))


def _copy_one(source: Path, destination: Path) -> str:
    if not source.exists():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(source, destination)
    except PermissionError:
        if destination.exists():
            return str(destination)
        raise
    return str(destination)


def _log_state(portable_root: Path) -> dict[str, Any]:
    files = portable_root / "MQL5" / "Files"
    startup_logs = sorted(files.glob("shadow_fix_observer_startup_*.csv")) if files.exists() else []
    signal_logs = sorted(files.glob("shadow_fix_observer_signal_log_*.csv")) if files.exists() else []
    latest_signal = max(signal_logs, key=lambda path: path.stat().st_mtime) if signal_logs else None
    return {
        "startup_log_count": len(startup_logs),
        "signal_log_count": len(signal_logs),
        "latest_signal_log": str(latest_signal) if latest_signal else "missing",
        "latest_signal_log_mtime": datetime.fromtimestamp(latest_signal.stat().st_mtime).isoformat() if latest_signal else "missing",
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 2 Shadow Fix Observer Terminal",
            "",
            f"Status: {payload['status']}",
            "",
            payload["authority"],
            "",
            f"Portable root: `{payload['portable_root']}`",
            f"Attachment report: `{payload['attachment_report']}`",
            f"Attachment count: `{payload['attachment_count']}`",
            f"Standard demo terminal touched: `{payload['standard_demo_terminal_touched']}`",
            f"Standard demo terminal closed/restarted: `{payload['standard_demo_terminal_closed_or_restarted']}`",
            f"Trading EAs touched: `{payload['trading_eas_touched']}`",
            f"Broker action allowed: `{payload['broker_action_allowed']}`",
            "",
            "## Logs",
            "",
            f"- Startup log count: `{payload['logs']['startup_log_count']}`",
            f"- Signal log count: `{payload['logs']['signal_log_count']}`",
            f"- Latest signal log: `{payload['logs']['latest_signal_log']}`",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare and launch isolated shadow-fix observer terminal.")
    parser.add_argument("--phase1-root", type=Path, default=Path("."))
    parser.add_argument("--install-root", type=Path, default=DEFAULT_INSTALL_ROOT)
    parser.add_argument("--source-data-dir", type=Path, default=DEFAULT_SOURCE_DATA_DIR)
    parser.add_argument("--portable-root", type=Path, default=DEFAULT_PORTABLE_ROOT)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--allow-prepare", action="store_true")
    parser.add_argument("--allow-attach", action="store_true")
    parser.add_argument("--allow-launch", action="store_true")
    parser.add_argument("--wait-seconds", type=int, default=60)
    args = parser.parse_args()

    output = setup_phase2_shadow_fix_observer_terminal(
        phase1_root=args.phase1_root,
        install_root=args.install_root,
        source_data_dir=args.source_data_dir,
        portable_root=args.portable_root,
        output_json=args.output_json,
        prepare=args.allow_prepare,
        attach=args.allow_attach,
        launch=args.allow_launch,
        wait_seconds=args.wait_seconds,
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
