from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
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


def parse_block(value: str) -> tuple[str, int]:
    if "@" not in value:
        raise argparse.ArgumentTypeError("block must use member@hour format")
    member, hour_text = value.rsplit("@", 1)
    try:
        hour = int(hour_text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("block hour must be an integer") from exc
    if hour < 0 or hour > 23:
        raise argparse.ArgumentTypeError("block hour must be between 0 and 23")
    if not member:
        raise argparse.ArgumentTypeError("block member cannot be blank")
    return member, hour


def apply_blocks(raw_by_member: dict[str, list[dict[str, Any]]], blocks: list[tuple[str, int]]) -> list[dict[str, Any]]:
    blocked = set(blocks)
    rows: list[dict[str, Any]] = []
    for member, trades in raw_by_member.items():
        for row in trades:
            if (member, int(row["entry_hour"])) in blocked:
                continue
            rows.append(row)
    return rows


def summarize_rows(name: str, trades: list[dict[str, Any]]) -> dict[str, Any]:
    if not trades:
        return {
            "bucket": name,
            "trades": 0,
            "win_rate_pct": 0.0,
            "net_usd": 0.0,
            "profit_factor": 0.0,
            "active_days": 0,
            "trades_per_active_day": 0.0,
            "positive_days": 0,
            "negative_days": 0,
            "max_closed_drawdown_usd": 0.0,
        }
    summary = summarize(name, trades)
    return {
        "bucket": name,
        "trades": summary["trades"],
        "win_rate_pct": summary["win_rate_pct"],
        "net_usd": summary["net_usd"],
        "profit_factor": summary["profit_factor"] or 0.0,
        "active_days": summary["active_days"],
        "trades_per_active_day": summary["trades_per_active_day"],
        "positive_days": summary["positive_days"],
        "negative_days": summary["negative_days"],
        "max_closed_drawdown_usd": summary["max_closed_drawdown_usd"],
    }


def half_year_bucket(row: dict[str, Any]) -> str:
    year, month, _day = row["entry_date"].split("-")
    half = "H1" if int(month) <= 6 else "H2"
    return f"{year}-{half}"


def quarter_bucket(row: dict[str, Any]) -> str:
    year, month, _day = row["entry_date"].split("-")
    quarter = ((int(month) - 1) // 3) + 1
    return f"{year}-Q{quarter}"


def group_by_bucket(trades: list[dict[str, Any]], bucket_fn) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in trades:
        grouped[bucket_fn(row)].append(row)
    return [summarize_rows(bucket, rows) for bucket, rows in sorted(grouped.items())]


def rolling_windows(trades: list[dict[str, Any]], window: int, step: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    ordered = sorted(trades, key=lambda row: (row["entry_time"], row["exit_time"], row["variant"]))
    for start in range(0, max(len(ordered) - window + 1, 0), step):
        sample = ordered[start : start + window]
        summary = summarize_rows(f"{start + 1}-{start + len(sample)}", sample)
        summary["start_trade"] = start + 1
        summary["end_trade"] = start + len(sample)
        summary["start_date"] = sample[0]["entry_date"]
        summary["end_date"] = sample[-1]["entry_date"]
        rows.append(summary)
    return rows


def losing_streaks(trades: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(trades, key=lambda row: (row["entry_time"], row["exit_time"], row["variant"]))
    current = 0
    longest = 0
    longest_start = ""
    longest_end = ""
    current_start = ""
    for row in ordered:
        if float(row["profit"]) < 0:
            if current == 0:
                current_start = row["entry_date"]
            current += 1
            if current > longest:
                longest = current
                longest_start = current_start
                longest_end = row["entry_date"]
        else:
            current = 0
            current_start = ""
    day_net: dict[str, float] = defaultdict(float)
    for row in ordered:
        day_net[row["entry_date"]] += float(row["profit"])
    current_days = 0
    longest_days = 0
    for day in sorted(day_net):
        if day_net[day] < 0:
            current_days += 1
            longest_days = max(longest_days, current_days)
        else:
            current_days = 0
    return {
        "longest_losing_trade_streak": longest,
        "longest_losing_trade_streak_start": longest_start,
        "longest_losing_trade_streak_end": longest_end,
        "longest_losing_day_streak": longest_days,
    }


def verdict(summary: dict[str, Any], half_years: list[dict[str, Any]], rolling_250: list[dict[str, Any]]) -> str:
    if summary["trades"] < 1500:
        return "REVISE_SAMPLE"
    if summary["trades_per_active_day"] < 3.0:
        return "REVISE_FREQUENCY"
    if summary["win_rate_pct"] < 58.0:
        return "REVISE_WIN_RATE"
    if summary["profit_factor"] < 1.25:
        return "REVISE_PF"
    if any(row["net_usd"] <= 0 for row in half_years if row["trades"] >= 100):
        return "REVISE_HALF_YEAR_INSTABILITY"
    if rolling_250 and min(float(row["profit_factor"] or 0.0) for row in rolling_250) < 0.95:
        return "REVIEW_WITH_ROLLING_PF_CAVEAT"
    return "REVIEW_FOR_FORWARD_TEST"


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# A1 XAU M5 Momentum Robust Portfolio Walk-Forward Stability",
        "",
        "Generated: 2026-07-02",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV analysis only. No MT5 runtime, charts, presets, orders, or positions were changed.",
        "",
        "## Candidate",
        "",
        "```text",
        "\n+\n".join(payload["members"]),
        "```",
        "",
        f"Applied blocks: `{', '.join(payload['blocks']) if payload['blocks'] else 'none'}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Trades | {summary['trades']} |",
        f"| Win rate | {summary['win_rate_pct']}% |",
        f"| Net USD | {summary['net_usd']} |",
        f"| Profit factor | {summary['profit_factor']} |",
        f"| Active days | {summary['active_days']} |",
        f"| Trades / active day | {summary['trades_per_active_day']} |",
        f"| Max closed DD USD | {summary['max_closed_drawdown_usd']} |",
        f"| Longest losing trade streak | {payload['streaks']['longest_losing_trade_streak']} |",
        f"| Longest losing day streak | {payload['streaks']['longest_losing_day_streak']} |",
        f"| Verdict | `{payload['verdict']}` |",
        "",
        "## Half-Year Walk-Forward Buckets",
        "",
        "| Bucket | Trades | WR % | Net USD | PF | Active days | T/active | DD |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["half_year"]:
        lines.append(
            f"| `{row['bucket']}` | {row['trades']} | {row['win_rate_pct']} | {row['net_usd']} | {row['profit_factor']} | {row['active_days']} | {row['trades_per_active_day']} | {row['max_closed_drawdown_usd']} |"
        )
    lines.extend(
        [
            "",
            "## Quarter Buckets",
            "",
            "| Bucket | Trades | WR % | Net USD | PF | Active days | T/active | DD |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in payload["quarter"]:
        lines.append(
            f"| `{row['bucket']}` | {row['trades']} | {row['win_rate_pct']} | {row['net_usd']} | {row['profit_factor']} | {row['active_days']} | {row['trades_per_active_day']} | {row['max_closed_drawdown_usd']} |"
        )
    lines.extend(
        [
            "",
            "## Rolling 250-Trade Windows",
            "",
            "| Window | Dates | WR % | Net USD | PF | Active days | T/active | DD |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in payload["rolling_250"]:
        lines.append(
            f"| `{row['start_trade']}-{row['end_trade']}` | {row['start_date']} -> {row['end_date']} | {row['win_rate_pct']} | {row['net_usd']} | {row['profit_factor']} | {row['active_days']} | {row['trades_per_active_day']} | {row['max_closed_drawdown_usd']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This is a stability report, not runtime approval. It checks whether the current robust candidate keeps the owner's required shape across time: many trades, active days, win rate above 50%, and positive net/PF. Any weak rolling or half-year bucket should be carried into reviewer discussion before demo attachment.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-md", type=Path, default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_WALKFORWARD_2026_07_02.md")
    parser.add_argument("--output-json", type=Path, default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_WALKFORWARD_2026_07_02.json")
    parser.add_argument("--output-half-year-csv", type=Path, default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_WALKFORWARD_HALF_YEAR_2026_07_02.csv")
    parser.add_argument("--output-rolling-csv", type=Path, default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_WALKFORWARD_ROLLING_2026_07_02.csv")
    parser.add_argument("--member", action="append", default=[])
    parser.add_argument("--block", action="append", type=parse_block, default=[])
    args = parser.parse_args()

    members = args.member or ROBUST_MEMBERS
    reports = sorted(path for path in REPORTS_DIR.glob("A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_*.json") if is_four_year_report(path))
    variants = load_variants(reports)
    missing = [name for name in members if name not in variants]
    if missing:
        raise SystemExit(f"Missing selected variants: {', '.join(missing)}")
    raw_by_member = {name: variants[name]["trades"] for name in members}
    priority = {name: index for index, name in enumerate(members)}
    raw = apply_blocks(raw_by_member, args.block)
    deduped = dedupe_trades(raw, priority)
    summary = summarize_rows("robust_portfolio_selected", deduped)
    half_year = group_by_bucket(deduped, half_year_bucket)
    quarter = group_by_bucket(deduped, quarter_bucket)
    rolling_250 = rolling_windows(deduped, 250, 50)
    rolling_500 = rolling_windows(deduped, 500, 100)
    payload = {
        "status": "ROBUST_PORTFOLIO_WALKFORWARD_COMPLETE",
        "boundary": "offline_exact_mt5_trade_csv_analysis_only_no_runtime_change",
        "members": members,
        "blocks": [f"{member}@{hour:02d}" for member, hour in args.block],
        "summary": summary,
        "half_year": half_year,
        "quarter": quarter,
        "rolling_250": rolling_250,
        "rolling_500": rolling_500,
        "streaks": losing_streaks(deduped),
        "verdict": verdict(summary, half_year, rolling_250),
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.output_md.write_text(render_markdown(payload), encoding="utf-8")
    write_csv(args.output_half_year_csv, half_year)
    write_csv(args.output_rolling_csv, rolling_250)
    print(args.output_md)
    print(args.output_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
