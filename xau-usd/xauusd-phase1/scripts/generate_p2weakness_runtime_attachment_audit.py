from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PHASE1_REPORTS_REL = Path("outputs") / "reports"
REPO_EA_REL = Path("mt5") / "Experts" / "Phase2WeaknessBreakoutRetestExecutor.mq5"
DEFAULT_TERMINAL_ROOT = Path("C:/MT5PortableP2WeaknessDemo")
DEFAULT_ORDER_LOG = DEFAULT_TERMINAL_ROOT / "MQL5" / "Files" / "p2weakness_br_v1_order_log_xauusd.csv"
DEFAULT_STARTUP_LOG = DEFAULT_TERMINAL_ROOT / "MQL5" / "Files" / "p2weakness_br_v1_startup_xauusd.csv"
DEFAULT_KILL_SWITCH = DEFAULT_TERMINAL_ROOT / "MQL5" / "Files" / "p2weakness_br_v1_kill_switch.txt"
REPORT_STEM = "P2WEAKNESS_BR_V1_RUNTIME_ATTACHMENT_AUDIT"
P2WEAKNESS_EA_NAME = "Phase2WeaknessBreakoutRetestExecutor"
OLD_MAGIC = 930101
HARDENED_MAGIC = 931000


@dataclass(frozen=True)
class ReportOutput:
    status: str
    paths: tuple[Path, Path]


def generate_p2weakness_runtime_attachment_audit(
    phase1_root: Path,
    terminal_root: Path = DEFAULT_TERMINAL_ROOT,
    output_dir: Path | None = None,
    order_log: Path = DEFAULT_ORDER_LOG,
    startup_log: Path = DEFAULT_STARTUP_LOG,
    kill_switch: Path = DEFAULT_KILL_SWITCH,
    use_mt5_bridge: bool = True,
) -> ReportOutput:
    phase1_root = phase1_root.resolve()
    terminal_root = terminal_root.resolve()
    output_dir = (output_dir or phase1_root / PHASE1_REPORTS_REL).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = build_audit_payload(
        phase1_root=phase1_root,
        terminal_root=terminal_root,
        order_log=order_log,
        startup_log=startup_log,
        kill_switch=kill_switch,
        use_mt5_bridge=use_mt5_bridge,
    )
    json_path = output_dir / f"{REPORT_STEM}.json"
    md_path = output_dir / f"{REPORT_STEM}.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(render_audit_markdown(payload), encoding="utf-8")
    return ReportOutput(status=str(payload["status"]), paths=(json_path, md_path))


