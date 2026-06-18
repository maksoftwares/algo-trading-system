from __future__ import annotations

import argparse
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
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "A3_EMERGENCY_PAUSE_APPLIED_2026_06_18.json"
STAMP = "20260618"
ACCOUNT_LOGIN = 1033669
SYMBOL = "XAUUSD"
A3_ENTRY_MAGICS = {933200, 933300, 933400}

PAUSE_TARGETS = {
    "Account3BreakoutImprovedExecutor": {
        "InpRunId": f"A3_BREAKOUT_IMPROVED_V1_PAUSED_{STAMP}",
        "InpDryRunOnly": "true",
        "InpBrokerActionAllowed": "false",
    },
    "Account3BreakoutTier1CompatExecutor": {
        "InpRunId": f"A3_BREAKOUT_TIER1_COMPAT_V1_PAUSED_{STAMP}",
        "InpDryRunOnly": "true",
        "InpBrokerActionAllowed": "false",
    },
    "Account3ProfitLockExitManager": {
        "InpRunId": f"A3_PROFIT_LOCK_EXIT_MANAGER_V1_DRYRUN_PAUSED_{STAMP}",
        "InpDryRunOnly": "true",
        "InpManageActionAllowed": "false",
    },
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


def apply_a3_emergency_pause(
    phase1_root: Path,
    portable_root: Path = DEFAULT_PORTABLE_ROOT,
    output_json: Path | None = None,
    launch: bool = True,
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
    target_errors = required_targets_status(before_charts)
    if target_errors:
        raise RuntimeError("; ".join(target_errors))

    terminal_closed = close_terminal(terminal_exe)
    profile_backup = backup_profile(profile_dir, portable_root)

    changed_charts: list[dict[str, Any]] = []
    for row in before_charts:
        if row.expert not in PAUSE_TARGETS:
            continue
        path = Path(row.path)
        before_text = read_text_any(path)
        after_text = update_chart_inputs(before_text, PAUSE_TARGETS[row.expert])
        if after_text != before_text:
            path.write_text(after_text, encoding="utf-8")
        changed_charts.append(
            {
                "chart": row.chart,
                "expert": row.expert,
                "before": row.__dict__,
                "after_inputs": dict(PAUSE_TARGETS[row.expert]),
                "changed": after_text != before_text,
            }
        )

    after_profile_edit = chart_inventory(profile_dir)
    launch_started_at = now_utc()
    relaunched = False
    if launch:
        subprocess.Popen([str(terminal_exe), "/portable"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        relaunched = True
        time.sleep(max(0, min(wait_seconds, 15)))
        wait_for_safe_startup(files_dir, wait_seconds)

    after_launch_charts = chart_inventory(profile_dir)
    after_broker = broker_state(terminal_exe)
    startup_logs = {
        "plain": log_state(files_dir / "a3_breakout_plain_startup.csv"),
        "improved": log_state(files_dir / "a3_breakout_improved_startup.csv"),
        "tier1_compat": log_state(files_dir / "a3_breakout_tier1_compat_startup.csv"),
        "profit_lock": log_state(files_dir / "a3_profit_lock_exit_manager_startup.csv"),
    }
    checks = build_checks(
        before_broker=before_broker,
        after_broker=after_broker,
        before_charts=before_charts,
        after_charts=after_launch_charts,
        changed_charts=changed_charts,
        profile_backup=profile_backup,
        terminal_closed=terminal_closed,
        relaunched=relaunched,
        startup_logs=startup_logs,
    )
    status = "PASS" if all(row["status"] in {"PASS", "INFO"} for row in checks) else "FAIL"
    payload: dict[str, Any] = {
        "status": status,
        "artifact_integrity_status": "PASS",
        "runtime_authorization_status": "A3_ENTRY_LANES_PAUSED",
        "runtime_performance_status": "FAIL_PRIOR_TO_PAUSE",
        "created_at_utc": now_utc(),
        "authority": "Reviewer FINAL_REVIEW_C9889CB_A3_FOLLOWUP_2026_06_18.md recommended emergency risk-reducing pause.",
        "boundary": "Demo-only maintenance. No trade close, no order send, no EA source change, no signal-filter deployment, no live/real-capital authorization.",
        "terminal": {
            "portable_root": str(portable_root),
            "terminal_exe": str(terminal_exe),
            "profile_dir": str(profile_dir),
            "files_dir": str(files_dir),
            "terminal_closed_before_profile_change": terminal_closed,
            "terminal_relaunched": relaunched,
            "launch_started_at_utc": launch_started_at,
            "profile_backup": str(profile_backup),
        },
        "pause_targets": PAUSE_TARGETS,
        "before_broker": before_broker,
        "after_broker": after_broker,
        "before_charts": [row.__dict__ for row in before_charts],
        "changed_charts": changed_charts,
        "after_charts": [row.__dict__ for row in after_launch_charts],
        "startup_logs": startup_logs,
        "checks": checks,
    }
    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
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
        positions = list(mt5.positions_get(symbol=SYMBOL) or [])
        orders = list(mt5.orders_get(symbol=SYMBOL) or [])
        a3_positions = [item._asdict() for item in positions if int(getattr(item, "magic", 0)) in A3_ENTRY_MAGICS]
        a3_orders = [item._asdict() for item in orders if int(getattr(item, "magic", 0)) in A3_ENTRY_MAGICS]
        return {
            "status": "PASS" if not a3_positions and not a3_orders else "FAIL",
            "account": account._asdict() if account else {},
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


def required_targets_status(rows: list[ChartRow]) -> list[str]:
    errors: list[str] = []
    experts = {row.expert: row for row in rows}
    for expert in PAUSE_TARGETS:
        if expert not in experts:
            errors.append(f"Missing required pause target chart for {expert}")
    plain = next((row for row in rows if row.magic == "933200"), None)
    if not plain:
        errors.append("Missing plain 933200 chart")
    elif plain.dry_run_only.lower() != "true" or plain.broker_action_allowed.lower() != "false":
        errors.append(f"Plain 933200 not already stopped: {plain}")
    return errors


def update_chart_inputs(text: str, replacements: dict[str, str]) -> str:
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


def backup_profile(profile_dir: Path, portable_root: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup = portable_root / "_codex_quarantine" / "profile_backups" / f"default_profile_before_a3_emergency_pause_{stamp}"
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(profile_dir, backup)
    return backup


def wait_for_safe_startup(files_dir: Path, wait_seconds: int) -> None:
    deadline = time.time() + max(0, wait_seconds)
    required = {
        "a3_breakout_improved_startup.csv": "A3_BREAKOUT_IMPROVED_V1_PAUSED_20260618",
        "a3_breakout_tier1_compat_startup.csv": "A3_BREAKOUT_TIER1_COMPAT_V1_PAUSED_20260618",
        "a3_profit_lock_exit_manager_startup.csv": "A3_PROFIT_LOCK_EXIT_MANAGER_V1_DRYRUN_PAUSED_20260618",
    }
    while time.time() < deadline:
        if all(token in log_state(files_dir / name).get("last_line", "") for name, token in required.items()):
            return
        time.sleep(1.0)


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


def build_checks(
    *,
    before_broker: dict[str, Any],
    after_broker: dict[str, Any],
    before_charts: list[ChartRow],
    after_charts: list[ChartRow],
    changed_charts: list[dict[str, Any]],
    profile_backup: Path,
    terminal_closed: bool,
    relaunched: bool,
    startup_logs: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    after_by_expert = {row.expert: row for row in after_charts}
    checks = [
        check("reviewer_pause_authority_recorded", "PASS", "FINAL_REVIEW_C9889CB_A3_FOLLOWUP_2026_06_18.md"),
        check("no_a3_open_positions_before_pause", before_broker.get("status", "UNKNOWN"), broker_summary(before_broker)),
        check("profile_backup_created", "PASS" if profile_backup.exists() else "FAIL", str(profile_backup)),
        check("terminal_closed_before_profile_change", "PASS" if terminal_closed else "FAIL", "terminal64.exe close/force-stop attempted"),
        check("terminal_relaunched", "PASS" if relaunched else "INFO", str(DEFAULT_PORTABLE_ROOT / "terminal64.exe")),
        check("no_a3_open_positions_after_pause", after_broker.get("status", "UNKNOWN"), broker_summary(after_broker)),
    ]
    for expert, expected in PAUSE_TARGETS.items():
        row = after_by_expert.get(expert)
        if not row:
            checks.append(check(f"{expert}_chart_present", "FAIL", "missing"))
            continue
        details = row.__dict__
        ok = all(str(details.get(input_to_field(key), "")).lower() == value.lower() for key, value in expected.items())
        checks.append(check(f"{expert}_profile_inputs_paused", "PASS" if ok else "FAIL", json.dumps(details, sort_keys=True)))
    checks.append(
        check(
            "plain_933200_still_stopped",
            "PASS" if any(row.magic == "933200" and row.dry_run_only == "true" and row.broker_action_allowed == "false" for row in after_charts) else "FAIL",
            "933200 dry-run/no-broker-action expected",
        )
    )
    checks.append(
        check(
            "changed_only_expected_pause_targets",
            "PASS" if sorted(row["expert"] for row in changed_charts) == sorted(PAUSE_TARGETS) else "FAIL",
            json.dumps(changed_charts, sort_keys=True),
        )
    )
    checks.extend(startup_checks(startup_logs))
    return checks


def startup_checks(startup_logs: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    expectations = {
        "improved": ["A3_BREAKOUT_IMPROVED_V1_PAUSED_20260618", "true", "false", "ATTACHED_A3_BREAKOUT_IMPROVED"],
        "tier1_compat": ["A3_BREAKOUT_TIER1_COMPAT_V1_PAUSED_20260618", "true", "false", "ATTACHED_A3_BREAKOUT_TIER1_COMPAT"],
        "profit_lock": ["A3_PROFIT_LOCK_EXIT_MANAGER_V1_DRYRUN_PAUSED_20260618", "true", "false", "ATTACHED_A3_PROFIT_LOCK_EXIT_MANAGER"],
    }
    rows = []
    for key, tokens in expectations.items():
        line = startup_logs.get(key, {}).get("last_line", "")
        rows.append(check(f"{key}_startup_log_paused", "PASS" if all(token in line for token in tokens) else "FAIL", line))
    return rows


def input_to_field(key: str) -> str:
    return {
        "InpRunId": "run_id",
        "InpDryRunOnly": "dry_run_only",
        "InpBrokerActionAllowed": "broker_action_allowed",
        "InpManageActionAllowed": "manage_action_allowed",
    }[key]


def broker_summary(state: dict[str, Any]) -> str:
    return (
        f"a3_positions={state.get('a3_positions_total')}; "
        f"a3_orders={state.get('a3_orders_total')}; "
        f"all_xau_positions={state.get('all_xau_positions_total')}; "
        f"all_xau_orders={state.get('all_xau_orders_total')}"
    )


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# A3 Emergency Pause Applied - 2026-06-18",
        "",
        f"Overall status: `{payload['status']}`",
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
        "| Moment | A3 positions | A3 orders | All XAU positions | All XAU orders |",
        "| --- | ---: | ---: | ---: | ---: |",
        broker_row("before", payload["before_broker"]),
        broker_row("after", payload["after_broker"]),
        "",
        "## Profile Change",
        "",
        f"- Profile backup: `{payload['terminal']['profile_backup']}`",
        f"- Terminal closed before edit: `{payload['terminal']['terminal_closed_before_profile_change']}`",
        f"- Terminal relaunched: `{payload['terminal']['terminal_relaunched']}`",
        "",
        "| Chart | Expert | New run id | Dry-run | Broker action | Manage action |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for row in payload["after_charts"]:
        if row["expert"] not in {"Account3BreakoutPlainExecutor", *PAUSE_TARGETS.keys()}:
            continue
        lines.append(
            "| {chart} | `{expert}` | `{run_id}` | `{dry}` | `{broker}` | `{manage}` |".format(
                chart=row["chart"],
                expert=escape_md(row["expert"]),
                run_id=escape_md(row["run_id"]),
                dry=escape_md(row["dry_run_only"]),
                broker=escape_md(row["broker_action_allowed"]),
                manage=escape_md(row["manage_action_allowed"]),
            )
        )
    lines.extend(["", "## Checks", "", "| Check | Status | Evidence |", "| --- | --- | --- |"])
    for item in payload["checks"]:
        lines.append(f"| `{escape_md(item['name'])}` | `{escape_md(item['status'])}` | {escape_md(item['evidence'])} |")
    lines.extend(
        [
            "",
            "No trade was closed and no order was sent by this maintenance action. The change only disables future A3 broker-action entries and disarms the profit-lock manager into dry-run.",
            "",
        ]
    )
    return "\n".join(lines)


def broker_row(label: str, state: dict[str, Any]) -> str:
    return (
        f"| {label} | `{state.get('a3_positions_total')}` | `{state.get('a3_orders_total')}` | "
        f"`{state.get('all_xau_positions_total')}` | `{state.get('all_xau_orders_total')}` |"
    )


def check(name: str, status: str, evidence: str) -> dict[str, str]:
    return {"name": name, "status": status, "evidence": str(evidence)}


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


def escape_md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def require_file(path: Path) -> None:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(path)


def require_dir(path: Path) -> None:
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply the A3 emergency broker-action pause.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--portable-root", type=Path, default=DEFAULT_PORTABLE_ROOT)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--no-launch", action="store_true")
    parser.add_argument("--wait-seconds", type=int, default=45)
    args = parser.parse_args(argv)
    payload = apply_a3_emergency_pause(
        args.phase1_root,
        portable_root=args.portable_root,
        output_json=args.output_json,
        launch=not args.no_launch,
        wait_seconds=args.wait_seconds,
    )
    print(json.dumps({"status": payload["status"], "output": str(args.output_json or args.phase1_root / DEFAULT_OUTPUT_JSON)}, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
