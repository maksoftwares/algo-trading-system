from __future__ import annotations

import argparse
import csv
import itertools
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_momentum_broad_portfolio_search import is_four_year_report, load_variants
from analyze_a1_momentum_deep_portfolio_search import dedupe_trades
from analyze_a1_momentum_portfolio_combinations import summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"

ROBUST_MEMBERS = [
    "v6_freq_v4_rr0p7_max2",
    "v13_ema_trend_h1h4_long_rr0p6_no_morning",
    "freq_h1_h4_short_rr0p7_v1_night_early",
]

WEAK_START = datetime(2022, 7, 1)
WEAK_END = datetime(2023, 1, 1)
SPLIT_DATE = datetime(2024, 7, 1)


def window_filter(trades: list[dict[str, Any]], start: datetime | None, end: datetime | None) -> list[dict[str, Any]]:
    return [
        row
        for row in trades
        if (start is None or row["entry_time"] >= start) and (end is None or row["entry_time"] < end)
    ]


def summarize_safe(name: str, trades: list[dict[str, Any]]) -> dict[str, Any]:
    if not trades:
        return {
            "name": name,
            "trades": 0,
            "win_rate_pct": 0.0,
            "net_usd": 0.0,
            "profit_factor": 0.0,
            "active_days": 0,
            "trades_per_active_day": 0.0,
            "positive_months": 0,
            "negative_months": 0,
            "worst_month_usd": 0.0,
            "top25_removed_usd": 0.0,
            "max_closed_drawdown_usd": 0.0,
        }
    return summarize(name, trades)


def top_removed(trades: list[dict[str, Any]], count: int) -> float:
    profits = sorted((float(row["profit"]) for row in trades if float(row["profit"]) > 0), reverse=True)
    return round(sum(float(row["profit"]) for row in trades) - sum(profits[:count]), 2)


def build_raw_by_member(variants: dict[str, dict[str, Any]], members: list[str]) -> dict[str, list[dict[str, Any]]]:
    missing = [name for name in members if name not in variants]
    if missing:
        raise SystemExit(f"Missing selected variants: {', '.join(missing)}")
    return {name: variants[name]["trades"] for name in members}


def apply_filters(
    raw_by_member: dict[str, list[dict[str, Any]]],
    filters: tuple[tuple[str, int], ...],
) -> list[dict[str, Any]]:
    blocked = set(filters)
    raw: list[dict[str, Any]] = []
    for member, trades in raw_by_member.items():
        for row in trades:
            if (member, int(row["entry_hour"])) in blocked:
                continue
            raw.append(row)
    priority = {name: index for index, name in enumerate(raw_by_member)}
    return dedupe_trades(raw, priority)


