from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import timedelta
import csv
from pathlib import Path
from typing import Any

from phase2_demo_repair_common import (
    DEFAULT_ACTUAL_TRADES,
    DEFAULT_POLICY,
    DEFAULT_WEAKNESS_JSON,
    duplicate_hidden,
    load_policy,
    metrics_table,
    parse_dt,
    read_json,
    read_trades,
    rows_before,
    rows_since,
    summarize,
    utc_now,
    write_json,
    write_markdown,
)


DEFAULT_RULES_CSV = Path("outputs") / "reports" / "PHASE2_REPAIR_CANDIDATE_RULES.csv"
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "PHASE2_DEMO_REPAIR_FORWARD_WEEK_REPORT.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "PHASE2_DEMO_REPAIR_FORWARD_WEEK_REPORT.md"
DEFAULT_SINCE = "2026-06-09 00:00:00"
TARGET_CANDIDATES = {
    "session_extreme_retest_v0",
    "symbol_normalized_round_retest_v0",
    "round_number_retest_v0",
}
REQUIRED_FORWARD_DAYS = 7.0
MIN_TARGET_CLOSED_TRADES = 30


@dataclass(frozen=True)
class ForwardWeekOutput:
    status: str
    json_path: Path
    markdown_path: Path


def generate_forward_week_report(
    root: Path,
    policy_path: Path | None = None,
    trades_csv: Path | None = None,
    weakness_json: Path | None = None,
    rules_csv: Path | None = None,
    since: str = DEFAULT_SINCE,
    output_json: Path | None = None,
) -> ForwardWeekOutput:
    root = root.resolve()
    policy_path = (policy_path or root / DEFAULT_POLICY).resolve()
    trades_csv = (trades_csv or root / DEFAULT_ACTUAL_TRADES).resolve()
    weakness_json = (weakness_json or root / DEFAULT_WEAKNESS_JSON).resolve()
    rules_csv = (rules_csv or root / DEFAULT_RULES_CSV).resolve()
    output_json = (output_json or root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = output_json.with_suffix(".md") if output_json.name != DEFAULT_OUTPUT_JSON.name else root / DEFAULT_OUTPUT_MD
    policy = load_policy(policy_path)
    rules = read_rules(rules_csv)
    rows = read_trades(trades_csv)
    weakness = read_json(weakness_json).get("weakness_shadow", {})
    pre_rows = duplicate_hidden(rows_before(rows, since))
    post_rows = duplicate_hidden(rows_since(rows, since))
    pre_target_rows = target_rows(pre_rows)
    post_target_rows = target_rows(post_rows)
    post_non_target_rows = [row for row in post_rows if row.get("candidate") not in TARGET_CANDIDATES]
    post_repair_keep = [row for row in post_target_rows if not should_block_by_repair_rule(row, rules)]
    post_repair_block = [row for row in post_target_rows if should_block_by_repair_rule(row, rules)]
    post_quarantine_keep = [row for row in post_target_rows if not should_block_by_quarantine(row, policy)]
    post_quarantine_block = [row for row in post_target_rows if should_block_by_quarantine(row, policy)]
    post_whole_after_repair = post_non_target_rows + post_repair_keep
    timeline = forward_timeline(post_rows, since)
    checks = confirmation_checks(post_target_rows, post_repair_keep, timeline)
    status = forward_status(post_rows, post_target_rows, timeline, checks)
    payload: dict[str, Any] = {
        "status": status,
        "generated_at_utc": utc_now(),
        "policy_id": policy.get("policy_id"),
        "since": since,
        "trade_source": str(trades_csv),
        "rules_csv": str(rules_csv),
        "boundary": "Forward-week report only. It does not authorize canonical Phase 2 or runtime promotion.",
        "pre_repair_baseline": summarize(pre_rows),
        "pre_repair_target_baseline": summarize(pre_target_rows),
        "post_repair_actual": summarize(post_rows),
        "post_target_baseline": summarize(post_target_rows),
        "post_repair_rule_v1": {
            "would_keep": summarize(post_repair_keep),
            "would_block": summarize(post_repair_block),
            "whole_portfolio_after_repair": summarize(post_whole_after_repair),
            "target_delta_closed_pnl_aed": pnl_delta(post_repair_keep, post_target_rows),
            "whole_portfolio_delta_closed_pnl_aed": pnl_delta(post_whole_after_repair, post_rows),
        },
        "post_strict_quarantine": {
            "would_keep": summarize(post_quarantine_keep),
            "would_block": summarize(post_quarantine_block),
            "target_delta_closed_pnl_aed": pnl_delta(post_quarantine_keep, post_target_rows),
        },
        "shadow_would_keep": weakness.get("combined_keep_summary", {}),
        "shadow_would_block": weakness.get("combined_block_summary", {}),
        "timeline": timeline,
        "confirmation_checks": checks,
        "promotion_requirement": [
            "Duplicate-hidden PF and PnL improve.",
            "Win rate improves or is preserved.",
            "Enough trade count remains.",
            "One fresh forward week survives.",
            "Owner/reviewer approval is recorded.",
        ],
        "promotion_decision": promotion_decision(status, checks),
    }
    write_json(output_json, payload)
    write_markdown(output_md, render_markdown(payload))
    return ForwardWeekOutput(status, output_json, output_md)


def target_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("candidate") in TARGET_CANDIDATES]


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
    return (
        row.get("candidate") in set(policy.get("suspend_candidates", []))
        or row.get("candidate") in set(policy.get("observer_only_candidates", []))
        or row.get("symbol") in set(policy.get("disable_symbols", []))
    )


