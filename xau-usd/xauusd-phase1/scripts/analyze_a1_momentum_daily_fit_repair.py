from __future__ import annotations

import argparse
import csv
import itertools
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from analyze_a1_momentum_broad_portfolio_search import is_four_year_report, load_variants
from analyze_a1_momentum_broad_portfolio_search import duplicate_like_stats
from analyze_a1_momentum_daily_fit_portfolio_search import (
    build_pool,
    daily_metrics,
    decision_for,
    portfolio_score,
    window_summary,
)
from analyze_a1_momentum_deep_portfolio_search import dedupe_trades
from analyze_a1_momentum_portfolio_combinations import summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
MEMBERS = [
    "freq_h1_h4_long_rr0p7_cost005_block_weak_hours_v1",
    "v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning",
]


def block_key(row: dict[str, Any]) -> str:
    return f"{row['variant']}@{int(row.get('entry_hour') or row['entry_time'].hour):02d}"


def top100_removed_usd(trades: list[dict[str, Any]]) -> float:
    profits = [float(row["profit"]) for row in trades]
    return round(sum(profits) - sum(sorted(profits, reverse=True)[:100]), 2)


def evaluate(raw_trades: list[dict[str, Any]], priority: dict[str, int], blocks: tuple[str, ...]) -> dict[str, Any]:
    blocked = set(blocks)
    filtered = [row for row in raw_trades if block_key(row) not in blocked]
    raw_dups = duplicate_like_stats(filtered)
    deduped = dedupe_trades(filtered, priority)
    deduped = sorted(deduped, key=lambda row: (row["entry_time"], row["exit_time"], row["variant"]))
    summary = summarize(" + ".join(MEMBERS), deduped)
    summary.update(daily_metrics(deduped))
    older = window_summary("older", deduped, None, __import__("datetime").datetime(2024, 7, 1))
    newer = window_summary("newer", deduped, __import__("datetime").datetime(2024, 7, 1), None)
    summary.update(
        {
            "blocks": list(blocks),
            "blocked_raw_trades": len(raw_trades) - len(filtered),
            "raw_trades": len(raw_trades),
            "raw_duplicate_like_trade_pct": raw_dups["duplicate_like_trade_pct"],
            "dedupe_removed_trades": len(filtered) - len(deduped),
            "trades": summary["trades"],
            "older_trades": older["trades"],
            "older_net_usd": older["net_usd"],
            "older_profit_factor": older["profit_factor"] or 0.0,
            "older_win_rate_pct": older["win_rate_pct"],
            "older_trades_per_active_day": older["trades_per_active_day"],
            "newer_trades": newer["trades"],
            "newer_net_usd": newer["net_usd"],
            "newer_profit_factor": newer["profit_factor"] or 0.0,
            "newer_win_rate_pct": newer["win_rate_pct"],
            "newer_trades_per_active_day": newer["trades_per_active_day"],
            "top100_removed_usd": top100_removed_usd(deduped),
        }
    )
    summary["decision"] = decision_for(summary)
    summary["score"] = round(portfolio_score(summary), 2)
    return summary