def build_audit_payload(
    phase1_root: Path,
    terminal_root: Path,
    order_log: Path,
    startup_log: Path,
    kill_switch: Path,
    use_mt5_bridge: bool,
) -> dict[str, Any]:
    repo_source = phase1_root / REPO_EA_REL
    deployed_source = terminal_root / "MQL5" / "Experts" / REPO_EA_REL.name
    deployed_ex5 = deployed_source.with_suffix(".ex5")
    chart_dir = terminal_root / "MQL5" / "Profiles" / "Charts" / "Default"
    chart_audit = _read_chart_profiles(chart_dir)
    source_audit = _source_audit(repo_source, deployed_source, deployed_ex5)
    order_rows = _csv_rows(order_log)
    startup_rows = _csv_rows(startup_log)
    latest_order = order_rows[-1] if order_rows else {}
    latest_startup = startup_rows[-1] if startup_rows else {}
    runtime_magics = sorted({magic for magic in (_to_int(row.get("magic")) for row in order_rows) if magic is not None})
    startup_old_runtime = _is_truthy(latest_startup.get("broker_action_allowed")) or _is_falsey(latest_startup.get("dry_run"))
    mt5_exposure = _read_mt5_exposure(terminal_root / "terminal64.exe") if use_mt5_bridge else _mt5_bridge_skipped()

    p2_charts = chart_audit["p2weakness_charts"]
    old_magic_attached = any(chart.get("magic") == OLD_MAGIC for chart in p2_charts)
    hardened_magic_attached = any(chart.get("magic") == HARDENED_MAGIC for chart in p2_charts)
    broker_action_capable_chart_active = any(chart.get("broker_action_capable") for chart in p2_charts)
    broker_action_enabled_chart_active = any(chart.get("broker_action_enabled") for chart in p2_charts)
    dry_run_disabled_chart_active = any(chart.get("dry_run_disabled") for chart in p2_charts)
    deployed_old_source = source_audit["deployed_source_magic"] == OLD_MAGIC
    deployed_hardened_source = (
        source_audit["deployed_source_magic"] == HARDENED_MAGIC
        and source_audit["deployed_dry_run_default"] == "true"
        and source_audit["deployed_broker_action_default"] == "false"
    )
    old_magic_log_evidence = OLD_MAGIC in runtime_magics or latest_startup.get("magic") == str(OLD_MAGIC)
    old_open_positions = [row for row in mt5_exposure["positions"] if row.get("magic") == OLD_MAGIC]
    old_open_orders = [row for row in mt5_exposure["orders"] if row.get("magic") == OLD_MAGIC]
    hardened_open_positions = [row for row in mt5_exposure["positions"] if row.get("magic") == HARDENED_MAGIC]
    hardened_open_orders = [row for row in mt5_exposure["orders"] if row.get("magic") == HARDENED_MAGIC]

    runtime_risks = []
    if deployed_old_source:
        runtime_risks.append("deployed_source_still_uses_old_magic_930101")
    if source_audit["deployed_broker_action_default"] == "true":
        runtime_risks.append("deployed_source_default_broker_action_allowed_true")
    if source_audit["deployed_dry_run_default"] == "false":
        runtime_risks.append("deployed_source_default_dry_run_false")
    if old_magic_attached:
        runtime_risks.append("chart_profile_contains_old_magic_930101")
    if broker_action_enabled_chart_active:
        runtime_risks.append("chart_profile_broker_action_allowed_true")
    if dry_run_disabled_chart_active:
        runtime_risks.append("chart_profile_dry_run_false")
    if old_open_positions:
        runtime_risks.append("open_positions_exist_with_old_magic_930101")
    if old_open_orders:
        runtime_risks.append("open_orders_exist_with_old_magic_930101")
    if startup_old_runtime:
        runtime_risks.append("latest_startup_log_reports_broker_action_runtime")

    status = "QUARANTINE_RUNTIME_RISK_FOUND" if runtime_risks else "NO_ACTIVE_P2WEAKNESS_RUNTIME_RISK_OBSERVED"
    if not terminal_root.exists():
        status = "P2WEAKNESS_TERMINAL_ROOT_MISSING"

    return {
        "status": status,
        "created_at_utc": _utc_now(),
        "authority": (
            "Read-only P2WEAKNESS_BR_V1 runtime attachment audit. This script reads profile files, deployed source, "
            "CSV logs, and optionally MT5 open positions/orders; it does not attach charts, deploy files, change presets, "
            "restart terminals, create kill switches, or authorize canonical Phase 2/live trading."
        ),
        "terminal_root": str(terminal_root),
        "terminal_exists": terminal_root.exists(),
        "terminal_exe": str(terminal_root / "terminal64.exe"),
        "mt5_runtime_touched_by_script": False,
        "standard_demo_terminal_touched": False,
        "new_deployments_paused": True,
        "canonical_phase2_authorized": False,
        "broker_side_execution_authorized": False,
        "live_or_real_capital_authorized": False,
        "runtime_decision": "KEEP_PAUSED_OR_QUARANTINED_UNTIL_OWNER_AUTH_KILL_SWITCH_AND_REVIEWER_SIGNOFF",
        "reviewer_questions": {
            "is_any_old_930101_ea_still_attached": _profile_answer(old_magic_attached, charts_scanned=chart_audit["chart_files_scanned"], p2_charts=len(p2_charts)),
            "is_any_broker_action_capable_chart_active": _profile_answer(
                broker_action_capable_chart_active,
                charts_scanned=chart_audit["chart_files_scanned"],
                p2_charts=len(p2_charts),
            ),
            "are_there_open_positions_by_old_magic": _yes_no_unknown(bool(old_open_positions), mt5_exposure["status"] == "PASS"),
            "are_there_open_orders_by_old_magic": _yes_no_unknown(bool(old_open_orders), mt5_exposure["status"] == "PASS"),
            "was_hardened_931000_source_deployed": "YES" if deployed_hardened_source else "NO",
        },
        "runtime_risks": runtime_risks,
        "old_magic_930101": {
            "attached_in_chart_profile": old_magic_attached,
            "observed_in_runtime_logs": old_magic_log_evidence,
            "deployed_source_uses_old_magic": deployed_old_source,
            "open_positions": len(old_open_positions),
            "open_orders": len(old_open_orders),
        },
        "hardened_magic_931000": {
            "attached_in_chart_profile": hardened_magic_attached,
            "deployed_source_hardened": deployed_hardened_source,
            "open_positions": len(hardened_open_positions),
            "open_orders": len(hardened_open_orders),
        },
        "source_audit": source_audit,
        "chart_audit": chart_audit,
        "open_exposure_audit": mt5_exposure,
        "logs": {
            "order_log": str(order_log),
            "startup_log": str(startup_log),
            "kill_switch_file": str(kill_switch),
            "order_log_exists": order_log.exists(),
            "startup_log_exists": startup_log.exists(),
            "kill_switch_exists": kill_switch.exists(),
            "order_rows": len(order_rows),
            "startup_rows": len(startup_rows),
            "runtime_magics_observed": runtime_magics,
            "latest_order": _mask_sensitive_row(latest_order),
            "latest_startup": _mask_sensitive_row(latest_startup),
        },
        "required_before_future_continuation": [
            "Owner authorization fields completed out-of-band.",
            "Kill switch file created and tested.",
            "Old 930101 runtime source/chart state stopped or explicitly quarantined.",
            "Fresh deployment uses only hardened 931000 source and owner-authorized preset.",
            "Startup log proves account whitelist, auth token, cost-suspension acknowledgement, and intended broker-action mode.",
            "Reviewer signs off before any P2WEAKNESS continuation.",
        ],
    }


