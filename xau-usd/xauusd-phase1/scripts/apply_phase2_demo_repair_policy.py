from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from phase2_demo_repair_common import (
    DEFAULT_ACTUAL_TRADES,
    DEFAULT_POLICY,
    DEFAULT_WEAKNESS_JSON,
    duplicate_hidden,
    load_policy,
    metrics_table,
    read_json,
    read_trades,
    summarize,
    utc_now,
    write_json,
    write_markdown,
)


DEFAULT_DRY_RUN_JSON = Path("outputs") / "reports" / "PHASE2_DEMO_REPAIR_POLICY_DRY_RUN.json"
DEFAULT_DRY_RUN_MD = Path("outputs") / "reports" / "PHASE2_DEMO_REPAIR_POLICY_DRY_RUN.md"
DEFAULT_BASELINE_JSON = Path("outputs") / "reports" / "PHASE2_DEMO_REPAIR_BASELINE_2026_06_09.json"
DEFAULT_BASELINE_MD = Path("outputs") / "reports" / "PHASE2_DEMO_REPAIR_BASELINE_2026_06_09.md"
DEFAULT_RECON_JSON = Path("outputs") / "reports" / "PHASE2_DEMO_REPAIR_RECONCILIATION_2026_06_09.json"
DEFAULT_RECON_MD = Path("outputs") / "reports" / "PHASE2_DEMO_REPAIR_RECONCILIATION_2026_06_09.md"


@dataclass(frozen=True)
class ApplyOutput:
    status: str
    dry_run_path: Path
    baseline_path: Path
    reconciliation_path: Path


def apply_repair_policy(
    root: Path,
    policy_path: Path | None = None,
    trades_csv: Path | None = None,
    weakness_json: Path | None = None,
    owner_approved_runtime_change: bool = False,
    profile_backup_path: Path | None = None,
) -> ApplyOutput:
    root = root.resolve()
    policy_path = (policy_path or root / DEFAULT_POLICY).resolve()
    trades_csv = (trades_csv or root / DEFAULT_ACTUAL_TRADES).resolve()
    weakness_json = (weakness_json or root / DEFAULT_WEAKNESS_JSON).resolve()
    reports = root / "outputs" / "reports"
    policy = load_policy(policy_path)
    rows = read_trades(trades_csv)
    weakness = read_json(weakness_json)

    baseline = build_baseline(policy, rows, weakness, trades_csv, profile_backup_path)
    status = "DRY_RUN_ONLY_NO_RUNTIME_CHANGE"
    runtime_allowed = False
    if owner_approved_runtime_change:
        status = "RUNTIME_CHANGE_BLOCKED_PENDING_PROFILE_BACKUP_EVIDENCE"
        runtime_allowed = False
        if profile_backup_path and profile_backup_path.exists():
            status = "OWNER_APPROVED_RUNTIME_CHANGE_REQUIRES_MANUAL_OPERATOR_EXECUTION"
    dry_run = {
        "status": status,
        "generated_at_utc": utc_now(),
        "policy_id": policy.get("policy_id"),
        "boundary": (
            "This script does not edit MT5 charts, profiles, EA inputs, orders, or positions. "
            "It produces operator evidence and target lists only."
        ),
        "owner_approved_runtime_change_flag": owner_approved_runtime_change,
        "runtime_mutation_performed": runtime_allowed,
        "target_suspend_candidates": policy.get("suspend_candidates", []),
        "target_disable_symbols": policy.get("disable_symbols", []),
        "target_observer_only_candidates": policy.get("observer_only_candidates", []),
        "baseline_report": str(root / DEFAULT_BASELINE_MD),
        "reconciliation_report": str(root / DEFAULT_RECON_MD),
    }
    reconciliation = build_reconciliation(status, policy, rows, profile_backup_path)

    write_json(reports / DEFAULT_DRY_RUN_JSON.name, dry_run)
    write_markdown(reports / DEFAULT_DRY_RUN_MD.name, render_dry_run(dry_run))
    write_json(reports / DEFAULT_BASELINE_JSON.name, baseline)
    write_markdown(reports / DEFAULT_BASELINE_MD.name, render_baseline(baseline))
    write_json(reports / DEFAULT_RECON_JSON.name, reconciliation)
    write_markdown(reports / DEFAULT_RECON_MD.name, render_reconciliation(reconciliation))
    return ApplyOutput(status, reports / DEFAULT_DRY_RUN_MD.name, reports / DEFAULT_BASELINE_MD.name, reports / DEFAULT_RECON_MD.name)