def pnl_delta(new_rows: list[dict[str, Any]], baseline_rows: list[dict[str, Any]]) -> float:
    return round(float(summarize(new_rows)["closed_pnl_aed"]) - float(summarize(baseline_rows)["closed_pnl_aed"]), 2)


def forward_timeline(post_rows: list[dict[str, Any]], since: str) -> dict[str, Any]:
    start = parse_dt(since)
    latest = max([row.get("entry_dt") for row in post_rows if row.get("entry_dt")], default=None)
    expected_end = start + timedelta(days=REQUIRED_FORWARD_DAYS) if start else None
    elapsed_days = ((latest - start).total_seconds() / 86400.0) if start and latest else 0.0
    return {
        "start": since,
        "latest_entry": latest.strftime("%Y-%m-%d %H:%M:%S") if latest else None,
        "expected_end": expected_end.strftime("%Y-%m-%d %H:%M:%S") if expected_end else None,
        "elapsed_days": round(max(elapsed_days, 0.0), 4),
        "required_days": REQUIRED_FORWARD_DAYS,
        "fresh_forward_week_complete": elapsed_days >= REQUIRED_FORWARD_DAYS,
    }


def confirmation_checks(
    post_target_rows: list[dict[str, Any]],
    post_repair_keep: list[dict[str, Any]],
    timeline: dict[str, Any],
) -> dict[str, Any]:
    baseline = summarize(post_target_rows)
    kept = summarize(post_repair_keep)
    baseline_wr = baseline["closed_win_rate_pct"] or 0.0
    kept_wr = kept["closed_win_rate_pct"] or 0.0
    baseline_pf = float(baseline["profit_factor_value"])
    kept_pf = float(kept["profit_factor_value"])
    retained_pct = (
        round(float(kept["closed_trades"]) / float(baseline["closed_trades"]) * 100.0, 2)
        if baseline["closed_trades"]
        else 0.0
    )
    return {
        "fresh_week_elapsed": bool(timeline["fresh_forward_week_complete"]),
        "min_target_closed_trades": baseline["closed_trades"] >= MIN_TARGET_CLOSED_TRADES,
        "repair_closed_pnl_improves": float(kept["closed_pnl_aed"]) > float(baseline["closed_pnl_aed"]),
        "repair_pf_preserved_or_improves": kept_pf >= baseline_pf,
        "repair_win_rate_preserved_or_improves": kept_wr >= baseline_wr,
        "retained_trade_pct": retained_pct,
        "required_target_closed_trades": MIN_TARGET_CLOSED_TRADES,
    }


def forward_status(
    post_rows: list[dict[str, Any]],
    post_target_rows: list[dict[str, Any]],
    timeline: dict[str, Any],
    checks: dict[str, Any],
) -> str:
    if summarize(post_rows)["closed_trades"] == 0:
        return "PENDING_FORWARD_WEEK_NO_POST_REPAIR_SAMPLE"
    if not timeline["fresh_forward_week_complete"]:
        return "PENDING_FORWARD_WEEK_IN_PROGRESS"
    if not checks["min_target_closed_trades"]:
        return "PENDING_FORWARD_WEEK_INSUFFICIENT_TARGET_TRADES"
    if all(
        checks[key]
        for key in (
            "repair_closed_pnl_improves",
            "repair_pf_preserved_or_improves",
            "repair_win_rate_preserved_or_improves",
        )
    ):
        return "FORWARD_CONFIRMATION_REVIEW_READY"
    return "FORWARD_CONFIRMATION_FAILED_REVIEW_REQUIRED"


