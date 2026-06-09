from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any

from phase2_demo_repair_common import (
    DEFAULT_ACTUAL_TRADES,
    DEFAULT_POLICY,
    duplicate_hidden,
    fmt,
    load_policy,
    metrics_table,
    read_trades,
    summarize,
    utc_now,
    write_json,
    write_markdown,
)


DEFAULT_RULES_CSV = Path("outputs") / "reports" / "PHASE2_REPAIR_CANDIDATE_RULES.csv"
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "PHASE2_DEMO_REPAIR_LAST_WEEK_BACKTEST.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "PHASE2_DEMO_REPAIR_LAST_WEEK_BACKTEST.md"
DEFAULT_OUTPUT_CSV = Path("outputs") / "reports" / "PHASE2_DEMO_REPAIR_LAST_WEEK_BACKTEST.csv"

TARGET_CANDIDATES = (
    "session_extreme_retest_v0",
    "symbol_normalized_round_retest_v0",
    "round_number_retest_v0",
)


@dataclass(frozen=True)
class LastWeekBacktestOutput:
    status: str
    json_path: Path
    markdown_path: Path
    csv_path: Path


def generate_last_week_repair_backtest(
    root: Path,
    trades_csv: Path | None = None,
    rules_csv: Path | None = None,
    policy_path: Path | None = None,
    output_json: Path | None = None,
) -> LastWeekBacktestOutput:
    root = root.resolve()
    trades_csv = (trades_csv or root / DEFAULT_ACTUAL_TRADES).resolve()
    rules_csv = (rules_csv or root / DEFAULT_RULES_CSV).resolve()
    policy_path = (policy_path or root / DEFAULT_POLICY).resolve()
    output_json = (output_json or root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_OUTPUT_JSON.name else root / DEFAULT_OUTPUT_MD
    output_csv = output_json.with_suffix(".csv") if output_json.name != DEFAULT_OUTPUT_JSON.name else root / DEFAULT_OUTPUT_CSV

    rows = read_trades(trades_csv)
    week_rows, start, end = select_last_available_week(rows)
    dedup_week_rows = duplicate_hidden(week_rows)
    target_rows = [row for row in dedup_week_rows if row.get("candidate") in TARGET_CANDIDATES]
    non_target_rows = [row for row in dedup_week_rows if row.get("candidate") not in TARGET_CANDIDATES]
    raw_target_rows = [row for row in week_rows if row.get("candidate") in TARGET_CANDIDATES]
    rules = read_rules(rules_csv)
    policy = load_policy(policy_path)

    repair_kept = [row for row in target_rows if not should_block_by_repair_rule(row, rules)]
    repair_blocked = [row for row in target_rows if should_block_by_repair_rule(row, rules)]
    quarantine_kept = [row for row in target_rows if not should_block_by_quarantine(row, policy)]
    quarantine_blocked = [row for row in target_rows if should_block_by_quarantine(row, policy)]
    whole_repair = non_target_rows + repair_kept
    whole_quarantine = non_target_rows + quarantine_kept

    candidate_rows = [
        candidate_backtest(candidate, target_rows, raw_target_rows, rules, policy)
        for candidate in TARGET_CANDIDATES
    ]
    payload: dict[str, Any] = {
        "status": "REPAIR_LAST_WEEK_BACKTEST_READY",
        "generated_at_utc": utc_now(),
        "boundary": (
            "Retrospective shadow backtest on actual demo broker rows only. No MT5 charts, inputs, "
            "orders, positions, presets, canonical Phase 2 status, or live-capital permissions are changed."
        ),
        "source_csv": str(trades_csv),
        "rules_csv": str(rules_csv),
        "policy_path": str(policy_path),
        "window": {
            "start": start.strftime("%Y-%m-%d %H:%M:%S") if start else None,
            "end": end.strftime("%Y-%m-%d %H:%M:%S") if end else None,
            "selection": "last available broker week ending at latest entry timestamp",
        },
        "all_duplicate_hidden_baseline": summarize(dedup_week_rows),
        "target_duplicate_hidden_baseline": summarize(target_rows),
        "target_raw_baseline": summarize(raw_target_rows),
        "repair_rule_v1": {
            "would_keep": summarize(repair_kept),
            "would_block": summarize(repair_blocked),
            "delta_vs_target_baseline_closed_pnl_aed": pnl_delta(repair_kept, target_rows),
            "whole_portfolio_after_repair": summarize(whole_repair),
            "whole_portfolio_delta_closed_pnl_aed": pnl_delta(whole_repair, dedup_week_rows),
        },
        "strict_quarantine_policy": {
            "would_keep": summarize(quarantine_kept),
            "would_block": summarize(quarantine_blocked),
            "delta_vs_target_baseline_closed_pnl_aed": pnl_delta(quarantine_kept, target_rows),
            "whole_portfolio_after_quarantine": summarize(whole_quarantine),
            "whole_portfolio_delta_closed_pnl_aed": pnl_delta(whole_quarantine, dedup_week_rows),
        },
        "candidate_results": candidate_rows,
        "interpretation": [
            "Repair-rule v1 is the best retrospective result, but it is still post-hoc shadow evidence.",
            "Strict quarantine improves account-level decision PnL by removing the weak candidates, but it also removes any positive repaired slices.",
            "Forward evidence is still required before enforcing any rule in demo runtime.",
        ],
    }
    write_json(output_json, payload)
    write_markdown(output_md, render_markdown(payload))
    write_candidate_csv(output_csv, candidate_rows)
    return LastWeekBacktestOutput(str(payload["status"]), output_json, output_md, output_csv)


def select_last_available_week(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], datetime | None, datetime | None]:
    dated = [row for row in rows if row.get("entry_dt")]
    if not dated:
        return [], None, None
    end = max(row["entry_dt"] for row in dated)
    start = datetime.combine((end - timedelta(days=7)).date(), time.min)
    return [row for row in dated if start <= row["entry_dt"] <= end], start, end