def build_baseline(
    policy: dict[str, Any],
    rows: list[dict[str, Any]],
    weakness: dict[str, Any],
    trades_csv: Path,
    profile_backup_path: Path | None,
) -> dict[str, Any]:
    open_rows = [row for row in rows if str(row.get("state", "")).upper() == "OPEN"]
    return {
        "status": "BASELINE_READY_NO_RUNTIME_CHANGE",
        "generated_at_utc": utc_now(),
        "policy_id": policy.get("policy_id"),
        "account": weakness.get("account", {}),
        "trade_source": str(trades_csv),
        "profile_backup_path": str(profile_backup_path) if profile_backup_path else "NOT_CREATED_DRY_RUN",
        "profile_backup_exists": bool(profile_backup_path and profile_backup_path.exists()),
        "raw_summary": summarize(rows),
        "duplicate_hidden_summary": summarize(duplicate_hidden(rows)),
        "open_positions": open_position_rows(open_rows),
        "open_position_summary": summarize(open_rows),
        "active_candidates": sorted({str(row.get("candidate", "")) for row in rows if row.get("candidate")}),
        "active_symbols": sorted({str(row.get("symbol", "")) for row in rows if row.get("symbol")}),
        "active_magics": sorted({str(row.get("magic", "")) for row in rows if row.get("magic")}),
        "target_suspend_candidates": policy.get("suspend_candidates", []),
        "target_disable_symbols": policy.get("disable_symbols", []),
        "target_observer_only_candidates": policy.get("observer_only_candidates", []),
    }


def open_position_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        output.append(
            {
                "entry_time": row.get("entry_time", ""),
                "candidate": row.get("candidate", ""),
                "symbol": row.get("symbol", ""),
                "direction": row.get("direction", ""),
                "volume": row.get("volume", ""),
                "profit_aed": row.get("profit_aed", ""),
                "position_ticket": row.get("position_ticket", ""),
                "magic": row.get("magic", ""),
            }
        )
    return output


def build_reconciliation(
    status: str,
    policy: dict[str, Any],
    rows: list[dict[str, Any]],
    profile_backup_path: Path | None,
) -> dict[str, Any]:
    return {
        "status": "RECONCILIATION_REPORT_ONLY_NO_RUNTIME_CHANGE",
        "generated_at_utc": utc_now(),
        "policy_id": policy.get("policy_id"),
        "applier_status": status,
        "weak_variants_cannot_send_new_orders": "NOT_PROVEN_DRY_RUN_ONLY",
        "existing_positions_closed": False,
        "profile_backup_path": str(profile_backup_path) if profile_backup_path else "NOT_CREATED_DRY_RUN",
        "profile_backup_exists": bool(profile_backup_path and profile_backup_path.exists()),
        "breakout_retest_remains_active_if_intended": "NO_RUNTIME_CHANGE_MADE",
        "p2weakness_remains_isolated": "NO_RUNTIME_CHANGE_MADE",
        "magic_collision_check": "REPORT_ONLY",
        "live_account_touched": False,
        "logs_continued_after_change": "NO_RUNTIME_CHANGE_MADE",
        "open_positions_after": open_position_rows([row for row in rows if str(row.get("state", "")).upper() == "OPEN"]),
    }


def render_dry_run(payload: dict[str, Any]) -> list[str]:
    return [
        "# Phase 2 Demo Repair Policy Dry Run",
        "",
        f"Overall status: {payload['status']}",
        "",
        str(payload["boundary"]),
        "",
        f"Generated at UTC: `{payload['generated_at_utc']}`",
        f"Policy ID: `{payload['policy_id']}`",
        f"Owner-approved runtime-change flag: `{str(payload['owner_approved_runtime_change_flag']).lower()}`",
        f"Runtime mutation performed: `{str(payload['runtime_mutation_performed']).lower()}`",
        "",
        "## Target Actions",
        "",
        f"- Suspend candidates: `{', '.join(payload['target_suspend_candidates'])}`",
        f"- Disable symbols: `{', '.join(payload['target_disable_symbols'])}`",
        f"- Observer-only candidates: `{', '.join(payload['target_observer_only_candidates'])}`",
        "",
        "This report is not a runtime change ticket by itself.",
    ]


