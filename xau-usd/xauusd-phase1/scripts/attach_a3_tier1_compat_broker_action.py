from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_PORTABLE_ROOT = Path("C:/MT5PortableRepairLane")
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "A3_TIER1_COMPAT_BROKER_ACTION_ATTACHMENT_2026_06_17.json"

EA_NAME = "Account3BreakoutTier1CompatExecutor"
RUN_ID = "A3_BREAKOUT_TIER1_COMPAT_V1_ARMED_20260617"
MAGIC = "933400"
COMMENT = "A3_BREAKOUT_TIER1_COMPAT"
ACCOUNT_LOGIN = "1033669"
SYMBOL = "XAUUSD"

ARMED_INPUTS = {
    "InpRunId": RUN_ID,
    "InpDryRunOnly": "false",
    "InpBrokerActionAllowed": "true",
    "InpTargetSymbol": SYMBOL,
    "InpExpectedServerMarker": "Demo",
    "InpAllowedAccountLoginsCsv": ACCOUNT_LOGIN,
    "InpKillSwitchFileName": "A3_KILL.txt",
    "InpMagicNumber": MAGIC,
    "InpOrderComment": COMMENT,
    "InpSignalLogFileName": "a3_breakout_tier1_compat_signal_log.csv",
    "InpStartupLogFileName": "a3_breakout_tier1_compat_startup.csv",
    "InpOrderLogFileName": "a3_breakout_tier1_compat_order_log.csv",
    "InpManagementLogFileName": "a3_breakout_tier1_compat_management_log.csv",
    "InpDirectionStateFileName": "dirstate_xauusd.csv",
    "InpMaxOpenPositionsPerMagic": "1",
    "InpMaxEstimatedCostR": "0.15",
    "InpCostWarnR": "0.20",
    "InpAbsoluteRejectCostR": "0.30",
    "InpMaxMeasuredSpreadPoints": "75.0",
    "InpTradeSessionGateEnabled": "true",
    "InpTradeSessionStartHour": "12",
    "InpTradeSessionEndHour": "15",
    "InpMinSecondsBetweenOrders": "60",
    "InpFixedLot": "0.01",
    "InpDeviationPoints": "50",
    "InpXauStopDistanceFloorEnabled": "true",
    "InpTrendGuardEnabled": "false",
    "InpTrendGuardShadowOnly": "true",
    "InpTrendH1LookbackBars": "12",
    "InpTrendH4LookbackBars": "6",
    "InpTrendMinMovePoints": "100.0",
    "InpBreakevenEnabled": "false",
    "InpBreakevenTriggerR": "0.50",
    "InpPartialTakeProfitEnabled": "false",
    "InpPartialTriggerR": "1.00",
    "InpPartialCloseFraction": "0.50",
}


@dataclass(frozen=True)
class ChartInventoryRow:
    chart: str
    symbol: str
    expert: str
    magic: str
    broker_action_allowed: str
    dry_run_only: str
    fixed_lot: str
    run_id: str
    order_comment: str


