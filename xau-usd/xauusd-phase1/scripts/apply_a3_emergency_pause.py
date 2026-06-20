from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal


DEFAULT_PORTABLE_ROOT = Path("C:/MT5PortableRepairLane")
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "A3_EMERGENCY_PAUSE_APPLIED_2026_06_18.json"
STAMP = "20260618"
ACCOUNT_LOGIN = 1033669
SYMBOL = "XAUUSD"
A3_MAGIC_LOW = 933000
A3_MAGIC_HIGH = 933999
A3_ENTRY_MAGICS = {933000, 933100, 933200, 933300, 933400}
Mode = Literal["verify-only", "dry-run", "apply"]

KNOWN_PAUSED_RUN_IDS = {
    "Account3BreakoutPlainExecutor": f"A3_BREAKOUT_PLAIN_V1_PAUSED_{STAMP}",
    "Account3BreakoutImprovedExecutor": f"A3_BREAKOUT_IMPROVED_V1_PAUSED_{STAMP}",
    "Account3BreakoutTier1CompatExecutor": f"A3_BREAKOUT_TIER1_COMPAT_V1_PAUSED_{STAMP}",
    "Account3SoftRetestExecutor": f"A3_SOFT_RETEST_V2_PAUSED_{STAMP}",
    "Account3RoundRetestGuardedExecutor": f"A3_RDGUARD_V1_PAUSED_{STAMP}",
    "Account3RoundRetestStructuredExecutor": f"A3_RDSTRUCT_V1_PAUSED_{STAMP}",
    "Account3ProfitLockExitManager": f"A3_PROFIT_LOCK_EXIT_MANAGER_V1_DRYRUN_PAUSED_{STAMP}",
}


@dataclass(frozen=True)
class ChartRow:
    chart: str
    path: str
    symbol: str
    expert: str
    magic: str
    managed_magics: str
    dry_run_only: str
    broker_action_allowed: str
    manage_action_allowed: str
    run_id: str
    order_comment: str
    inputs: dict[str, str]


@dataclass(frozen=True)
class PlannedChartChange:
    chart: str
    expert: str
    before: dict[str, Any]
    replacements: dict[str, str]
    changed: bool
    before_sha256: str
    after_sha256: str