def render_baseline(payload: dict[str, Any]) -> list[str]:
    lines = [
        "# Phase 2 Demo Repair Baseline - 2026-06-09",
        "",
        f"Overall status: {payload['status']}",
        "",
        "Baseline before any repair enforcement. No runtime changes were made by the generator.",
        "",
        f"Generated at UTC: `{payload['generated_at_utc']}`",
        f"Policy ID: `{payload['policy_id']}`",
        f"Server: `{payload['account'].get('server', 'UNKNOWN')}`",
        f"Currency: `{payload['account'].get('currency', 'UNKNOWN')}`",
        f"Profile backup path: `{payload['profile_backup_path']}`",
        f"Profile backup exists: `{str(payload['profile_backup_exists']).lower()}`",
        "",
        "## Account / Trade Summary",
        "",
        metrics_table(
            [
                ("Raw broker view", payload["raw_summary"]),
                ("Duplicate-hidden decision view", payload["duplicate_hidden_summary"]),
                ("Open positions", payload["open_position_summary"]),
            ]
        ),
        "",
        "## Open Positions",
        "",
        "| Candidate | Symbol | Direction | Volume | Floating PnL | Position | Magic |",
        "|---|---|---|---:|---:|---|---|",
    ]
    for row in payload["open_positions"]:
        lines.append(
            f"| {row['candidate']} | {row['symbol']} | {row['direction']} | {row['volume']} | "
            f"{row['profit_aed']} | {row['position_ticket']} | {row['magic']} |"
        )
    lines.extend(["", "## Targets", ""])
    lines.extend(f"- Suspend new entries: `{item}`" for item in payload["target_suspend_candidates"])
    lines.extend(f"- Disable symbol: `{item}`" for item in payload["target_disable_symbols"])
    lines.extend(f"- Observer-only: `{item}`" for item in payload["target_observer_only_candidates"])
    return lines


def render_reconciliation(payload: dict[str, Any]) -> list[str]:
    lines = [
        "# Phase 2 Demo Repair Reconciliation - 2026-06-09",
        "",
        f"Overall status: {payload['status']}",
        "",
        "No runtime change was made by this report. Runtime reconciliation remains pending until an owner-approved operator action is performed and re-checked.",
        "",
        f"Generated at UTC: `{payload['generated_at_utc']}`",
        f"Policy ID: `{payload['policy_id']}`",
        f"Applier status: `{payload['applier_status']}`",
        "",
        "## Checks",
        "",
        f"- Weak variants cannot send new orders: `{payload['weak_variants_cannot_send_new_orders']}`",
        f"- Existing positions closed: `{str(payload['existing_positions_closed']).lower()}`",
        f"- Profile backup exists: `{str(payload['profile_backup_exists']).lower()}`",
        f"- Breakout-retest remains active if intended: `{payload['breakout_retest_remains_active_if_intended']}`",
        f"- P2WEAKNESS remains isolated: `{payload['p2weakness_remains_isolated']}`",
        f"- Live account touched: `{str(payload['live_account_touched']).lower()}`",
        f"- Logs continued after change: `{payload['logs_continued_after_change']}`",
    ]
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dry-run the Phase 2 demo repair policy.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--policy", type=Path, default=None)
    parser.add_argument("--trades-csv", type=Path, default=None)
    parser.add_argument("--weakness-json", type=Path, default=None)
    parser.add_argument("--owner-approved-runtime-change", action="store_true")
    parser.add_argument("--profile-backup-path", type=Path, default=None)
    args = parser.parse_args(argv)
    output = apply_repair_policy(
        args.root,
        args.policy,
        args.trades_csv,
        args.weakness_json,
        args.owner_approved_runtime_change,
        args.profile_backup_path,
    )
    print(f"Phase 2 demo repair policy dry run: {output.status}")
    print(output.dry_run_path)
    print(output.baseline_path)
    print(output.reconciliation_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
