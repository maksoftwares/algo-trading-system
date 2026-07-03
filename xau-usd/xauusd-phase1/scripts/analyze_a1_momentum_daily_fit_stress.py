from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_momentum_broad_portfolio_search import is_four_year_report, load_variants
from analyze_a1_momentum_daily_fit_portfolio_search import build_pool, daily_metrics, evaluate_combo
from analyze_a1_momentum_deep_portfolio_search import dedupe_trades
from analyze_a1_momentum_portfolio_combinations import max_drawdown, summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
DEFAULT_MEMBERS = [
    "freq_h1_h4_long_rr0p7_cost005_block_weak_hours_v1",
    "v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning",
]


def parse_dt(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def remove_top_winners(trades: list[dict[str, Any]], count: int) -> dict[str, Any]:
    profits = sorted((float(row["profit"]) for row in trades), reverse=True)
    base = sum(float(row["profit"]) for row in trades)
    return {
        "removed_count": count,
        "net_usd": round(base - sum(profits[:count]), 2),
    }


def bucket_for_half_year(dt: datetime) -> str:
    return f"{dt.year}-H1" if dt.month <= 6 else f"{dt.year}-H2"


def bucket_for_quarter(dt: datetime) -> str:
    quarter = ((dt.month - 1) // 3) + 1
    return f"{dt.year}-Q{quarter}"


def summarize_bucket(name: str, trades: list[dict[str, Any]]) -> dict[str, Any]:
    summary = summarize(name, trades) if trades else {
        "name": name,
        "trades": 0,
        "wins": 0,
        "losses": 0,
        "win_rate_pct": 0.0,
        "net_usd": 0.0,
        "gross_profit": 0.0,
        "gross_loss": 0.0,
        "profit_factor": 0.0,
        "active_days": 0,
        "trades_per_active_day": 0.0,
        "positive_months": 0,
        "negative_months": 0,
        "worst_month_usd": 0.0,
        "top25_removed_usd": 0.0,
        "max_closed_drawdown_usd": 0.0,
    }
    summary.update(daily_metrics(trades))
    return summary


def grouped_summaries(trades: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in trades:
        dt = row["entry_time"]
        if kind == "half_year":
            key = bucket_for_half_year(dt)
        elif kind == "quarter":
            key = bucket_for_quarter(dt)
        elif kind == "month":
            key = dt.strftime("%Y-%m")
        elif kind == "member":
            key = str(row.get("variant", ""))
        elif kind == "direction":
            key = str(row.get("direction", ""))
        elif kind == "hour":
            key = f"{int(row.get('entry_hour') or dt.hour):02d}"
        else:
            raise ValueError(kind)
        grouped[key].append(row)
    return [summarize_bucket(key, rows) for key, rows in sorted(grouped.items())]


def rolling_windows(trades: list[dict[str, Any]], size: int, step: int) -> list[dict[str, Any]]:
    ordered = sorted(trades, key=lambda row: (row["entry_time"], row["exit_time"], row["variant"]))
    rows: list[dict[str, Any]] = []
    for start in range(0, max(len(ordered) - size + 1, 0), step):
        chunk = ordered[start : start + size]
        summary = summarize_bucket(f"{start + 1}-{start + size}", chunk)
        summary.update(
            {
                "start_trade": start + 1,
                "end_trade": start + size,
                "start_date": chunk[0]["entry_time"].date().isoformat(),
                "end_date": chunk[-1]["entry_time"].date().isoformat(),
            }
        )
        rows.append(summary)
    return rows


def daily_ledger(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in trades:
        grouped[row["entry_date"]].append(row)
    rows: list[dict[str, Any]] = []
    for day, day_trades in sorted(grouped.items()):
        profits = [float(row["profit"]) for row in day_trades]
        wins = sum(1 for value in profits if value > 0)
        losses = sum(1 for value in profits if value < 0)
        by_member: dict[str, float] = defaultdict(float)
        for row in day_trades:
            by_member[str(row["variant"])] += float(row["profit"])
        rows.append(
            {
                "date": day,
                "trades": len(day_trades),
                "wins": wins,
                "losses": losses,
                "win_rate_pct": round(100.0 * wins / len(day_trades), 2) if day_trades else 0.0,
                "net_usd": round(sum(profits), 2),
                "members": "; ".join(f"{key}={value:.2f}" for key, value in sorted(by_member.items())),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def table(lines: list[str], rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> None:
    lines.append("| " + " | ".join(title for title, _ in columns) + " |")
    lines.append("|" + "|".join("---" for _ in columns) + "|")
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(key, "")) for _, key in columns) + " |")


def render_markdown(
    candidate: dict[str, Any],
    outliers: list[dict[str, Any]],
    half_year: list[dict[str, Any]],
    quarter: list[dict[str, Any]],
    rolling_250: list[dict[str, Any]],
    members: list[dict[str, Any]],
    directions: list[dict[str, Any]],
    hours: list[dict[str, Any]],
    output_json: Path,
    ledger_csv: Path,
) -> str:
    weakest_half = min(half_year, key=lambda row: float(row.get("profit_factor") or 0.0)) if half_year else {}
    weakest_quarter = min(quarter, key=lambda row: float(row.get("profit_factor") or 0.0)) if quarter else {}
    weakest_rolling = min(rolling_250, key=lambda row: float(row.get("net_usd") or 0.0)) if rolling_250 else {}
    lines = [
        "# A1 XAU M5 Momentum Daily-Fit Portfolio Stress",
        "",
        "Generated: 2026-07-02",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV analysis only. No MT5 runtime, charts, presets, orders, or positions were changed.",
        "",
        "## Candidate",
        "",
        "```text",
        "\n+\n".join(candidate.get("members", [])),
        "```",
        "",
        "## Headline",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Decision | `{candidate.get('decision')}` |",
        f"| Trades | {candidate.get('trades')} |",
        f"| Win rate | {candidate.get('win_rate_pct')}% |",
        f"| Net USD | {candidate.get('net_usd')} |",
        f"| Profit factor | {candidate.get('profit_factor')} |",
        f"| Active days | {candidate.get('active_days')} |",
        f"| Trades / active day | {candidate.get('trades_per_active_day')} |",
        f"| 3+ trade active days | {candidate.get('three_plus_trade_day_pct')}% |",
        f"| Positive active days | {candidate.get('positive_day_pct')}% |",
        f"| Median active-day PnL | {candidate.get('median_day_usd')} |",
        f"| Worst active day | {candidate.get('worst_day_usd')} |",
        f"| Max closed DD | {candidate.get('max_closed_drawdown_usd')} |",
        f"| Raw duplicate-like overlap | {candidate.get('raw_duplicate_like_trade_pct')}% |",
        f"| Older split net / PF | {candidate.get('older_net_usd')} / {candidate.get('older_profit_factor')} |",
        f"| Newer split net / PF | {candidate.get('newer_net_usd')} / {candidate.get('newer_profit_factor')} |",
        "",
        "## Outlier Removal",
        "",
    ]
    table(lines, outliers, [("Removed winners", "removed_count"), ("Net USD", "net_usd")])
    lines.extend(
        [
            "",
            "## Weakest Time Buckets",
            "",
            "| Bucket type | Bucket | Trades | WR % | Net USD | PF | Active days | T/active | Positive day % | DD |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            f"| Half-year | `{weakest_half.get('name', '')}` | {weakest_half.get('trades', '')} | {weakest_half.get('win_rate_pct', '')} | {weakest_half.get('net_usd', '')} | {weakest_half.get('profit_factor', '')} | {weakest_half.get('active_days', '')} | {weakest_half.get('trades_per_active_day', '')} | {weakest_half.get('positive_day_pct', '')} | {weakest_half.get('max_closed_drawdown_usd', '')} |",
            f"| Quarter | `{weakest_quarter.get('name', '')}` | {weakest_quarter.get('trades', '')} | {weakest_quarter.get('win_rate_pct', '')} | {weakest_quarter.get('net_usd', '')} | {weakest_quarter.get('profit_factor', '')} | {weakest_quarter.get('active_days', '')} | {weakest_quarter.get('trades_per_active_day', '')} | {weakest_quarter.get('positive_day_pct', '')} | {weakest_quarter.get('max_closed_drawdown_usd', '')} |",
            f"| Rolling 250 | `{weakest_rolling.get('name', '')}` | {weakest_rolling.get('trades', '')} | {weakest_rolling.get('win_rate_pct', '')} | {weakest_rolling.get('net_usd', '')} | {weakest_rolling.get('profit_factor', '')} | {weakest_rolling.get('active_days', '')} | {weakest_rolling.get('trades_per_active_day', '')} | {weakest_rolling.get('positive_day_pct', '')} | {weakest_rolling.get('max_closed_drawdown_usd', '')} |",
            "",
            "## Member Contribution",
            "",
        ]
    )
    table(lines, members, [("Member", "name"), ("Trades", "trades"), ("WR %", "win_rate_pct"), ("Net", "net_usd"), ("PF", "profit_factor"), ("Active", "active_days"), ("T/active", "trades_per_active_day")])
    lines.extend(["", "## Direction Contribution", ""])
    table(lines, directions, [("Direction", "name"), ("Trades", "trades"), ("WR %", "win_rate_pct"), ("Net", "net_usd"), ("PF", "profit_factor"), ("Active", "active_days"), ("T/active", "trades_per_active_day")])
    lines.extend(["", "## Hour Contribution", ""])
    table(lines, hours, [("Hour", "name"), ("Trades", "trades"), ("WR %", "win_rate_pct"), ("Net", "net_usd"), ("PF", "profit_factor"), ("Active", "active_days"), ("T/active", "trades_per_active_day")])
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This candidate passes the daily-fit screen, but it is not proof. The key caveat is still split-period asymmetry: the newer half is much stronger than the older half. Forward demo should therefore be frozen, low-lot, and judged by both trade-level and active-day-level metrics.",
            "",
            f"Daily ledger CSV: `{ledger_csv}`",
            "",
            f"Machine-readable output: `{output_json}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--member", action="append", default=DEFAULT_MEMBERS)
    parser.add_argument("--pool-limit", type=int, default=24)
    parser.add_argument(
        "--output-md",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_STRESS_2026_07_02.md",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_STRESS_2026_07_02.json",
    )
    parser.add_argument(
        "--output-ledger-csv",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_DAILY_LEDGER_2026_07_02.csv",
    )
    args = parser.parse_args()

    reports = sorted(path for path in REPORTS_DIR.glob("A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_*FOUR_YEAR*.json") if is_four_year_report(path))
    variants = load_variants(reports)
    pool = build_pool(variants, args.pool_limit)
    by_name = {str(item["name"]): item for item in pool}
    missing = [name for name in args.member if name not in by_name]
    if missing:
        raise SystemExit(f"Missing members from pool: {missing}")

    priority = {str(item["name"]): index for index, item in enumerate(pool)}
    combo = tuple(by_name[name] for name in args.member)
    candidate = evaluate_combo(combo, priority)

    raw_trades: list[dict[str, Any]] = []
    for item in combo:
        raw_trades.extend(item["trades"])
    deduped = dedupe_trades(raw_trades, priority)
    deduped = sorted(deduped, key=lambda row: (row["entry_time"], row["exit_time"], row["variant"]))

    outliers = [remove_top_winners(deduped, count) for count in [1, 3, 5, 10, 25, 50, 100, 150]]
    half_year = grouped_summaries(deduped, "half_year")
    quarter = grouped_summaries(deduped, "quarter")
    month = grouped_summaries(deduped, "month")
    rolling_250 = rolling_windows(deduped, 250, 50)
    rolling_500 = rolling_windows(deduped, 500, 100)
    members = grouped_summaries(deduped, "member")
    directions = grouped_summaries(deduped, "direction")
    hours = grouped_summaries(deduped, "hour")
    ledger = daily_ledger(deduped)

    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_ledger_csv, ledger)
    args.output_json.write_text(
        json.dumps(
            {
                "status": "DAILY_FIT_PORTFOLIO_STRESS_COMPLETE",
                "boundary": "offline_exact_mt5_trade_csv_analysis_only_no_runtime_change",
                "source_reports": [str(path) for path in reports],
                "candidate": candidate,
                "outlier_removal": outliers,
                "half_year": half_year,
                "quarter": quarter,
                "month": month,
                "rolling_250": rolling_250,
                "rolling_500": rolling_500,
                "members": members,
                "directions": directions,
                "hours": hours,
                "daily_ledger_csv": str(args.output_ledger_csv),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    args.output_md.write_text(
        render_markdown(candidate, outliers, half_year, quarter, rolling_250, members, directions, hours, args.output_json, args.output_ledger_csv),
        encoding="utf-8",
    )
    print(args.output_md)
    print(args.output_json)
    print(args.output_ledger_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
