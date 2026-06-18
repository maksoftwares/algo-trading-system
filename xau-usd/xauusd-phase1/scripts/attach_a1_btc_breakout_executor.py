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
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "A1_BTC_BREAKOUT_EXECUTOR_ATTACHMENT_2026_06_18.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "A1_BTC_BREAKOUT_EXECUTOR_ATTACHMENT_2026_06_18.md"

EA_NAME = "Phase2ExperimentalDemoExecutor"
EA_SOURCE = Path("mt5") / "Experts" / f"{EA_NAME}.mq5"
RUN_ID = "phase2-a1-btc-breakout-experiment-v0.1"
CANDIDATE = "breakout_retest"
SYMBOL = "BTCUSD"
ACCOUNT_LOGIN = "1025742"
SERVER = "Capital.ComMena-Demo"
MAGIC = 920105
REQUIRED_EXPERIMENTAL_AUTHORIZATION_TOKEN = "EXPERIMENTAL_DEMO_AUTHORIZED_REVIEW_ONLY"
REQUIRED_COST_SUSPENSION_ACKNOWLEDGEMENT_TOKEN = "I_ACKNOWLEDGE_COST_SUSPENDED_NON_CANONICAL_EXPERIMENT"


def attach_a1_btc_breakout_executor(
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
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_OUTPUT_JSON.name else phase1_root / DEFAULT_OUTPUT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    profile_dir = terminal_data_dir / "MQL5" / "Profiles" / "Charts" / "Default"
    if not profile_dir.exists():
        raise FileNotFoundError(f"Default profile not found: {profile_dir}")

    inherited_inputs = _read_existing_executor_inputs(profile_dir)
    allowed_accounts = inherited_inputs.get("InpAllowedAccountLoginsCsv", "")
    auth_token = inherited_inputs.get("InpExperimentalAuthorizationToken", "")
    cost_ack = inherited_inputs.get("InpCostSuspensionAcknowledgementToken", "")
    _validate_inherited_inputs(allowed_accounts, auth_token, cost_ack)

    symbol_info = _read_symbol_info(terminal_exe, SYMBOL)
    _ensure_no_existing_btc_chart(profile_dir)
    _ensure_no_btc_magic_exposure(terminal_exe)
    deployed_sources = _deploy_sources(phase1_root, terminal_data_dir)
    compile_log = _compile_ea(metaeditor_exe, terminal_data_dir)
    terminal_closed = _close_terminal(terminal_exe)
    backup_dir = _backup_profile(profile_dir, terminal_data_dir)
    chart_path = _append_chart(
        profile_dir,
        allowed_accounts=allowed_accounts,
        auth_token=auth_token,
        cost_ack=cost_ack,
    )
    if launch:
        subprocess.Popen([str(terminal_exe)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(7.0)

    startup = _read_startup_tail(terminal_data_dir)
    payload: dict[str, Any] = {
        "status": "A1_BTC_BREAKOUT_EXECUTOR_APPENDED",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": (
            "Owner-requested A1 demo-only BTCUSD breakout experiment. This is not a canonical Phase 2 "
            "approval, not live trading, and not real capital."
        ),
        "terminal": {
            "terminal_exe": str(terminal_exe),
            "terminal_data_dir": str(terminal_data_dir),
            "profile": "Default",
            "profile_backup_dir": str(backup_dir),
            "terminal_closed_before_profile_append": terminal_closed,
            "terminal_relaunched": launch,
        },
        "ea": {
            "name": EA_NAME,
            "run_id": RUN_ID,
            "candidate": CANDIDATE,
            "symbol": SYMBOL,
            "magic": MAGIC,
            "fixed_lot": 0.01,
            "dry_run_only": False,
            "broker_action_allowed": True,
            "demo_account_login": ACCOUNT_LOGIN,
            "demo_server": SERVER,
            "deployed_sources": [str(path) for path in deployed_sources],
            "compile_log": str(compile_log),
            "startup_log_file": "experimental_demo_executor_startup_v02_breakout_retest_btcusd.csv",
            "signal_log_file": "experimental_demo_executor_signal_log_v02_breakout_retest_btcusd.csv",
            "order_log_file": "experimental_demo_executor_order_log_v02_breakout_retest_btcusd.csv",
        },
        "symbol_info": symbol_info,
        "profile_changes": {
            "existing_profile_preserved": True,
            "appended_chart": str(chart_path),
            "existing_charts_removed": 0,
        },
        "startup_tail": startup,
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return payload


def _validate_inherited_inputs(allowed_accounts: str, auth_token: str, cost_ack: str) -> None:
    if ACCOUNT_LOGIN not in {item.strip() for item in allowed_accounts.split(",") if item.strip()}:
        raise RuntimeError(f"A1 account {ACCOUNT_LOGIN} is not present in inherited InpAllowedAccountLoginsCsv.")
    if auth_token != REQUIRED_EXPERIMENTAL_AUTHORIZATION_TOKEN:
        raise RuntimeError("Inherited experimental authorization token is missing or invalid.")
    if cost_ack != REQUIRED_COST_SUSPENSION_ACKNOWLEDGEMENT_TOKEN:
        raise RuntimeError("Inherited cost-suspension acknowledgement token is missing or invalid.")


def _read_existing_executor_inputs(profile_dir: Path) -> dict[str, str]:
    for chart in sorted(profile_dir.glob("chart*.chr")):
        text = _read_chart_text(chart)
        if f"name={EA_NAME}" not in text:
            continue
        values: dict[str, str] = {}
        for raw in text.splitlines():
            if raw.startswith("Inp") and "=" in raw:
                key, value = raw.split("=", 1)
                values[key] = value
        return values
    raise RuntimeError("No existing Phase2ExperimentalDemoExecutor chart found to inherit A1 tokens from.")


def _read_symbol_info(terminal_exe: Path, symbol: str) -> dict[str, Any]:
    script = f"""
import json
import MetaTrader5 as mt5
if not mt5.initialize(path=r'{terminal_exe}'):
    raise SystemExit(json.dumps({{'status':'INIT_FAILED','last_error':str(mt5.last_error())}}))
try:
    account = mt5.account_info()
    info = mt5.symbol_info('{symbol}')
    if info is None:
        print(json.dumps({{'status':'SYMBOL_MISSING','symbol':'{symbol}'}}))
    else:
        mt5.symbol_select('{symbol}', True)
        tick = mt5.symbol_info_tick('{symbol}')
        print(json.dumps({{
            'status':'SYMBOL_AVAILABLE',
            'account_login': getattr(account, 'login', None),
            'account_server': getattr(account, 'server', None),
            'symbol': info.name,
            'trade_mode': info.trade_mode,
            'digits': info.digits,
            'point': info.point,
            'volume_min': info.volume_min,
            'volume_step': info.volume_step,
            'visible_after_select': bool(mt5.symbol_info('{symbol}').visible),
            'tick_present': tick is not None,
            'bid': getattr(tick, 'bid', None) if tick else None,
            'ask': getattr(tick, 'ask', None) if tick else None,
        }}))
finally:
    mt5.shutdown()
"""
    result = subprocess.run(
        [str(_venv_python()), "-c", script],
        text=True,
        capture_output=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"MT5 symbol query failed: {result.stdout}\n{result.stderr}")
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    if payload.get("status") != "SYMBOL_AVAILABLE":
        raise RuntimeError(f"BTC symbol is not available: {payload}")
    if str(payload.get("account_login")) != ACCOUNT_LOGIN:
        raise RuntimeError(f"MT5 account mismatch: {payload}")
    if payload.get("account_server") != SERVER:
        raise RuntimeError(f"MT5 server mismatch: {payload}")
    if not payload.get("tick_present"):
        raise RuntimeError(f"BTC symbol has no tick yet: {payload}")
    return payload


def _ensure_no_existing_btc_chart(profile_dir: Path) -> None:
    for chart in sorted(profile_dir.glob("chart*.chr")):
        text = _read_chart_text(chart)
        if f"name={EA_NAME}" in text and f"InpTargetSymbol={SYMBOL}" in text and f"InpCandidate={CANDIDATE}" in text:
            raise RuntimeError(f"Existing BTC breakout executor chart already exists: {chart}")


def _ensure_no_btc_magic_exposure(terminal_exe: Path) -> None:
    script = f"""
import json
import MetaTrader5 as mt5
if not mt5.initialize(path=r'{terminal_exe}'):
    raise SystemExit(json.dumps({{'status':'INIT_FAILED','last_error':str(mt5.last_error())}}))
try:
    positions = [p._asdict() for p in (mt5.positions_get() or []) if getattr(p, 'magic', 0) == {MAGIC}]
    orders = [o._asdict() for o in (mt5.orders_get() or []) if getattr(o, 'magic', 0) == {MAGIC}]
    print(json.dumps({{'positions': len(positions), 'orders': len(orders)}}))
finally:
    mt5.shutdown()
"""
    result = subprocess.run([str(_venv_python()), "-c", script], text=True, capture_output=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"MT5 exposure query failed: {result.stdout}\n{result.stderr}")
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    if payload["positions"] or payload["orders"]:
        raise RuntimeError(f"Magic {MAGIC} already has exposure: {payload}")


def _deploy_sources(phase1_root: Path, terminal_data_dir: Path) -> list[Path]:
    mql5_root = terminal_data_dir / "MQL5"
    experts_dir = mql5_root / "Experts"
    include_phase1_dir = mql5_root / "Include" / "Phase1"
    experts_dir.mkdir(parents=True, exist_ok=True)
    include_phase1_dir.mkdir(parents=True, exist_ok=True)
    deployed: list[Path] = []
    copies = [
        (phase1_root / EA_SOURCE, experts_dir / f"{EA_NAME}.mq5"),
        (phase1_root / "mt5" / "Include" / "Phase1" / "Phase1Types.mqh", include_phase1_dir / "Phase1Types.mqh"),
        (phase1_root / "mt5" / "Include" / "Phase1" / "Phase1BreakoutRetest.mqh", include_phase1_dir / "Phase1BreakoutRetest.mqh"),
        (phase1_root / "mt5" / "Include" / "DirectionStateShadow.mqh", mql5_root / "Include" / "DirectionStateShadow.mqh"),
    ]
    for source, target in copies:
        if not source.exists():
            raise FileNotFoundError(f"Missing source: {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        deployed.append(target)
    return deployed


def _compile_ea(metaeditor_exe: Path, terminal_data_dir: Path) -> Path:
    scratch_root = Path("C:/MT5CompileScratchA1BTC")
    scratch_mql5 = scratch_root / "MQL5"
    scratch_experts = scratch_mql5 / "Experts"
    scratch_include_phase1 = scratch_mql5 / "Include" / "Phase1"
    scratch_include = scratch_mql5 / "Include"
    scratch_experts.mkdir(parents=True, exist_ok=True)
    scratch_include_phase1.mkdir(parents=True, exist_ok=True)
    shutil.copy2(terminal_data_dir / "MQL5" / "Experts" / f"{EA_NAME}.mq5", scratch_experts / f"{EA_NAME}.mq5")
    for include_name in ("Phase1Types.mqh", "Phase1BreakoutRetest.mqh"):
        shutil.copy2(terminal_data_dir / "MQL5" / "Include" / "Phase1" / include_name, scratch_include_phase1 / include_name)
    shutil.copy2(terminal_data_dir / "MQL5" / "Include" / "DirectionStateShadow.mqh", scratch_include / "DirectionStateShadow.mqh")
    scratch_log = scratch_root / f"compile_{EA_NAME}_a1_btc.log"
    if scratch_log.exists():
        scratch_log.unlink()
    subprocess.run([str(metaeditor_exe), f"/compile:{scratch_experts / (EA_NAME + '.mq5')}", f"/log:{scratch_log}"], check=False, timeout=90)
    scratch_ex5 = scratch_experts / f"{EA_NAME}.ex5"
    if not scratch_ex5.exists():
        raise RuntimeError(f"MetaEditor did not produce EX5. Log:\n{_read_text(scratch_log)}")
    target_ex5 = terminal_data_dir / "MQL5" / "Experts" / f"{EA_NAME}.ex5"
    shutil.copy2(scratch_ex5, target_ex5)
    log_path = terminal_data_dir / "MQL5" / "Logs" / f"compile_{EA_NAME}_a1_btc.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(scratch_log, log_path)
    log_text = _read_text(scratch_log)
    if "error(s)" in log_text.lower() and "0 error(s)" not in log_text.lower():
        raise RuntimeError(f"MetaEditor compile reported errors:\n{log_text}")
    return log_path


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
    backup_dir = terminal_data_dir / "_codex_quarantine" / "profile_backups" / f"default_profile_before_a1_btc_breakout_append_{stamp}"
    shutil.copytree(profile_dir, backup_dir)
    return backup_dir


def _append_chart(profile_dir: Path, *, allowed_accounts: str, auth_token: str, cost_ack: str) -> Path:
    index = _next_chart_index(profile_dir)
    chart = profile_dir / f"chart{index:02d}.chr"
    chart.write_text(
        _render_chart(index, allowed_accounts=allowed_accounts, auth_token=auth_token, cost_ack=cost_ack),
        encoding="utf-8",
    )
    return chart


def _next_chart_index(profile_dir: Path) -> int:
    indexes: list[int] = []
    for chart in profile_dir.glob("chart*.chr"):
        match = re.fullmatch(r"chart(\d+)\.chr", chart.name)
        if match:
            indexes.append(int(match.group(1)))
    return max(indexes, default=0) + 1


def _render_chart(index: int, *, allowed_accounts: str, auth_token: str, cost_ack: str) -> str:
    left = 20 + ((index - 1) % 3) * 42
    top = 20 + ((index - 1) // 3) * 35
    right = left + 980
    bottom = top + 720
    return "\n".join(
        [
            "<chart>",
            f"id={int(time.time())}{index:04d}",
            f"symbol={SYMBOL}",
            f"description={SYMBOL}",
            "period_type=0",
            "period_size=5",
            "digits=2",
            "tick_size=0.01",
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
            f"InpRunId={RUN_ID}",
            "InpDryRunOnly=false",
            "InpBrokerActionAllowed=true",
            f"InpCandidate={CANDIDATE}",
            "InpCandidateStatus=BTC_EXPERIMENTAL_DEMO_REVIEW_ONLY",
            "InpFamilyLifecycleStatus=COST_SUSPENDED_CANONICAL",
            f"InpTargetSymbol={SYMBOL}",
            f"InpQualifiedSymbolsCsv={SYMBOL}",
            "InpExpectedServerMarker=Demo",
            f"InpAllowedAccountLoginsCsv={allowed_accounts}",
            f"InpExperimentalAuthorizationToken={auth_token}",
            f"InpRequiredExperimentalAuthorizationToken={REQUIRED_EXPERIMENTAL_AUTHORIZATION_TOKEN}",
            f"InpCostSuspensionAcknowledgementToken={cost_ack}",
            f"InpRequiredCostSuspensionAcknowledgementToken={REQUIRED_COST_SUSPENSION_ACKNOWLEDGEMENT_TOKEN}",
            f"InpAuthorizedCandidatesCsv={CANDIDATE}",
            "InpAttachmentLogFileName=experimental_demo_executor_signal_log_v02_breakout_retest_btcusd.csv",
            "InpStartupLogFileName=experimental_demo_executor_startup_v02_breakout_retest_btcusd.csv",
            "InpOrderLogFileName=experimental_demo_executor_order_log_v02_breakout_retest_btcusd.csv",
            "InpDirectionStateFileName=dirstate_btcusd.csv",
            "InpKillSwitchFileName=experimental_demo_kill_switch.txt",
            "InpFixedLot=0.01",
            "InpEURUSDFixedLot=0.01",
            "InpGBPUSDFixedLot=0.01",
            "InpMaxOrdersPerDay=0",
            "InpMaxAccountOrdersPerDay=0",
            "InpMinSecondsBetweenOrders=0",
            "InpMaxOpenPositionsPerInstance=0",
            "InpDeviationPoints=100",
            "InpMaxEstimatedCostR=0.00",
            "InpMaxMeasuredSpreadPoints=0.0",
            "InpTradeSessionGateEnabled=false",
            "InpTradeSessionStartHour=0",
            "InpTradeSessionEndHour=23",
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


def _read_startup_tail(terminal_data_dir: Path) -> list[str]:
    path = terminal_data_dir / "MQL5" / "Files" / "experimental_demo_executor_startup_v02_breakout_retest_btcusd.csv"
    for _ in range(12):
        if path.exists():
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            return lines[-3:]
        time.sleep(2.5)
    return []


def _read_chart_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-16", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeError:
            continue
    return path.read_text(errors="replace")


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    for encoding in ("utf-16", "utf-8", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeError:
            continue
    return path.read_text(errors="replace")


def _venv_python() -> Path:
    return Path(__file__).resolve().parents[1] / ".." / "xauusd-phase0" / ".venv" / "Scripts" / "python.exe"


def _render_markdown(payload: dict[str, Any]) -> str:
    startup_tail = payload.get("startup_tail") or []
    lines = [
        "# A1 BTC Breakout Executor Attachment - 2026-06-18",
        "",
        f"Status: `{payload['status']}`",
        "",
        payload["authority"],
        "",
        "## Attachment",
        "",
        f"- Account: `{ACCOUNT_LOGIN} / {SERVER}`",
        f"- Symbol: `{SYMBOL}`",
        f"- Candidate: `{CANDIDATE}`",
        f"- Magic: `{MAGIC}`",
        f"- Lot: `0.01`",
        f"- Chart: `{payload['profile_changes']['appended_chart']}`",
        f"- Profile backup: `{payload['terminal']['profile_backup_dir']}`",
        f"- Compile log: `{payload['ea']['compile_log']}`",
        "",
        "## Boundary",
        "",
        "- Demo only.",
        "- Not canonical Phase 2.",
        "- Not live trading.",
        "- BTC has no approved Phase 0 edge; this is an owner-requested experiment.",
        "- Existing charts were preserved; this script appended one BTCUSD chart only.",
        "",
        "## Symbol Check",
        "",
        f"- Broker symbol status: `{payload['symbol_info']['status']}`",
        f"- Visible after select: `{payload['symbol_info']['visible_after_select']}`",
        f"- Tick present: `{payload['symbol_info']['tick_present']}`",
        f"- Volume min/step: `{payload['symbol_info']['volume_min']}` / `{payload['symbol_info']['volume_step']}`",
        "",
        "## Startup Tail",
        "",
    ]
    if startup_tail:
        lines.extend(f"- `{line}`" for line in startup_tail)
    else:
        lines.append("- `PENDING_STARTUP_LOG_NOT_SEEN_YET`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Append A1 BTCUSD breakout executor chart to the standard demo terminal.")
    parser.add_argument("--phase1-root", type=Path, default=Path("."))
    parser.add_argument("--terminal-data-dir", type=Path, default=DEFAULT_TERMINAL_DATA_DIR)
    parser.add_argument("--terminal-exe", type=Path, default=DEFAULT_TERMINAL_EXE)
    parser.add_argument("--metaeditor-exe", type=Path, default=DEFAULT_METAEDITOR_EXE)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--no-launch", action="store_true")
    args = parser.parse_args()
    payload = attach_a1_btc_breakout_executor(
        phase1_root=args.phase1_root,
        terminal_data_dir=args.terminal_data_dir,
        terminal_exe=args.terminal_exe,
        metaeditor_exe=args.metaeditor_exe,
        output_json=args.output_json,
        launch=not args.no_launch,
    )
    print(payload["status"])
    print(payload["profile_changes"]["appended_chart"])
    print(payload["ea"]["compile_log"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
