from __future__ import annotations

import argparse
import json
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
    Path("outputs") / "reports" / "A1_DAILY_PROFIT_FLOOR_GUARDIAN_ATTACHMENT_2026_06_18.json"
)
DEFAULT_OUTPUT_MD = (
    Path("outputs") / "reports" / "A1_DAILY_PROFIT_FLOOR_GUARDIAN_ATTACHMENT_2026_06_18.md"
)

EA_NAME = "Account1DailyProfitFloorGuardian"
ACCOUNT_LOGIN = "1025742"
SERVER = "Capital.ComMena-Demo"
CHART_SYMBOL = "XAUUSD"
OWNER_TOKEN = "A1_DAILY_PROFIT_FLOOR_OWNER_AUTHORIZED_20260618"
LOCAL_PRESET_NAME = "Account1DailyProfitFloorGuardian.armed_owner_20260618.set"


def attach_a1_daily_profit_floor_guardian(
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
        raise FileNotFoundError(f"Default profile not found: {profile_dir}")

    account_before = _read_account_state(terminal_exe)
    _validate_account(account_before)
    _ensure_no_existing_guardian_chart(profile_dir)
    deployed_source = _deploy_source(phase1_root, terminal_data_dir)
    local_preset = _write_local_armed_preset(terminal_data_dir)
    compile_log = _compile_ea(metaeditor_exe, terminal_data_dir)
    terminal_closed = _close_terminal(terminal_exe)
    backup_dir = _backup_profile(profile_dir, terminal_data_dir)
    chart_path = _append_chart(profile_dir)
    if launch:
        subprocess.Popen([str(terminal_exe)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(8.0)
    account_after = _read_account_state(terminal_exe)
    startup_tail = _read_tail(files_dir / "A1_DAILY_PROFIT_FLOOR_GUARDIAN_STARTUP.csv")
    event_tail = _read_tail(files_dir / "A1_DAILY_PROFIT_FLOOR_GUARDIAN_EVENTS.csv")
    state_tail = _read_tail(files_dir / "A1_DAILY_PROFIT_FLOOR_GUARDIAN_STATE.txt")
    checks = _build_checks(compile_log, startup_tail, account_before, account_after, chart_path, backup_dir)
    status = "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL"
    payload: dict[str, Any] = {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": (
            "Owner-authorized A1 live-demo close-only daily +100 AED profit-floor guardian. "
            "Demo only; no canonical Phase 2/3 change; no live/real capital."
        ),
        "boundaries": {
            "account": f"{ACCOUNT_LOGIN} / {SERVER}",
            "a2_touched": False,
            "a3_touched": False,
            "entry_eas_edited": False,
            "opens_trades": False,
            "close_only": True,
            "daily_loss_stop_enabled": False,
        },
        "terminal": {
            "terminal_exe": str(terminal_exe),
            "terminal_data_dir": str(terminal_data_dir),
            "profile": "Default",
            "profile_backup_dir": str(backup_dir),
            "terminal_closed_before_profile_append": terminal_closed,
            "terminal_relaunched": launch,
        },
        "guardian": {
            "ea_name": EA_NAME,
            "chart": str(chart_path),
            "chart_symbol": CHART_SYMBOL,
            "source_deployed": str(deployed_source),
            "compile_log": str(compile_log),
            "local_armed_preset": str(local_preset),
            "committed_defaults_non_executing": True,
            "runtime_dry_run": False,
            "runtime_close_action_allowed": True,
            "daily_floor_aed": 100.0,
            "daily_loss_stop_enabled": False,
            "entry_halt_file": str(files_dir / "experimental_demo_kill_switch.txt"),
            "state_file": str(files_dir / "A1_DAILY_PROFIT_FLOOR_GUARDIAN_STATE.txt"),
            "event_log": str(files_dir / "A1_DAILY_PROFIT_FLOOR_GUARDIAN_EVENTS.csv"),
            "daily_summary_log": str(files_dir / "A1_DAILY_PROFIT_FLOOR_GUARDIAN_DAILY_SUMMARY.csv"),
            "startup_log": str(files_dir / "A1_DAILY_PROFIT_FLOOR_GUARDIAN_STARTUP.csv"),
        },
        "entry_halt_verification": {
            "entry_ea_kill_file": "experimental_demo_kill_switch.txt",
            "verified_entry_time_guard": (
                "Phase2ExperimentalDemoExecutor checks KillSwitchActive() inside TradingGuardsPass() "
                "before sending orders, so the halt file blocks future entries without editing entry EAs."
            ),
            "keep_flat_backstop": True,
        },
        "account_before": account_before,
        "account_after": account_after,
        "checks": checks,
        "startup_tail": startup_tail,
        "event_tail": event_tail,
        "state_tail": state_tail,
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return payload


def _validate_account(account: dict[str, Any]) -> None:
    if str(account.get("login")) != ACCOUNT_LOGIN:
        raise RuntimeError(f"A1 account mismatch: {account}")
    if str(account.get("server")) != SERVER:
        raise RuntimeError(f"A1 server mismatch: {account}")
    if not account.get("trade_allowed"):
        raise RuntimeError(f"A1 trade_allowed is false: {account}")


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


def _deploy_source(phase1_root: Path, terminal_data_dir: Path) -> Path:
    source = phase1_root / "mt5" / "Experts" / f"{EA_NAME}.mq5"
    target = terminal_data_dir / "MQL5" / "Experts" / f"{EA_NAME}.mq5"
    if not source.exists():
        raise FileNotFoundError(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def _write_local_armed_preset(terminal_data_dir: Path) -> Path:
    preset = terminal_data_dir / "MQL5" / "Presets" / LOCAL_PRESET_NAME
    preset.parent.mkdir(parents=True, exist_ok=True)
    preset.write_text(
        "\n".join(
            [
                "InpRunId=A1_DAILY_PROFIT_FLOOR_GUARDIAN_V1_ARMED_20260618",
                "InpDryRunOnly=false",
                "InpCloseActionAllowed=true",
                "InpAllowedAccountLogin=1025742",
                "InpExpectedServerMarker=Demo",
                f"InpOwnerAuthorizationToken={OWNER_TOKEN}",
                f"InpRequiredOwnerAuthorizationToken={OWNER_TOKEN}",
                "InpDailyFloorAed=100.0",
                "InpHaltEntriesWhenArmed=true",
                "InpDailyLossStopEnabled=false",
                "InpDailyLossStopAed=-150.0",
                "InpDubaiUtcOffsetMinutes=240",
                "InpTimerSeconds=2",
                "InpDeviationPoints=100",
                "InpGuardianMagic=919100",
                "InpGuardianKillSwitchFileName=A1_DAILY_PROFIT_FLOOR_GUARDIAN_KILL.txt",
                "InpEntryHaltFileName=experimental_demo_kill_switch.txt",
                "InpStateFileName=A1_DAILY_PROFIT_FLOOR_GUARDIAN_STATE.txt",
                "InpEventLogFileName=A1_DAILY_PROFIT_FLOOR_GUARDIAN_EVENTS.csv",
                "InpDailySummaryFileName=A1_DAILY_PROFIT_FLOOR_GUARDIAN_DAILY_SUMMARY.csv",
                "InpStartupLogFileName=A1_DAILY_PROFIT_FLOOR_GUARDIAN_STARTUP.csv",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return preset


def _compile_ea(metaeditor_exe: Path, terminal_data_dir: Path) -> Path:
    # MetaEditor CLI can truncate /compile paths that contain spaces on this
    # Windows setup, so compile from a scratch folder and copy the EX5/log back.
    scratch_root = Path("C:/MT5CompileScratchA1ProfitFloorGuardian")
    scratch_experts = scratch_root / "MQL5" / "Experts"
    scratch_experts.mkdir(parents=True, exist_ok=True)
    scratch_source = scratch_experts / f"{EA_NAME}.mq5"
    shutil.copy2(terminal_data_dir / "MQL5" / "Experts" / f"{EA_NAME}.mq5", scratch_source)
    scratch_log = scratch_root / f"compile_{EA_NAME}_20260618.log"
    if scratch_log.exists():
        scratch_log.unlink()
    subprocess.run(
        [str(metaeditor_exe), f"/compile:{scratch_source}", f"/log:{scratch_log}"],
        text=True,
        capture_output=True,
        timeout=90,
    )
    scratch_ex5 = scratch_experts / f"{EA_NAME}.ex5"
    if not scratch_ex5.exists():
        raise RuntimeError(f"MetaEditor did not produce EX5. Log:\n{_read_text(scratch_log)}")
    target_ex5 = terminal_data_dir / "MQL5" / "Experts" / f"{EA_NAME}.ex5"
    shutil.copy2(scratch_ex5, target_ex5)
    log = terminal_data_dir / "MQL5" / "Logs" / "compile_Account1DailyProfitFloorGuardian_20260618.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(scratch_log, log)
    text = _read_text(log)
    if "0 errors, 0 warnings" not in text:
        raise RuntimeError(f"Guardian compile failed:\n{text[-4000:]}")
    return log


def _ensure_no_existing_guardian_chart(profile_dir: Path) -> None:
    for chart in sorted(profile_dir.glob("chart*.chr")):
        text = _read_text(chart)
        if f"name={EA_NAME}" in text:
            raise RuntimeError(f"Existing {EA_NAME} chart already exists: {chart}")


def _close_terminal(terminal_exe: Path) -> bool:
    ps = (
        "Get-Process terminal64 -ErrorAction SilentlyContinue | "
        f"Where-Object {{ $_.Path -eq '{terminal_exe}' }} | "
        "ForEach-Object { $_.CloseMainWindow() | Out-Null }"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], text=True, capture_output=True, timeout=20)
    time.sleep(5.0)
    ps_check = (
        "Get-Process terminal64 -ErrorAction SilentlyContinue | "
        f"Where-Object {{ $_.Path -eq '{terminal_exe}' }} | "
        "Select-Object -ExpandProperty Id"
    )
    result = subprocess.run(["powershell", "-NoProfile", "-Command", ps_check], text=True, capture_output=True, timeout=20)
    ids = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if ids:
        subprocess.run(["powershell", "-NoProfile", "-Command", f"Stop-Process -Id {','.join(ids)} -Force"], timeout=20)
        time.sleep(1.0)
    return True


def _backup_profile(profile_dir: Path, terminal_data_dir: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup = terminal_data_dir / "_codex_quarantine" / "profile_backups" / f"default_profile_before_a1_profit_floor_guardian_{stamp}"
    shutil.copytree(profile_dir, backup)
    return backup


def _append_chart(profile_dir: Path) -> Path:
    existing = sorted(profile_dir.glob("chart*.chr"))
    next_id = 1
    if existing:
        next_id = max(int(path.stem.replace("chart", "")) for path in existing if path.stem.replace("chart", "").isdigit()) + 1
    chart = profile_dir / f"chart{next_id:02d}.chr"
    chart.write_text(_chart_text(), encoding="utf-16")
    return chart


def _chart_text() -> str:
    return f"""<chart>
id={int(time.time())}26
symbol={CHART_SYMBOL}
description={CHART_SYMBOL}
period_type=0
period_size=5
digits=2
tick_size=0.01
scale_fix=0
scale_fixed_min=0.000000
scale_fixed_max=0.000000
scale=3
mode=1
fore=0
grid=0
volume=0
scroll=1
shift=1
ohlc=0
one_click=0
one_click_btn=0
askline=1
days=0
window_left=40
window_top=340
window_right=980
window_bottom=920
windows_total=1

<expert>
name={EA_NAME}
path=Experts\\{EA_NAME}.ex5
expertmode=1
<inputs>
InpRunId=A1_DAILY_PROFIT_FLOOR_GUARDIAN_V1_ARMED_20260618
InpDryRunOnly=false
InpCloseActionAllowed=true
InpAllowedAccountLogin=1025742
InpExpectedServerMarker=Demo
InpOwnerAuthorizationToken={OWNER_TOKEN}
InpRequiredOwnerAuthorizationToken={OWNER_TOKEN}
InpDailyFloorAed=100.0
InpHaltEntriesWhenArmed=true
InpDailyLossStopEnabled=false
InpDailyLossStopAed=-150.0
InpDubaiUtcOffsetMinutes=240
InpTimerSeconds=2
InpDeviationPoints=100
InpGuardianMagic=919100
InpGuardianKillSwitchFileName=A1_DAILY_PROFIT_FLOOR_GUARDIAN_KILL.txt
InpEntryHaltFileName=experimental_demo_kill_switch.txt
InpStateFileName=A1_DAILY_PROFIT_FLOOR_GUARDIAN_STATE.txt
InpEventLogFileName=A1_DAILY_PROFIT_FLOOR_GUARDIAN_EVENTS.csv
InpDailySummaryFileName=A1_DAILY_PROFIT_FLOOR_GUARDIAN_DAILY_SUMMARY.csv
InpStartupLogFileName=A1_DAILY_PROFIT_FLOOR_GUARDIAN_STARTUP.csv
</inputs>
</expert>

<window>
height=100.000000
objects=0
<indicator>
name=Main
path=
apply=1
</indicator>
</window>
</chart>
"""


def _build_checks(
    compile_log: Path,
    startup_tail: list[str],
    account_before: dict[str, Any],
    account_after: dict[str, Any],
    chart_path: Path,
    backup_dir: Path,
) -> list[dict[str, str]]:
    startup_text = "\n".join(startup_tail)
    return [
        _check("a1_account_login", str(account_before.get("login")) == ACCOUNT_LOGIN, str(account_before)),
        _check("profile_backup_created", backup_dir.exists(), str(backup_dir)),
        _check("chart_appended", chart_path.exists(), str(chart_path)),
        _check("compile_0_errors_0_warnings", "0 errors, 0 warnings" in _read_compile_text(compile_log), str(compile_log)),
        _check("startup_log_attached", "ATTACHED_A1_DAILY_PROFIT_FLOOR_GUARDIAN" in startup_text, startup_text[-500:]),
        _check("guardian_does_not_open_on_attach", account_after.get("positions_total", 0) <= account_before.get("positions_total", 0), f"before={account_before}; after={account_after}"),
    ]


def _check(name: str, passed: bool, evidence: str) -> dict[str, str]:
    return {"name": name, "status": "PASS" if passed else "FAIL", "evidence": evidence}


def _read_compile_text(path: Path) -> str:
    if not path.exists():
        return ""
    data = path.read_bytes()
    for encoding in ("utf-16", "utf-8", "cp1252"):
        try:
            return data.decode(encoding, errors="ignore")
        except UnicodeError:
            continue
    return data.decode(errors="ignore")


def _read_tail(path: Path, lines: int = 10) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8", errors="ignore").splitlines()[-lines:]


def _read_text(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-16", "utf-8", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeError:
            continue
    return data.decode(errors="ignore")


def _venv_python() -> Path:
    return Path(__file__).resolve().parents[2] / "xauusd-phase0" / ".venv" / "Scripts" / "python.exe"


def _render_markdown(payload: dict[str, Any]) -> str:
    checks = "\n".join(
        f"| {row['name']} | `{row['status']}` | {row['evidence']} |" for row in payload["checks"]
    )
    startup = "\n".join(payload["startup_tail"][-5:]) or "No startup rows found."
    events = "\n".join(payload["event_tail"][-5:]) or "No event rows found."
    state = "\n".join(payload["state_tail"][-20:]) or "No state rows found."
    return "\n".join(
        [
            "# A1 Daily Profit-Floor Guardian Attachment - 2026-06-18",
            "",
            f"Status: `{payload['status']}`",
            "",
            payload["authority"],
            "",
            "## Boundary",
            "",
            f"- Account: `{payload['boundaries']['account']}`",
            f"- A2 touched: `{str(payload['boundaries']['a2_touched']).lower()}`",
            f"- A3 touched: `{str(payload['boundaries']['a3_touched']).lower()}`",
            f"- Entry EAs edited: `{str(payload['boundaries']['entry_eas_edited']).lower()}`",
            f"- Opens trades: `{str(payload['boundaries']['opens_trades']).lower()}`",
            f"- Close-only broker action: `{str(payload['boundaries']['close_only']).lower()}`",
            f"- Daily loss stop enabled: `{str(payload['boundaries']['daily_loss_stop_enabled']).lower()}`",
            "",
            "## Runtime",
            "",
            f"- EA: `{payload['guardian']['ea_name']}`",
            f"- Chart: `{payload['guardian']['chart']}`",
            f"- Source deployed: `{payload['guardian']['source_deployed']}`",
            f"- Compile log: `{payload['guardian']['compile_log']}`",
            f"- Local armed preset: `{payload['guardian']['local_armed_preset']}`",
            f"- Runtime dry-run: `{str(payload['guardian']['runtime_dry_run']).lower()}`",
            f"- Runtime close action allowed: `{str(payload['guardian']['runtime_close_action_allowed']).lower()}`",
            f"- Daily floor: `{payload['guardian']['daily_floor_aed']:.2f} AED`",
            f"- Entry halt file: `{payload['guardian']['entry_halt_file']}`",
            "",
            "## Entry-Halt Verification",
            "",
            payload["entry_halt_verification"]["verified_entry_time_guard"],
            "",
            "## Checks",
            "",
            "| Check | Status | Evidence |",
            "|---|---|---|",
            checks,
            "",
            "## Startup Tail",
            "",
            "```text",
            startup,
            "```",
            "",
            "## Event Tail",
            "",
            "```text",
            events,
            "```",
            "",
            "## State Tail",
            "",
            "```text",
            state,
            "```",
            "",
            "## Owner-Acknowledged Expectations",
            "",
            "- This caps bleed; it does not make A1 profitable by itself.",
            "- The fixed +100 AED floor can clip recovery days.",
            "- A trigger closes protected breakout-core positions too.",
            "- Locked result is approximately +100 AED minus closing slippage.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Attach the owner-authorized A1 daily profit-floor guardian.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--terminal-data-dir", type=Path, default=DEFAULT_TERMINAL_DATA_DIR)
    parser.add_argument("--terminal-exe", type=Path, default=DEFAULT_TERMINAL_EXE)
    parser.add_argument("--metaeditor-exe", type=Path, default=DEFAULT_METAEDITOR_EXE)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--no-launch", action="store_true")
    args = parser.parse_args()
    payload = attach_a1_daily_profit_floor_guardian(
        args.phase1_root,
        args.terminal_data_dir,
        args.terminal_exe,
        args.metaeditor_exe,
        args.output_json,
        launch=not args.no_launch,
    )
    print(payload["status"])
    print(payload["guardian"]["chart"])
    print(payload["guardian"]["compile_log"])
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