def promotion_decision(status: str, checks: dict[str, Any]) -> str:
    if status.startswith("PENDING"):
        return "NOT_ELIGIBLE_FORWARD_WEEK_PENDING"
    if status == "FORWARD_CONFIRMATION_REVIEW_READY":
        return "REVIEW_REQUIRED_BEFORE_PROMOTION"
    return "NOT_ELIGIBLE_WEAK_FORWARD_RESULT"


def render_markdown(payload: dict[str, Any]) -> list[str]:
    lines = [
        "# Phase 2 Demo Repair Forward Week Report",
        "",
        f"Overall status: {payload['status']}",
        "",
        str(payload["boundary"]),
        "",
        f"Generated at UTC: `{payload['generated_at_utc']}`",
        f"Policy ID: `{payload['policy_id']}`",
        f"Forward window starts: `{payload['since']}`",
        f"Expected window end: `{payload['timeline']['expected_end']}`",
        f"Latest post-start entry: `{payload['timeline']['latest_entry']}`",
        f"Elapsed days: `{payload['timeline']['elapsed_days']}` / `{payload['timeline']['required_days']}`",
        f"Promotion decision: `{payload['promotion_decision']}`",
        "",
        "## Required Comparison",
        "",
        metrics_table(
            [
                ("Pre-repair baseline", payload["pre_repair_baseline"]),
                ("Pre-repair target baseline", payload["pre_repair_target_baseline"]),
                ("Post-repair actual", payload["post_repair_actual"]),
                ("Post target baseline", payload["post_target_baseline"]),
                ("Post repair-rule v1 would keep", payload["post_repair_rule_v1"]["would_keep"]),
                ("Post repair-rule v1 would block", payload["post_repair_rule_v1"]["would_block"]),
                ("Post whole portfolio after repair-rule v1", payload["post_repair_rule_v1"]["whole_portfolio_after_repair"]),
                ("Post strict quarantine would keep", payload["post_strict_quarantine"]["would_keep"]),
                ("Post strict quarantine would block", payload["post_strict_quarantine"]["would_block"]),
                ("Shadow would keep", payload["shadow_would_keep"] or empty_summary()),
                ("Shadow would block", payload["shadow_would_block"] or empty_summary()),
            ]
        ),
        "",
        f"Post repair-rule target PnL delta: `{payload['post_repair_rule_v1']['target_delta_closed_pnl_aed']}` AED",
        f"Post repair-rule whole-portfolio PnL delta: `{payload['post_repair_rule_v1']['whole_portfolio_delta_closed_pnl_aed']}` AED",
        f"Post strict-quarantine target PnL delta: `{payload['post_strict_quarantine']['target_delta_closed_pnl_aed']}` AED",
        "",
        "## Confirmation Checks",
        "",
        "| Check | Value |",
        "|---|---:|",
    ]
    for key, value in payload["confirmation_checks"].items():
        lines.append(f"| {key} | `{value}` |")
    lines.extend(
        [
            "",
            "## Promotion Requirement",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload["promotion_requirement"])
    lines.extend(["", "No rule can be promoted from shadow to demo enforcement without owner/reviewer approval."])
    return lines


def empty_summary() -> dict[str, Any]:
    return {
        "actual_trades": 0,
        "closed_trades": 0,
        "open_trades": 0,
        "wins": 0,
        "losses": 0,
        "closed_win_rate_pct": None,
        "closed_pnl_aed": 0.0,
        "floating_pnl_aed": 0.0,
        "total_pnl_aed": 0.0,
        "profit_factor": None,
        "avg_win_aed": None,
        "avg_loss_aed": None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 2 demo repair forward-week report.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--policy", type=Path, default=None)
    parser.add_argument("--trades-csv", type=Path, default=None)
    parser.add_argument("--weakness-json", type=Path, default=None)
    parser.add_argument("--rules-csv", type=Path, default=None)
    parser.add_argument("--since", default=DEFAULT_SINCE)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args(argv)
    output = generate_forward_week_report(args.root, args.policy, args.trades_csv, args.weakness_json, args.rules_csv, args.since, args.output_json)
    print(f"Phase 2 demo repair forward week: {output.status}")
    print(output.markdown_path)
    print(output.json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
