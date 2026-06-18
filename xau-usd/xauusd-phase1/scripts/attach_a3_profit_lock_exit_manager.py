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
DEFAULT_GATE_JSON = Path("outputs") / "reports" / "A3_PROFIT_LOCK_EXIT_MANAGER_GATE_2026_06_17.json"
DEFAULT_OUTPUT_JSON = Path("A3_PROFIT_LOCK_EXIT_MANAGER_ATTACHMENT_2026_06_17.json")

EA_NAME = "Account3ProfitLockExitManager"
RUN_ID = "A3_PROFIT_LOCK_EXIT_MANAGER_V1_ARMED_20260618"
ACCOUNT_LOGIN = "1033669"
SYMBOL = "XAUUSD"
MANAGED_MAGICS = "933200,933400"
EXCLUDED_MAGIC = "933300"
ATTACHED_STATUS = "ATTACHED_A3_PROFIT_LOCK_EXIT_MANAGER"

ARMED_INPUTS = {
    "InpRunId": RUN_ID,
    "InpDryRunOnly": "false",
    "InpManageActionAllowed": "true",
    "InpTargetSymbol": SYMBOL,
    "InpExpectedServerMarker": "Demo",
    "InpAllowedAccountLoginsCsv": ACCOUNT_LOGIN,
    "InpExecutionKillSwitchFileName": "A3_EXECUTION_KILL.txt",
    "InpFullStopFileName": "A3_FULL_STOP.txt",
    "InpManagedMagicsCsv": MANAGED_MAGICS,
    "InpPrimaryRungEnabled": "true",
    "InpPrimaryTriggerR": "1.25",
    "InpPrimaryLockR": "0.80",
    "InpSecondaryRungEnabled": "false",
    "InpSecondaryTriggerR": "1.00",
    "InpSecondaryLockR": "0.50",
    "InpTertiaryRungEnabled": "false",
    "InpTertiaryTriggerR": "0.75",
    "InpTertiaryLockR": "0.25",
    "InpTimerSeconds": "2",
    "InpDeviationPoints": "50",
    "InpStartupLogFileName": "a3_profit_lock_exit_manager_startup.csv",
    "InpManagementLogFileName": "a3_profit_lock_exit_manager_log.csv",
}


@dataclass(frozen=True)
class ChartInventoryRow:
    chart: str
    symbol: str
    expert: str
    magic: str
    managed_magics: str
    manage_action_allowed: str
    broker_action_allowed: str
    dry_run_only: str
    run_id: str
    order_comment: str


