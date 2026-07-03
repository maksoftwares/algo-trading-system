from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_momentum_daily_fit_portfolio_search import daily_metrics, window_summary
from analyze_a1_momentum_daily_state_guard_search import day_tail_stats, top_removed_usd
from analyze_a1_momentum_feature_band_day_state_search import month_stats
from analyze_a1_momentum_feature_band_reliability_residual_search import (
    apply_reliability_guard,
    as_float,
    enrich_base_trades,
)
from analyze_a1_momentum_portfolio_combinations import summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_STRESS_2026_07_02"
SPLIT_DATE = datetime(2024, 7, 1)


def residual_filter(row: dict[str, Any]) -> tuple[bool, str]:
    direction = row.get("direction")
    if direction == "LONG" and row.get("entry_hour") == 18:
        return True, "block_LONG_entry_hour_18"
    if direction == "SHORT" and as_float(row.get("close_to_recent_extreme")) >= -0.92:
        return True, "block_SHORT_close_to_recent_extreme_>=_-0.92"
    return False, ""


def build_candidate(base_trades: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    kept: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for row in base_trades:
        should_block, reason = residual_filter(row)
        if should_block:
            copied = dict(row)
            copied["residual_block_reason"] = reason
            blocked.append(copied)
        else:
            kept.append(row)
    selected, guard_stats = apply_reliability_guard(kept)
    return selected, guard_stats, blocked


def profit_factor(profits: list[float]) -> float | None:
    gross_profit = sum(value for value in profits if value > 0)
    gross_loss = -sum(value for value in profits if value < 0)
    if gross_loss == 0:
        return None
    return round(gross_profit / gross_loss, 2)


def max_drawdown(profits: list[float], starting_balance: float = 1000.0) -> float:
    equity = starting_balance
    peak = starting_balance
    max_dd = 0.0
    for profit in profits:
        equity += profit
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    return round(max_dd, 2)


def day_count_distribution(trades: list[dict[str, Any]]) -> dict[str, Any]:
    by_day: dict[str, int] = defaultdict(int)
    for row in trades:
        by_day[row["entry_date"]] += 1
    counts = Counter(by_day.values())
    active_days = len(by_day)
    two_plus = sum(1 for count in by_day.values() if count >= 2)
    three_plus = sum(1 for count in by_day.values() if count >= 3)
    return {
        "one_trade_days": counts.get(1, 0),
        "two_trade_days": counts.get(2, 0),
        "three_trade_days": counts.get(3, 0),
        "four_trade_days": counts.get(4, 0),
        "five_trade_days": counts.get(5, 0),
        "six_plus_trade_days": sum(value for key, value in counts.items() if key >= 6),
        "two_plus_trade_day_pct": round(100.0 * two_plus / active_days, 2) if active_days else 0.0,
        "three_plus_trade_day_pct": round(100.0 * three_plus / active_days, 2) if active_days else 0.0,
    }


def summarize_view(name: str, trades: list[dict[str, Any]]) -> dict[str, Any]:
    summary = summarize(name, trades)
    summary.update(daily_metrics(trades))
    summary.update(day_tail_stats(trades))
    summary.update(month_stats(trades))
    summary.update(day_count_distribution(trades))
    summary["top1_removed_usd"] = top_removed_usd(trades, 1)
    summary["top3_removed_usd"] = top_removed_usd(trades, 3)
    summary["top5_removed_usd"] = top_removed_usd(trades, 5)
    summary["top10_removed_usd"] = top_removed_usd(trades, 10)
    summary["top25_removed_usd"] = top_removed_usd(trades, 25)
    summary["top50_removed_usd"] = top_removed_usd(trades, 50)
    summary["top100_removed_usd"] = top_removed_usd(trades, 100)
    summary["top200_removed_usd"] = top_removed_usd(trades, 200)
    older = window_summary("older", trades, None, SPLIT_DATE)
    newer = window_summary("newer", trades, SPLIT_DATE, None)
    summary["older_net_usd"] = older.get("net_usd", 0.0)
    summary["older_profit_factor"] = older.get("profit_factor") or 0.0
    summary["newer_net_usd"] = newer.get("net_usd", 0.0)
    summary["newer_profit_factor"] = newer.get("profit_factor") or 0.0
    return summary


def bucket_key(row: dict[str, Any], bucket: str) -> str:
    dt = row["entry_time"]
    if bucket == "half_year":
        return f"{dt.year}-H{1 if dt.month <= 6 else 2}"
    if bucket == "quarter":
        return f"{dt.year}-Q{((dt.month - 1) // 3) + 1}"
    if bucket == "month":
        return dt.strftime("%Y-%m")
    if bucket == "direction":
        return str(row.get("direction", ""))
    if bucket == "session":
        return str(row.get("entry_session", ""))
    if bucket == "hour":
        return f"{int(row.get('entry_hour', dt.hour)):02d}"
    raise ValueError(f"unknown bucket {bucket}")


def summarize_buckets(trades: list[dict[str, Any]], bucket: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in trades:
        grouped[bucket_key(row, bucket)].append(row)
    rows: list[dict[str, Any]] = []
    for key in sorted(grouped):
        summary = summarize_view(key, grouped[key])
        rows.append(
            {
                "bucket_type": bucket,
                "bucket": key,
                "trades": summary["trades"],
                "win_rate_pct": summary["win_rate_pct"],
                "net_usd": summary["net_usd"],
                "profit_factor": summary["profit_factor"],
                "active_days": summary.get("active_days", 0),
                "trades_per_active_day": summary.get("trades_per_active_day", 0.0),
                "positive_day_pct": summary.get("positive_day_pct", 0.0),
                "three_plus_trade_day_pct": summary.get("three_plus_trade_day_pct", 0.0),
                "max_closed_drawdown_usd": summary.get("max_closed_drawdown_usd", 0.0),
            }
        )
    return rows


def rolling_trade_windows(trades: list[dict[str, Any]], window: int = 250, step: int = 25) -> list[dict[str, Any]]:
    ordered = sorted(trades, key=lambda row: (row["exit_time"], row["entry_time"], row["variant"]))
    rows: list[dict[str, Any]] = []
    if len(ordered) < window:
        return rows
    for start in range(0, len(ordered) - window + 1, step):
        selected = ordered[start : start + window]
        profits = [float(row["profit"]) for row in selected]
        rows.append(
            {
                "start_index": start,
                "end_index": start + window - 1,
                "start_time": selected[0]["entry_time"].strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": selected[-1]["entry_time"].strftime("%Y-%m-%d %H:%M:%S"),
                "trades": len(selected),
                "net_usd": round(sum(profits), 2),
                "profit_factor": profit_factor(profits),
                "win_rate_pct": round(100.0 * sum(1 for value in profits if value > 0) / len(profits), 2),
                "max_closed_drawdown_usd": max_drawdown(profits),
            }
        )
    return rows


def stress_decision(summary: dict[str, Any], bucket_rows: list[dict[str, Any]], rolling_rows: list[dict[str, Any]]) -> str:
    half_year_rows = [row for row in bucket_rows if row["bucket_type"] == "half_year"]
    negative_half_years = [row for row in half_year_rows if float(row["net_usd"]) <= 0]
    negative_rolling = [row for row in rolling_rows if float(row["net_usd"]) <= 0]
    if summary["trades"] < 1800:
        return "FAIL_SAMPLE"
    if summary["trades_per_active_day"] < 2.0:
        return "FAIL_SPARSE_STRATEGY_BUSINESS_REQUIREMENT"
    if summary["trades_per_active_day"] < 3.0:
        return "FAIL_PREFERRED_DAILY_CADENCE"
    if summary["three_plus_trade_day_pct"] < 50.0:
        return "FAIL_THREE_PLUS_DAY_COVERAGE"
    if summary["win_rate_pct"] < 65.0:
        return "FAIL_WIN_RATE"
    if (summary["profit_factor"] or 0.0) < 1.45:
        return "FAIL_PROFIT_FACTOR"
    if summary["positive_day_pct"] < 60.0:
        return "FAIL_POSITIVE_DAY_RATE"
    if summary["top100_removed_usd"] <= 0:
        return "FAIL_TOP100_ROBUSTNESS"
    if summary["older_net_usd"] <= 0 or summary["newer_net_usd"] <= 0:
        return "FAIL_OLDER_NEWER_SPLIT"
    if negative_half_years:
        return "REVIEW_WITH_WEAK_HALF_YEAR_BUCKET"
    if negative_rolling:
        return "REVIEW_WITH_NEGATIVE_ROLLING_250_TRADE_WINDOWS"
    return "RESIDUAL_RELIABILITY_STRESS_PASS_REVIEW_READY"


def write_bucket_csv(rows: list[dict[str, Any]], path: Path) -> None:
    fields = [
        "bucket_type",
        "bucket",
        "trades",
        "win_rate_pct",
        "net_usd",
        "profit_factor",
        "active_days",
        "trades_per_active_day",
        "positive_day_pct",
        "three_plus_trade_day_pct",
        "max_closed_drawdown_usd",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def compact_summary(summary: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "trades",
        "win_rate_pct",
        "net_usd",
        "profit_factor",
        "active_days",
        "trades_per_active_day",
        "one_trade_days",
        "two_trade_days",
        "three_trade_days",
        "four_trade_days",
        "five_trade_days",
        "six_plus_trade_days",
        "two_plus_trade_day_pct",
        "three_plus_trade_day_pct",
        "positive_day_pct",
        "positive_months",
        "negative_months",
        "worst_month_usd",
        "best_month_usd",
        "top1_removed_usd",
        "top3_removed_usd",
        "top5_removed_usd",
        "top10_removed_usd",
        "top25_removed_usd",
        "top50_removed_usd",
        "top100_removed_usd",
        "top200_removed_usd",
        "max_closed_drawdown_usd",
        "older_net_usd",
        "older_profit_factor",
        "newer_net_usd",
        "newer_profit_factor",
    ]
    return {key: summary.get(key) for key in keys}


def render(
    baseline: dict[str, Any],
    residual: dict[str, Any],
    blocked: list[dict[str, Any]],
    bucket_rows: list[dict[str, Any]],
    rolling_rows: list[dict[str, Any]],
    decision: str,
    json_path: Path,
    csv_path: Path,
) -> str:
    negative_half_years = [row for row in bucket_rows if row["bucket_type"] == "half_year" and row["net_usd"] <= 0]
    negative_rolling = [row for row in rolling_rows if row["net_usd"] <= 0]
    lines = [
        "# A1 XAU M5 Momentum Feature-Band Residual-Reliability Stress - 2026-07-02",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Scope: offline MT5 Strategy Tester trade CSV and signal-log analysis only. No MT5 runtime, charts, presets, orders, or positions were changed.",
        "",
        f"Decision: `{decision}`",
        "",
        "## Business Requirement",
        "",
        "Sparse strategies are rejected even if their statistics look clean. The owner requirement is multiple intraday opportunities: hard minimum 2 trades per active day, preferred 3-5 trades per active day, and at least 50% of active days with 3+ trades.",
        "",
        "## Candidate Definition",
        "",
        "- Base package: feature-band daily-reliability candidate, +50 USD package target, max 6 package trades/day, no daily loss stop, 15-minute cooldown after a package losing trade.",
        "- Residual filter: block LONG entries at server hour 18; block SHORT entries where `close_to_recent_extreme >= -0.92`.",
        "- Planned forward magics remain analysis-only here: 932296/932297. This stress report does not attach them.",
        "",
        "## Headline",
        "",
        "| View | Trades | WR % | Net | PF | Active days | T/active | 2+ day % | 3+ day % | Pos day % | Top100 removed | DD | Older PF/net | Newer PF/net |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label, row in [("Daily-reliability baseline", baseline), ("Residual-reliability candidate", residual)]:
        lines.append(
            f"| {label} | {row['trades']} | {row['win_rate_pct']:.2f} | {row['net_usd']:.2f} | {row['profit_factor']} | {row['active_days']} | {row['trades_per_active_day']:.2f} | {row['two_plus_trade_day_pct']:.2f} | {row['three_plus_trade_day_pct']:.2f} | {row['positive_day_pct']:.2f} | {row['top100_removed_usd']:.2f} | {row['max_closed_drawdown_usd']:.2f} | {row['older_profit_factor']:.2f} / {row['older_net_usd']:.2f} | {row['newer_profit_factor']:.2f} / {row['newer_net_usd']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Trade Count Distribution",
            "",
            "| View | 1-trade days | 2-trade days | 3-trade days | 4-trade days | 5-trade days | 6+ trade days |",
            "|---|---:|---:|---:|---:|---:|---:|",
            f"| Baseline | {baseline['one_trade_days']} | {baseline['two_trade_days']} | {baseline['three_trade_days']} | {baseline['four_trade_days']} | {baseline['five_trade_days']} | {baseline['six_plus_trade_days']} |",
            f"| Residual | {residual['one_trade_days']} | {residual['two_trade_days']} | {residual['three_trade_days']} | {residual['four_trade_days']} | {residual['five_trade_days']} | {residual['six_plus_trade_days']} |",
            "",
            "## Robustness",
            "",
            "| View | Top1 removed | Top3 removed | Top5 removed | Top10 removed | Top25 removed | Top50 removed | Top100 removed | Top200 removed |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            f"| Baseline | {baseline['top1_removed_usd']:.2f} | {baseline['top3_removed_usd']:.2f} | {baseline['top5_removed_usd']:.2f} | {baseline['top10_removed_usd']:.2f} | {baseline['top25_removed_usd']:.2f} | {baseline['top50_removed_usd']:.2f} | {baseline['top100_removed_usd']:.2f} | {baseline['top200_removed_usd']:.2f} |",
            f"| Residual | {residual['top1_removed_usd']:.2f} | {residual['top3_removed_usd']:.2f} | {residual['top5_removed_usd']:.2f} | {residual['top10_removed_usd']:.2f} | {residual['top25_removed_usd']:.2f} | {residual['top50_removed_usd']:.2f} | {residual['top100_removed_usd']:.2f} | {residual['top200_removed_usd']:.2f} |",
            "",
            "## Half-Year Buckets",
            "",
            "| Bucket | Trades | WR % | Net | PF | Active days | T/active | Pos day % | 3+ day % |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in [item for item in bucket_rows if item["bucket_type"] == "half_year"]:
        lines.append(
            f"| {row['bucket']} | {row['trades']} | {row['win_rate_pct']:.2f} | {row['net_usd']:.2f} | {row['profit_factor']} | {row['active_days']} | {row['trades_per_active_day']:.2f} | {row['positive_day_pct']:.2f} | {row['three_plus_trade_day_pct']:.2f} |"
        )
    worst_rolling = min(rolling_rows, key=lambda row: row["net_usd"]) if rolling_rows else {}
    best_rolling = max(rolling_rows, key=lambda row: row["net_usd"]) if rolling_rows else {}
    lines.extend(
        [
            "",
            "## Rolling 250-Trade Windows",
            "",
            f"- Windows tested: `{len(rolling_rows)}`",
            f"- Negative windows: `{len(negative_rolling)}`",
            f"- Worst window: `{worst_rolling.get('start_time', '')}` to `{worst_rolling.get('end_time', '')}` / net `{worst_rolling.get('net_usd', 0.0)}` / PF `{worst_rolling.get('profit_factor')}`",
            f"- Best window: `{best_rolling.get('start_time', '')}` to `{best_rolling.get('end_time', '')}` / net `{best_rolling.get('net_usd', 0.0)}` / PF `{best_rolling.get('profit_factor')}`",
            "",
            "## Blocked Residual Trades",
            "",
            f"- Raw blocked trades before daily guard: `{len(blocked)}`",
            f"- Raw blocked net: `{round(sum(float(row['profit']) for row in blocked), 2)}`",
            f"- Blocked reasons: `{dict(Counter(row.get('residual_block_reason', '') for row in blocked))}`",
            "",
            "## Interpretation",
            "",
        ]
    )
    if negative_half_years:
        lines.append(f"- Weak half-year buckets require review: `{[row['bucket'] for row in negative_half_years]}`.")
    else:
        lines.append("- No half-year bucket is net negative.")
    if negative_rolling:
        lines.append("- At least one rolling 250-trade window is net negative, so the edge is not monotonic through time.")
    else:
        lines.append("- No rolling 250-trade window is net negative.")
    lines.extend(
        [
            "- The candidate passes the owner's frequency shape if it remains above 2 trades per active day and preferably around 3-5 trades per active day. Sparse two-trades-per-month systems are not eligible.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path}`",
            f"- Bucket CSV: `{csv_path}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    base_trades = enrich_base_trades()
    baseline_selected, _baseline_guard = apply_reliability_guard(base_trades)
    residual_selected, residual_guard, blocked = build_candidate(base_trades)

    baseline_summary = summarize_view("daily_reliability_baseline", baseline_selected)
    residual_summary = summarize_view("residual_reliability_candidate", residual_selected)
    residual_summary.update(residual_guard)

    bucket_rows: list[dict[str, Any]] = []
    for bucket in ("half_year", "quarter", "month", "direction", "session", "hour"):
        bucket_rows.extend(summarize_buckets(residual_selected, bucket))
    rolling_rows = rolling_trade_windows(residual_selected)
    decision = stress_decision(residual_summary, bucket_rows, rolling_rows)

    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"

    payload = {
        "status": decision,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "business_requirement": {
            "hard_min_trades_per_active_day": 2.0,
            "preferred_trades_per_active_day_min": 3.0,
            "preferred_trades_per_active_day_max": 5.0,
            "min_three_plus_trade_day_pct": 50.0,
            "sparse_strategy_policy": "Fail any strategy that wins by becoming too selective.",
        },
        "baseline": compact_summary(baseline_summary),
        "residual": compact_summary(residual_summary),
        "blocked": {
            "raw_trades": len(blocked),
            "raw_net_usd": round(sum(float(row["profit"]) for row in blocked), 2),
            "reasons": dict(Counter(row.get("residual_block_reason", "") for row in blocked)),
        },
        "buckets": bucket_rows,
        "rolling_250_trade_windows": rolling_rows,
    }
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    write_bucket_csv(bucket_rows, output_csv)
    output_md.write_text(
        render(baseline_summary, residual_summary, blocked, bucket_rows, rolling_rows, decision, output_json, output_csv),
        encoding="utf-8",
    )
    print(output_md)
    print(json.dumps({"status": decision, "residual": compact_summary(residual_summary)}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
