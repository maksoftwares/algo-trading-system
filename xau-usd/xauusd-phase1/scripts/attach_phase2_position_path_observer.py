from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STANDARD_DEMO_TERMINAL_DATA_DIR = Path(
    "C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075"
)
STANDARD_DEMO_TERMINAL_EXE = Path("C:/Program Files/MetaTrader 5/terminal64.exe")
DEFAULT_INSTALL_ROOT = Path("C:/Program Files/MetaTrader 5")
DEFAULT_SOURCE_DATA_DIR = STANDARD_DEMO_TERMINAL_DATA_DIR
DEFAULT_PORTABLE_ROOT = Path("C:/MT5PortablePositionPathObserver")
DEFAULT_METAEDITOR_EXE = Path("C:/Program Files/MetaTrader 5/MetaEditor64.exe")
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "PHASE2_POSITION_PATH_OBSERVER_ATTACHMENT.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "PHASE2_POSITION_PATH_OBSERVER_ATTACHMENT.md"

EA_NAME = "Phase2PositionPathObserver"
EA_SOURCE = Path("mt5") / "Experts" / f"{EA_NAME}.mq5"
PRESET_SOURCE = Path("mt5") / "Presets" / "Phase2PositionPathObserver.demo_account_readonly.set"


def attach_phase2_position_path_observer(
    phase1_root: Path,
    install_root: Path = DEFAULT_INSTALL_ROOT,
    source_data_dir: Path = DEFAULT_SOURCE_DATA_DIR,
    portable_root: Path = DEFAULT_PORTABLE_ROOT,
    metaeditor_exe: Path = DEFAULT_METAEDITOR_EXE,
    output_json: Path | None = None,
    prepare: bool = False,
    attach: bool = False,
    launch: bool = False,
    wait_seconds: int = 45,
    allow_standard_demo_terminal: bool = False,
) -> Path:
    phase1_root = phase1_root.resolve()
    install_root = install_root.resolve()
    source_data_dir = source_data_dir.resolve()
    portable_root = portable_root.resolve()
    terminal_exe = portable_root / "terminal64.exe"
    metaeditor_exe = metaeditor_exe.resolve()
    if not allow_standard_demo_terminal:
        _guard_not_standard_demo_terminal(portable_root, terminal_exe)

    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_OUTPUT_JSON.name else phase1_root / DEFAULT_OUTPUT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    copied_paths: list[str] = []
    if prepare:
        copied_paths = _prepare_portable_root(install_root, source_data_dir, portable_root)

    deployed_sources: list[str] = []
    compile_log = "not_requested"
    profile_backup_dir = "not_requested"
    terminal_closed = False
    observer_log_backup_dir = "not_requested"
    if attach:
        deployed_sources = [str(path) for path in _deploy_sources(phase1_root, portable_root)]
        compile_log = str(_compile_ea(metaeditor_exe, portable_root))
        terminal_closed = _close_terminal(terminal_exe)
        observer_log_backup_dir = _archive_existing_observer_logs(portable_root)
        profile_backup_dir = str(_replace_default_profile(portable_root, phase1_root))

    if launch:
        if not terminal_exe.exists():
            raise FileNotFoundError(f"Terminal not found: {terminal_exe}")
        subprocess.Popen([str(terminal_exe), "/portable"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if wait_seconds > 0:
            deadline = time.time() + wait_seconds
            while time.time() < deadline:
                logs = _log_state(portable_root)
                if logs["startup_log_exists"]:
                    break
                time.sleep(1.0)

    logs = _log_state(portable_root)
    if launch and logs["startup_log_exists"]:
        status = "POSITION_PATH_OBSERVER_TERMINAL_RUNNING"
    elif attach:
        status = "POSITION_PATH_OBSERVER_ATTACHED_NOT_VERIFIED_RUNNING"
    else:
        status = "REPORT_ONLY"

    payload: dict[str, Any] = {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": (
            "Position path observer is telemetry-only. It reads open demo positions and writes CSV snapshots. "
            "It does not place orders, modify positions, close positions, or change canonical Phase 2 status."
        ),
        "portable_root": str(portable_root),
        "terminal_exe": str(terminal_exe),
        "prepare_attempted": prepare,
        "attach_attempted": attach,
        "launch_started": launch,
        "allow_standard_demo_terminal": allow_standard_demo_terminal,
        "standard_demo_terminal_path_requested": portable_root.resolve() == STANDARD_DEMO_TERMINAL_DATA_DIR.resolve(),
        "broker_action_allowed": False,
        "existing_trading_eas_touched": allow_standard_demo_terminal,
        "copied_paths": copied_paths,
        "deployed_sources": deployed_sources,
        "compile_log": compile_log,
        "profile_backup_dir": profile_backup_dir,
        "observer_log_backup_dir": observer_log_backup_dir,
        "terminal_closed_before_profile_replace": terminal_closed,
        "logs": logs,
        "chart": {
            "symbol": "XAUUSD",
            "timeframe": "M5",
            "ea": EA_NAME,
            "instances": 1,
        },
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return output_json


def _guard_not_standard_demo_terminal(terminal_data_dir: Path, terminal_exe: Path) -> None:
    if terminal_data_dir.resolve() == STANDARD_DEMO_TERMINAL_DATA_DIR.resolve():
        raise RuntimeError("Refusing to attach position-path observer to the standard demo trading terminal without explicit owner approval.")
    if terminal_exe.resolve() == STANDARD_DEMO_TERMINAL_EXE.resolve():
        raise RuntimeError("Refusing to launch standard demo trading terminal without explicit owner approval.")


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


def _deploy_sources(phase1_root: Path, portable_root: Path) -> list[Path]:
    experts_dir = portable_root / "MQL5" / "Experts"
    presets_dir = portable_root / "MQL5" / "Presets"
    experts_dir.mkdir(parents=True, exist_ok=True)
    presets_dir.mkdir(parents=True, exist_ok=True)
    deployed: list[Path] = []
    ea_source = phase1_root / EA_SOURCE
    ea_target = experts_dir / ea_source.name
    shutil.copy2(ea_source, ea_target)
    deployed.append(ea_target)
    preset_source = phase1_root / PRESET_SOURCE
    preset_target = presets_dir / preset_source.name
    shutil.copy2(preset_source, preset_target)
    deployed.append(preset_target)
    return deployed


def _compile_ea(metaeditor_exe: Path, portable_root: Path) -> Path:
    if not metaeditor_exe.exists():
        raise FileNotFoundError(f"MetaEditor not found: {metaeditor_exe}")
    scratch_root = Path("C:/MT5CompileScratchPositionPath")
    scratch_experts = scratch_root / "MQL5" / "Experts"
    scratch_experts.mkdir(parents=True, exist_ok=True)
    source = portable_root / "MQL5" / "Experts" / f"{EA_NAME}.mq5"
    scratch_source = scratch_experts / source.name
    shutil.copy2(source, scratch_source)
    scratch_log = scratch_root / "Logs" / f"compile_{EA_NAME}.log"
    scratch_log.parent.mkdir(parents=True, exist_ok=True)
    if scratch_log.exists():
        scratch_log.unlink()
    subprocess.run([str(metaeditor_exe), f"/compile:{scratch_source}", f"/log:{scratch_log}"], check=False, timeout=90)
    scratch_ex5 = scratch_experts / f"{EA_NAME}.ex5"
    target_ex5 = portable_root / "MQL5" / "Experts" / f"{EA_NAME}.ex5"
    if not scratch_ex5.exists():
        raise RuntimeError(f"MetaEditor did not produce {EA_NAME}.ex5. Compile log:\n{_read_text(scratch_log)}")
    shutil.copy2(scratch_ex5, target_ex5)
    log_path = portable_root / "MQL5" / "Logs" / f"compile_{EA_NAME}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(scratch_log, log_path)
    log_text = _read_text(log_path)
    if "error(s)" in log_text.lower() and "0 error(s)" not in log_text.lower():
        raise RuntimeError(f"MetaEditor compile reported errors:\n{log_text}")
    return log_path


def _close_terminal(terminal_exe: Path) -> bool:
    if not terminal_exe.exists():
        return False
    ps = f"""
$target = (Resolve-Path -LiteralPath '{terminal_exe}').Path
$procs = Get-CimInstance Win32_Process | Where-Object {{ $_.ExecutablePath -eq $target }}
if(-not $procs) {{ exit 0 }}
foreach($proc in $procs) {{
  $p = Get-Process -Id $proc.ProcessId -ErrorAction SilentlyContinue
  if($p) {{ [void]$p.CloseMainWindow() }}
}}
Start-Sleep -Seconds 5
foreach($proc in $procs) {{
  $p = Get-Process -Id $proc.ProcessId -ErrorAction SilentlyContinue
  if($p) {{ Stop-Process -Id $proc.ProcessId -Force }}
}}
exit 0
"""
    result = subprocess.run(["powershell", "-NoProfile", "-Command", ps], text=True, capture_output=True, timeout=30)
    return result.returncode == 0


def _archive_existing_observer_logs(portable_root: Path) -> str:
    files_dir = portable_root / "MQL5" / "Files"
    candidates = [
        *files_dir.glob("position_path_log_*.csv"),
        files_dir / "position_path_summary.csv",
        files_dir / "position_path_observer_startup.csv",
    ]
    existing = [path for path in candidates if path.exists()]
    if not existing:
        return "none"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = portable_root / "_codex_quarantine" / "observer_logs" / f"position_path_logs_{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    for path in existing:
        shutil.move(str(path), str(backup_dir / path.name))
    return str(backup_dir)


def _replace_default_profile(portable_root: Path, phase1_root: Path) -> Path:
    charts_root = portable_root / "MQL5" / "Profiles" / "Charts"
    default_profile = charts_root / "Default"
    backup_root = portable_root / "_codex_quarantine" / "profile_backups"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = backup_root / f"default_profile_before_position_path_observer_{stamp}"
    backup_dir.parent.mkdir(parents=True, exist_ok=True)
    if default_profile.exists():
        shutil.copytree(default_profile, backup_dir)
        shutil.rmtree(default_profile)
    default_profile.mkdir(parents=True, exist_ok=True)
    (default_profile / "chart01.chr").write_text(_render_chart(phase1_root), encoding="utf-8")
    return backup_dir


def _render_chart(phase1_root: Path) -> str:
    preset_inputs = [
        line.strip()
        for line in (phase1_root / PRESET_SOURCE).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith(";")
    ]
    return "\n".join(
        [
            "<chart>",
            f"id={int(time.time())}0001",
            "symbol=XAUUSD",
            "description=XAUUSD",
            "period_type=0",
            "period_size=5",
            "digits=2",
            "tick_size=0.01",
            "scale_fix=0",
            "scale=3",
            "mode=1",
            "fore=0",
            "grid=0",
            "volume=0",
            "scroll=1",
            "shift=1",
            "ohlc=0",
            "one_click=0",
            "one_click_btn=0",
            "askline=1",
            "days=0",
            "window_left=20",
            "window_top=20",
            "window_right=1000",
            "window_bottom=740",
            "windows_total=1",
            "",
            "<expert>",
            f"name={EA_NAME}",
            f"path=Experts\\{EA_NAME}.ex5",
            "expertmode=1",
            "<inputs>",
            *preset_inputs,
            "</inputs>",
            "</expert>",
            "",
            "<window>",
            "height=100.000000",
            "objects=0",
            "<indicator>",
            "name=Main",
            "path=",
            "apply=1",
            "</indicator>",
            "</window>",
            "</chart>",
            "",
        ]
    )


def _log_state(portable_root: Path) -> dict[str, Any]:
    files = portable_root / "MQL5" / "Files"
    startup = files / "position_path_observer_startup.csv"
    summaries = files / "position_path_summary.csv"
    snapshots = sorted(files.glob("position_path_log_*.csv")) if files.exists() else []
    latest_snapshot = max(snapshots, key=lambda path: path.stat().st_mtime) if snapshots else None
    return {
        "startup_log_exists": startup.exists(),
        "summary_log_exists": summaries.exists(),
        "snapshot_log_count": len(snapshots),
        "latest_snapshot_log": str(latest_snapshot) if latest_snapshot else "missing",
        "latest_snapshot_log_mtime": datetime.fromtimestamp(latest_snapshot.stat().st_mtime).isoformat() if latest_snapshot else "missing",
    }


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for encoding in ("utf-16", "utf-8", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeError:
            continue
    return path.read_text(errors="replace")


def _render_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 2 Position Path Observer Attachment",
            "",
            f"Status: {payload['status']}",
            "",
            payload["authority"],
            "",
            f"Portable root: `{payload['portable_root']}`",
            f"Attach attempted: `{payload['attach_attempted']}`",
            f"Launch started: `{payload['launch_started']}`",
            f"Allow standard demo terminal: `{payload['allow_standard_demo_terminal']}`",
            f"Existing trading EAs touched: `{payload['existing_trading_eas_touched']}`",
            f"Broker action allowed: `{payload['broker_action_allowed']}`",
            f"Compile log: `{payload['compile_log']}`",
            f"Profile backup: `{payload['profile_backup_dir']}`",
            "",
            "## Logs",
            "",
            f"- Startup log exists: `{payload['logs']['startup_log_exists']}`",
            f"- Summary log exists: `{payload['logs']['summary_log_exists']}`",
            f"- Snapshot log count: `{payload['logs']['snapshot_log_count']}`",
            f"- Latest snapshot log: `{payload['logs']['latest_snapshot_log']}`",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Attach one read-only position path observer.")
    parser.add_argument("--phase1-root", type=Path, default=Path("."))
    parser.add_argument("--install-root", type=Path, default=DEFAULT_INSTALL_ROOT)
    parser.add_argument("--source-data-dir", type=Path, default=DEFAULT_SOURCE_DATA_DIR)
    parser.add_argument("--portable-root", type=Path, default=DEFAULT_PORTABLE_ROOT)
    parser.add_argument("--metaeditor-exe", type=Path, default=DEFAULT_METAEDITOR_EXE)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--allow-prepare", action="store_true")
    parser.add_argument("--allow-attach", action="store_true")
    parser.add_argument("--allow-launch", action="store_true")
    parser.add_argument("--allow-standard-demo-terminal", action="store_true")
    parser.add_argument("--wait-seconds", type=int, default=45)
    args = parser.parse_args()

    output = attach_phase2_position_path_observer(
        phase1_root=args.phase1_root,
        install_root=args.install_root,
        source_data_dir=args.source_data_dir,
        portable_root=args.portable_root,
        metaeditor_exe=args.metaeditor_exe,
        output_json=args.output_json,
        prepare=args.allow_prepare,
        attach=args.allow_attach,
        launch=args.allow_launch,
        wait_seconds=args.wait_seconds,
        allow_standard_demo_terminal=args.allow_standard_demo_terminal,
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