def render_audit_markdown(payload: dict[str, Any]) -> str:
    questions = payload["reviewer_questions"]
    source = payload["source_audit"]
    charts = payload["chart_audit"]
    exposure = payload["open_exposure_audit"]
    logs = payload["logs"]
    lines = [
        "# P2WEAKNESS BR V1 Runtime Attachment Audit",
        "",
        f"Status: {payload['status']}",
        "",
        payload["authority"],
        "",
        f"Created at UTC: `{payload['created_at_utc']}`",
        "",
        "## Reviewer Questions",
        "",
        "| Question | Answer |",
        "|---|---|",
        f"| Is any old `930101` EA still attached? | `{questions['is_any_old_930101_ea_still_attached']}` |",
        f"| Is any broker-action-capable P2WEAKNESS chart active? | `{questions['is_any_broker_action_capable_chart_active']}` |",
        f"| Are there open positions by old magic `930101`? | `{questions['are_there_open_positions_by_old_magic']}` |",
        f"| Are there open orders by old magic `930101`? | `{questions['are_there_open_orders_by_old_magic']}` |",
        f"| Was the hardened `931000` source deployed? | `{questions['was_hardened_931000_source_deployed']}` |",
        "",
        "## Runtime Boundary",
        "",
        f"- Terminal root: `{payload['terminal_root']}`",
        f"- MT5 runtime touched by script: `{payload['mt5_runtime_touched_by_script']}`",
        f"- Standard demo terminal touched: `{payload['standard_demo_terminal_touched']}`",
        f"- New deployments paused: `{payload['new_deployments_paused']}`",
        f"- Broker-side execution authorized: `{payload['broker_side_execution_authorized']}`",
        f"- Live/real capital authorized: `{payload['live_or_real_capital_authorized']}`",
        f"- Runtime decision: `{payload['runtime_decision']}`",
        "",
        "## Runtime Risks",
        "",
    ]
    if payload["runtime_risks"]:
        lines.extend(f"- `{risk}`" for risk in payload["runtime_risks"])
    else:
        lines.append("- No active P2WEAKNESS runtime risks were observed by this read-only audit.")
    lines.extend([
        "",
        "## Deployed Source",
        "",
        f"- Repo source SHA256: `{source['repo_source_sha256']}`",
        f"- Deployed source exists: `{source['deployed_source_exists']}`",
        f"- Deployed source SHA256: `{source['deployed_source_sha256']}`",
        f"- Deployed source matches repo: `{source['deployed_source_matches_repo']}`",
        f"- Deployed EX5 exists: `{source['deployed_ex5_exists']}`",
        f"- Deployed source magic: `{source['deployed_source_magic']}`",
        f"- Deployed dry-run default: `{source['deployed_dry_run_default']}`",
        f"- Deployed broker-action default: `{source['deployed_broker_action_default']}`",
        "",
        "## Chart Profile Scan",
        "",
        f"- Chart directory: `{charts['chart_dir']}`",
        f"- Chart files scanned: `{charts['chart_files_scanned']}`",
        f"- P2WEAKNESS charts found: `{len(charts['p2weakness_charts'])}`",
        "",
        "| Chart | Symbol | Expert | Magic | Dry run | Broker action | Evidence |",
        "|---|---|---|---:|---|---|---|",
    ])
    if charts["p2weakness_charts"]:
        for chart in charts["p2weakness_charts"]:
            lines.append(
                f"| `{chart['path']}` | `{chart.get('symbol', '')}` | `{chart.get('expert_name', '')}` | "
                f"{chart.get('magic', '')} | `{chart.get('dry_run', '')}` | `{chart.get('broker_action_allowed', '')}` | "
                f"`{chart.get('evidence', '')}` |"
            )
    else:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | No P2WEAKNESS chart block found in profile files. |")
    lines.extend([
        "",
        "## Open Exposure",
        "",
        f"- MT5 bridge status: `{exposure['status']}`",
        f"- MT5 bridge note: `{exposure['note']}`",
        f"- Positions with magic `930101`: `{payload['old_magic_930101']['open_positions']}`",
        f"- Orders with magic `930101`: `{payload['old_magic_930101']['open_orders']}`",
        f"- Positions with magic `931000`: `{payload['hardened_magic_931000']['open_positions']}`",
        f"- Orders with magic `931000`: `{payload['hardened_magic_931000']['open_orders']}`",
        "",
        "## Log Evidence",
        "",
        f"- Order log exists: `{logs['order_log_exists']}`",
        f"- Startup log exists: `{logs['startup_log_exists']}`",
        f"- Kill switch exists: `{logs['kill_switch_exists']}`",
        f"- Order rows: `{logs['order_rows']}`",
        f"- Startup rows: `{logs['startup_rows']}`",
        f"- Runtime magics observed: `{logs['runtime_magics_observed']}`",
        f"- Latest order action: `{logs['latest_order'].get('action', '')}`",
        f"- Latest order magic: `{logs['latest_order'].get('magic', '')}`",
        f"- Latest guard reason: `{logs['latest_order'].get('guard_reason', '')}`",
        f"- Latest startup dry-run: `{logs['latest_startup'].get('dry_run', '')}`",
        f"- Latest startup broker-action allowed: `{logs['latest_startup'].get('broker_action_allowed', '')}`",
        f"- Latest startup status: `{logs['latest_startup'].get('startup_status', '')}`",
        "",
        "## Required Before Future Continuation",
        "",
    ])
    lines.extend(f"- {item}" for item in payload["required_before_future_continuation"])
    lines.append("")
    return "\n".join(lines)


