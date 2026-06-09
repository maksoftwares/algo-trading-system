from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from phase2_demo_repair_common import (
    DEFAULT_ACTUAL_TRADES,
    DEFAULT_POLICY,
    DEFAULT_WEAKNESS_JSON,
    load_policy,
    read_json,
    read_trades,
    rows_since,
    utc_now,
    write_json,
    write_markdown,
)


DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "PHASE2_DEMO_REPAIR_MONITOR_LATEST.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "PHASE2_DEMO_REPAIR_MONITOR_LATEST.md"
DEFAULT_SINCE = "2026-06-09 00:00:00"


@dataclass(frozen=True)
class RepairMonitorOutput:
    status: str
    json_path: Path
    markdown_path: Path
    finding_count: int


def generate_repair_monitor(
    root: Path,
    policy_path: Path | None = None,
    trades_csv: Path | None = None,
    weakness_json: Path | None = None,
    since: str = DEFAULT_SINCE,
    output_json: Path | None = None,
) -> RepairMonitorOutput:
    root = root.resolve()
    policy_path = (policy_path or root / DEFAULT_POLICY).resolve()
    trades_csv = (trades_csv or root / DEFAULT_ACTUAL_TRADES).resolve()
    weakness_json = (weakness_json or root / DEFAULT_WEAKNESS_JSON).resolve()
    output_json = (output_json or root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_OUTPUT_JSON.name else root / DEFAULT_OUTPUT_MD
    policy = load_policy(policy_path)
    weakness = read_json(weakness_json)
    rows = rows_since(read_trades(trades_csv), since)
    policy_enforced = bool(policy.get("effective_at_dubai"))
    findings = repair_findings(rows, policy, weakness, policy_enforced)
    status = monitor_status(findings, policy_enforced)
    payload = {
        "status": status,
        "generated_at_utc": utc_now(),
        "since": since,
        "policy_id": policy.get("policy_id"),
        "policy_enforced": policy_enforced,
        "policy_effective_at_dubai": policy.get("effective_at_dubai"),
        "trade_source": str(trades_csv),
        "boundary": "Monitor/report only. No MT5 runtime is modified.",
        "rows_checked": len(rows),
        "findings": findings,
        "summary": {
            "weak_variant_order_attempts": count_matching(rows, candidate_set=set(policy.get("suspend_candidates", []))),
            "blocked_by_repair_policy": len(findings),
            "orders_after_quarantine_by_candidate": count_by(rows, "candidate", set(policy.get("suspend_candidates", []))),
            "symbol_normalized_new_orders_after_suspend": count_candidate(rows, "symbol_normalized_round_retest_v0"),
            "session_extreme_new_orders_after_suspend": count_candidate(rows, "session_extreme_retest_v0"),
            "usdjpy_new_orders_after_disable": count_symbol(rows, "USDJPY"),
        },
    }
    write_json(output_json, payload)
    write_markdown(output_md, render_markdown(payload))
    return RepairMonitorOutput(status, output_json, output_md, len(findings))


def monitor_status(findings: list[dict[str, Any]], policy_enforced: bool) -> str:
    if findings and policy_enforced:
        return "RED_REPAIR_POLICY_LEAK_FOUND"
    if findings:
        return "SHADOW_REPAIR_POLICY_WOULD_BLOCK_EVENTS_OBSERVED"
    if policy_enforced:
        return "GREEN_NO_REPAIR_POLICY_LEAKS"
    return "SHADOW_NO_REPAIR_POLICY_EVENTS"


def repair_findings(
    rows: list[dict[str, Any]],
    policy: dict[str, Any],
    weakness: dict[str, Any],
    policy_enforced: bool,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    severity = "RED" if policy_enforced else "SHADOW"
    suspended = set(policy.get("suspend_candidates", []))
    disabled_symbols = set(policy.get("disable_symbols", []))
    p2weakness = policy.get("p2weakness", {})
    expected_magic = int(p2weakness.get("magic", 931000))
    expected_lot = float(p2weakness.get("fixed_lot", 0.01))
    account = weakness.get("account", {})
    server = str(account.get("server", ""))
    if server and "demo" not in server.lower() and "practice" not in server.lower():
        findings.append({"severity": "RED", "type": "NON_DEMO_SERVER", "detail": f"Account server `{server}` is not marked Demo/Practice."})
    for row in rows:
        candidate = str(row.get("candidate", ""))
        symbol = str(row.get("symbol", ""))
        magic = int(row.get("magic_value", 0))
        volume = float(row.get("volume_value", 0.0))
        ticket = str(row.get("position_ticket", ""))
        if candidate in suspended:
            findings.append({"severity": severity, "type": "SUSPENDED_CANDIDATE_ORDER", "candidate": candidate, "symbol": symbol, "ticket": ticket})
        if symbol in disabled_symbols:
            findings.append({"severity": severity, "type": "DISABLED_SYMBOL_ORDER", "candidate": candidate, "symbol": symbol, "ticket": ticket})
        if candidate == "p2weakness_br_v1" or magic == expected_magic:
            if magic != expected_magic:
                findings.append({"severity": severity, "type": "P2WEAKNESS_WRONG_MAGIC", "magic": magic, "expected_magic": expected_magic, "ticket": ticket})
            if volume > expected_lot + 1e-9:
                findings.append({"severity": severity, "type": "P2WEAKNESS_LOT_EXCEEDED", "volume": volume, "expected_lot": expected_lot, "ticket": ticket})
    return findings


def count_matching(rows: list[dict[str, Any]], candidate_set: set[str]) -> int:
    return sum(1 for row in rows if str(row.get("candidate", "")) in candidate_set)


def count_candidate(rows: list[dict[str, Any]], candidate: str) -> int:
    return sum(1 for row in rows if str(row.get("candidate", "")) == candidate)


def count_symbol(rows: list[dict[str, Any]], symbol: str) -> int:
    return sum(1 for row in rows if str(row.get("symbol", "")) == symbol)


def count_by(rows: list[dict[str, Any]], field: str, allowed: set[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(field, ""))
        if value in allowed:
            counts[value] = counts.get(value, 0) + 1
    return counts


def render_markdown(payload: dict[str, Any]) -> list[str]:
    lines = [
        "# Phase 2 Demo Repair Monitor",
        "",
        f"Overall status: {payload['status']}",
        "",
        str(payload["boundary"]),
        "",
        f"Generated at UTC: `{payload['generated_at_utc']}`",
        f"Policy ID: `{payload['policy_id']}`",
        f"Policy enforced: `{str(payload['policy_enforced']).lower()}`",
        f"Policy effective at Dubai: `{payload['policy_effective_at_dubai']}`",
        f"Since: `{payload['since']}`",
        f"Rows checked: `{payload['rows_checked']}`",
        "",
        "## Counters",
        "",
        "| Counter | Value |",
        "|---|---:|",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"| {key} | `{value}` |")
    lines.extend(["", "## Findings", "", "| Severity | Type | Candidate | Symbol | Ticket | Detail |", "|---|---|---|---|---|---|"])
    for finding in payload["findings"]:
        lines.append(
            f"| {finding.get('severity', '')} | {finding.get('type', '')} | {finding.get('candidate', '')} | {finding.get('symbol', '')} | "
            f"{finding.get('ticket', '')} | {finding.get('detail', '')} |"
        )
    if not payload["findings"]:
        lines.append("| none | none |  |  |  | No repair-policy findings detected in the checked window. |")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 2 demo repair monitor report.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--policy", type=Path, default=None)
    parser.add_argument("--trades-csv", type=Path, default=None)
    parser.add_argument("--weakness-json", type=Path, default=None)
    parser.add_argument("--since", default=DEFAULT_SINCE)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    output = generate_repair_monitor(args.root, args.policy, args.trades_csv, args.weakness_json, args.since, args.output_json)
    print(f"Phase 2 demo repair monitor: {output.status}")
    print(output.markdown_path)
    print(output.json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
