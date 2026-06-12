from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STANDARD_DEMO_TERMINAL_DATA_DIR = Path(
    "C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075"
)
STANDARD_DEMO_TERMINAL_EXE = Path("C:/Program Files/MetaTrader 5/terminal64.exe")
DEFAULT_INSTALL_ROOT = Path("C:/Program Files/MetaTrader 5")
DEFAULT_SOURCE_DATA_DIR = STANDARD_DEMO_TERMINAL_DATA_DIR
DEFAULT_PORTABLE_ROOT = Path("C:/MT5PortableTrendGuardedFixObservers")
DEFAULT_METAEDITOR_EXE = Path("C:/Program Files/MetaTrader 5/MetaEditor64.exe")
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "PHASE2_TREND_GUARDED_FIX_OBSERVER_ATTACHMENTS.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "PHASE2_TREND_GUARDED_FIX_OBSERVER_ATTACHMENTS.md"
DEFAULT_TERMINAL_JSON = Path("outputs") / "reports" / "PHASE2_TREND_GUARDED_FIX_OBSERVER_TERMINAL.json"
DEFAULT_TERMINAL_MD = Path("outputs") / "reports" / "PHASE2_TREND_GUARDED_FIX_OBSERVER_TERMINAL.md"

EA_NAME = "Phase2TrendGuardedFixObserver"
EA_SOURCE = Path("mt5") / "Experts" / f"{EA_NAME}.mq5"
RUN_ID = "phase2-trend-guarded-fix-observer-v0.1"
POLICY_VERSION = "trend_guarded_fix_policy_20260612_v2"
PRIMARY_SYMBOL = "XAUUSD"
SYMBOL_CANDIDATES = {
    "XAUUSD": (
        "breakout_retest",
        "swing_breakout_retest_v0",
        "symbol_normalized_round_retest_v0",
        "round_number_retest_v0",
        "session_extreme_retest_v0",
    ),
    "EURUSD": (
        "breakout_retest",
        "swing_breakout_retest_v0",
        "symbol_normalized_round_retest_v0",
        "session_extreme_retest_v0",
        "session_extreme_retest_v0_repair_v1",
    ),
    "GBPUSD": (
        "breakout_retest",
        "swing_breakout_retest_v0",
        "symbol_normalized_round_retest_v0",
        "session_extreme_retest_v0",
    ),
}
CANDIDATES = SYMBOL_CANDIDATES[PRIMARY_SYMBOL]


@dataclass(frozen=True)
class AttachmentRow:
    candidate: str
    symbol: str = PRIMARY_SYMBOL


@dataclass(frozen=True)
class AttachOutput:
    status: str
    json_path: Path
    markdown_path: Path
    terminal_json_path: Path
    terminal_markdown_path: Path
    attachment_count: int