def _read_chart_profiles(chart_dir: Path) -> dict[str, Any]:
    charts = []
    if chart_dir.exists():
        for path in sorted(chart_dir.glob("chart*.chr")):
            charts.append(_parse_chart(path))
    p2_charts = [chart for chart in charts if chart["is_p2weakness"]]
    return {
        "chart_dir": str(chart_dir),
        "chart_dir_exists": chart_dir.exists(),
        "chart_files_scanned": len(charts),
        "p2weakness_charts": p2_charts,
        "charts": charts,
    }


def _parse_chart(path: Path) -> dict[str, Any]:
    text = _read(path)
    symbol = _match_line(text, "symbol")
    expert_blocks = re.findall(r"<expert>\s*(.*?)\s*</expert>", text, flags=re.DOTALL | re.IGNORECASE)
    expert_name = ""
    expert_path = ""
    inputs: dict[str, str] = {}
    evidence = "NO_EXPERT_BLOCK"
    if expert_blocks:
        block = expert_blocks[-1]
        expert_name = _match_line(block, "name")
        expert_path = _match_line(block, "path")
        inputs = _key_values(block)
        evidence = "EXPERT_BLOCK"
    is_p2weakness = P2WEAKNESS_EA_NAME.lower() in (expert_name + " " + expert_path + " " + text).lower()
    magic = _to_int(inputs.get("InpMagicNumber"))
    dry_run = inputs.get("InpDryRunOnly", "")
    broker_action = inputs.get("InpBrokerActionAllowed", "")
    return {
        "path": str(path),
        "symbol": symbol,
        "expert_name": expert_name,
        "expert_path": expert_path,
        "inputs": inputs,
        "magic": magic,
        "dry_run": dry_run,
        "broker_action_allowed": broker_action,
        "is_p2weakness": is_p2weakness,
        "broker_action_capable": is_p2weakness,
        "broker_action_enabled": _is_truthy(broker_action),
        "dry_run_disabled": _is_falsey(dry_run),
        "evidence": evidence,
    }