def bucket_diagnostics(deduped: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in deduped:
        grouped[(str(row.get("variant", "")), int(row["entry_hour"]))].append(row)
    rows: list[dict[str, Any]] = []
    for (member, hour), trades in grouped.items():
        all_summary = summarize_safe(f"{member}_{hour:02d}", trades)
        weak_summary = summarize_safe(f"{member}_{hour:02d}_weak", window_filter(trades, WEAK_START, WEAK_END))
        older_summary = summarize_safe(f"{member}_{hour:02d}_older", window_filter(trades, None, SPLIT_DATE))
        rows.append(
            {
                "member": member,
                "hour": hour,
                "trades": all_summary["trades"],
                "net_usd": all_summary["net_usd"],
                "profit_factor": all_summary["profit_factor"] or 0.0,
                "win_rate_pct": all_summary["win_rate_pct"],
                "weak_trades": weak_summary["trades"],
                "weak_net_usd": weak_summary["net_usd"],
                "weak_profit_factor": weak_summary["profit_factor"] or 0.0,
                "weak_win_rate_pct": weak_summary["win_rate_pct"],
                "older_trades": older_summary["trades"],
                "older_net_usd": older_summary["net_usd"],
                "older_profit_factor": older_summary["profit_factor"] or 0.0,
            }
        )
    rows.sort(key=lambda row: (row["weak_net_usd"], row["net_usd"]))
    return rows


def evaluate(name: str, deduped: list[dict[str, Any]], filters: tuple[tuple[str, int], ...]) -> dict[str, Any]:
    all_summary = summarize_safe(name, deduped)
    weak = summarize_safe(name + "_2022h2", window_filter(deduped, WEAK_START, WEAK_END))
    older = summarize_safe(name + "_older", window_filter(deduped, None, SPLIT_DATE))
    newer = summarize_safe(name + "_newer", window_filter(deduped, SPLIT_DATE, None))
    filter_text = [f"{member}@{hour:02d}" for member, hour in filters]
    row = {
        "name": name,
        "filters": filter_text,
        "filter_count": len(filters),
        "trades": all_summary["trades"],
        "win_rate_pct": all_summary["win_rate_pct"],
        "net_usd": all_summary["net_usd"],
        "profit_factor": all_summary["profit_factor"] or 0.0,
        "active_days": all_summary["active_days"],
        "trades_per_active_day": all_summary["trades_per_active_day"],
        "positive_months": all_summary["positive_months"],
        "negative_months": all_summary["negative_months"],
        "worst_month_usd": all_summary["worst_month_usd"],
        "top25_removed_usd": top_removed(deduped, 25),
        "top100_removed_usd": top_removed(deduped, 100),
        "max_closed_drawdown_usd": all_summary["max_closed_drawdown_usd"],
        "weak_trades": weak["trades"],
        "weak_win_rate_pct": weak["win_rate_pct"],
        "weak_net_usd": weak["net_usd"],
        "weak_profit_factor": weak["profit_factor"] or 0.0,
        "older_trades": older["trades"],
        "older_net_usd": older["net_usd"],
        "older_profit_factor": older["profit_factor"] or 0.0,
        "newer_trades": newer["trades"],
        "newer_net_usd": newer["net_usd"],
        "newer_profit_factor": newer["profit_factor"] or 0.0,
    }
    row["decision"] = decision(row)
    row["score"] = round(score(row), 2)
    return row


def decision(row: dict[str, Any]) -> str:
    if row["trades"] < 2200:
        return "FAIL_SAMPLE"
    if row["active_days"] < 560:
        return "FAIL_ACTIVE_DAYS"
    if row["trades_per_active_day"] < 3.5:
        return "FAIL_FREQUENCY"
    if row["win_rate_pct"] < 62.0:
        return "FAIL_WIN_RATE"
    if row["profit_factor"] < 1.30:
        return "FAIL_PF"
    if row["net_usd"] < 1600:
        return "FAIL_NET"
    if row["top100_removed_usd"] <= 0:
        return "FAIL_TOP_WINNER_STRESS"
    if row["weak_net_usd"] < 25:
        return "REVIEW_WEAK_WINDOW_STILL_THIN"
    if row["weak_profit_factor"] < 1.08:
        return "REVIEW_WEAK_WINDOW_STILL_THIN"
    return "REVIEW_REPAIR_CANDIDATE"


def score(row: dict[str, Any]) -> float:
    return (
        float(row["profit_factor"]) * 1100.0
        + float(row["win_rate_pct"]) * 12.0
        + float(row["net_usd"]) / max(float(row["max_closed_drawdown_usd"]), 1.0) * 95.0
        + float(row["active_days"])
        + float(row["trades_per_active_day"]) * 100.0
        + float(row["weak_net_usd"]) * 3.0
        + float(row["weak_profit_factor"]) * 400.0
        - float(row["negative_months"]) * 20.0
    )


def candidate_filters(bucket_rows: list[dict[str, Any]], max_items: int) -> list[tuple[str, int]]:
    candidates: list[tuple[str, int]] = []
    for row in bucket_rows:
        if row["weak_trades"] < 5:
            continue
        if row["weak_net_usd"] >= 0 and row["weak_profit_factor"] >= 1.0:
            continue
        candidates.append((row["member"], int(row["hour"])))
    return candidates[:max_items]


def render_markdown(payload: dict[str, Any]) -> str:
    baseline = payload["baseline"]
    lines = [
        "# A1 XAU M5 Momentum Robust Portfolio Repair Diagnostic",
        "",
        "Generated: 2026-07-02",
        "",
        "Scope: offline diagnostic only. No MT5 runtime, charts, presets, orders, or positions were changed.",
        "",
        "## Purpose",
        "",
        "The robust portfolio matches the owner's frequency and win-rate target, but 2022-H2 is thin. This diagnostic tests small member-hour blocks to see whether the weak window can be improved without destroying frequency.",
        "",
        "## Baseline",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Trades | {baseline['trades']} |",
        f"| Win rate | {baseline['win_rate_pct']}% |",
        f"| Net USD | {baseline['net_usd']} |",
        f"| PF | {baseline['profit_factor']} |",
        f"| Active days | {baseline['active_days']} |",
        f"| Trades / active day | {baseline['trades_per_active_day']} |",
        f"| 2022-H2 net / PF | {baseline['weak_net_usd']} / {baseline['weak_profit_factor']} |",
        f"| Top100 removed USD | {baseline['top100_removed_usd']} |",
        "",
        "## Top Repair Candidates",
        "",
        "| Rank | Decision | Filters | Trades | WR % | Net | PF | Active | T/active | 2022-H2 net/PF | Older net/PF | Newer net/PF | Top100 removed | DD |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(payload["top_candidates"], 1):
        filters = ", ".join(row["filters"]) if row["filters"] else "none"
        lines.append(
            f"| {index} | `{row['decision']}` | `{filters}` | {row['trades']} | {row['win_rate_pct']} | {row['net_usd']} | {row['profit_factor']} | {row['active_days']} | {row['trades_per_active_day']} | {row['weak_net_usd']} / {row['weak_profit_factor']} | {row['older_net_usd']} / {row['older_profit_factor']} | {row['newer_net_usd']} / {row['newer_profit_factor']} | {row['top100_removed_usd']} | {row['max_closed_drawdown_usd']} |"
        )
    lines.extend(
        [
            "",
            "## Weakest Member-Hour Buckets In 2022-H2",
            "",
            "| Rank | Member | Hour | 2022-H2 trades | 2022-H2 net | 2022-H2 PF | All net | All PF |",
            "|---:|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for index, row in enumerate(payload["weak_buckets"][:20], 1):
        lines.append(
            f"| {index} | `{row['member']}` | {row['hour']:02d} | {row['weak_trades']} | {row['weak_net_usd']} | {row['weak_profit_factor']} | {row['net_usd']} | {row['profit_factor']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This is not a permission slip to change runtime. A repair is only interesting if it improves the weak 2022-H2 window while keeping the all-period frequency and PF high. If a filter improves 2022-H2 only by deleting too much profitable recent behavior, it should be rejected.",
            "",
        ]
    )
    return "\n".join(lines)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["filters"] = " | ".join(out["filters"])
            writer.writerow(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-md", type=Path, default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_REPAIR_DIAGNOSTIC_2026_07_02.md")
    parser.add_argument("--output-json", type=Path, default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_REPAIR_DIAGNOSTIC_2026_07_02.json")
    parser.add_argument("--output-csv", type=Path, default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_REPAIR_DIAGNOSTIC_2026_07_02.csv")
    parser.add_argument("--max-filter-items", type=int, default=18)
    args = parser.parse_args()

    reports = sorted(path for path in REPORTS_DIR.glob("A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_*.json") if is_four_year_report(path))
    variants = load_variants(reports)
    raw_by_member = build_raw_by_member(variants, ROBUST_MEMBERS)
    baseline_trades = apply_filters(raw_by_member, tuple())
    baseline = evaluate("baseline", baseline_trades, tuple())
    buckets = bucket_diagnostics(baseline_trades)
    filters = candidate_filters(buckets, args.max_filter_items)
    rows = [baseline]
    for size in [1, 2]:
        for combo in itertools.combinations(filters, size):
            deduped = apply_filters(raw_by_member, combo)
            rows.append(evaluate("repair_" + "_".join(f"{m}@{h:02d}" for m, h in combo), deduped, combo))
    rows.sort(key=lambda row: (row["decision"] not in {"REVIEW_REPAIR_CANDIDATE", "REVIEW_WEAK_WINDOW_STILL_THIN"}, -row["score"]))
    payload = {
        "status": "ROBUST_PORTFOLIO_REPAIR_DIAGNOSTIC_COMPLETE",
        "boundary": "offline_exact_mt5_trade_csv_analysis_only_no_runtime_change",
        "members": ROBUST_MEMBERS,
        "baseline": baseline,
        "candidate_filter_pool": [f"{member}@{hour:02d}" for member, hour in filters],
        "top_candidates": rows[:25],
        "weak_buckets": buckets,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.output_md.write_text(render_markdown(payload), encoding="utf-8")
    write_csv(args.output_csv, rows)
    print(args.output_md)
    print(args.output_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