def read_rules(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def should_block_by_repair_rule(row: dict[str, Any], rules: list[dict[str, str]]) -> bool:
    for rule in rules:
        if rule.get("candidate") != row.get("candidate"):
            continue
        rule_type = rule.get("rule_type")
        if rule_type in {"DUPLICATE_ONLY_REBUILD", "OBSERVER_ONLY_REBUILD"}:
            return True
        if rule_type != "BLOCK_CLUSTER":
            continue
        if (
            rule.get("symbol") == row.get("symbol")
            and rule.get("time_bucket") == row.get("time_bucket")
            and rule.get("direction") == row.get("direction")
        ):
            return True
    return False


def should_block_by_quarantine(row: dict[str, Any], policy: dict[str, Any]) -> bool:
    candidate = str(row.get("candidate", ""))
    symbol = str(row.get("symbol", ""))
    return (
        candidate in set(policy.get("suspend_candidates", []))
        or candidate in set(policy.get("observer_only_candidates", []))
        or symbol in set(policy.get("disable_symbols", []))
    )


def candidate_backtest(
    candidate: str,
    target_rows: list[dict[str, Any]],
    raw_target_rows: list[dict[str, Any]],
    rules: list[dict[str, str]],
    policy: dict[str, Any],
) -> dict[str, Any]:
    rows = [row for row in target_rows if row.get("candidate") == candidate]
    raw_rows = [row for row in raw_target_rows if row.get("candidate") == candidate]
    repair_kept = [row for row in rows if not should_block_by_repair_rule(row, rules)]
    repair_blocked = [row for row in rows if should_block_by_repair_rule(row, rules)]
    quarantine_kept = [row for row in rows if not should_block_by_quarantine(row, policy)]
    quarantine_blocked = [row for row in rows if should_block_by_quarantine(row, policy)]
    return {
        "candidate": candidate,
        "raw_baseline": summarize(raw_rows),
        "duplicate_hidden_baseline": summarize(rows),
        "repair_rule_v1_keep": summarize(repair_kept),
        "repair_rule_v1_block": summarize(repair_blocked),
        "repair_rule_v1_delta_closed_pnl_aed": pnl_delta(repair_kept, rows),
        "strict_quarantine_keep": summarize(quarantine_kept),
        "strict_quarantine_block": summarize(quarantine_blocked),
        "strict_quarantine_delta_closed_pnl_aed": pnl_delta(quarantine_kept, rows),
    }


def pnl_delta(new_rows: list[dict[str, Any]], baseline_rows: list[dict[str, Any]]) -> float:
    return round(float(summarize(new_rows)["closed_pnl_aed"]) - float(summarize(baseline_rows)["closed_pnl_aed"]), 2)


def render_markdown(payload: dict[str, Any]) -> list[str]:
    lines = [
        "# Phase 2 Demo Repair Last-Week Backtest",
        "",
        f"Overall status: {payload['status']}",
        "",
        str(payload["boundary"]),
        "",
        f"Generated at UTC: `{payload['generated_at_utc']}`",
        f"Window: `{payload['window']['start']}` to `{payload['window']['end']}`",
        f"Source CSV: `{payload['source_csv']}`",
        f"Rules CSV: `{payload['rules_csv']}`",
        "",
        "## Portfolio Summary",
        "",
        metrics_table(
            [
                ("All duplicate-hidden baseline", payload["all_duplicate_hidden_baseline"]),
                ("Target weak-EA baseline", payload["target_duplicate_hidden_baseline"]),
                ("Repair-rule v1 target keep", payload["repair_rule_v1"]["would_keep"]),
                ("Strict quarantine target keep", payload["strict_quarantine_policy"]["would_keep"]),
                ("Whole portfolio after repair-rule v1", payload["repair_rule_v1"]["whole_portfolio_after_repair"]),
                ("Whole portfolio after strict quarantine", payload["strict_quarantine_policy"]["whole_portfolio_after_quarantine"]),
            ]
        ),
        "",
        f"Repair-rule v1 target PnL delta: `{fmt(payload['repair_rule_v1']['delta_vs_target_baseline_closed_pnl_aed'])}` AED",
        f"Repair-rule v1 whole-portfolio PnL delta: `{fmt(payload['repair_rule_v1']['whole_portfolio_delta_closed_pnl_aed'])}` AED",
        f"Strict quarantine target PnL delta: `{fmt(payload['strict_quarantine_policy']['delta_vs_target_baseline_closed_pnl_aed'])}` AED",
        f"Strict quarantine whole-portfolio PnL delta: `{fmt(payload['strict_quarantine_policy']['whole_portfolio_delta_closed_pnl_aed'])}` AED",
        "",
        "## Per-Candidate Results",
        "",
        "| Candidate | Baseline Closed | Baseline WR | Baseline PnL | Baseline PF | Repair Keep Closed | Repair WR | Repair PnL | Repair PF | Repair Delta | Quarantine Delta |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["candidate_results"]:
        baseline = row["duplicate_hidden_baseline"]
        repair = row["repair_rule_v1_keep"]
        lines.append(
            f"| {row['candidate']} | {baseline['closed_trades']} | {fmt(baseline['closed_win_rate_pct'], pct=True)} | "
            f"{fmt(baseline['closed_pnl_aed'])} | {fmt(baseline['profit_factor'])} | {repair['closed_trades']} | "
            f"{fmt(repair['closed_win_rate_pct'], pct=True)} | {fmt(repair['closed_pnl_aed'])} | "
            f"{fmt(repair['profit_factor'])} | {fmt(row['repair_rule_v1_delta_closed_pnl_aed'])} | "
            f"{fmt(row['strict_quarantine_delta_closed_pnl_aed'])} |"
        )
    lines.extend(["", "## Interpretation", ""])
    lines.extend(f"- {item}" for item in payload["interpretation"])
    return lines


def write_candidate_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "candidate",
        "baseline_closed",
        "baseline_win_rate_pct",
        "baseline_closed_pnl_aed",
        "baseline_profit_factor",
        "repair_keep_closed",
        "repair_keep_win_rate_pct",
        "repair_keep_closed_pnl_aed",
        "repair_keep_profit_factor",
        "repair_delta_closed_pnl_aed",
        "quarantine_delta_closed_pnl_aed",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            baseline = row["duplicate_hidden_baseline"]
            repair = row["repair_rule_v1_keep"]
            writer.writerow(
                {
                    "candidate": row["candidate"],
                    "baseline_closed": baseline["closed_trades"],
                    "baseline_win_rate_pct": baseline["closed_win_rate_pct"],
                    "baseline_closed_pnl_aed": baseline["closed_pnl_aed"],
                    "baseline_profit_factor": baseline["profit_factor"],
                    "repair_keep_closed": repair["closed_trades"],
                    "repair_keep_win_rate_pct": repair["closed_win_rate_pct"],
                    "repair_keep_closed_pnl_aed": repair["closed_pnl_aed"],
                    "repair_keep_profit_factor": repair["profit_factor"],
                    "repair_delta_closed_pnl_aed": row["repair_rule_v1_delta_closed_pnl_aed"],
                    "quarantine_delta_closed_pnl_aed": row["strict_quarantine_delta_closed_pnl_aed"],
                }
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backtest Phase 2 demo repair rules over the last available broker week.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--trades-csv", type=Path, default=None)
    parser.add_argument("--rules-csv", type=Path, default=None)
    parser.add_argument("--policy", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    output = generate_last_week_repair_backtest(args.root, args.trades_csv, args.rules_csv, args.policy, args.output_json)
    print(f"Phase 2 demo repair last-week backtest: {output.status}")
    print(output.markdown_path)
    print(output.json_path)
    print(output.csv_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