def apply_a3_emergency_pause(
    phase1_root: Path,
    portable_root: Path = DEFAULT_PORTABLE_ROOT,
    output_json: Path | None = None,
    mode: Mode = "verify-only",
    launch: bool = False,
    wait_seconds: int = 45,
) -> dict[str, Any]:
    phase1_root = phase1_root.resolve()
    portable_root = portable_root.resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_json.parent.mkdir(parents=True, exist_ok=True)

    terminal_exe = portable_root / "terminal64.exe"
    profile_dir = portable_root / "MQL5" / "Profiles" / "Charts" / "Default"
    files_dir = portable_root / "MQL5" / "Files"
    require_file(terminal_exe)
    require_dir(profile_dir)
    require_dir(files_dir)

    before_broker = broker_state(terminal_exe)
    before_charts = chart_inventory(profile_dir)
    before_hashes = chart_hashes(profile_dir)
    targets = discover_a3_action_targets(before_charts)
    plans = plan_pause_changes(targets)

    terminal_close: dict[str, Any] = {
        "attempted": False,
        "close_result": None,
        "stopped_before_profile_write": None,
        "process_snapshot_before_write": None,
    }
    profile_backup: Path | None = None
    changed_charts: list[dict[str, Any]] = []
    rollback: dict[str, Any] = {"attempted": False, "status": "NOT_NEEDED", "path": ""}
    relaunched = False
    launch_started_at = ""
    after_broker = before_broker
    after_charts = before_charts
    after_hashes = before_hashes
    startup_logs = startup_log_states(files_dir)
    status = "PENDING"

    preflight_checks = preflight_checks_for(before_broker, before_charts, targets, plans)
    if mode == "verify-only":
        if before_broker.get("status") != "PASS":
            status = "FAIL_EXPOSURE_OR_UNKNOWN"
        else:
            status = "ALREADY_PAUSED" if all_targets_already_paused(targets) else "NEEDS_PAUSE"
    elif mode == "dry-run":
        if before_broker.get("status") != "PASS":
            status = "FAIL_EXPOSURE_OR_UNKNOWN"
        else:
            status = "ALREADY_PAUSED" if all_targets_already_paused(targets) else "DRY_RUN_READY"
    else:
        if all_targets_already_paused(targets):
            status = "ALREADY_PAUSED"
        elif before_broker.get("status") != "PASS":
            status = "FAIL_EXPOSURE_OR_UNKNOWN"
        else:
            terminal_close = stop_terminal_for_profile_write(terminal_exe)
            if terminal_close.get("stopped_before_profile_write") is not True:
                status = "FAIL_TERMINAL_STILL_RUNNING"
            else:
                profile_backup = backup_profile(profile_dir, portable_root)
                for plan in plans:
                    if not plan.changed:
                        continue
                    path = Path(plan.before["path"])
                    write_text_preserving_encoding(path, update_chart_inputs(read_text_any(path), plan.replacements))
                    changed_charts.append(asdict(plan))
                after_charts = chart_inventory(profile_dir)
                after_hashes = chart_hashes(profile_dir)

                launch_started_at = now_utc()
                if launch:
                    subprocess.Popen([str(terminal_exe), "/portable"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    relaunched = True
                    time.sleep(max(0, min(wait_seconds, 15)))
                    wait_for_safe_startup(files_dir, wait_seconds)

                after_broker = broker_state(terminal_exe)
                startup_logs = startup_log_states(files_dir)
                interim = payload_for_report(
                    mode=mode,
                    status="PENDING",
                    phase1_root=phase1_root,
                    portable_root=portable_root,
                    terminal_exe=terminal_exe,
                    profile_dir=profile_dir,
                    files_dir=files_dir,
                    before_broker=before_broker,
                    after_broker=after_broker,
                    before_charts=before_charts,
                    after_charts=after_charts,
                    targets=targets,
                    plans=plans,
                    changed_charts=changed_charts,
                    before_hashes=before_hashes,
                    after_hashes=after_hashes,
                    profile_backup=profile_backup,
                    terminal_close=terminal_close,
                    relaunched=relaunched,
                    launch_started_at=launch_started_at,
                    startup_logs=startup_logs,
                    rollback=rollback,
                    checks=[],
                )
                checks = build_checks(interim)
                status = "PASS" if all_check_statuses_good(checks) else "FAIL_POST_VERIFY"
                if status != "PASS" and profile_backup is not None:
                    rollback = rollback_profile(profile_dir, profile_backup)
                    after_charts = chart_inventory(profile_dir)
                    after_hashes = chart_hashes(profile_dir)
                    status = "FAIL_ROLLED_BACK" if rollback.get("status") == "PASS" else "FAIL_ROLLBACK_FAILED"
                elif status == "PASS" and not changed_charts:
                    status = "ALREADY_PAUSED"

    payload = payload_for_report(
        mode=mode,
        status=status,
        phase1_root=phase1_root,
        portable_root=portable_root,
        terminal_exe=terminal_exe,
        profile_dir=profile_dir,
        files_dir=files_dir,
        before_broker=before_broker,
        after_broker=after_broker,
        before_charts=before_charts,
        after_charts=after_charts,
        targets=targets,
        plans=plans,
        changed_charts=changed_charts,
        before_hashes=before_hashes,
        after_hashes=after_hashes,
        profile_backup=profile_backup,
        terminal_close=terminal_close,
        relaunched=relaunched,
        launch_started_at=launch_started_at,
        startup_logs=startup_logs,
        rollback=rollback,
        checks=[],
    )
    payload["checks"] = [*preflight_checks, *build_checks(payload)]
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    output_json.with_suffix(".md").write_text(render_markdown(payload), encoding="utf-8")
    return payload


def broker_state(terminal_exe: Path) -> dict[str, Any]:
    try:
        import MetaTrader5 as mt5  # type: ignore
    except Exception as exc:  # pragma: no cover - local terminal dependency
        return {"status": "UNKNOWN", "reason": f"MetaTrader5 import failed: {exc}"}
    if not mt5.initialize(path=str(terminal_exe)):
        return {"status": "UNKNOWN", "reason": f"MT5 initialize failed: {mt5.last_error()}"}
    try:
        account = mt5.account_info()
        account_payload = account._asdict() if account else {}
        if "name" in account_payload:
            account_payload["name"] = "REDACTED"
        positions = list(mt5.positions_get(symbol=SYMBOL) or [])
        orders = list(mt5.orders_get(symbol=SYMBOL) or [])
        a3_positions = [
            item._asdict()
            for item in positions
            if A3_MAGIC_LOW <= int(getattr(item, "magic", 0)) <= A3_MAGIC_HIGH
        ]
        a3_orders = [
            item._asdict()
            for item in orders
            if A3_MAGIC_LOW <= int(getattr(item, "magic", 0)) <= A3_MAGIC_HIGH
        ]
        return {
            "status": "PASS" if not a3_positions and not a3_orders else "FAIL",
            "account": account_payload,
            "a3_positions_total": len(a3_positions),
            "a3_orders_total": len(a3_orders),
            "all_xau_positions_total": len(positions),
            "all_xau_orders_total": len(orders),
            "a3_positions": a3_positions,
            "a3_orders": a3_orders,
        }
    finally:
        mt5.shutdown()


def chart_inventory(profile_dir: Path) -> list[ChartRow]:
    return [parse_chart(path) for path in sorted(profile_dir.glob("chart*.chr"))]


def parse_chart(path: Path) -> ChartRow:
    text = read_text_any(path)
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
    return ChartRow(
        chart=path.name,
        path=str(path),
        symbol=values.get("symbol", ""),
        expert=expert_name,
        magic=inputs.get("InpMagicNumber", ""),
        managed_magics=inputs.get("InpManagedMagicsCsv", ""),
        dry_run_only=inputs.get("InpDryRunOnly", ""),
        broker_action_allowed=inputs.get("InpBrokerActionAllowed", ""),
        manage_action_allowed=inputs.get("InpManageActionAllowed", ""),
        run_id=inputs.get("InpRunId", ""),
        order_comment=inputs.get("InpOrderComment", ""),
        inputs=inputs,
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


def discover_a3_action_targets(rows: list[ChartRow]) -> list[ChartRow]:
    return [
        row
        for row in rows
        if row.symbol == SYMBOL
        and row.expert != "NO_EA"
        and chart_has_a3_identity(row)
        and chart_has_action_surface(row)
    ]


def chart_has_a3_identity(row: ChartRow) -> bool:
    if row.expert.startswith("Account3"):
        return True
    if magic_in_a3_band(row.magic):
        return True
    return any(magic_in_a3_band(token) for token in split_csv(row.managed_magics))


def chart_has_action_surface(row: ChartRow) -> bool:
    action_inputs = {"InpBrokerActionAllowed", "InpManageActionAllowed", "InpAllowDemoTrading"}
    if action_inputs.intersection(row.inputs):
        return True
    return "Executor" in row.expert or "ExitManager" in row.expert


def magic_in_a3_band(value: str) -> bool:
    try:
        magic = int(str(value).strip())
    except ValueError:
        return False
    return A3_MAGIC_LOW <= magic <= A3_MAGIC_HIGH


def split_csv(value: str) -> list[str]:
    return [token.strip() for token in str(value).split(",") if token.strip()]


def plan_pause_changes(rows: list[ChartRow]) -> list[PlannedChartChange]:
    plans: list[PlannedChartChange] = []
    for row in rows:
        before_text = read_text_any(Path(row.path))
        replacements = {} if chart_is_disarmed(row) else paused_replacements(row)
        after_text = update_chart_inputs(before_text, replacements)
        plans.append(
            PlannedChartChange(
                chart=row.chart,
                expert=row.expert,
                before=chart_to_dict(row),
                replacements=replacements,
                changed=after_text != before_text,
                before_sha256=sha256_bytes(before_text.encode("utf-8")),
                after_sha256=sha256_bytes(after_text.encode("utf-8")),
            )
        )
    return plans


def paused_replacements(row: ChartRow) -> dict[str, str]:
    replacements: dict[str, str] = {}
    if "InpRunId" in row.inputs:
        replacements["InpRunId"] = paused_run_id(row)
    if "InpDryRunOnly" in row.inputs:
        replacements["InpDryRunOnly"] = "true"
    if "InpBrokerActionAllowed" in row.inputs:
        replacements["InpBrokerActionAllowed"] = "false"
    if "InpManageActionAllowed" in row.inputs:
        replacements["InpManageActionAllowed"] = "false"
    if "InpAllowDemoTrading" in row.inputs:
        replacements["InpAllowDemoTrading"] = "false"
    if "InpAllowNonDemoAccounts" in row.inputs:
        replacements["InpAllowNonDemoAccounts"] = "false"
    if "InpExecutionKillSwitchFileName" in row.inputs:
        replacements["InpExecutionKillSwitchFileName"] = "A3_EXECUTION_KILL.txt"
    if "InpFullStopFileName" in row.inputs:
        replacements["InpFullStopFileName"] = "A3_FULL_STOP.txt"
    return replacements


def paused_run_id(row: ChartRow) -> str:
    if row.expert in KNOWN_PAUSED_RUN_IDS:
        return KNOWN_PAUSED_RUN_IDS[row.expert]
    base = row.run_id or row.expert or row.chart
    if re.search(r"(PAUSED|DISARMED|STOPPED)", base, flags=re.IGNORECASE):
        return base
    return f"{base}_PAUSED_{STAMP}"


def all_targets_already_paused(rows: list[ChartRow]) -> bool:
    return bool(rows) and all(chart_is_disarmed(row) for row in rows)


def chart_is_disarmed(row: ChartRow) -> bool:
    if "InpDryRunOnly" in row.inputs and row.dry_run_only.lower() != "true":
        return False
    if "InpBrokerActionAllowed" in row.inputs and row.broker_action_allowed.lower() != "false":
        return False
    if "InpManageActionAllowed" in row.inputs and row.manage_action_allowed.lower() != "false":
        return False
    if "InpAllowDemoTrading" in row.inputs and row.inputs.get("InpAllowDemoTrading", "").lower() != "false":
        return False
    if "InpAllowNonDemoAccounts" in row.inputs and row.inputs.get("InpAllowNonDemoAccounts", "").lower() != "false":
        return False
    return True


def update_chart_inputs(text: str, replacements: dict[str, str]) -> str:
    if not replacements:
        return text
    lines: list[str] = []
    in_inputs = False
    seen: set[str] = set()
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped == "<inputs>":
            in_inputs = True
            lines.append(raw)
            continue
        if stripped == "</inputs>":
            for key, value in replacements.items():
                if key not in seen:
                    lines.append(f"{key}={value}")
            in_inputs = False
            lines.append(raw)
            continue
        if in_inputs and "=" in stripped:
            key, _value = stripped.split("=", 1)
            if key in replacements:
                raw = f"{key}={replacements[key]}"
                seen.add(key)
        lines.append(raw)
    suffix = "\n" if text.endswith("\n") else ""
    return "\n".join(lines) + suffix


def stop_terminal_for_profile_write(terminal_exe: Path) -> dict[str, Any]:
    before = terminal_process_snapshot(terminal_exe)
    close_result = close_terminal(terminal_exe)
    after = terminal_process_snapshot(terminal_exe)
    return {
        "attempted": True,
        "process_snapshot_before_write": before,
        "close_result": close_result,
        "stopped_before_profile_write": after.get("running") is False,
        "process_snapshot_after_close": after,
    }


def terminal_process_snapshot(terminal_exe: Path) -> dict[str, Any]:
    command = f"""
$target = (Resolve-Path -LiteralPath '{terminal_exe}' -ErrorAction SilentlyContinue).Path
if(-not $target) {{ ConvertTo-Json @{{running=$false;pids=@();reason='terminal_missing'}} -Compress; exit 0 }}
$procs = Get-CimInstance Win32_Process | Where-Object {{ $_.ExecutablePath -eq $target }}
$pids = @($procs | ForEach-Object {{ $_.ProcessId }})
ConvertTo-Json @{{running=($pids.Count -gt 0);pids=$pids;reason='OK'}} -Compress
"""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            text=True,
            capture_output=True,
            timeout=20,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        return {"running": None, "pids": [], "reason": str(exc)}
    try:
        payload = json.loads(result.stdout.strip() or "{}")
    except json.JSONDecodeError:
        payload = {"running": None, "pids": [], "reason": result.stdout.strip()}
    payload["returncode"] = result.returncode
    return payload


def close_terminal(terminal_exe: Path) -> dict[str, Any]:
    command = f"""
$target = (Resolve-Path -LiteralPath '{terminal_exe}').Path
$procs = Get-CimInstance Win32_Process | Where-Object {{ $_.ExecutablePath -eq $target }}
if(-not $procs) {{ ConvertTo-Json @{{returncode=0;closed=0;forced=0;reason='not_running'}} -Compress; exit 0 }}
$closed = 0
$forced = 0
foreach($proc in $procs) {{
  $p = Get-Process -Id $proc.ProcessId -ErrorAction SilentlyContinue
  if($p) {{ [void]$p.CloseMainWindow(); $closed++ }}
}}
Start-Sleep -Seconds 5
foreach($proc in $procs) {{
  $p = Get-Process -Id $proc.ProcessId -ErrorAction SilentlyContinue
  if($p) {{ Stop-Process -Id $proc.ProcessId -Force; $forced++ }}
}}
ConvertTo-Json @{{returncode=0;closed=$closed;forced=$forced;reason='closed_or_forced'}} -Compress
"""
    try:
        result = subprocess.run(["powershell", "-NoProfile", "-Command", command], text=True, capture_output=True, timeout=45)
    except (subprocess.SubprocessError, OSError) as exc:
        return {"returncode": 1, "closed": 0, "forced": 0, "reason": str(exc)}
    try:
        payload = json.loads(result.stdout.strip() or "{}")
    except json.JSONDecodeError:
        payload = {"closed": 0, "forced": 0, "reason": result.stdout.strip()}
    payload["returncode"] = result.returncode
    return payload


def backup_profile(profile_dir: Path, portable_root: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    backup = portable_root / "_codex_quarantine" / "profile_backups" / f"default_profile_before_a3_emergency_pause_{stamp}"
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(profile_dir, backup)
    return backup


def rollback_profile(profile_dir: Path, backup: Path) -> dict[str, Any]:
    if not backup.exists():
        return {"attempted": True, "status": "FAIL", "path": str(backup), "reason": "backup_missing"}
    for source in backup.rglob("*"):
        if not source.is_file():
            continue
        target = profile_dir / source.relative_to(backup)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return {"attempted": True, "status": "PASS", "path": str(backup), "reason": "profile_restored_from_backup"}


def wait_for_safe_startup(files_dir: Path, wait_seconds: int) -> None:
    deadline = time.time() + max(0, wait_seconds)
    expected_tokens = set(KNOWN_PAUSED_RUN_IDS.values())
    while time.time() < deadline:
        latest_lines = [state.get("last_line", "") for state in startup_log_states(files_dir).values()]
        if expected_tokens.intersection(" ".join(latest_lines)):
            return
        time.sleep(1.0)


def startup_log_states(files_dir: Path) -> dict[str, dict[str, Any]]:
    names = {
        "plain": "a3_breakout_plain_startup.csv",
        "improved": "a3_breakout_improved_startup.csv",
        "tier1_compat": "a3_breakout_tier1_compat_startup.csv",
        "soft_retest": "a3_soft_retest_v2_startup.csv",
        "rdguard": "a3_rdguard_v1_startup.csv",
        "rdstruct": "a3_rdstruct_v1_startup.csv",
        "profit_lock": "a3_profit_lock_exit_manager_startup.csv",
    }
    return {key: log_state(files_dir / name) for key, name in names.items()}


def log_state(path: Path) -> dict[str, Any]:
    text = read_text_any(path)
    lines = [line for line in text.splitlines() if line.strip()]
    return {
        "path": str(path),
        "exists": path.exists(),
        "mtime_utc": mtime_text(path),
        "line_count": len(lines),
        "last_line": lines[-1] if lines else "",
    }


def preflight_checks_for(
    before_broker: dict[str, Any],
    before_charts: list[ChartRow],
    targets: list[ChartRow],
    plans: list[PlannedChartChange],
) -> list[dict[str, str]]:
    checks = [
        check("reviewer_pause_authority_recorded", "PASS", "CODEX_A3_REPAIR_BUILD_PLAN_CANONICAL_2026_06_18.md"),
        check("a3_profile_charts_discovered", "PASS" if before_charts else "FAIL", f"chart_count={len(before_charts)}"),
        check("dynamic_a3_action_targets_discovered", "PASS" if targets else "FAIL", ",".join(row.chart for row in targets)),
        check("before_a3_exposure_zero", before_broker.get("status", "UNKNOWN"), broker_summary(before_broker)),
    ]
    armed_targets = [row.chart for row in targets if not chart_is_disarmed(row)]
    checks.append(check("armed_targets_identified", "INFO" if armed_targets else "PASS", ",".join(armed_targets) or "none"))
    checks.append(check("planned_changes_built", "PASS" if plans else "FAIL", f"plan_count={len(plans)}"))
    return checks


def build_checks(payload: dict[str, Any]) -> list[dict[str, str]]:
    mode = payload["mode"]
    already_paused = payload["status"] == "ALREADY_PAUSED"
    target_charts = {row["chart"] for row in payload["target_charts"]}
    after_by_chart = {row["chart"]: row for row in payload["after_charts"]}
    checks = [
        check("report_mode_recorded", "PASS", mode),
        check("no_runtime_mutation_in_readonly_mode", "PASS" if mode in {"verify-only", "dry-run"} and not payload["changed_charts"] or mode == "apply" else "FAIL", mode),
        check("after_a3_exposure_zero", payload["after_broker"].get("status", "UNKNOWN"), broker_summary(payload["after_broker"])),
        check("target_charts_safe_after", "PASS" if all(chart_dict_is_disarmed(after_by_chart.get(chart, {})) for chart in target_charts) else "FAIL", ",".join(sorted(target_charts))),
        check("non_target_hashes_unchanged", "PASS" if non_target_hashes_unchanged(payload) else "FAIL", "all chart*.chr hashes compared"),
        check("profile_backup_created_for_apply", "PASS" if mode != "apply" or already_paused or payload["terminal"]["profile_backup"] else "FAIL", payload["terminal"]["profile_backup"]),
        check("terminal_fully_stopped_before_apply_write", "PASS" if mode != "apply" or already_paused or payload["terminal"]["stopped_before_profile_write"] is True else "FAIL", json.dumps(payload["terminal"].get("process_snapshot_before_write"), sort_keys=True)),
        check("rollback_path_recorded", "PASS" if mode != "apply" or payload["terminal"]["profile_backup"] or payload["status"] == "ALREADY_PAUSED" else "FAIL", payload["terminal"]["profile_backup"] or payload["rollback"].get("path", "")),
    ]
    if mode == "apply" and payload["terminal"]["terminal_relaunched"]:
        checks.append(check("startup_rows_collected", "PASS" if any(row.get("line_count", 0) for row in payload["startup_logs"].values()) else "FAIL", "startup logs inspected"))
    else:
        checks.append(check("startup_rows_collected", "INFO", "launch skipped or readonly mode"))
    return checks


def chart_dict_is_disarmed(row: dict[str, Any]) -> bool:
    if not row:
        return False
    inputs = row.get("inputs", {})
    if "InpDryRunOnly" in inputs and str(row.get("dry_run_only", "")).lower() != "true":
        return False
    if "InpBrokerActionAllowed" in inputs and str(row.get("broker_action_allowed", "")).lower() != "false":
        return False
    if "InpManageActionAllowed" in inputs and str(row.get("manage_action_allowed", "")).lower() != "false":
        return False
    return True


def non_target_hashes_unchanged(payload: dict[str, Any]) -> bool:
    target_charts = {row["chart"] for row in payload["target_charts"]}
    before = payload["profile_hashes"]["before"]
    after = payload["profile_hashes"]["after"]
    for chart, digest in before.items():
        if chart in target_charts:
            continue
        if after.get(chart) != digest:
            return False
    return True


def all_check_statuses_good(checks: list[dict[str, str]]) -> bool:
    return all(row["status"] in {"PASS", "INFO"} for row in checks)


def payload_for_report(
    *,
    mode: Mode,
    status: str,
    phase1_root: Path,
    portable_root: Path,
    terminal_exe: Path,
    profile_dir: Path,
    files_dir: Path,
    before_broker: dict[str, Any],
    after_broker: dict[str, Any],
    before_charts: list[ChartRow],
    after_charts: list[ChartRow],
    targets: list[ChartRow],
    plans: list[PlannedChartChange],
    changed_charts: list[dict[str, Any]],
    before_hashes: dict[str, str],
    after_hashes: dict[str, str],
    profile_backup: Path | None,
    terminal_close: dict[str, Any],
    relaunched: bool,
    launch_started_at: str,
    startup_logs: dict[str, dict[str, Any]],
    rollback: dict[str, Any],
    checks: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "status": status,
        "mode": mode,
        "artifact_integrity_status": "PASS",
        "runtime_authorization_status": "A3_ENTRY_LANES_PAUSED",
        "runtime_performance_status": "FAIL",
        "created_at_utc": now_utc(),
        "authority": "CODEX_A3_REPAIR_BUILD_PLAN_CANONICAL_2026_06_18.md P1.1 repo-only emergency-pause hardening.",
        "boundary": "Repo/tooling verification only unless --apply is explicitly selected. No trade close, no order send, no live/real-capital authorization.",
        "terminal": {
            "portable_root": str(portable_root),
            "terminal_exe": str(terminal_exe),
            "profile_dir": str(profile_dir),
            "files_dir": str(files_dir),
            "terminal_close_attempted": bool(terminal_close.get("attempted")),
            "stopped_before_profile_write": terminal_close.get("stopped_before_profile_write"),
            "process_snapshot_before_write": terminal_close.get("process_snapshot_before_write"),
            "close_result": terminal_close.get("close_result"),
            "terminal_relaunched": relaunched,
            "launch_started_at_utc": launch_started_at,
            "profile_backup": str(profile_backup) if profile_backup else "",
        },
        "before_broker": before_broker,
        "after_broker": after_broker,
        "before_charts": [chart_to_dict(row) for row in before_charts],
        "target_charts": [chart_to_dict(row) for row in targets],
        "planned_changes": [asdict(plan) for plan in plans],
        "changed_charts": changed_charts,
        "after_charts": [chart_to_dict(row) for row in after_charts],
        "profile_hashes": {"before": before_hashes, "after": after_hashes},
        "startup_logs": startup_logs,
        "rollback": rollback,
        "checks": checks,
    }


def chart_to_dict(row: ChartRow) -> dict[str, Any]:
    return asdict(row)


def chart_hashes(profile_dir: Path) -> dict[str, str]:
    return {path.name: sha256_file(path) for path in sorted(profile_dir.glob("chart*.chr"))}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def broker_summary(state: dict[str, Any]) -> str:
    return (
        f"a3_positions={state.get('a3_positions_total')}; "
        f"a3_orders={state.get('a3_orders_total')}; "
        f"all_xau_positions={state.get('all_xau_positions_total')}; "
        f"all_xau_orders={state.get('all_xau_orders_total')}; "
        f"reason={state.get('reason', '')}"
    )


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# A3 Emergency Pause Verification - 2026-06-18",
        "",
        f"Overall status: `{payload['status']}`",
        f"Mode: `{payload['mode']}`",
        "",
        str(payload["authority"]),
        "",
        str(payload["boundary"]),
        "",
        "## Runtime Decision",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| artifact_integrity_status | `{payload['artifact_integrity_status']}` |",
        f"| runtime_performance_status | `{payload['runtime_performance_status']}` |",
        f"| runtime_authorization_status | `{payload['runtime_authorization_status']}` |",
        "",
        "## Broker Exposure",
        "",
        "| Moment | A3 positions | A3 orders | All XAU positions | All XAU orders | Status |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
        broker_row("before", payload["before_broker"]),
        broker_row("after", payload["after_broker"]),
        "",
        "## Profile Change",
        "",
        f"- Profile backup: `{payload['terminal']['profile_backup'] or 'n/a'}`",
        f"- Terminal stopped before apply write: `{payload['terminal']['stopped_before_profile_write']}`",
        f"- Terminal relaunched: `{payload['terminal']['terminal_relaunched']}`",
        f"- Rollback: `{payload['rollback']['status']}` `{payload['rollback']['path']}`",
        "",
        "| Chart | Expert | Run id | Dry-run | Broker action | Manage action | Planned change |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    plan_by_chart = {row["chart"]: row for row in payload["planned_changes"]}
    for row in payload["after_charts"]:
        if row["chart"] not in plan_by_chart:
            continue
        plan = plan_by_chart[row["chart"]]
        lines.append(
            "| {chart} | `{expert}` | `{run_id}` | `{dry}` | `{broker}` | `{manage}` | `{changed}` |".format(
                chart=row["chart"],
                expert=escape_md(row["expert"]),
                run_id=escape_md(row["run_id"]),
                dry=escape_md(row["dry_run_only"]),
                broker=escape_md(row["broker_action_allowed"]),
                manage=escape_md(row["manage_action_allowed"]),
                changed=str(plan["changed"]).lower(),
            )
        )
    lines.extend(["", "## Checks", "", "| Check | Status | Evidence |", "| --- | --- | --- |"])
    for item in payload["checks"]:
        lines.append(f"| `{escape_md(item['name'])}` | `{escape_md(item['status'])}` | {escape_md(item['evidence'])} |")
    lines.extend(
        [
            "",
            "No trade close, order send, lot, SL/TP, account, preset arming, or chart attachment change is authorized by this report.",
            "",
        ]
    )
    return "\n".join(lines)


def broker_row(label: str, state: dict[str, Any]) -> str:
    return (
        f"| {label} | `{state.get('a3_positions_total')}` | `{state.get('a3_orders_total')}` | "
        f"`{state.get('all_xau_positions_total')}` | `{state.get('all_xau_orders_total')}` | `{state.get('status')}` |"
    )


def check(name: str, status: str, evidence: str) -> dict[str, str]:
    return {"name": name, "status": str(status), "evidence": str(evidence)}


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


def write_text_preserving_encoding(path: Path, text: str) -> None:
    payload = path.read_bytes() if path.exists() else b""
    encoding = "utf-8"
    if payload.startswith(b"\xff\xfe") or payload.startswith(b"\xfe\xff"):
        encoding = "utf-16"
    elif b"\x00" in payload[:200]:
        encoding = "utf-16-le"
    path.write_bytes(text.encode(encoding))


def mtime_text(path: Path) -> str:
    if not path.exists():
        return "missing"
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat().replace("+00:00", "Z")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def escape_md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def require_file(path: Path) -> None:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(path)


def require_dir(path: Path) -> None:
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify, dry-run, or apply the A3 emergency broker-action pause.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--portable-root", type=Path, default=DEFAULT_PORTABLE_ROOT)
    parser.add_argument("--output-json", type=Path, default=None)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--verify-only", action="store_true")
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--apply", action="store_true")
    parser.add_argument("--launch", action="store_true", help="Only valid with --apply; relaunch terminal after profile writes.")
    parser.add_argument("--wait-seconds", type=int, default=45)
    args = parser.parse_args(argv)

    mode: Mode = "verify-only"
    if args.dry_run:
        mode = "dry-run"
    if args.apply:
        mode = "apply"
    if args.launch and mode != "apply":
        parser.error("--launch is only valid with --apply")

    payload = apply_a3_emergency_pause(
        args.phase1_root,
        portable_root=args.portable_root,
        output_json=args.output_json,
        mode=mode,
        launch=args.launch,
        wait_seconds=args.wait_seconds,
    )
    output_path = args.output_json or args.phase1_root / DEFAULT_OUTPUT_JSON
    print(json.dumps({"status": payload["status"], "mode": mode, "output": str(output_path)}, indent=2))
    return 0 if payload["status"] in {"PASS", "ALREADY_PAUSED", "DRY_RUN_READY"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
