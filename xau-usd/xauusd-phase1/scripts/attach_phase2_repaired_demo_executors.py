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


DEFAULT_TERMINAL_DATA_DIR = Path(
    "C:/Users/ZHAO ZHU INFORMATION/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075"
)
DEFAULT_TERMINAL_EXE = Path("C:/Program Files/MetaTrader 5/terminal64.exe")
DEFAULT_METAEDITOR_EXE = Path("C:/Program Files/MetaTrader 5/MetaEditor64.exe")
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "PHASE2_REPAIRED_DEMO_EXECUTOR_ATTACHMENTS.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "PHASE2_REPAIRED_DEMO_EXECUTOR_ATTACHMENTS.md"

EA_NAME = "Phase2ExperimentalDemoRepairExecutor"
EA_SOURCE = Path("mt5") / "Experts" / f"{EA_NAME}.mq5"
RUN_ID = "phase2-demo-repair-executor-v1"
REQUIRED_EXPERIMENTAL_AUTHORIZATION_TOKEN = "EXPERIMENTAL_DEMO_AUTHORIZED_REVIEW_ONLY"
REQUIRED_COST_SUSPENSION_ACKNOWLEDGEMENT_TOKEN = "I_ACKNOWLEDGE_COST_SUSPENDED_NON_CANONICAL_EXPERIMENT"
EXECUTOR_CANDIDATE_STATUS = "REPAIRED_EXPERIMENTAL_DEMO_V1"
FAMILY_LIFECYCLE_STATUS = "COST_SUSPENDED_CANONICAL"
DEFAULT_AUTHORIZED_CANDIDATES_CSV = "symbol_normalized_round_retest_v0_repair_v1,session_extreme_retest_v0_repair_v1"


@dataclass(frozen=True)
class RepairAttachment:
    candidate: str
    symbol: str
    fixed_lot: float
    qualification_source: str
    active_filter: str


@dataclass(frozen=True)
class AttachOutput:
    status: str
    json_path: Path
    markdown_path: Path
    attachment_count: int


def build_attachment_plan() -> list[RepairAttachment]:
    return [
        RepairAttachment(
            candidate="symbol_normalized_round_retest_v0_repair_v1",
            symbol="XAUUSD",
            fixed_lot=0.01,
            qualification_source="PHASE2_REPAIR_CANDIDATE_RULES.csv:PREFERRED_CLUSTER",
            active_filter="XAUUSD Evening 16:00-19:59 SHORT only",
        ),
        RepairAttachment(
            candidate="session_extreme_retest_v0_repair_v1",
            symbol="XAUUSD",
            fixed_lot=0.01,
            qualification_source="PHASE2_REPAIR_CANDIDATE_RULES.csv:PREFERRED_CLUSTER",
            active_filter="XAUUSD Afternoon 12:00-15:59 or Evening 16:00-19:59 SHORT only",
        ),
        RepairAttachment(
            candidate="session_extreme_retest_v0_repair_v1",
            symbol="EURUSD",
            fixed_lot=0.05,
            qualification_source="PHASE2_REPAIR_CANDIDATE_RULES.csv:PREFERRED_CLUSTER",
            active_filter="EURUSD Night 20:00-05:59 SHORT only",
        ),
    ]