def summarize_pockets(raw_trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in raw_trades:
        grouped[block_key(row)].append(row)
    rows: list[dict[str, Any]] = []
    for key, trades in grouped.items():
        summary = summarize(key, trades)
        summary.update(daily_metrics(trades))
        rows.append(summary)
    rows.sort(key=lambda row: (float(row.get("net_usd") or 0.0), float(row.get("profit_factor") or 0.0)))
    return rows


def candidate_blocks(pockets: list[dict[str, Any]]) -> list[str]:
    blocks: list[str] = []
    for row in pockets:
        trades = int(row.get("trades") or 0)
        net = float(row.get("net_usd") or 0.0)
        pf = float(row.get("profit_factor") or 0.0)
        positive_day_pct = float(row.get("positive_day_pct") or 0.0)
        if trades < 20:
            continue
        if net < 0 or pf < 1.05 or positive_day_pct < 48.0:
            blocks.append(str(row["name"]))
    return blocks[:18]


def compact(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "decision",
        "score",
        "blocks",
        "blocked_raw_trades",
        "trades",
        "win_rate_pct",
        "net_usd",
        "profit_factor",
        "active_days",
        "trades_per_active_day",
        "positive_day_pct",
        "three_plus_trade_day_pct",
        "median_day_usd",
        "worst_day_usd",
        "positive_months",
        "negative_months",
        "worst_month_usd",
        "top25_removed_usd",
        "top100_removed_usd",
        "max_closed_drawdown_usd",
        "older_net_usd",
        "older_profit_factor",
        "newer_net_usd",
        "newer_profit_factor",
    ]
    return {key: row.get(key) for key in keys}


def render_markdown(baseline: dict[str, Any], pockets: list[dict[str, Any]], repairs: list[dict[str, Any]], output_json: Path) -> str:
    lines = [
        "# A1 XAU M5 Momentum Daily-Fit Repair Diagnostic",
        "",
        "Generated: 2026-07-02",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV analysis only. No MT5 runtime, charts, presets, orders, or positions were changed.",
        "",
        "## Baseline Daily-Fit Candidate",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Trades | {baseline.get('trades')} |",
        f"| WR | {baseline.get('win_rate_pct')}% |",
        f"| Net USD | {baseline.get('net_usd')} |",
        f"| PF | {baseline.get('profit_factor')} |",
        f"| Active days | {baseline.get('active_days')} |",
        f"| Trades / active day | {baseline.get('trades_per_active_day')} |",
        f"| Positive day pct | {baseline.get('positive_day_pct')}% |",
        f"| 3+ trade day pct | {baseline.get('three_plus_trade_day_pct')}% |",
        f"| Older net/PF | {baseline.get('older_net_usd')} / {baseline.get('older_profit_factor')} |",
        f"| Newer net/PF | {baseline.get('newer_net_usd')} / {baseline.get('newer_profit_factor')} |",
        "",
        "## Worst Member-Hour Pockets",
        "",
        "| Pocket | Trades | WR % | Net | PF | Positive day % | T/active |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in pockets[:18]:
        lines.append(
            f"| `{row.get('name')}` | {row.get('trades')} | {row.get('win_rate_pct')} | {row.get('net_usd')} | {row.get('profit_factor')} | {row.get('positive_day_pct')} | {row.get('trades_per_active_day')} |"
        )
    lines.extend(
        [
            "",
            "## Top Simple Repairs",
            "",
            "| Rank | Decision | Blocks | Blocked raw | Trades | WR % | Net | PF | Active | T/active | Pos day % | 3+ day % | Top100 removed | Older net/PF | Newer net/PF |",
            "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for index, row in enumerate(repairs[:20], 1):
        blocks = "<br>".join(row.get("blocks") or [])
        lines.append(
            f"| {index} | `{row.get('decision')}` | {blocks} | {row.get('blocked_raw_trades')} | {row.get('trades')} | {row.get('win_rate_pct')} | {row.get('net_usd')} | {row.get('profit_factor')} | {row.get('active_days')} | {row.get('trades_per_active_day')} | {row.get('positive_day_pct')} | {row.get('three_plus_trade_day_pct')} | {row.get('top100_removed_usd')} | {row.get('older_net_usd')}/{row.get('older_profit_factor')} | {row.get('newer_net_usd')}/{row.get('newer_profit_factor')} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This is a repair diagnostic, not promotion. A repair is useful only if it improves daily-fit metrics without killing active-day frequency. Single-block repairs are preferred unless a two-block repair has a large, explainable improvement.",
            "",
            f"Machine-readable output: `{output_json}`",
        ]
    )
    return "\n".join(lines) + "\n"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = list(compact(rows[0]).keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            compacted = compact(row)
            compacted["blocks"] = " + ".join(compacted["blocks"] or [])
            writer.writerow(compacted)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool-limit", type=int, default=24)
    parser.add_argument("--max-blocks", type=int, default=2)
    parser.add_argument(
        "--output-md",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_DAILY_FIT_REPAIR_DIAGNOSTIC_2026_07_02.md",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_DAILY_FIT_REPAIR_DIAGNOSTIC_2026_07_02.json",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_DAILY_FIT_REPAIR_DIAGNOSTIC_2026_07_02.csv",
    )
    args = parser.parse_args()

    reports = sorted(path for path in REPORTS_DIR.glob("A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_*FOUR_YEAR*.json") if is_four_year_report(path))
    variants = load_variants(reports)
    pool = build_pool(variants, args.pool_limit)
    by_name = {str(item["name"]): item for item in pool}
    missing = [name for name in MEMBERS if name not in by_name]
    if missing:
        raise SystemExit(f"Missing members from pool: {missing}")

    priority = {str(item["name"]): index for index, item in enumerate(pool)}
    raw_trades: list[dict[str, Any]] = []
    for name in MEMBERS:
        raw_trades.extend(by_name[name]["trades"])

    baseline = evaluate(raw_trades, priority, ())
    pockets = summarize_pockets(raw_trades)
    blocks = candidate_blocks(pockets)

    repairs: list[dict[str, Any]] = [baseline]
    for size in range(1, args.max_blocks + 1):
        for combo in itertools.combinations(blocks, size):
            repairs.append(evaluate(raw_trades, priority, tuple(combo)))
    repairs.sort(key=lambda row: (row["decision"] != "DAILY_FIT_REVIEW_CANDIDATE", -float(row.get("score") or 0.0)))

    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(
            {
                "status": "DAILY_FIT_REPAIR_DIAGNOSTIC_COMPLETE",
                "boundary": "offline_exact_mt5_trade_csv_analysis_only_no_runtime_change",
                "members": MEMBERS,
                "candidate_blocks": blocks,
                "baseline": compact(baseline),
                "worst_pockets": [compact(row) | {"name": row.get("name")} for row in pockets[:25]],
                "top_repairs": [compact(row) for row in repairs[:50]],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    args.output_md.write_text(render_markdown(baseline, pockets, repairs, args.output_json), encoding="utf-8")
    write_csv(args.output_csv, repairs)
    print(args.output_md)
    print(args.output_json)
    print(args.output_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