def attach_a3_profit_lock_exit_manager(
    phase1_root: Path,
    portable_root: Path = DEFAULT_PORTABLE_ROOT,
    gate_json: Path | None = None,
    output_json: Path | None = None,
    launch: bool = True,
    wait_seconds: int = 90,
    allow_existing_chart: bool = False,
) -> dict[str, Any]:
    phase1_root = phase1_root.resolve()
    repo_root = phase1_root.parents[1]
    portable_root = portable_root.resolve()
    gate_json = (gate_json or phase1_root / DEFAULT_GATE_JSON).resolve()
    output_json = (output_json or repo_root / DEFAULT_OUTPUT_JSON).resolve()
    output_json.parent.mkdir(parents=True, exist_ok=True)

    terminal_exe = portable_root / "terminal64.exe"
    metaeditor_exe = portable_root / "MetaEditor64.exe"
    profile_dir = portable_root / "MQL5" / "Profiles" / "Charts" / "Default"
    files_dir = portable_root / "MQL5" / "Files"
    preset_dir = portable_root / "MQL5" / "Presets"

    require_file(terminal_exe)
    require_file(metaeditor_exe)
    require_dir(profile_dir)
    gate_payload = load_gate_payload(gate_json)
    if gate_payload.get("status") != "PASS":
        raise RuntimeError(f"Profit-lock replay gate is not PASS: {gate_payload.get('status')}")

    runtime_before = broker_runtime_state(terminal_exe)
    before = chart_inventory(profile_dir)
    duplicate_charts = [row.chart for row in before if row.expert == EA_NAME]
    if duplicate_charts and not allow_existing_chart:
        raise RuntimeError(f"{EA_NAME} is already attached: {duplicate_charts}")

    compiled = compile_ea(phase1_root, portable_root, metaeditor_exe)
    if not compiled["compile_pass"]:
        raise RuntimeError(f"Compile failed; see {compiled['compile_log']}")

    terminal_closed = close_terminal(terminal_exe)
    profile_backup = backup_profile(profile_dir, portable_root)
    deployed = deploy_ea(phase1_root, portable_root, compiled)
    armed_preset = write_local_armed_preset(preset_dir)
    new_chart = profile_dir / duplicate_charts[0] if duplicate_charts else append_chart(profile_dir)
    after_profile_edit = chart_inventory(profile_dir)

    startup_before = log_state(files_dir, ARMED_INPUTS["InpStartupLogFileName"])
    launch_started_at = now_utc()
    launched = False
    if launch:
        subprocess.Popen([str(terminal_exe), "/portable"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        launched = True
        wait_for_startup(files_dir, ARMED_INPUTS["InpStartupLogFileName"], startup_before["line_count"], wait_seconds)
    startup_after = log_state(files_dir, ARMED_INPUTS["InpStartupLogFileName"])
    after_launch = chart_inventory(profile_dir)
    runtime_after = broker_runtime_state(terminal_exe) if launch else {"status": "SKIPPED"}

    checks = [
        check("step0_replay_gate_pass", "PASS", gate_summary(gate_payload)),
        check("compile_0_errors_0_warnings", "PASS" if compiled["compile_pass"] else "FAIL", compiled["compile_log"]),
        check("profile_backup_created", "PASS" if Path(profile_backup).exists() else "FAIL", str(profile_backup)),
        check("local_armed_preset_written", "PASS" if Path(armed_preset["path"]).exists() else "FAIL", armed_preset["path"]),
        check("new_chart_added", "PASS" if any(row.expert == EA_NAME for row in after_profile_edit) else "FAIL", str(new_chart)),
        check("manager_defaults_armed_only_in_local_preset", armed_preset_status(armed_preset["values"]), "DryRunOnly=false and ManageActionAllowed=true only in local owner preset/chart."),
        check("managed_magic_allowlist_excludes_933300", "PASS" if EXCLUDED_MAGIC not in ARMED_INPUTS["InpManagedMagicsCsv"] else "FAIL", ARMED_INPUTS["InpManagedMagicsCsv"]),
        check("existing_a3_lanes_preserved", existing_lanes_status(after_profile_edit), "Required entry magics 933200, 933300, and 933400 remain attached."),
        check("terminal_relaunched", "PASS" if launched else "SKIPPED", str(terminal_exe)),
        check("startup_log_present", "PASS" if startup_after["exists"] else "PENDING_RUNTIME_EVIDENCE", startup_after["path"]),
        check("startup_log_armed", startup_armed_status(startup_after), startup_after.get("last_line", "")),
        check("runtime_account_1033669_demo", runtime_account_status(runtime_after), json.dumps(runtime_after.get("account", {}), sort_keys=True)),
        check("execution_kill_switch_absent_at_attach", kill_switch_status(files_dir), str(files_dir / ARMED_INPUTS["InpExecutionKillSwitchFileName"])),
    ]
    status = "PASS" if all(item["status"] in {"PASS", "SKIPPED"} for item in checks) else "PENDING"
    payload: dict[str, Any] = {
        "status": status,
        "created_at_utc": now_utc(),
        "authority": "Owner work order CODEX_WORK_ORDER_A3_PROFIT_LOCK_EXIT_MANAGER_LIVE_2026_06_17.md; Step0 replay gate passed before arming.",
        "boundary": "A3 demo account 1033669 only; XAUUSD only; separate exit manager; no entry EA/kernel edits; SLTP modifications only.",
        "gate": gate_payload,
        "terminal": {
            "portable_root": str(portable_root),
            "terminal_exe": str(terminal_exe),
            "metaeditor_exe": str(metaeditor_exe),
            "terminal_closed_before_profile_change": terminal_closed,
            "terminal_relaunched": launched,
            "launch_started_at_utc": launch_started_at,
            "profile_backup": str(profile_backup),
        },
        "manager": {
            "ea": EA_NAME,
            "symbol": SYMBOL,
            "timeframe": "M5",
            "account_login": ACCOUNT_LOGIN,
            "managed_magics": MANAGED_MAGICS,
            "excluded_magic": EXCLUDED_MAGIC,
            "dry_run": ARMED_INPUTS["InpDryRunOnly"],
            "manage_action_allowed": ARMED_INPUTS["InpManageActionAllowed"],
            "primary_trigger_r": ARMED_INPUTS["InpPrimaryTriggerR"],
            "primary_lock_r": ARMED_INPUTS["InpPrimaryLockR"],
            "secondary_enabled": ARMED_INPUTS["InpSecondaryRungEnabled"],
            "tertiary_enabled": ARMED_INPUTS["InpTertiaryRungEnabled"],
        },
        "compiled": compiled,
        "deployed": deployed,
        "local_armed_preset": armed_preset,
        "new_chart": str(new_chart),
        "startup_log_before": startup_before,
        "startup_log_after": startup_after,
        "runtime_before": runtime_before,
        "runtime_after": runtime_after,
        "before_charts": [row.__dict__ for row in before],
        "after_charts": [row.__dict__ for row in after_launch],
        "checks": checks,
    }
    write_report_pair(output_json, payload, render_report(payload))
    return payload


def load_gate_payload(path: Path) -> dict[str, Any]:
    require_file(path)
    return json.loads(path.read_text(encoding="utf-8"))


def compile_ea(phase1_root: Path, terminal_data_dir: Path, metaeditor_exe: Path) -> dict[str, Any]:
    experts_dir = terminal_data_dir / "MQL5" / "Experts"
    experts_dir.mkdir(parents=True, exist_ok=True)
    source = phase1_root / "mt5" / "Experts" / f"{EA_NAME}.mq5"
    target_source = experts_dir / f"{EA_NAME}.mq5"
    target_ex5 = experts_dir / f"{EA_NAME}.ex5"
    target_log = terminal_data_dir / "MQL5" / "Logs" / "compile_Account3ProfitLockExitManager_20260618.log"
    require_file(source)
    shutil.copy2(source, target_source)
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
        "source": str(source),
        "target_source": str(target_source),
        "target_ex5": str(target_ex5),
        "compile_log": str(target_log),
        "returncode": completed.returncode,
        "compile_pass": target_ex5.exists() and compile_log_passed(target_log),
    }


def deploy_ea(phase1_root: Path, terminal_data_dir: Path, compiled: dict[str, Any]) -> list[str]:
    experts_dir = terminal_data_dir / "MQL5" / "Experts"
    deployed: list[str] = []
    for source, target in [
        (phase1_root / "mt5" / "Experts" / f"{EA_NAME}.mq5", experts_dir / f"{EA_NAME}.mq5"),
        (Path(compiled["target_ex5"]), experts_dir / f"{EA_NAME}.ex5"),
    ]:
        require_file(source)
        if source.resolve() != target.resolve():
            shutil.copy2(source, target)
        deployed.append(str(target))
    return deployed


def write_local_armed_preset(preset_dir: Path) -> dict[str, Any]:
    preset_dir.mkdir(parents=True, exist_ok=True)
    path = preset_dir / f"{EA_NAME}.armed_owner_20260618.set"
    content = "\n".join(f"{key}={value}" for key, value in ARMED_INPUTS.items()) + "\n"
    path.write_text(content, encoding="utf-8")
    return {
        "path": str(path),
        "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "values": dict(ARMED_INPUTS),
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


def broker_runtime_state(terminal_exe: Path) -> dict[str, Any]:
    try:
        import MetaTrader5 as mt5  # type: ignore
    except Exception as exc:
        return {"status": "UNKNOWN", "reason": f"MetaTrader5 import failed: {exc}"}
    if not mt5.initialize(path=str(terminal_exe)):
        return {"status": "UNKNOWN", "reason": f"MetaTrader5 initialize failed: {mt5.last_error()}"}
    try:
        account = mt5.account_info()
        positions = mt5.positions_get(symbol=SYMBOL) or []
        orders = mt5.orders_get(symbol=SYMBOL) or []
        return {
            "status": "PASS" if account and int(account.login) == int(ACCOUNT_LOGIN) and "Demo" in str(account.server) else "FAIL",
            "account": {
                "login": int(account.login) if account else None,
                "server": str(account.server) if account else "",
                "trade_allowed": bool(account.trade_allowed) if account else False,
            },
            "xauusd_positions": [
                {
                    "ticket": int(item.ticket),
                    "magic": int(getattr(item, "magic", 0)),
                    "type": int(getattr(item, "type", 0)),
                    "volume": float(getattr(item, "volume", 0.0)),
                    "price_open": float(getattr(item, "price_open", 0.0)),
                    "sl": float(getattr(item, "sl", 0.0)),
                    "tp": float(getattr(item, "tp", 0.0)),
                    "profit": float(getattr(item, "profit", 0.0)),
                    "comment": str(getattr(item, "comment", "")),
                }
                for item in positions
            ],
            "xauusd_orders": [
                {
                    "ticket": int(item.ticket),
                    "magic": int(getattr(item, "magic", 0)),
                    "type": int(getattr(item, "type", 0)),
                    "volume_current": float(getattr(item, "volume_current", 0.0)),
                    "price_open": float(getattr(item, "price_open", 0.0)),
                    "sl": float(getattr(item, "sl", 0.0)),
                    "tp": float(getattr(item, "tp", 0.0)),
                    "comment": str(getattr(item, "comment", "")),
                }
                for item in orders
            ],
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
        values[key.strip()] = value.strip()
        if in_expert and key.strip() == "name":
            expert_name = value.strip()
    inputs = parse_inputs(text)
    return ChartInventoryRow(
        chart=chart.name,
        symbol=values.get("symbol", ""),
        expert=expert_name,
        magic=inputs.get("InpMagicNumber", ""),
        managed_magics=inputs.get("InpManagedMagicsCsv", ""),
        manage_action_allowed=inputs.get("InpManageActionAllowed", ""),
        broker_action_allowed=inputs.get("InpBrokerActionAllowed", ""),
        dry_run_only=inputs.get("InpDryRunOnly", ""),
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
    backup = terminal_data_dir / "_codex_quarantine" / "profile_backups" / f"default_profile_before_a3_profit_lock_{stamp}"
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(profile_dir, backup)
    return backup


def wait_for_startup(files_dir: Path, startup_name: str, previous_line_count: int, wait_seconds: int) -> None:
    deadline = time.time() + max(0, wait_seconds)
    while time.time() < deadline:
        state = log_state(files_dir, startup_name)
        if (
            state["exists"]
            and state["line_count"] > previous_line_count
            and RUN_ID in state.get("last_line", "")
            and ATTACHED_STATUS in state.get("last_line", "")
        ):
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
    required = [RUN_ID, SYMBOL, MANAGED_MAGICS, "false", "true", ATTACHED_STATUS]
    return "PASS" if all(token in line for token in required) else "PENDING_RUNTIME_EVIDENCE"


def existing_lanes_status(rows: list[ChartInventoryRow]) -> str:
    magics = {row.magic for row in rows}
    return "PASS" if {"933200", "933300", "933400"}.issubset(magics) else "FAIL"


def armed_preset_status(values: dict[str, str]) -> str:
    return "PASS" if values.get("InpDryRunOnly") == "false" and values.get("InpManageActionAllowed") == "true" else "FAIL"


def runtime_account_status(state: dict[str, Any]) -> str:
    account = state.get("account", {})
    return "PASS" if state.get("status") == "PASS" and account.get("login") == int(ACCOUNT_LOGIN) and "Demo" in account.get("server", "") else "FAIL"


def kill_switch_status(files_dir: Path) -> str:
    return "PASS" if not (files_dir / ARMED_INPUTS["InpExecutionKillSwitchFileName"]).exists() else "FAIL"


def gate_summary(payload: dict[str, Any]) -> str:
    dedup = payload.get("views", {}).get("duplicate_hidden", {})
    return (
        f"status={payload.get('status')}; delta={dedup.get('delta_aed')} AED; "
        f"best_day_removed={dedup.get('best_day_removed_delta_aed')} AED; rows={dedup.get('rows')}"
    )


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
    dedup = payload["gate"]["views"]["duplicate_hidden"]
    lines = [
        "# A3 Profit-Lock Exit Manager Attachment",
        "",
        f"Overall status: `{payload['status']}`",
        "",
        str(payload["authority"]),
        "",
        str(payload["boundary"]),
        "",
        "## Step0 Gate",
        "",
        f"- Duplicate-hidden path-covered rows: `{dedup['rows']}`",
        f"- Control PnL: `{dedup['control_aed']:.2f} AED`",
        f"- Replay PnL: `{dedup['replay_aed']:.2f} AED`",
        f"- Delta: `{dedup['delta_aed']:.2f} AED`",
        f"- Best-day-removed delta: `{dedup['best_day_removed_delta_aed']:.2f} AED`",
        "",
        "## Armed Manager",
        "",
        "| Field | Value |",
        "| --- | --- |",
    ]
    for key, value in payload["manager"].items():
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
    lines.extend(["", "## Open XAUUSD Positions After Attach", "", "| Ticket | Magic | Type | Volume | Open | SL | TP | Profit | Comment |", "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |"])
    for row in payload.get("runtime_after", {}).get("xauusd_positions", []):
        lines.append(
            f"| {row['ticket']} | {row['magic']} | {row['type']} | {row['volume']:.2f} | {row['price_open']:.2f} | {row['sl']:.2f} | {row['tp']:.2f} | {row['profit']:.2f} | {escape_md(row['comment'])} |"
        )
    lines.extend(["", "## Before Charts", "", *inventory_table(payload["before_charts"])])
    lines.extend(["", "## After Charts", "", *inventory_table(payload["after_charts"]), ""])
    return "\n".join(lines)


def inventory_table(rows: list[dict[str, str]]) -> list[str]:
    lines = [
        "| Chart | Symbol | Expert | Magic | Managed Magics | Manage Action | Broker Action | Dry Run | Run Id | Comment |",
        "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        values = {key: escape_md(value) for key, value in row.items()}
        lines.append(
            "| {chart} | {symbol} | {expert} | {magic} | {managed_magics} | {manage_action_allowed} | {broker_action_allowed} | {dry_run_only} | {run_id} | {order_comment} |".format(
                **values
            )
        )
    return lines


def escape_md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Attach A3 profit-lock exit manager to the A3 demo portable terminal.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--portable-root", type=Path, default=DEFAULT_PORTABLE_ROOT)
    parser.add_argument("--gate-json", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--no-launch", action="store_true")
    parser.add_argument("--wait-seconds", type=int, default=90)
    parser.add_argument("--allow-existing-chart", action="store_true")
    args = parser.parse_args(argv)
    payload = attach_a3_profit_lock_exit_manager(
        phase1_root=args.phase1_root,
        portable_root=args.portable_root,
        gate_json=args.gate_json,
        output_json=args.output_json,
        launch=not args.no_launch,
        wait_seconds=args.wait_seconds,
        allow_existing_chart=args.allow_existing_chart,
    )
    print(f"A3 profit-lock exit manager attachment: {payload['status']}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