def attach_phase2_repaired_demo_executors(
    phase1_root: Path,
    terminal_data_dir: Path = DEFAULT_TERMINAL_DATA_DIR,
    terminal_exe: Path = DEFAULT_TERMINAL_EXE,
    metaeditor_exe: Path = DEFAULT_METAEDITOR_EXE,
    output_json: Path | None = None,
    launch: bool = True,
    allowed_account_logins_csv: str = "",
    experimental_authorization_token: str = "",
    cost_suspension_acknowledgement_token: str = "",
    authorized_candidates_csv: str = DEFAULT_AUTHORIZED_CANDIDATES_CSV,
    max_account_orders_per_day: int = 0,
    max_estimated_cost_r: float = 0.30,
    max_measured_spread_points: float = 75.0,
    kill_switch_file_name: str = "phase2_demo_repair_kill_switch.txt",
) -> AttachOutput:
    phase1_root = phase1_root.resolve()
    terminal_data_dir = terminal_data_dir.resolve()
    terminal_exe = terminal_exe.resolve()
    metaeditor_exe = metaeditor_exe.resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_OUTPUT_JSON.name else phase1_root / DEFAULT_OUTPUT_MD
    output_json.parent.mkdir(parents=True, exist_ok=True)

    attachments = build_attachment_plan()
    existing_inputs = _read_existing_executor_inputs(terminal_data_dir)
    allowed_account_logins_csv = allowed_account_logins_csv or existing_inputs.get("InpAllowedAccountLoginsCsv", "")
    experimental_authorization_token = experimental_authorization_token or existing_inputs.get("InpExperimentalAuthorizationToken", "")
    cost_suspension_acknowledgement_token = (
        cost_suspension_acknowledgement_token or existing_inputs.get("InpCostSuspensionAcknowledgementToken", "")
    )
    _validate_authorization_inputs(
        allowed_account_logins_csv=allowed_account_logins_csv,
        experimental_authorization_token=experimental_authorization_token,
        cost_suspension_acknowledgement_token=cost_suspension_acknowledgement_token,
    )
    kill_switch_state = _kill_switch_state(terminal_data_dir, kill_switch_file_name)
    if kill_switch_state == "ACTIVE_KILL":
        raise RuntimeError(f"Repair kill switch is active: {kill_switch_file_name}")

    deployed_sources = _deploy_sources(phase1_root, terminal_data_dir)
    compile_log = _compile_ea(metaeditor_exe, terminal_data_dir)
    terminal_closed = _close_terminal(terminal_exe)
    profile_backup_dir, removed_repair_charts, added_charts = _append_repair_charts(
        terminal_data_dir=terminal_data_dir,
        attachments=attachments,
        allowed_account_logins_csv=allowed_account_logins_csv,
        experimental_authorization_token=experimental_authorization_token,
        cost_suspension_acknowledgement_token=cost_suspension_acknowledgement_token,
        authorized_candidates_csv=authorized_candidates_csv,
        max_account_orders_per_day=max_account_orders_per_day,
        max_estimated_cost_r=max_estimated_cost_r,
        max_measured_spread_points=max_measured_spread_points,
        kill_switch_file_name=kill_switch_file_name,
    )
    if launch:
        subprocess.Popen([str(terminal_exe)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5.0)

    payload: dict[str, Any] = {
        "status": "REPAIRED_EXECUTORS_APPENDED_TO_DEMO_TERMINAL",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authority": (
            "Owner-requested experimental demo repair lane. Existing demo executor charts are preserved; "
            "only prior repair-lane charts are replaced to avoid duplicates."
        ),
        "boundary": "Demo only; no live trading; does not authorize canonical Phase 2 or real capital.",
        "run_id": RUN_ID,
        "terminal": {
            "terminal_exe": str(terminal_exe),
            "terminal_data_dir": str(terminal_data_dir),
            "profile": "Default",
            "profile_backup_dir": str(profile_backup_dir),
            "terminal_closed_before_profile_append": terminal_closed,
            "terminal_relaunched": launch,
        },
        "ea": {
            "name": EA_NAME,
            "deployed_sources": [str(path) for path in deployed_sources],
            "compile_log": str(compile_log),
            "dry_run_only": False,
            "broker_action_allowed": True,
            "magic_namespace": "921000-921999",
            "comment_prefix": "P2REPAIR",
            "authorized_candidates_csv": authorized_candidates_csv,
            "authorization_token_configured": experimental_authorization_token == REQUIRED_EXPERIMENTAL_AUTHORIZATION_TOKEN,
            "cost_suspension_acknowledgement_token_configured": (
                cost_suspension_acknowledgement_token == REQUIRED_COST_SUSPENSION_ACKNOWLEDGEMENT_TOKEN
            ),
            "max_orders_per_day_per_instance": 12,
            "max_orders_per_day_account": "UNLIMITED" if max_account_orders_per_day <= 0 else max_account_orders_per_day,
            "max_open_positions_per_instance": 1,
            "max_open_positions_account": "UNLIMITED",
            "max_estimated_cost_R": max_estimated_cost_r,
            "max_measured_spread_points": max_measured_spread_points,
            "repair_time_bucket_clock": "UTC+240 minutes (Dubai)",
            "kill_switch_file_name": kill_switch_file_name,
            "kill_switch_state": kill_switch_state,
        },
        "profile_changes": {
            "existing_profile_preserved": True,
            "removed_prior_repair_charts": removed_repair_charts,
            "added_charts": [str(path) for path in added_charts],
        },
        "attachment_count": len(attachments),
        "attachments": [_attachment_payload(row) for row in attachments],
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return AttachOutput("REPAIRED_EXECUTORS_APPENDED_TO_DEMO_TERMINAL", output_json, output_md, len(attachments))


def _validate_authorization_inputs(
    *,
    allowed_account_logins_csv: str,
    experimental_authorization_token: str,
    cost_suspension_acknowledgement_token: str,
) -> None:
    if not allowed_account_logins_csv.strip():
        raise RuntimeError("No allowed account login found. Provide --allowed-account-logins-csv.")
    if experimental_authorization_token != REQUIRED_EXPERIMENTAL_AUTHORIZATION_TOKEN:
        raise RuntimeError("Experimental authorization token is missing or invalid.")
    if cost_suspension_acknowledgement_token != REQUIRED_COST_SUSPENSION_ACKNOWLEDGEMENT_TOKEN:
        raise RuntimeError("Cost-suspension acknowledgement token is missing or invalid.")


def _read_existing_executor_inputs(terminal_data_dir: Path) -> dict[str, str]:
    profile = terminal_data_dir / "MQL5" / "Profiles" / "Charts" / "Default"
    for chart in sorted(profile.glob("chart*.chr")):
        text = _read_chart_text(chart)
        if "name=Phase2ExperimentalDemoExecutor" not in text:
            continue
        values: dict[str, str] = {}
        for raw in text.splitlines():
            if raw.startswith("Inp") and "=" in raw:
                key, value = raw.split("=", 1)
                values[key] = value
        return values
    return {}


def _kill_switch_state(terminal_data_dir: Path, file_name: str) -> str:
    path = terminal_data_dir / "MQL5" / "Files" / file_name
    if not path.exists():
        return "ABSENT"
    text = _read_text(path)
    return "ACTIVE_KILL" if "KILL" in text.upper() else "PRESENT_NOT_KILL"


def _deploy_sources(phase1_root: Path, terminal_data_dir: Path) -> list[Path]:
    mql5_root = terminal_data_dir / "MQL5"
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


def _compile_ea(metaeditor_exe: Path, terminal_data_dir: Path) -> Path:
    if not metaeditor_exe.exists():
        raise FileNotFoundError(f"MetaEditor not found: {metaeditor_exe}")
    scratch_root = Path("C:/MT5CompileScratch")
    scratch_mql5 = scratch_root / "MQL5"
    scratch_experts = scratch_mql5 / "Experts"
    scratch_include = scratch_mql5 / "Include" / "Phase1"
    scratch_experts.mkdir(parents=True, exist_ok=True)
    scratch_include.mkdir(parents=True, exist_ok=True)
    source = terminal_data_dir / "MQL5" / "Experts" / f"{EA_NAME}.mq5"
    scratch_source = scratch_experts / source.name
    shutil.copy2(source, scratch_source)
    for include_name in ("Phase1Types.mqh", "Phase1BreakoutRetest.mqh"):
        shutil.copy2(terminal_data_dir / "MQL5" / "Include" / "Phase1" / include_name, scratch_include / include_name)
    scratch_log = scratch_root / f"compile_{EA_NAME}.log"
    if scratch_log.exists():
        scratch_log.unlink()
    command = [str(metaeditor_exe), f"/compile:{scratch_source}", f"/log:{scratch_log}"]
    subprocess.run(command, check=False, timeout=90)
    scratch_ex5 = scratch_experts / f"{EA_NAME}.ex5"
    target_ex5 = terminal_data_dir / "MQL5" / "Experts" / f"{EA_NAME}.ex5"
    if not scratch_ex5.exists():
        raise RuntimeError(f"MetaEditor did not produce {EA_NAME}.ex5. Compile log:\n{_read_text(scratch_log)}")
    shutil.copy2(scratch_ex5, target_ex5)
    log_path = terminal_data_dir / "MQL5" / "Logs" / f"compile_{EA_NAME}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if scratch_log.exists():
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


def _append_repair_charts(
    *,
    terminal_data_dir: Path,
    attachments: list[RepairAttachment],
    allowed_account_logins_csv: str,
    experimental_authorization_token: str,
    cost_suspension_acknowledgement_token: str,
    authorized_candidates_csv: str,
    max_account_orders_per_day: int,
    max_estimated_cost_r: float,
    max_measured_spread_points: float,
    kill_switch_file_name: str,
) -> tuple[Path, list[str], list[Path]]:
    default_profile = terminal_data_dir / "MQL5" / "Profiles" / "Charts" / "Default"
    default_profile.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = terminal_data_dir / "_codex_quarantine" / "profile_backups" / f"default_profile_before_repair_append_{stamp}"
    shutil.copytree(default_profile, backup_dir)

    removed: list[str] = []
    for chart in sorted(default_profile.glob("chart*.chr")):
        text = _read_chart_text(chart)
        if f"name={EA_NAME}" in text or RUN_ID in text:
            removed.append(chart.name)
            chart.unlink()

    next_index = _next_chart_index(default_profile)
    added: list[Path] = []
    for offset, row in enumerate(attachments):
        chart = default_profile / f"chart{next_index + offset:02d}.chr"
        chart.write_text(
            _render_chart(
                row,
                next_index + offset,
                allowed_account_logins_csv=allowed_account_logins_csv,
                experimental_authorization_token=experimental_authorization_token,
                cost_suspension_acknowledgement_token=cost_suspension_acknowledgement_token,
                authorized_candidates_csv=authorized_candidates_csv,
                max_account_orders_per_day=max_account_orders_per_day,
                max_estimated_cost_r=max_estimated_cost_r,
                max_measured_spread_points=max_measured_spread_points,
                kill_switch_file_name=kill_switch_file_name,
            ),
            encoding="utf-8",
        )
        added.append(chart)
    return backup_dir, removed, added


def _next_chart_index(profile: Path) -> int:
    indexes: list[int] = []
    for chart in profile.glob("chart*.chr"):
        digits = "".join(ch for ch in chart.stem if ch.isdigit())
        if digits:
            indexes.append(int(digits))
    return (max(indexes) + 1) if indexes else 1


def _render_chart(
    row: RepairAttachment,
    index: int,
    *,
    allowed_account_logins_csv: str,
    experimental_authorization_token: str,
    cost_suspension_acknowledgement_token: str,
    authorized_candidates_csv: str,
    max_account_orders_per_day: int,
    max_estimated_cost_r: float,
    max_measured_spread_points: float,
    kill_switch_file_name: str,
) -> str:
    left = 20 + ((index - 1) % 4) * 42
    top = 20 + ((index - 1) // 4) * 35
    right = left + 980
    bottom = top + 720
    digits, tick_size = _symbol_format(row.symbol)
    slug = _instance_slug(row)
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
            f"InpRunId={RUN_ID}",
            "InpDryRunOnly=false",
            "InpBrokerActionAllowed=true",
            f"InpCandidate={row.candidate}",
            f"InpCandidateStatus={EXECUTOR_CANDIDATE_STATUS}",
            f"InpFamilyLifecycleStatus={FAMILY_LIFECYCLE_STATUS}",
            f"InpTargetSymbol={row.symbol}",
            f"InpQualifiedSymbolsCsv={row.symbol}",
            "InpExpectedServerMarker=Demo",
            f"InpAllowedAccountLoginsCsv={allowed_account_logins_csv}",
            f"InpExperimentalAuthorizationToken={experimental_authorization_token}",
            f"InpRequiredExperimentalAuthorizationToken={REQUIRED_EXPERIMENTAL_AUTHORIZATION_TOKEN}",
            f"InpCostSuspensionAcknowledgementToken={cost_suspension_acknowledgement_token}",
            f"InpRequiredCostSuspensionAcknowledgementToken={REQUIRED_COST_SUSPENSION_ACKNOWLEDGEMENT_TOKEN}",
            f"InpAuthorizedCandidatesCsv={authorized_candidates_csv}",
            f"InpAttachmentLogFileName=phase2_demo_repair_executor_signal_log_v1_{slug}.csv",
            f"InpStartupLogFileName=phase2_demo_repair_executor_startup_v1_{slug}.csv",
            f"InpOrderLogFileName=phase2_demo_repair_executor_order_log_v1_{slug}.csv",
            f"InpKillSwitchFileName={kill_switch_file_name}",
            f"InpFixedLot={row.fixed_lot:.2f}",
            "InpEURUSDFixedLot=0.05",
            "InpGBPUSDFixedLot=0.05",
            "InpMaxOrdersPerDay=0",
            f"InpMaxAccountOrdersPerDay={max_account_orders_per_day}",
            "InpMinSecondsBetweenOrders=0",
            "InpMaxOpenPositionsPerInstance=0",
            "InpDeviationPoints=50",
            "InpMaxEstimatedCostR=0.00",
            "InpMaxMeasuredSpreadPoints=0.0",
            "InpDubaiUtcOffsetMinutes=240",
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


def _attachment_payload(row: RepairAttachment) -> dict[str, Any]:
    return {
        "candidate": row.candidate,
        "status": EXECUTOR_CANDIDATE_STATUS,
        "family_lifecycle_status": FAMILY_LIFECYCLE_STATUS,
        "symbol": row.symbol,
        "fixed_lot": row.fixed_lot,
        "magic": _instance_magic(row),
        "comment_prefix": "P2REPAIR",
        "qualification_source": row.qualification_source,
        "active_filter": row.active_filter,
        "signal_log_file": f"phase2_demo_repair_executor_signal_log_v1_{_instance_slug(row)}.csv",
        "startup_log_file": f"phase2_demo_repair_executor_startup_v1_{_instance_slug(row)}.csv",
        "order_log_file": f"phase2_demo_repair_executor_order_log_v1_{_instance_slug(row)}.csv",
    }


def _instance_magic(row: RepairAttachment) -> int:
    candidate_code = 10 if row.candidate == "symbol_normalized_round_retest_v0_repair_v1" else 20
    symbol_code = {"XAUUSD": 1, "EURUSD": 2, "GBPUSD": 4}.get(row.symbol, 9)
    return 921000 + candidate_code * 10 + symbol_code


def _instance_slug(row: RepairAttachment) -> str:
    raw = f"{row.candidate}_{row.symbol}".lower()
    return "".join(char if char.isalnum() or char == "_" else "_" for char in raw)


def _symbol_format(symbol: str) -> tuple[int, str]:
    if symbol == "XAUUSD":
        return 2, "0.01"
    if symbol == "USDJPY":
        return 3, "0.001"
    return 5, "0.00001"


def _read_chart_text(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8", "utf-16", "utf-16-le", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeError:
            continue
    return data.decode(errors="replace")


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    data = path.read_bytes()
    for encoding in ("utf-8", "utf-16", "utf-16-le", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeError:
            continue
    return data.decode(errors="replace")


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 2 Repaired Demo Executor Attachments",
        "",
        f"Status: {payload['status']}",
        "",
        str(payload["authority"]),
        "",
        str(payload["boundary"]),
        "",
        f"Run ID: `{payload['run_id']}`",
        f"Attachment count: `{payload['attachment_count']}`",
        f"Terminal: `{payload['terminal']['terminal_exe']}`",
        f"Data folder: `{payload['terminal']['terminal_data_dir']}`",
        f"Profile backup: `{payload['terminal']['profile_backup_dir']}`",
        f"Existing profile preserved: `{payload['profile_changes']['existing_profile_preserved']}`",
        f"Removed prior repair charts: `{payload['profile_changes']['removed_prior_repair_charts']}`",
        f"Magic namespace: `{payload['ea']['magic_namespace']}`",
        f"Comment prefix: `{payload['ea']['comment_prefix']}`",
        f"Account order cap: `{payload['ea']['max_orders_per_day_account']}`",
        f"Repair time bucket clock: `{payload['ea']['repair_time_bucket_clock']}`",
        f"Kill switch: `{payload['ea']['kill_switch_file_name']}` / `{payload['ea']['kill_switch_state']}`",
        "",
        "| Candidate | Symbol | Lot | Magic | Filter | Qualification | Logs |",
        "|---|---|---:|---:|---|---|---|",
    ]
    for item in payload["attachments"]:
        lines.append(
            f"| {item['candidate']} | {item['symbol']} | {float(item['fixed_lot']):.2f} | {item['magic']} | "
            f"{item['active_filter']} | {item['qualification_source']} | {item['order_log_file']} |"
        )
    lines.extend(
        [
            "",
            "These repaired charts are additive. They do not delete the existing experimental demo executor charts.",
            "Round-number repair v1 is not attached for broker action because the research output marks it rebuild/observer-only.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Append repaired experimental demo executors to the standard MT5 demo terminal.")
    parser.add_argument("--phase1-root", type=Path, default=Path("."))
    parser.add_argument("--terminal-data-dir", type=Path, default=DEFAULT_TERMINAL_DATA_DIR)
    parser.add_argument("--terminal-exe", type=Path, default=DEFAULT_TERMINAL_EXE)
    parser.add_argument("--metaeditor-exe", type=Path, default=DEFAULT_METAEDITOR_EXE)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--no-launch", action="store_true")
    parser.add_argument("--allowed-account-logins-csv", default="")
    parser.add_argument("--experimental-authorization-token", default="")
    parser.add_argument("--cost-suspension-acknowledgement-token", default="")
    parser.add_argument("--authorized-candidates-csv", default=DEFAULT_AUTHORIZED_CANDIDATES_CSV)
    parser.add_argument("--max-account-orders-per-day", type=int, default=0)
    parser.add_argument("--max-estimated-cost-r", type=float, default=0.30)
    parser.add_argument("--max-measured-spread-points", type=float, default=75.0)
    parser.add_argument("--kill-switch-file-name", default="phase2_demo_repair_kill_switch.txt")
    args = parser.parse_args()
    output = attach_phase2_repaired_demo_executors(
        phase1_root=args.phase1_root,
        terminal_data_dir=args.terminal_data_dir,
        terminal_exe=args.terminal_exe,
        metaeditor_exe=args.metaeditor_exe,
        output_json=args.output_json,
        launch=not args.no_launch,
        allowed_account_logins_csv=args.allowed_account_logins_csv,
        experimental_authorization_token=args.experimental_authorization_token,
        cost_suspension_acknowledgement_token=args.cost_suspension_acknowledgement_token,
        authorized_candidates_csv=args.authorized_candidates_csv,
        max_account_orders_per_day=args.max_account_orders_per_day,
        max_estimated_cost_r=args.max_estimated_cost_r,
        max_measured_spread_points=args.max_measured_spread_points,
        kill_switch_file_name=args.kill_switch_file_name,
    )
    print(f"{output.status}: {output.attachment_count} attachments")
    print(output.json_path)
    print(output.markdown_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
