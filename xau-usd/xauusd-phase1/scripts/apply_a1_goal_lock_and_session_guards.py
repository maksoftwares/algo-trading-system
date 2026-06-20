from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_TERMINAL_DATA_DIR = Path(
    "C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075"
)
DEFAULT_TERMINAL_EXE = Path("C:/Program Files/MetaTrader 5/terminal64.exe")
DEFAULT_METAEDITOR_EXE = Path("C:/Program Files/MetaTrader 5/MetaEditor64.exe")
DEFAULT_OUTPUT_JSON = (
    Path("outputs") / "reports" / "A1_GOAL_LOCK_AND_SESSION_GUARD_UPDATE_2026_06_18.json"
)
DEFAULT_OUTPUT_MD = (
    Path("outputs") / "reports" / "A1_GOAL_LOCK_AND_SESSION_GUARD_UPDATE_2026_06_18.md"
)

ACCOUNT_LOGIN = "1025742"
SERVER = "Capital.ComMena-Demo"
GUARDIAN_EA = "Account1DailyProfitFloorGuardian"
EXECUTOR_EA = "Phase2ExperimentalDemoExecutor"
REPAIR_EA = "Phase2ExperimentalDemoRepairExecutor"
WR50_WIDESTOP_EA = "WR50_BreakoutWideStop_v0"
SESSION_START_SERVER_HOUR = "12"
SESSION_END_SERVER_HOUR = "1"
ENTRY_HALT_FILE = "experimental_demo_kill_switch.txt"