def _source_audit(repo_source: Path, deployed_source: Path, deployed_ex5: Path) -> dict[str, Any]:
    repo_text = _read(repo_source)
    deployed_text = _read(deployed_source)
    repo_inputs = _source_inputs(repo_text)
    deployed_inputs = _source_inputs(deployed_text)
    return {
        "repo_source": str(repo_source),
        "deployed_source": str(deployed_source),
        "deployed_ex5": str(deployed_ex5),
        "repo_source_exists": repo_source.exists(),
        "deployed_source_exists": deployed_source.exists(),
        "deployed_ex5_exists": deployed_ex5.exists(),
        "repo_source_sha256": _sha256(repo_source),
        "deployed_source_sha256": _sha256(deployed_source),
        "deployed_source_matches_repo": repo_source.exists() and deployed_source.exists() and _sha256(repo_source) == _sha256(deployed_source),
        "repo_source_magic": _to_int(repo_inputs.get("InpMagicNumber")),
        "deployed_source_magic": _to_int(deployed_inputs.get("InpMagicNumber")),
        "repo_dry_run_default": repo_inputs.get("InpDryRunOnly", ""),
        "repo_broker_action_default": repo_inputs.get("InpBrokerActionAllowed", ""),
        "deployed_dry_run_default": deployed_inputs.get("InpDryRunOnly", ""),
        "deployed_broker_action_default": deployed_inputs.get("InpBrokerActionAllowed", ""),
        "repo_inputs": repo_inputs,
        "deployed_inputs": deployed_inputs,
    }


def _read_mt5_exposure(terminal_exe: Path) -> dict[str, Any]:
    if not terminal_exe.exists():
        return {
            "status": "SKIPPED_TERMINAL_EXE_MISSING",
            "note": "terminal64.exe was not found; open exposure was not queried.",
            "positions": [],
            "orders": [],
        }
    try:
        import MetaTrader5 as mt5  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        return {
            "status": "SKIPPED_MT5_MODULE_UNAVAILABLE",
            "note": f"MetaTrader5 import failed: {exc}",
            "positions": [],
            "orders": [],
        }
    initialized = False
    try:
        initialized = bool(mt5.initialize(path=str(terminal_exe)))
        if not initialized:
            return {
                "status": "FAIL_MT5_INITIALIZE",
                "note": f"mt5.initialize failed: {mt5.last_error()}",
                "positions": [],
                "orders": [],
            }
        positions = [_position_to_dict(position) for position in (mt5.positions_get() or [])]
        orders = [_order_to_dict(order) for order in (mt5.orders_get() or [])]
        relevant_positions = [row for row in positions if _is_relevant_exposure(row)]
        relevant_orders = [row for row in orders if _is_relevant_exposure(row)]
        return {
            "status": "PASS",
            "note": "Read-only MT5 positions_get/orders_get query completed.",
            "positions": relevant_positions,
            "orders": relevant_orders,
            "total_positions": len(positions),
            "total_orders": len(orders),
        }
    except Exception as exc:  # pragma: no cover - environment dependent
        return {
            "status": "FAIL_MT5_QUERY",
            "note": str(exc),
            "positions": [],
            "orders": [],
        }
    finally:
        if initialized:
            mt5.shutdown()