def attach_phase2_trend_guarded_fix_observers(
    phase1_root: Path,
    install_root: Path = DEFAULT_INSTALL_ROOT,
    source_data_dir: Path = DEFAULT_SOURCE_DATA_DIR,
    portable_root: Path = DEFAULT_PORTABLE_ROOT,
    metaeditor_exe: Path = DEFAULT_METAEDITOR_EXE,
    output_json: Path | None = None,
    terminal_json: Path | None = None,
    prepare: bool = False,
    attach: bool = False,
    launch: bool = False,
    wait_seconds: int = 90,
) -> AttachOutput:
    phase1_root = phase1_root.resolve()
    install_root = install_root.resolve()
    source_data_dir = source_data_dir.resolve()
    portable_root = portable_root.resolve()
    metaeditor_exe = metaeditor_exe.resolve()
    terminal_exe = portable_root / "terminal64.exe"
    _guard_not_standard_demo_terminal(portable_root, terminal_exe)

    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_OUTPUT_JSON.name else phase1_root / DEFAULT_OUTPUT_MD
    terminal_json = (terminal_json or phase1_root / DEFAULT_TERMINAL_JSON).resolve()
    terminal_md = terminal_json.with_suffix(".md") if terminal_json.name != DEFAULT_TERMINAL_JSON.name else phase1_root / DEFAULT_TERMINAL_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)
    terminal_json.parent.mkdir(parents=True, exist_ok=True)

    copied_paths: list[str] = []
    if prepare:
        copied_paths = _prepare_portable_root(install_root, source_data_dir, portable_root)

    attachments = _build_attachment_plan()
    deployed_sources: list[Path] = []
    compile_log = "not_requested"
    profile_backup_dir = "not_requested"
    observer_log_backup_dir = "not_requested"
    terminal_closed = False
    if attach:
        deployed_sources = _deploy_sources(phase1_root, portable_root)
        compile_log = str(_compile_ea(metaeditor_exe, portable_root))
        terminal_closed = _close_terminal(terminal_exe)
        observer_log_backup_dir = _archive_existing_observer_logs(portable_root)
        profile_backup_dir = str(_replace_default_profile(portable_root, phase1_root, attachments))

    if launch:
        if not terminal_exe.exists():
            raise FileNotFoundError(f"Terminal not found: {terminal_exe}")
        subprocess.Popen([str(terminal_exe), "/portable"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if launch and wait_seconds > 0:
        deadline = time.time() + wait_seconds
        while time.time() < deadline:
            logs = _log_state(portable_root)
            if logs["startup_log_count"] >= len(attachments):
                break
            time.sleep(1.0)

    logs = _log_state(portable_root)
    if launch and logs["startup_log_count"] >= len(attachments):
        terminal_status = "TREND_GUARDED_FIX_OBSERVER_TERMINAL_RUNNING"
    elif attach:
        terminal_status = "TREND_GUARDED_FIX_OBSERVER_TERMINAL_PREPARED"
    else:
        terminal_status = "REPORT_ONLY"

    attachment_payload: dict[str, Any] = {
        "status": "TREND_GUARDED_FIX_OBSERVERS_ATTACHED_TO_ISOLATED_TERMINAL" if attach else "REPORT_ONLY",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": (
            "Trend-guarded fix observers are telemetry-only. They run in a separate portable terminal, "
            "do not touch current demo trading EAs, do not place orders, and do not change canonical Phase 2 status."
        ),
        "run_id": RUN_ID,
        "policy_version": POLICY_VERSION,
        "portable_root": str(portable_root),
        "terminal_exe": str(terminal_exe),
        "standard_demo_terminal_touched": False,
        "standard_demo_terminal_closed_or_restarted": False,
        "existing_trading_eas_touched": False,
        "broker_action_allowed": False,
        "profile_backup_dir": profile_backup_dir,
        "observer_log_backup_dir": observer_log_backup_dir,
        "terminal_closed_before_profile_replace": terminal_closed,
        "deployed_sources": [str(path) for path in deployed_sources],
        "compile_log": compile_log,
        "attachment_count": len(attachments) if attach else 0,
        "attachments": [_attachment_payload(row) for row in attachments],
    }
    terminal_payload: dict[str, Any] = {
        "status": terminal_status,
        "created_at_utc": attachment_payload["created_at_utc"],
        "authority": attachment_payload["authority"],
        "portable_root": str(portable_root),
        "prepare_attempted": prepare,
        "attach_attempted": attach,
        "launch_started": launch,
        "copied_paths": copied_paths,
        "attachment_report": str(output_md),
        "attachment_count": attachment_payload["attachment_count"],
        "logs": logs,
        "standard_demo_terminal_touched": False,
        "standard_demo_terminal_closed_or_restarted": False,
        "existing_trading_eas_touched": False,
        "broker_action_allowed": False,
    }

    output_json.write_text(json.dumps(attachment_payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_attachment_markdown(attachment_payload), encoding="utf-8")
    terminal_json.write_text(json.dumps(terminal_payload, indent=2), encoding="utf-8")
    terminal_md.write_text(_render_terminal_markdown(terminal_payload), encoding="utf-8")
    return AttachOutput(
        status=terminal_status,
        json_path=output_json,
        markdown_path=output_md,
        terminal_json_path=terminal_json,
        terminal_markdown_path=terminal_md,
        attachment_count=attachment_payload["attachment_count"],
    )


def _guard_not_standard_demo_terminal(terminal_data_dir: Path, terminal_exe: Path) -> None:
    if terminal_data_dir.resolve() == STANDARD_DEMO_TERMINAL_DATA_DIR.resolve():
        raise RuntimeError("Refusing to attach trend-guarded observers to the standard demo trading terminal data folder.")
    if terminal_exe.resolve() == STANDARD_DEMO_TERMINAL_EXE.resolve():
        raise RuntimeError("Refusing to attach trend-guarded observers with the standard demo trading terminal executable.")


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
    mql5_root = portable_root / "MQL5"
    experts_dir = mql5_root / "Experts"
    include_phase1_dir = mql5_root / "Include" / "Phase1"
    experts_dir.mkdir(parents=True, exist_ok=True)
    include_phase1_dir.mkdir(parents=True, exist_ok=True)

    deployed: list[Path] = []
    ea_source = phase1_root / EA_SOURCE
    ea_target = experts_dir / ea_source.name
    shutil.copy2(ea_source, ea_target)
    deployed.append(ea_target)
    for include_name in ("Phase1Types.mqh", "Phase1BreakoutRetest.mqh"):
        source = phase1_root / "mt5" / "Include" / "Phase1" / include_name
        target = include_phase1_dir / include_name
        shutil.copy2(source, target)
        deployed.append(target)
    return deployed


def _compile_ea(metaeditor_exe: Path, portable_root: Path) -> Path:
    scratch_root = Path("C:/MT5CompileScratch/RepoPhase1Portable")
    scratch_metaeditor = scratch_root / "MetaEditor64.exe"
    if scratch_metaeditor.exists():
        metaeditor_exe = scratch_metaeditor
    if not metaeditor_exe.exists():
        raise FileNotFoundError(f"MetaEditor not found: {metaeditor_exe}")

    scratch_mql5 = scratch_root / "MQL5"
    scratch_experts = scratch_mql5 / "Experts"
    scratch_include = scratch_mql5 / "Include" / "Phase1"
    scratch_experts.mkdir(parents=True, exist_ok=True)
    scratch_include.mkdir(parents=True, exist_ok=True)

    source = portable_root / "MQL5" / "Experts" / f"{EA_NAME}.mq5"
    scratch_source = scratch_experts / source.name
    shutil.copy2(source, scratch_source)
    for include_name in ("Phase1Types.mqh", "Phase1BreakoutRetest.mqh"):
        shutil.copy2(portable_root / "MQL5" / "Include" / "Phase1" / include_name, scratch_include / include_name)

    scratch_log = scratch_root / f"compile_{EA_NAME}.log"
    if scratch_log.exists():
        scratch_log.unlink()
    scratch_ex5 = scratch_experts / f"{EA_NAME}.ex5"
    if scratch_ex5.exists():
        scratch_ex5.unlink()
    subprocess.run([str(metaeditor_exe), "/portable", f"/compile:{scratch_source}", f"/log:{scratch_log}"], check=False, timeout=90)
    target_ex5 = portable_root / "MQL5" / "Experts" / f"{EA_NAME}.ex5"
    if not scratch_ex5.exists():
        raise RuntimeError(f"MetaEditor did not produce {EA_NAME}.ex5. Compile log:\n{_read_text(scratch_log)}")
    shutil.copy2(scratch_ex5, target_ex5)

    log_path = portable_root / "MQL5" / "Logs" / f"compile_{EA_NAME}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if scratch_log.exists():
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
        *files_dir.glob("trend_guarded_fix_observer*_signal_log*.csv"),
        *files_dir.glob("trend_guarded_fix_observer*_startup*.csv"),
    ]
    existing = [path for path in candidates if path.exists()]
    if not existing:
        return "none"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = portable_root / "_codex_quarantine" / "observer_logs" / f"trend_guarded_fix_logs_{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    for path in existing:
        shutil.move(str(path), str(backup_dir / path.name))
    return str(backup_dir)


def _replace_default_profile(portable_root: Path, phase1_root: Path, attachments: list[AttachmentRow]) -> Path:
    charts_root = portable_root / "MQL5" / "Profiles" / "Charts"
    default_profile = charts_root / "Default"
    backup_root = portable_root / "_codex_quarantine" / "profile_backups"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = backup_root / f"default_profile_before_trend_guarded_fix_attach_{stamp}"
    backup_dir.parent.mkdir(parents=True, exist_ok=True)
    if default_profile.exists():
        shutil.copytree(default_profile, backup_dir)
        shutil.rmtree(default_profile)
    default_profile.mkdir(parents=True, exist_ok=True)

    for index, row in enumerate(attachments, start=1):
        chart = default_profile / f"chart{index:02d}.chr"
        chart.write_text(_render_chart(phase1_root, row, index), encoding="utf-8")
    return backup_dir


def _build_attachment_plan() -> list[AttachmentRow]:
    rows: list[AttachmentRow] = []
    for symbol, candidates in SYMBOL_CANDIDATES.items():
        for candidate in candidates:
            rows.append(AttachmentRow(candidate=candidate, symbol=symbol))
    return rows


def _render_chart(phase1_root: Path, row: AttachmentRow, index: int) -> str:
    left = 20 + ((index - 1) % 3) * 42
    top = 20 + ((index - 1) // 3) * 35
    right = left + 980
    bottom = top + 720
    digits, tick_size = _symbol_format(row.symbol)
    preset_inputs = _preset_inputs(row)
    return "\n".join(
        [
            "<chart>",
            f"id={int(time.time())}{index:04d}",
            f"symbol={row.symbol}",
            f"description={row.symbol}",
            "period_type=0",
            "period_size=5",
            f"digits={digits}",
            f"tick_size={tick_size}",
            "scale_fix=0",
            "scale_fixed_min=0.000000",
            "scale_fixed_max=0.000000",
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
            f"window_left={left}",
            f"window_top={top}",
            f"window_right={right}",
            f"window_bottom={bottom}",
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


def _preset_inputs(row: AttachmentRow) -> list[str]:
    slug = _instance_slug(row)
    return [
        f"InpRunId={RUN_ID}",
        "InpDryRunOnly=true",
        f"InpCandidate={row.candidate}",
        "InpCandidateStatus=TREND_GUARDED_FIX_OBSERVER_V2",
        f"InpTargetSymbol={row.symbol}",
        f"InpQualifiedSymbolsCsv={row.symbol}",
        "InpExpectedServerMarker=Demo",
        f"InpShadowPolicyVersion={POLICY_VERSION}",
        f"InpAttachmentLogFileName=trend_guarded_fix_observer_v2_signal_log_{slug}.csv",
        f"InpStartupLogFileName=trend_guarded_fix_observer_v2_startup_{slug}.csv",
        "InpTrendVetoEnabled=true",
        "InpTrendSlopeLookbackBars=3",
        "InpMinSlopePoints=50.0",
        "InpDubaiUtcOffsetMinutes=240",
    ]


def _symbol_format(symbol: str) -> tuple[int, str]:
    if symbol == "XAUUSD":
        return 2, "0.01"
    if symbol == "USDJPY":
        return 3, "0.001"
    return 5, "0.00001"


def _attachment_payload(row: AttachmentRow) -> dict[str, Any]:
    return {
        "candidate": row.candidate,
        "symbol": row.symbol,
        "timeframe": "M5",
        "dry_run_only": True,
        "broker_action_allowed": False,
        "policy_version": POLICY_VERSION,
        "attachment_log_file": f"trend_guarded_fix_observer_v2_signal_log_{_instance_slug(row)}.csv",
        "startup_log_file": f"trend_guarded_fix_observer_v2_startup_{_instance_slug(row)}.csv",
    }


def _instance_slug(row: AttachmentRow) -> str:
    raw = f"{row.candidate}_{row.symbol}".lower()
    return "".join(char if char.isalnum() or char == "_" else "_" for char in raw)


def _log_state(portable_root: Path) -> dict[str, Any]:
    files = portable_root / "MQL5" / "Files"
    startup_logs = sorted(files.glob("trend_guarded_fix_observer_v2_startup_*.csv")) if files.exists() else []
    signal_logs = sorted(files.glob("trend_guarded_fix_observer_v2_signal_log_*.csv")) if files.exists() else []
    latest_signal = max(signal_logs, key=lambda path: path.stat().st_mtime) if signal_logs else None
    latest_startup = max(startup_logs, key=lambda path: path.stat().st_mtime) if startup_logs else None
    return {
        "startup_log_count": len(startup_logs),
        "signal_log_count": len(signal_logs),
        "latest_startup_log": str(latest_startup) if latest_startup else "missing",
        "latest_startup_log_mtime": datetime.fromtimestamp(latest_startup.stat().st_mtime).isoformat() if latest_startup else "missing",
        "latest_signal_log": str(latest_signal) if latest_signal else "missing",
        "latest_signal_log_mtime": datetime.fromtimestamp(latest_signal.stat().st_mtime).isoformat() if latest_signal else "missing",
        "startup_logs": [str(path) for path in startup_logs],
        "signal_logs": [str(path) for path in signal_logs],
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


def _render_attachment_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 2 Trend-Guarded Fix Observer Attachments",
        "",
        f"Status: {payload['status']}",
        "",
        payload["authority"],
        "",
        f"Run ID: `{payload['run_id']}`",
        f"Policy version: `{payload['policy_version']}`",
        f"Portable root: `{payload['portable_root']}`",
        f"Attachment count: `{payload['attachment_count']}`",
        f"Compile log: `{payload['compile_log']}`",
        f"Profile backup: `{payload['profile_backup_dir']}`",
        f"Observer log backup: `{payload['observer_log_backup_dir']}`",
        f"Standard demo terminal touched: `{payload['standard_demo_terminal_touched']}`",
        f"Standard demo terminal closed/restarted: `{payload['standard_demo_terminal_closed_or_restarted']}`",
        f"Existing trading EAs touched: `{payload['existing_trading_eas_touched']}`",
        f"Broker action allowed: `{payload['broker_action_allowed']}`",
        "",
        "| Candidate | Symbol | Timeframe | Dry-run | Broker action | Signal log |",
        "|---|---|---|---|---|---|",
    ]
    for item in payload["attachments"]:
        lines.append(
            f"| {item['candidate']} | {item['symbol']} | {item['timeframe']} | {item['dry_run_only']} | "
            f"{item['broker_action_allowed']} | `{item['attachment_log_file']}` |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_terminal_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 2 Trend-Guarded Fix Observer Terminal",
            "",
            f"Status: {payload['status']}",
            "",
            payload["authority"],
            "",
            f"Portable root: `{payload['portable_root']}`",
            f"Prepare attempted: `{payload['prepare_attempted']}`",
            f"Attach attempted: `{payload['attach_attempted']}`",
            f"Launch started: `{payload['launch_started']}`",
            f"Attachment count: `{payload['attachment_count']}`",
            f"Standard demo terminal touched: `{payload['standard_demo_terminal_touched']}`",
            f"Standard demo terminal closed/restarted: `{payload['standard_demo_terminal_closed_or_restarted']}`",
            f"Existing trading EAs touched: `{payload['existing_trading_eas_touched']}`",
            f"Broker action allowed: `{payload['broker_action_allowed']}`",
            "",
            "## Logs",
            "",
            f"- Startup log count: `{payload['logs']['startup_log_count']}`",
            f"- Signal log count: `{payload['logs']['signal_log_count']}`",
            f"- Latest startup log: `{payload['logs']['latest_startup_log']}`",
            f"- Latest signal log: `{payload['logs']['latest_signal_log']}`",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Attach trend-guarded fix observers to an isolated MT5 terminal.")
    parser.add_argument("--phase1-root", type=Path, default=Path("."))
    parser.add_argument("--install-root", type=Path, default=DEFAULT_INSTALL_ROOT)
    parser.add_argument("--source-data-dir", type=Path, default=DEFAULT_SOURCE_DATA_DIR)
    parser.add_argument("--portable-root", type=Path, default=DEFAULT_PORTABLE_ROOT)
    parser.add_argument("--metaeditor-exe", type=Path, default=DEFAULT_METAEDITOR_EXE)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--terminal-json", type=Path, default=None)
    parser.add_argument("--allow-prepare", action="store_true")
    parser.add_argument("--allow-attach", action="store_true")
    parser.add_argument("--allow-launch", action="store_true")
    parser.add_argument("--wait-seconds", type=int, default=90)
    args = parser.parse_args()

    output = attach_phase2_trend_guarded_fix_observers(
        phase1_root=args.phase1_root,
        install_root=args.install_root,
        source_data_dir=args.source_data_dir,
        portable_root=args.portable_root,
        metaeditor_exe=args.metaeditor_exe,
        output_json=args.output_json,
        terminal_json=args.terminal_json,
        prepare=args.allow_prepare,
        attach=args.allow_attach,
        launch=args.allow_launch,
        wait_seconds=args.wait_seconds,
    )
    print(f"{output.status}: {output.attachment_count} attachments")
    print(output.json_path)
    print(output.markdown_path)
    print(output.terminal_json_path)
    print(output.terminal_markdown_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