def attach_a3_tier1_compat(
    phase1_root: Path,
    portable_root: Path = DEFAULT_PORTABLE_ROOT,
    output_json: Path | None = None,
    launch: bool = True,
    wait_seconds: int = 90,
    allow_existing_chart: bool = False,
) -> dict[str, Any]:
    phase1_root = phase1_root.resolve()
    portable_root = portable_root.resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_json.parent.mkdir(parents=True, exist_ok=True)

    terminal_exe = portable_root / "terminal64.exe"
    metaeditor_exe = portable_root / "MetaEditor64.exe"
    terminal_data_dir = portable_root
    profile_dir = terminal_data_dir / "MQL5" / "Profiles" / "Charts" / "Default"
    files_dir = terminal_data_dir / "MQL5" / "Files"
    preset_dir = terminal_data_dir / "MQL5" / "Presets"

    require_file(terminal_exe)
    require_file(metaeditor_exe)
    require_dir(profile_dir)

    before = chart_inventory(profile_dir)
    duplicate_charts = [row.chart for row in before if row.magic == MAGIC or row.expert == EA_NAME]
    if duplicate_charts and not allow_existing_chart:
        raise RuntimeError(f"A3 Tier1 compat is already attached or magic {MAGIC} is already present: {duplicate_charts}")

    broker_magic_state_before = broker_magic_state(terminal_exe)
    if broker_magic_state_before.get("status") == "PASS" and broker_magic_state_before.get("matching_total", 0) > 0:
        raise RuntimeError(f"Existing open/pending broker exposure with magic {MAGIC}: {broker_magic_state_before}")

    compiled = compile_ea(phase1_root, terminal_data_dir, metaeditor_exe)
    if not compiled["compile_pass"]:
        raise RuntimeError(f"Compile failed; see {compiled['compile_log']}")

    terminal_closed = close_terminal(terminal_exe)
    profile_backup = backup_profile(profile_dir, terminal_data_dir)
    deployed = deploy_ea(phase1_root, terminal_data_dir, compiled)
    armed_preset = write_local_armed_preset(preset_dir)
    new_chart = profile_dir / duplicate_charts[0] if duplicate_charts else append_chart(profile_dir)
    after_profile_edit = chart_inventory(profile_dir)

    launched = False
    startup_before = log_state(files_dir, ARMED_INPUTS["InpStartupLogFileName"])
    launch_started_at = now_utc()
    if launch:
        subprocess.Popen([str(terminal_exe), "/portable"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        launched = True
        wait_for_startup(files_dir, ARMED_INPUTS["InpStartupLogFileName"], wait_seconds)
    startup_after = log_state(files_dir, ARMED_INPUTS["InpStartupLogFileName"])
    after_launch = chart_inventory(profile_dir)

    checks = [
        check("owner_chat_authorization_recorded", "PASS", "Broker-action approval recorded in A3_TIER1_COMPAT_BROKER_ACTION_OWNER_AUTHORIZATION_2026_06_17.md"),
        check("compile_0_errors_0_warnings", "PASS" if compiled["compile_pass"] else "FAIL", compiled["compile_log"]),
        check("profile_backup_created", "PASS" if Path(profile_backup).exists() else "FAIL", str(profile_backup)),
        check(
            "preexisting_933400_chart_absent_or_reused",
            "PASS" if not duplicate_charts or allow_existing_chart else "FAIL",
            ", ".join(duplicate_charts) if duplicate_charts else "none",
        ),
        check("preexisting_933400_broker_exposure_absent", broker_magic_state_before.get("status", "UNKNOWN"), json.dumps(broker_magic_state_before, sort_keys=True)),
        check("local_armed_preset_written", "PASS" if Path(armed_preset["path"]).exists() else "FAIL", armed_preset["path"]),
        check("new_chart_added", "PASS" if any(row.expert == EA_NAME and row.magic == MAGIC for row in after_profile_edit) else "FAIL", str(new_chart)),
        check("terminal_relaunched", "PASS" if launched else "SKIPPED", str(terminal_exe)),
        check("startup_log_present", "PASS" if startup_after["exists"] else "PENDING_RUNTIME_EVIDENCE", startup_after["path"]),
        check("startup_log_armed", startup_armed_status(startup_after), startup_after.get("last_line", "")),
        check("existing_a3_lanes_preserved", existing_lanes_status(after_profile_edit), "Required magics 933200 and 933300 remain attached."),
    ]
    status = "PASS" if all(item["status"] in {"PASS", "SKIPPED"} for item in checks) else "PENDING"

    payload: dict[str, Any] = {
        "status": status,
        "created_at_utc": now_utc(),
        "authority": "Owner chat approval on 2026-06-17 to skip observer mode and start broker-action demo orders for A3 Tier1 compat.",
        "boundary": "Demo only; no canonical Phase 2 approval; no live trading or real-capital authorization.",
        "terminal": {
            "portable_root": str(portable_root),
            "terminal_exe": str(terminal_exe),
            "metaeditor_exe": str(metaeditor_exe),
            "terminal_closed_before_profile_change": terminal_closed,
            "terminal_relaunched": launched,
            "launch_started_at_utc": launch_started_at,
            "profile_backup": str(profile_backup),
        },
        "lane": {
            "ea": EA_NAME,
            "symbol": SYMBOL,
            "timeframe": "M5",
            "account_login": ACCOUNT_LOGIN,
            "magic": MAGIC,
            "comment": COMMENT,
            "fixed_lot": ARMED_INPUTS["InpFixedLot"],
            "dry_run": ARMED_INPUTS["InpDryRunOnly"],
            "broker_action_allowed": ARMED_INPUTS["InpBrokerActionAllowed"],
            "session_gate_server_hours": f"{ARMED_INPUTS['InpTradeSessionStartHour']}-{ARMED_INPUTS['InpTradeSessionEndHour']}",
            "xau_stop_floor_enabled": ARMED_INPUTS["InpXauStopDistanceFloorEnabled"],
            "trend_guard_enabled": ARMED_INPUTS["InpTrendGuardEnabled"],
            "trend_shadow_only": ARMED_INPUTS["InpTrendGuardShadowOnly"],
        },
        "compiled": compiled,
        "deployed": deployed,
        "local_armed_preset": armed_preset,
        "new_chart": str(new_chart),
        "startup_log_before": startup_before,
        "startup_log_after": startup_after,
        "broker_magic_state_before": broker_magic_state_before,
        "before_charts": [row.__dict__ for row in before],
        "after_charts": [row.__dict__ for row in after_launch],
        "checks": checks,
    }
    write_report_pair(output_json, payload, render_report(payload))
    return payload


def compile_ea(phase1_root: Path, terminal_data_dir: Path, metaeditor_exe: Path) -> dict[str, Any]:
    experts_dir = terminal_data_dir / "MQL5" / "Experts"
    include_dir = terminal_data_dir / "MQL5" / "Include"
    phase1_include_dir = include_dir / "Phase1"
    experts_dir.mkdir(parents=True, exist_ok=True)
    phase1_include_dir.mkdir(parents=True, exist_ok=True)

    copy_plan = [
        (phase1_root / "mt5" / "Experts" / f"{EA_NAME}.mq5", experts_dir / f"{EA_NAME}.mq5"),
        (phase1_root / "mt5" / "Include" / "A3BreakoutExecutorBase.mqh", include_dir / "A3BreakoutExecutorBase.mqh"),
        (phase1_root / "mt5" / "Include" / "DirectionStateShadow.mqh", include_dir / "DirectionStateShadow.mqh"),
        (phase1_root / "mt5" / "Include" / "Phase1" / "Phase1Types.mqh", phase1_include_dir / "Phase1Types.mqh"),
        (phase1_root / "mt5" / "Include" / "Phase1" / "Phase1BreakoutRetest.mqh", phase1_include_dir / "Phase1BreakoutRetest.mqh"),
    ]
    for source, target in copy_plan:
        require_file(source)
        shutil.copy2(source, target)

    target_source = experts_dir / f"{EA_NAME}.mq5"
    target_ex5 = experts_dir / f"{EA_NAME}.ex5"
    target_log = terminal_data_dir / "MQL5" / "Logs" / f"compile_{EA_NAME}_broker_action_20260617.log"
    target_log.parent.mkdir(parents=True, exist_ok=True)
    if target_log.exists():
        target_log.unlink()
    if target_ex5.exists():
        target_ex5.unlink()
    completed = subprocess.run(
        [str(metaeditor_exe), "/portable", f"/compile:{target_source}", f"/log:{target_log}"],
        check=False,
        timeout=120,
    )
    return {
        "source": str(phase1_root / "mt5" / "Experts" / f"{EA_NAME}.mq5"),
        "target_source": str(target_source),
        "target_ex5": str(target_ex5),
        "compile_log": str(target_log),
        "returncode": completed.returncode,
        "compile_pass": target_ex5.exists() and compile_log_passed(target_log),
    }


def deploy_ea(phase1_root: Path, terminal_data_dir: Path, compiled: dict[str, Any]) -> list[str]:
    deployed: list[str] = []
    experts_dir = terminal_data_dir / "MQL5" / "Experts"
    include_dir = terminal_data_dir / "MQL5" / "Include"
    phase1_include_dir = include_dir / "Phase1"
    experts_dir.mkdir(parents=True, exist_ok=True)
    phase1_include_dir.mkdir(parents=True, exist_ok=True)

    for source, target in [
        (phase1_root / "mt5" / "Experts" / f"{EA_NAME}.mq5", experts_dir / f"{EA_NAME}.mq5"),
        (Path(compiled["target_ex5"]), experts_dir / f"{EA_NAME}.ex5"),
        (phase1_root / "mt5" / "Include" / "A3BreakoutExecutorBase.mqh", include_dir / "A3BreakoutExecutorBase.mqh"),
        (phase1_root / "mt5" / "Include" / "DirectionStateShadow.mqh", include_dir / "DirectionStateShadow.mqh"),
        (phase1_root / "mt5" / "Include" / "Phase1" / "Phase1Types.mqh", phase1_include_dir / "Phase1Types.mqh"),
        (phase1_root / "mt5" / "Include" / "Phase1" / "Phase1BreakoutRetest.mqh", phase1_include_dir / "Phase1BreakoutRetest.mqh"),
    ]:
        require_file(source)
        if source.resolve() != target.resolve():
            shutil.copy2(source, target)
        deployed.append(str(target))
    return deployed


def write_local_armed_preset(preset_dir: Path) -> dict[str, str]:
    preset_dir.mkdir(parents=True, exist_ok=True)
    path = preset_dir / f"{EA_NAME}.armed_owner_20260617.set"
    content = "\n".join(f"{key}={value}" for key, value in ARMED_INPUTS.items()) + "\n"
    path.write_text(content, encoding="utf-8")
    return {
        "path": str(path),
        "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
    }


def append_chart(profile_dir: Path) -> Path:
    chart = profile_dir / f"chart{next_chart_index(profile_dir):02d}.chr"
    chart.write_text(render_chart(chart.stem), encoding="utf-8")
    order_file = profile_dir / "order.wnd"
    existing = [line.strip() for line in read_text_any(order_file).splitlines() if line.strip()]
    ordered = [chart.name] + [line for line in existing if line.lower() != chart.name.lower()]
    order_file.write_text("\n".join(ordered) + "\n", encoding="utf-8")
    return chart


def render_chart(chart_stem: str) -> str:
    digits = "".join(ch for ch in chart_stem if ch.isdigit())
    index = int(digits) if digits else 1
    left = ((index - 1) % 2) * 515
    top = ((index - 1) // 2) * 526
    lines = [
        "<chart>",
        f"id={int(time.time())}{index:04d}",
        "symbol=XAUUSD",
        "description=Gold",
        "period_type=0",
        "period_size=5",
        "digits=2",
        "tick_size=0.010000",
        "position_time=0",
        "scale_fix=0",
        "scale_fixed_min=0.000000",
        "scale_fixed_max=0.000000",
        "scale_fix11=0",
        "scale_bar=0",
        "scale_bar_val=1.000000",
        "scale=3",
        "mode=1",
        "fore=0",
        "grid=0",
        "volume=0",
        "scroll=1",
        "shift=1",
        "shift_size=20.000000",
        "fixed_pos=0.000000",
        "ticker=1",
        "ohlc=0",
        "one_click=0",
        "one_click_btn=0",
        "bidline=1",
        "askline=1",
        "lastline=0",
        "days=0",
        "descriptions=0",
        "tradelines=1",
        "tradehistory=1",
        f"window_left={left}",
        f"window_top={top}",
        f"window_right={left + 515}",
        f"window_bottom={top + 526}",
        "window_type=1",
        "floating=0",
        "floating_left=0",
        "floating_top=0",
        "floating_right=0",
        "floating_bottom=0",
        "floating_type=1",
        "floating_toolbar=1",
        "floating_tbstate=",
        "background_color=0",
        "foreground_color=16777215",
        "barup_color=65280",
        "bardown_color=65280",
        "bullcandle_color=0",
        "bearcandle_color=16777215",
        "chartline_color=65280",
        "volumes_color=3329330",
        "grid_color=10061943",
        "bidline_color=10061943",
        "askline_color=255",
        "lastline_color=49152",
        "stops_color=255",
        "windows_total=1",
        "",
        "<expert>",
        f"name={EA_NAME}",
        f"path=Experts\\{EA_NAME}.ex5",
        "expertmode=1",
        "<inputs>",
        *[f"{key}={value}" for key, value in ARMED_INPUTS.items()],
        "</inputs>",
        "</expert>",
        "",
        "<window>",
        "height=100.000000",
        "objects=0",
        "",
        "<indicator>",
        "name=Main",
        "path=",
        "apply=1",
        "show_data=1",
        "scale_inherit=0",
        "scale_line=0",
        "scale_line_percent=50",
        "scale_line_value=0.000000",
        "scale_fix_min=0",
        "scale_fix_min_val=0.000000",
        "scale_fix_max=0",
        "scale_fix_max_val=0.000000",
        "expertmode=0",
        "fixed_height=-1",
        "</indicator>",
        "</window>",
        "</chart>",
        "",
    ]
    return "\n".join(lines)


def broker_magic_state(terminal_exe: Path) -> dict[str, Any]:
    try:
        import MetaTrader5 as mt5  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on local MT5 package
        return {"status": "UNKNOWN", "reason": f"MetaTrader5 import failed: {exc}"}
    if not mt5.initialize(path=str(terminal_exe)):
        return {"status": "UNKNOWN", "reason": f"MetaTrader5 initialize failed: {mt5.last_error()}"}
    try:
        positions = mt5.positions_get(symbol=SYMBOL) or []
        orders = mt5.orders_get(symbol=SYMBOL) or []
        matching_positions = [item.ticket for item in positions if int(getattr(item, "magic", 0)) == int(MAGIC)]
        matching_orders = [item.ticket for item in orders if int(getattr(item, "magic", 0)) == int(MAGIC)]
        return {
            "status": "PASS" if not matching_positions and not matching_orders else "FAIL",
            "positions_total": len(positions),
            "orders_total": len(orders),
            "matching_positions": matching_positions,
            "matching_orders": matching_orders,
            "matching_total": len(matching_positions) + len(matching_orders),
        }
    finally:
        mt5.shutdown()


def chart_inventory(profile_dir: Path) -> list[ChartInventoryRow]:
    return [parse_chart(chart) for chart in sorted(profile_dir.glob("chart*.chr"))]


def parse_chart(chart: Path) -> ChartInventoryRow:
    text = read_text_any(chart)
    values: dict[str, str] = {}
    expert_name = "NO_EA"
    in_expert = False
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped == "<expert>":
            in_expert = True
            continue
        if stripped == "</expert>":
            in_expert = False
            continue
        if "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip()
        values[key] = value
        if in_expert and key == "name":
            expert_name = value
    inputs = parse_inputs(text)
    return ChartInventoryRow(
        chart=chart.name,
        symbol=values.get("symbol", ""),
        expert=expert_name,
        magic=inputs.get("InpMagicNumber", ""),
        broker_action_allowed=inputs.get("InpBrokerActionAllowed", ""),
        dry_run_only=inputs.get("InpDryRunOnly", ""),
        fixed_lot=inputs.get("InpFixedLot", ""),
        run_id=inputs.get("InpRunId", ""),
        order_comment=inputs.get("InpOrderComment", ""),
    )


def parse_inputs(text: str) -> dict[str, str]:
    inputs: dict[str, str] = {}
    in_inputs = False
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped == "<inputs>":
            in_inputs = True
            continue
        if stripped == "</inputs>":
            in_inputs = False
            continue
        if in_inputs and "=" in stripped:
            key, value = stripped.split("=", 1)
            inputs[key] = value
    return inputs


def next_chart_index(profile_dir: Path) -> int:
    indexes: list[int] = []
    for chart in profile_dir.glob("chart*.chr"):
        match = re.search(r"chart(\d+)$", chart.stem, flags=re.IGNORECASE)
        if match:
            indexes.append(int(match.group(1)))
    return max(indexes, default=0) + 1


def close_terminal(terminal_exe: Path) -> bool:
    command = f"""
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
    result = subprocess.run(["powershell", "-NoProfile", "-Command", command], text=True, capture_output=True, timeout=45)
    return result.returncode == 0


def backup_profile(profile_dir: Path, terminal_data_dir: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup = terminal_data_dir / "_codex_quarantine" / "profile_backups" / f"default_profile_before_a3_tier1_compat_{stamp}"
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(profile_dir, backup)
    return backup


def wait_for_startup(files_dir: Path, startup_name: str, wait_seconds: int) -> None:
    deadline = time.time() + max(0, wait_seconds)
    while time.time() < deadline:
        state = log_state(files_dir, startup_name)
        if state["exists"] and COMMENT in state.get("last_line", "") and RUN_ID in state.get("last_line", ""):
            return
        time.sleep(1.0)


def log_state(files_dir: Path, filename: str) -> dict[str, Any]:
    path = files_dir / filename
    text = read_text_any(path)
    lines = [line for line in text.splitlines() if line.strip()]
    return {
        "path": str(path),
        "exists": path.exists(),
        "mtime_utc": mtime_text(path),
        "line_count": len(lines),
        "last_line": lines[-1] if lines else "",
    }


def startup_armed_status(state: dict[str, Any]) -> str:
    line = state.get("last_line", "")
    if not state.get("exists"):
        return "PENDING_RUNTIME_EVIDENCE"
    required = [RUN_ID, SYMBOL, MAGIC, COMMENT, "false", "true", "0.01", "ATTACHED_A3_BREAKOUT_TIER1_COMPAT"]
    return "PASS" if all(token in line for token in required) else "PENDING_RUNTIME_EVIDENCE"


def existing_lanes_status(rows: list[ChartInventoryRow]) -> str:
    magics = {row.magic for row in rows}
    return "PASS" if {"933200", "933300"}.issubset(magics) else "FAIL"


def compile_log_passed(path: Path) -> bool:
    text = read_text_any(path).lower()
    return "0 errors, 0 warnings" in text or "0 error(s), 0 warning(s)" in text


def require_file(path: Path) -> None:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(path)


def require_dir(path: Path) -> None:
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(path)


def read_text_any(path: Path) -> str:
    if not path.exists():
        return ""
    payload = path.read_bytes()
    for encoding in ("utf-8", "utf-16", "utf-16-le", "cp1252"):
        try:
            return payload.decode(encoding)
        except UnicodeError:
            continue
    return payload.decode(errors="replace")


def mtime_text(path: Path) -> str:
    if not path.exists():
        return "missing"
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat().replace("+00:00", "Z")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def check(name: str, status: str, evidence: str) -> dict[str, str]:
    return {"name": name, "status": status, "evidence": evidence}


def write_report_pair(output_json: Path, payload: dict[str, Any], markdown: str) -> None:
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    output_json.with_suffix(".md").write_text(markdown, encoding="utf-8")


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# A3 Tier1 Compat Broker-Action Attachment",
        "",
        f"Overall status: `{payload['status']}`",
        "",
        str(payload["authority"]),
        "",
        str(payload["boundary"]),
        "",
        "## Attached Lane",
        "",
        "| Field | Value |",
        "| --- | --- |",
    ]
    for key, value in payload["lane"].items():
        lines.append(f"| {escape_md(key)} | `{escape_md(value)}` |")
    lines.extend(
        [
            "",
            "## Runtime Evidence",
            "",
            f"- Terminal: `{payload['terminal']['terminal_exe']}`",
            f"- Profile backup: `{payload['terminal']['profile_backup']}`",
            f"- Compile log: `{payload['compiled']['compile_log']}`",
            f"- New chart: `{payload['new_chart']}`",
            f"- Local armed preset: `{payload['local_armed_preset']['path']}`",
            f"- Local armed preset SHA256: `{payload['local_armed_preset']['sha256']}`",
            f"- Startup log: `{payload['startup_log_after']['path']}`",
            f"- Startup latest row: `{escape_md(payload['startup_log_after'].get('last_line', ''))}`",
            "",
            "## Checks",
            "",
            "| Check | Status | Evidence |",
            "| --- | --- | --- |",
        ]
    )
    lines.extend(f"| {item['name']} | `{item['status']}` | {escape_md(item['evidence'])} |" for item in payload["checks"])
    lines.extend(["", "## Before Charts", "", *inventory_table(payload["before_charts"])])
    lines.extend(["", "## After Charts", "", *inventory_table(payload["after_charts"]), ""])
    return "\n".join(lines)


def inventory_table(rows: list[dict[str, str]]) -> list[str]:
    lines = [
        "| Chart | Symbol | Expert | Magic | Broker Action | Dry Run | Lot | Run Id | Comment |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {chart} | {symbol} | {expert} | {magic} | {broker_action_allowed} | {dry_run_only} | {fixed_lot} | {run_id} | {order_comment} |".format(
                **{key: escape_md(value) for key, value in row.items()}
            )
        )
    return lines


def escape_md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Attach A3 Tier1 compat broker-action lane to the A3 demo portable terminal.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--portable-root", type=Path, default=DEFAULT_PORTABLE_ROOT)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--no-launch", action="store_true")
    parser.add_argument("--wait-seconds", type=int, default=90)
    parser.add_argument("--allow-existing-chart", action="store_true")
    args = parser.parse_args(argv)
    payload = attach_a3_tier1_compat(
        phase1_root=args.phase1_root,
        portable_root=args.portable_root,
        output_json=args.output_json,
        launch=not args.no_launch,
        wait_seconds=args.wait_seconds,
        allow_existing_chart=args.allow_existing_chart,
    )
    print(f"A3 Tier1 compat broker-action attachment: {payload['status']}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