def _position_to_dict(position: Any) -> dict[str, Any]:
    data = position._asdict() if hasattr(position, "_asdict") else {}
    return {
        "ticket": _to_int(data.get("ticket")),
        "symbol": str(data.get("symbol", "")),
        "type": _to_int(data.get("type")),
        "volume": _to_float(data.get("volume")),
        "magic": _to_int(data.get("magic")),
        "profit": _to_float(data.get("profit")),
        "comment": str(data.get("comment", "")),
    }


def _order_to_dict(order: Any) -> dict[str, Any]:
    data = order._asdict() if hasattr(order, "_asdict") else {}
    return {
        "ticket": _to_int(data.get("ticket")),
        "symbol": str(data.get("symbol", "")),
        "type": _to_int(data.get("type")),
        "volume_current": _to_float(data.get("volume_current")),
        "magic": _to_int(data.get("magic")),
        "comment": str(data.get("comment", "")),
    }


def _is_relevant_exposure(row: dict[str, Any]) -> bool:
    magic = row.get("magic")
    comment = str(row.get("comment", ""))
    return magic in {OLD_MAGIC, HARDENED_MAGIC} or comment.startswith("P2WEAKNESS_BR_V1")


def _mt5_bridge_skipped() -> dict[str, Any]:
    return {"status": "SKIPPED_BY_ARGUMENT", "note": "MT5 bridge query disabled by argument.", "positions": [], "orders": []}


def _source_inputs(source: str) -> dict[str, str]:
    values: dict[str, str] = {}
    pattern = re.compile(r"^\s*input\s+\w+\s+(\w+)\s*=\s*(.+?);\s*$")
    for line in source.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        raw = match.group(2).strip()
        if raw.startswith('"') and raw.endswith('"'):
            raw = raw[1:-1]
        values[match.group(1)] = raw
    return values


def _key_values(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _match_line(text: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}=(.*)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def _csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _profile_answer(value: bool, charts_scanned: int, p2_charts: int) -> str:
    if charts_scanned <= 0:
        return "UNKNOWN"
    if p2_charts <= 0:
        return "NO_PROFILE_EVIDENCE"
    return "YES" if value else "NO"


def _yes_no_unknown(value: bool, observable: bool) -> str:
    if not observable:
        return "UNKNOWN"
    return "YES" if value else "NO"


def _mask_sensitive_row(row: dict[str, Any]) -> dict[str, Any]:
    masked = dict(row)
    for key in ("account_login", "account", "login", "allowed_account_logins"):
        if key in masked:
            masked[key] = _mask_account(masked[key])
    return masked


def _mask_account(value: object) -> str:
    text = str(value or "")
    if len(text) <= 3:
        return "***"
    return "*" * (len(text) - 3) + text[-3:]


def _is_truthy(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _is_falsey(value: object) -> bool:
    return str(value).strip().lower() in {"false", "0", "no", "n"}


def _to_int(value: object) -> int | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return int(float(str(value)))
    except ValueError:
        return None


def _to_float(value: object) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(str(value))
    except ValueError:
        return None


def _sha256(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a read-only P2WEAKNESS_BR_V1 runtime attachment audit.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--terminal-root", type=Path, default=DEFAULT_TERMINAL_ROOT)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--order-log", type=Path, default=DEFAULT_ORDER_LOG)
    parser.add_argument("--startup-log", type=Path, default=DEFAULT_STARTUP_LOG)
    parser.add_argument("--kill-switch", type=Path, default=DEFAULT_KILL_SWITCH)
    parser.add_argument("--skip-mt5-bridge", action="store_true", help="Skip read-only positions/orders query.")
    args = parser.parse_args(argv)

    output = generate_p2weakness_runtime_attachment_audit(
        phase1_root=args.phase1_root,
        terminal_root=args.terminal_root,
        output_dir=args.output_dir,
        order_log=args.order_log,
        startup_log=args.startup_log,
        kill_switch=args.kill_switch,
        use_mt5_bridge=not args.skip_mt5_bridge,
    )
    print(f"P2WEAKNESS runtime attachment audit: {output.status}")
    for path in output.paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