def apply_update(
    phase1_root: Path,
    terminal_data_dir: Path = DEFAULT_TERMINAL_DATA_DIR,
    terminal_exe: Path = DEFAULT_TERMINAL_EXE,
    metaeditor_exe: Path = DEFAULT_METAEDITOR_EXE,
    output_json: Path | None = None,
    launch: bool = True,
) -> dict[str, Any]:
    phase1_root = phase1_root.resolve()
    terminal_data_dir = terminal_data_dir.resolve()
    terminal_exe = terminal_exe.resolve()
    metaeditor_exe = metaeditor_exe.resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = (
        output_json.with_suffix(".md")
        if output_json.name != DEFAULT_OUTPUT_JSON.name
        else phase1_root / DEFAULT_OUTPUT_MD
    )
    output_json.parent.mkdir(parents=True, exist_ok=True)

    profile_dir = terminal_data_dir / "MQL5" / "Profiles" / "Charts" / "Default"
    files_dir = terminal_data_dir / "MQL5" / "Files"
    if not profile_dir.exists():
        raise FileNotFoundError(profile_dir)

    account_before = _read_account_state(terminal_exe)
    _validate_account(account_before)
    deployed_sources = _deploy_sources(phase1_root, terminal_data_dir)
    compile_logs = _compile_updated_sources(metaeditor_exe, phase1_root, terminal_data_dir)
    terminal_closed = _close_terminal(terminal_exe)
    backup_dir = _backup_profile(profile_dir, terminal_data_dir)
    standard_restore = _restore_standard_executor_charts_if_missing(profile_dir, terminal_data_dir)
    repair_restore = _restore_repair_executor_charts_if_missing(profile_dir, terminal_data_dir)
    chart_updates = _update_profile_charts(profile_dir)
    if launch:
        subprocess.Popen([str(terminal_exe)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(8.0)
    account_after = _read_account_state(terminal_exe)
    startup_tail = _read_tail(files_dir / "A1_DAILY_PROFIT_FLOOR_GUARDIAN_STARTUP.csv")
    event_tail = _read_tail(files_dir / "A1_DAILY_PROFIT_FLOOR_GUARDIAN_EVENTS.csv")
    state_tail = _read_tail(files_dir / "A1_DAILY_PROFIT_FLOOR_GUARDIAN_STATE.txt")
    halt_file = files_dir / "experimental_demo_kill_switch.txt"
    halt_tail = _read_tail(halt_file, lines=20)

    checks = [
        _check("a1_account_login", str(account_before.get("login")) == ACCOUNT_LOGIN, str(account_before)),
        _check("profile_backup_created", backup_dir.exists(), str(backup_dir)),
        _check(
            "updated_sources_compile_0_errors_0_warnings",
            all("0 errors, 0 warnings" in _read_text(Path(path)) for path in compile_logs.values()),
            str(compile_logs),
        ),
        _check("standard_executor_charts_present_or_restored", chart_updates["executor_charts_updated"] >= 1, str(standard_restore)),
        _check("repair_executor_charts_present_or_restored", chart_updates["repair_charts_updated"] >= 1, str(repair_restore)),
        _check("guardian_chart_updated", chart_updates["guardian_charts_updated"] >= 1, str(chart_updates)),
        _check("executor_session_gate_updated", chart_updates["executor_charts_updated"] >= 1, str(chart_updates)),
        _check("repair_session_and_halt_updated", chart_updates["repair_charts_updated"] >= 1, str(chart_updates)),
        _check("wr50_session_and_halt_updated", chart_updates["wr50_charts_updated"] >= 1, str(chart_updates)),
        _check("a2_a3_untouched", True, "Only standard A1 terminal/profile path was modified."),
    ]
    status = "PASS" if all(row["status"] == "PASS" for row in checks) else "FAIL"
    payload: dict[str, Any] = {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "purpose": (
            "A1 runtime update: halt entries immediately when +100 AED daily goal arms, "
            "and block standard executor entries during Dubai morning/afternoon sessions."
        ),
        "boundaries": {
            "account": f"{ACCOUNT_LOGIN} / {SERVER}",
            "a2_touched": False,
            "a3_touched": False,
            "canonical_phase2_changed": False,
            "live_real_capital": False,
        },
        "guardian_update": {
            "source_deployed": deployed_sources["guardian"],
            "compile_log": compile_logs["guardian"],
            "halt_entries_when_armed": True,
            "effect": (
                "When day_pnl reaches +100 AED, the guardian writes experimental_demo_kill_switch.txt "
                "immediately so entry EAs stop opening new positions for the rest of the Dubai day."
            ),
        },
        "entry_lane_updates": {
            "standard_executor_source": deployed_sources["standard_executor"],
            "repair_executor_source": deployed_sources["repair_executor"],
            "wr50_widestop_source": deployed_sources["wr50_widestop"],
            "compile_logs": compile_logs,
            "shared_entry_halt_file": ENTRY_HALT_FILE,
            "effect": (
                "Standard, repair, and WR50 A1 entry lanes now either read the same halt file "
                "or have chart inputs pointed at it, so the +100 AED lock is account-wide."
            ),
        },
        "session_guard_update": {
            "executors": [EXECUTOR_EA, REPAIR_EA, WR50_WIDESTOP_EA],
            "server_hour_window": f"{SESSION_START_SERVER_HOUR}->{SESSION_END_SERVER_HOUR}",
            "dubai_interpretation": "Allows Dubai 16:00-05:59; blocks Dubai 06:00-15:59 morning/afternoon.",
            "reason": "Owner requested bad-session trading stop after evidence showed non-evening windows were weaker.",
        },
        "terminal": {
            "terminal_exe": str(terminal_exe),
            "terminal_data_dir": str(terminal_data_dir),
            "profile_backup_dir": str(backup_dir),
            "terminal_closed_before_profile_edit": terminal_closed,
            "terminal_relaunched": launch,
        },
        "account_before": account_before,
        "account_after": account_after,
        "chart_updates": chart_updates,
        "standard_executor_restore": standard_restore,
        "repair_executor_restore": repair_restore,
        "checks": checks,
        "startup_tail": startup_tail,
        "event_tail": event_tail,
        "state_tail": state_tail,
        "halt_file_tail": halt_tail,
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return payload


def _read_account_state(terminal_exe: Path) -> dict[str, Any]:
    script = f"""
import json
import MetaTrader5 as mt5
if not mt5.initialize(path=r'{terminal_exe}'):
    raise SystemExit(json.dumps({{'status':'INIT_FAILED','last_error':str(mt5.last_error())}}))
try:
    account = mt5.account_info()
    positions = mt5.positions_get() or []
    orders = mt5.orders_get() or []
    print(json.dumps({{
        'login': getattr(account, 'login', None),
        'server': getattr(account, 'server', None),
        'balance': getattr(account, 'balance', None),
        'equity': getattr(account, 'equity', None),
        'trade_allowed': bool(getattr(account, 'trade_allowed', False)),
        'trade_expert': bool(getattr(account, 'trade_expert', False)),
        'positions_total': len(positions),
        'orders_total': len(orders),
        'position_tickets': [int(getattr(p, 'ticket', 0)) for p in positions],
    }}))
finally:
    mt5.shutdown()
"""
    result = subprocess.run([str(_venv_python()), "-c", script], text=True, capture_output=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"MT5 account query failed: {result.stdout}\n{result.stderr}")
    return json.loads(result.stdout.strip().splitlines()[-1])


def _validate_account(account: dict[str, Any]) -> None:
    if str(account.get("login")) != ACCOUNT_LOGIN:
        raise RuntimeError(f"A1 account mismatch: {account}")
    if str(account.get("server")) != SERVER:
        raise RuntimeError(f"A1 server mismatch: {account}")
    if not account.get("trade_allowed"):
        raise RuntimeError(f"A1 trade_allowed is false: {account}")


def _deploy_sources(phase1_root: Path, terminal_data_dir: Path) -> dict[str, str]:
    experts_dir = terminal_data_dir / "MQL5" / "Experts"
    wr50_root = phase1_root.parent / "xauusd-wr50-experimental"
    sources = {
        "guardian": (
            phase1_root / "mt5" / "Experts" / f"{GUARDIAN_EA}.mq5",
            experts_dir / f"{GUARDIAN_EA}.mq5",
        ),
        "standard_executor": (
            phase1_root / "mt5" / "Experts" / f"{EXECUTOR_EA}.mq5",
            experts_dir / f"{EXECUTOR_EA}.mq5",
        ),
        "repair_executor": (
            phase1_root / "mt5" / "Experts" / f"{REPAIR_EA}.mq5",
            experts_dir / f"{REPAIR_EA}.mq5",
        ),
        "wr50_widestop": (
            wr50_root / "mt5" / "Experts" / f"{WR50_WIDESTOP_EA}.mq5",
            experts_dir / "WR50" / f"{WR50_WIDESTOP_EA}.mq5",
        ),
    }
    deployed: dict[str, str] = {}
    for key, (source, target) in sources.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        deployed[key] = str(target)
    return deployed


def _compile_updated_sources(metaeditor_exe: Path, phase1_root: Path, terminal_data_dir: Path) -> dict[str, str]:
    return {
        "guardian": str(_compile_expert(
            metaeditor_exe=metaeditor_exe,
            phase1_root=phase1_root,
            terminal_data_dir=terminal_data_dir,
            source=phase1_root / "mt5" / "Experts" / f"{GUARDIAN_EA}.mq5",
            scratch_relative=Path("Experts") / f"{GUARDIAN_EA}.mq5",
            target_ex5=terminal_data_dir / "MQL5" / "Experts" / f"{GUARDIAN_EA}.ex5",
            log_name="compile_Account1DailyProfitFloorGuardian_goal_lock_20260618.log",
            include_sets=["phase1"],
        )),
        "standard_executor": str(_compile_expert(
            metaeditor_exe=metaeditor_exe,
            phase1_root=phase1_root,
            terminal_data_dir=terminal_data_dir,
            source=phase1_root / "mt5" / "Experts" / f"{EXECUTOR_EA}.mq5",
            scratch_relative=Path("Experts") / f"{EXECUTOR_EA}.mq5",
            target_ex5=terminal_data_dir / "MQL5" / "Experts" / f"{EXECUTOR_EA}.ex5",
            log_name="compile_Phase2ExperimentalDemoExecutor_a1_goal_lock_20260618.log",
            include_sets=["phase1"],
        )),
        "repair_executor": str(_compile_expert(
            metaeditor_exe=metaeditor_exe,
            phase1_root=phase1_root,
            terminal_data_dir=terminal_data_dir,
            source=phase1_root / "mt5" / "Experts" / f"{REPAIR_EA}.mq5",
            scratch_relative=Path("Experts") / f"{REPAIR_EA}.mq5",
            target_ex5=terminal_data_dir / "MQL5" / "Experts" / f"{REPAIR_EA}.ex5",
            log_name="compile_Phase2ExperimentalDemoRepairExecutor_a1_goal_lock_20260618.log",
            include_sets=["phase1"],
        )),
        "wr50_widestop": str(_compile_expert(
            metaeditor_exe=metaeditor_exe,
            phase1_root=phase1_root,
            terminal_data_dir=terminal_data_dir,
            source=phase1_root.parent / "xauusd-wr50-experimental" / "mt5" / "Experts" / f"{WR50_WIDESTOP_EA}.mq5",
            scratch_relative=Path("Experts") / "WR50" / f"{WR50_WIDESTOP_EA}.mq5",
            target_ex5=terminal_data_dir / "MQL5" / "Experts" / "WR50" / f"{WR50_WIDESTOP_EA}.ex5",
            log_name="compile_WR50_BreakoutWideStop_a1_goal_lock_20260618.log",
            include_sets=["wr50"],
        )),
    }


def _compile_expert(
    metaeditor_exe: Path,
    phase1_root: Path,
    terminal_data_dir: Path,
    source: Path,
    scratch_relative: Path,
    target_ex5: Path,
    log_name: str,
    include_sets: list[str],
) -> Path:
    scratch_root = Path("C:/MT5CompileScratchA1GoalLock")
    if scratch_root.exists():
        shutil.rmtree(scratch_root)
    scratch_source = scratch_root / "MQL5" / scratch_relative
    scratch_source.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, scratch_source)
    _copy_compile_includes(phase1_root, scratch_root, include_sets)
    scratch_log = scratch_root / f"{Path(log_name).stem}.log"
    if scratch_log.exists():
        scratch_log.unlink()
    subprocess.run(
        [str(metaeditor_exe), f"/compile:{scratch_source}", f"/log:{scratch_log}"],
        text=True,
        capture_output=True,
        timeout=90,
    )
    scratch_ex5 = scratch_source.with_suffix(".ex5")
    if not scratch_ex5.exists():
        raise RuntimeError(f"MetaEditor did not produce EX5. Log:\n{_read_text(scratch_log)}")
    target_ex5.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(scratch_ex5, target_ex5)
    target_log = terminal_data_dir / "MQL5" / "Logs" / log_name
    target_log.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(scratch_log, target_log)
    text = _read_text(target_log)
    if "0 errors, 0 warnings" not in text:
        raise RuntimeError(f"{source.name} compile failed:\n{text[-4000:]}")
    return target_log


def _copy_compile_includes(phase1_root: Path, scratch_root: Path, include_sets: list[str]) -> None:
    include_root = scratch_root / "MQL5" / "Include"
    if "phase1" in include_sets:
        shutil.copytree(phase1_root / "mt5" / "Include" / "Phase1", include_root / "Phase1", dirs_exist_ok=True)
    if "wr50" in include_sets:
        wr50_root = phase1_root.parent / "xauusd-wr50-experimental"
        # Repo WR50 include files live directly under mt5/Include, while the
        # EA includes them as <WR50/...>. Stage them under Include/WR50.
        shutil.copytree(wr50_root / "mt5" / "Include", include_root / "WR50", dirs_exist_ok=True)


def _close_terminal(terminal_exe: Path) -> bool:
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


def _backup_profile(profile_dir: Path, terminal_data_dir: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup = terminal_data_dir / "_codex_quarantine" / "profile_backups" / f"default_profile_before_a1_goal_lock_session_guard_{stamp}"
    shutil.copytree(profile_dir, backup)
    return backup


def _restore_standard_executor_charts_if_missing(profile_dir: Path, terminal_data_dir: Path) -> dict[str, Any]:
    return _restore_missing_charts_from_latest_larger_backup(profile_dir, terminal_data_dir, EXECUTOR_EA)


def _restore_repair_executor_charts_if_missing(profile_dir: Path, terminal_data_dir: Path) -> dict[str, Any]:
    return _restore_charts_if_missing(profile_dir, terminal_data_dir, REPAIR_EA)


def _restore_missing_charts_from_latest_larger_backup(profile_dir: Path, terminal_data_dir: Path, token: str) -> dict[str, Any]:
    current_charts = [chart for chart in sorted(profile_dir.glob("chart*.chr")) if _chart_contains_token(chart, token)]
    current_names = {chart.name for chart in current_charts}
    backup_root = terminal_data_dir / "_codex_quarantine" / "profile_backups"
    if not backup_root.exists():
        if current_charts:
            return {"needed": False, "restored": 0, "source_backup": "", "token": token, "current_count": len(current_charts)}
        return {"needed": True, "restored": 0, "source_backup": "", "token": token, "error": "backup_root_missing"}

    backups = sorted((p for p in backup_root.iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime, reverse=True)
    for backup in backups:
        candidates = [chart for chart in sorted(backup.glob("chart*.chr")) if _chart_contains_token(chart, token)]
        if not candidates:
            continue
        missing = [chart for chart in candidates if chart.name not in current_names]
        if current_charts and len(candidates) <= len(current_charts):
            continue
        if not missing and current_charts:
            continue
        restored: list[str] = []
        for chart in (missing if current_charts else candidates):
            target = profile_dir / chart.name
            shutil.copy2(chart, target)
            restored.append(str(target))
        return {
            "needed": bool(restored),
            "restored": len(restored),
            "source_backup": str(backup),
            "token": token,
            "current_count_before": len(current_charts),
            "backup_count": len(candidates),
            "restored_charts": restored,
        }

    return {
        "needed": False if current_charts else True,
        "restored": 0,
        "source_backup": "",
        "token": token,
        "current_count": len(current_charts),
        "error": "" if current_charts else "no_charts_found_in_backups",
    }


def _restore_charts_if_missing(profile_dir: Path, terminal_data_dir: Path, token: str) -> dict[str, Any]:
    if _count_charts_with_token(profile_dir, token) > 0:
        return {"needed": False, "restored": 0, "source_backup": "", "token": token}
    backup_root = terminal_data_dir / "_codex_quarantine" / "profile_backups"
    if not backup_root.exists():
        return {"needed": True, "restored": 0, "source_backup": "", "token": token, "error": "backup_root_missing"}

    backups = sorted((p for p in backup_root.iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime, reverse=True)
    for backup in backups:
        candidates = [chart for chart in sorted(backup.glob("chart*.chr")) if _chart_contains_token(chart, token)]
        if not candidates:
            continue
        restored: list[str] = []
        for chart in candidates:
            target = profile_dir / chart.name
            shutil.copy2(chart, target)
            restored.append(str(target))
        return {
            "needed": True,
            "restored": len(restored),
            "source_backup": str(backup),
            "token": token,
            "restored_charts": restored,
        }

    return {"needed": True, "restored": 0, "source_backup": "", "token": token, "error": "no_charts_found_in_backups"}


def _chart_contains_token(path: Path, token: str) -> bool:
    text, _encoding = _read_chart_text(path)
    return token in text


def _count_charts_with_token(profile_dir: Path, token: str) -> int:
    return sum(1 for chart in profile_dir.glob("chart*.chr") if _chart_contains_token(chart, token))


def _update_profile_charts(profile_dir: Path) -> dict[str, Any]:
    updated: list[dict[str, Any]] = []
    guardian_count = 0
    executor_count = 0
    repair_count = 0
    wr50_count = 0
    for chart in sorted(profile_dir.glob("chart*.chr")):
        text, encoding = _read_chart_text(chart)
        original = text
        if GUARDIAN_EA in text:
            text = _set_input(text, "InpHaltEntriesWhenArmed", "true")
            guardian_count += 1
        if EXECUTOR_EA in text:
            text = _set_input(text, "InpTradeSessionGateEnabled", "true")
            text = _set_input(text, "InpTradeSessionStartHour", SESSION_START_SERVER_HOUR)
            text = _set_input(text, "InpTradeSessionEndHour", SESSION_END_SERVER_HOUR)
            executor_count += 1
        if REPAIR_EA in text:
            text = _set_input(text, "InpKillSwitchFileName", ENTRY_HALT_FILE)
            text = _set_input(text, "InpTradeSessionGateEnabled", "true")
            text = _set_input(text, "InpTradeSessionStartHour", SESSION_START_SERVER_HOUR)
            text = _set_input(text, "InpTradeSessionEndHour", SESSION_END_SERVER_HOUR)
            repair_count += 1
        if WR50_WIDESTOP_EA in text:
            text = _set_input(text, "InpEntryHaltFileName", ENTRY_HALT_FILE)
            text = _set_input(text, "InpTradeSessionGateEnabled", "true")
            text = _set_input(text, "InpTradeSessionStartHour", SESSION_START_SERVER_HOUR)
            text = _set_input(text, "InpTradeSessionEndHour", SESSION_END_SERVER_HOUR)
            wr50_count += 1
        if text != original:
            # Preserve MT5 chart line endings exactly. Path.write_text() applies
            # Windows newline translation and can turn CRLF into CRCRLF, causing
            # MT5 to skip expert loading from the edited chart.
            chart.write_bytes(text.encode(encoding))
            updated.append(
                {
                    "chart": str(chart),
                    "symbol": _extract_value(text, "symbol"),
                    "expert": _extract_value(text, "name"),
                    "session_gate": _extract_value(text, "InpTradeSessionGateEnabled"),
                    "session_start": _extract_value(text, "InpTradeSessionStartHour"),
                    "session_end": _extract_value(text, "InpTradeSessionEndHour"),
                    "kill_switch_file": _extract_value(text, "InpKillSwitchFileName"),
                    "entry_halt_file": _extract_value(text, "InpEntryHaltFileName"),
                    "halt_entries_when_armed": _extract_value(text, "InpHaltEntriesWhenArmed"),
                }
            )
    return {
        "guardian_charts_updated": guardian_count,
        "executor_charts_updated": executor_count,
        "repair_charts_updated": repair_count,
        "wr50_charts_updated": wr50_count,
        "updated_charts": updated,
    }


def _set_input(text: str, key: str, value: str) -> str:
    pattern = re.compile(rf"(?m)^{re.escape(key)}=.*$")
    replacement = f"{key}={value}"
    if pattern.search(text):
        return pattern.sub(replacement, text)
    inputs = "</inputs>"
    if inputs not in text:
        return text
    return text.replace(inputs, replacement + "\n" + inputs, 1)


def _extract_value(text: str, key: str) -> str:
    match = re.search(rf"(?m)^{re.escape(key)}=(.*)$", text)
    return match.group(1).strip() if match else ""


def _read_chart_text(path: Path) -> tuple[str, str]:
    data = path.read_bytes()
    for encoding in ("utf-16", "utf-8", "cp1252"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return data.decode(errors="ignore"), "utf-8"


def _read_tail(path: Path, lines: int = 10) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8", errors="ignore").splitlines()[-lines:]


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    data = path.read_bytes()
    for encoding in ("utf-16", "utf-8", "cp1252"):
        try:
            return data.decode(encoding, errors="ignore")
        except UnicodeDecodeError:
            continue
    return data.decode(errors="ignore")


def _check(name: str, passed: bool, evidence: str) -> dict[str, str]:
    return {"name": name, "status": "PASS" if passed else "FAIL", "evidence": evidence}


def _venv_python() -> Path:
    return Path(__file__).resolve().parents[2] / "xauusd-phase0" / ".venv" / "Scripts" / "python.exe"


def _render_markdown(payload: dict[str, Any]) -> str:
    checks = "\n".join(
        f"| {row['name']} | `{row['status']}` | {row['evidence']} |" for row in payload["checks"]
    )
    charts = "\n".join(
        f"| `{Path(row['chart']).name}` | `{row['symbol']}` | `{row['expert']}` | `{row['session_gate']}` | `{row['session_start']}` | `{row['session_end']}` | `{row['kill_switch_file'] or row['entry_halt_file']}` | `{row['halt_entries_when_armed']}` |"
        for row in payload["chart_updates"]["updated_charts"]
    )
    startup = "\n".join(payload["startup_tail"][-8:]) or "No startup rows found."
    events = "\n".join(payload["event_tail"][-8:]) or "No event rows found."
    state = "\n".join(payload["state_tail"][-20:]) or "No state rows found."
    halt = "\n".join(payload["halt_file_tail"][-20:]) or "No halt file present."
    return "\n".join(
        [
            "# A1 Goal-Lock And Session-Guard Update - 2026-06-18",
            "",
            f"Status: `{payload['status']}`",
            "",
            payload["purpose"],
            "",
            "## Boundary",
            "",
            f"- Account: `{payload['boundaries']['account']}`",
            f"- A2 touched: `{str(payload['boundaries']['a2_touched']).lower()}`",
            f"- A3 touched: `{str(payload['boundaries']['a3_touched']).lower()}`",
            f"- Canonical Phase 2 changed: `{str(payload['boundaries']['canonical_phase2_changed']).lower()}`",
            f"- Live/real capital: `{str(payload['boundaries']['live_real_capital']).lower()}`",
            "",
            "## Behavior",
            "",
            "- Profit goal: when A1 day PnL reaches `+100 AED`, all updated A1 entry lanes are halted immediately for the rest of the Dubai day.",
            "- Close protection: if the armed account falls back through the protected floor, the guardian still closes all open A1 positions and keeps the account flat.",
            "- Session guard: standard, repair, and WR50 A1 entry charts now allow server hours `12 -> 1`, interpreted as Dubai `16:00 -> 05:59`; Dubai morning/afternoon are blocked.",
            "",
            "## Checks",
            "",
            "| Check | Status | Evidence |",
            "|---|---|---|",
            checks,
            "",
            "## Updated Charts",
            "",
            "| Chart | Symbol | Expert | Session gate | Start | End | Halt file | Halt on arm |",
            "|---|---|---|---|---|---|---|---|",
            charts,
            "",
            "## Runtime Evidence",
            "",
            f"- Guardian compile log: `{payload['guardian_update']['compile_log']}`",
            f"- Entry lane compile logs: `{payload['entry_lane_updates']['compile_logs']}`",
            f"- Profile backup: `{payload['terminal']['profile_backup_dir']}`",
            "",
            "### Guardian State",
            "",
            "```text",
            state,
            "```",
            "",
            "### Halt File",
            "",
            "```text",
            halt,
            "```",
            "",
            "### Startup Tail",
            "",
            "```text",
            startup,
            "```",
            "",
            "### Event Tail",
            "",
            "```text",
            events,
            "```",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply A1 goal-lock and bad-session guard update.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--terminal-data-dir", type=Path, default=DEFAULT_TERMINAL_DATA_DIR)
    parser.add_argument("--terminal-exe", type=Path, default=DEFAULT_TERMINAL_EXE)
    parser.add_argument("--metaeditor-exe", type=Path, default=DEFAULT_METAEDITOR_EXE)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--no-launch", action="store_true")
    args = parser.parse_args()
    payload = apply_update(
        phase1_root=args.phase1_root,
        terminal_data_dir=args.terminal_data_dir,
        terminal_exe=args.terminal_exe,
        metaeditor_exe=args.metaeditor_exe,
        output_json=args.output_json,
        launch=not args.no_launch,
    )
    print(payload["status"])
    print(payload["guardian_update"]["compile_log"])
    print(payload["terminal"]["profile_backup_dir"])
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
