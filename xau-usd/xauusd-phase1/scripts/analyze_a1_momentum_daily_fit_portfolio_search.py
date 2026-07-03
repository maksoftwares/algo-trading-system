from __future__ import annotations

import argparse
import csv
import itertools
import json
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_momentum_broad_portfolio_search import (
    duplicate_like_stats,
    is_four_year_report,
    load_variants,
)
from analyze_a1_momentum_deep_portfolio_search import dedupe_trades
from analyze_a1_momentum_portfolio_combinations import summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
SPLIT_DATE = datetime(2024, 7, 1)


def daily_metrics(trades: list[dict[str, Any]]) -> dict[str, Any]:
    by_day: dict[str, list[float]] = defaultdict(list)
    for row in trades:
        by_day[row["entry_date"]].append(float(row["profit"]))
    day_totals = [round(sum(values), 2) for values in by_day.values()]
    day_counts = [len(values) for values in by_day.values()]
    active_days = len(day_totals)
    positive_days = sum(1 for value in day_totals if value > 0)
    negative_days = sum(1 for value in day_totals if value < 0)
    three_plus_days = sum(1 for count in day_counts if count >= 3)
    five_plus_days = sum(1 for count in day_counts if count >= 5)
    return {
        "active_days": active_days,
        "positive_days": positive_days,
        "negative_days": negative_days,
        "positive_day_pct": round(100.0 * positive_days / active_days, 2) if active_days else 0.0,
        "three_plus_trade_days": three_plus_days,
        "three_plus_trade_day_pct": round(100.0 * three_plus_days / active_days, 2) if active_days else 0.0,
        "five_plus_trade_days": five_plus_days,
        "five_plus_trade_day_pct": round(100.0 * five_plus_days / active_days, 2) if active_days else 0.0,
        "avg_day_usd": round(statistics.mean(day_totals), 2) if day_totals else 0.0,
        "median_day_usd": round(statistics.median(day_totals), 2) if day_totals else 0.0,
        "worst_day_usd": round(min(day_totals), 2) if day_totals else 0.0,
        "best_day_usd": round(max(day_totals), 2) if day_totals else 0.0,
    }


def window_summary(name: str, trades: list[dict[str, Any]], start: datetime | None, end: datetime | None) -> dict[str, Any]:
    selected = [
        row
        for row in trades
        if (start is None or row["entry_time"] >= start) and (end is None or row["entry_time"] < end)
    ]
    return summarize(name, selected) if selected else {
        "name": name,
        "trades": 0,
        "win_rate_pct": 0.0,
        "net_usd": 0.0,
        "profit_factor": 0.0,
        "active_days": 0,
        "trades_per_active_day": 0.0,
        "top25_removed_usd": 0.0,
        "max_closed_drawdown_usd": 0.0,
    }


def single_score(summary: dict[str, Any]) -> float:
    pf = float(summary.get("profit_factor") or 0.0)
    wr = float(summary.get("win_rate_pct") or 0.0)
    net = float(summary.get("net_usd") or 0.0)
    active = float(summary.get("active_days") or 0.0)
    tpa = float(summary.get("trades_per_active_day") or 0.0)
    dd = max(float(summary.get("max_closed_drawdown_usd") or 1.0), 1.0)
    neg_months = float(summary.get("negative_months") or 0.0)
    return pf * 800.0 + wr * 8.0 + active + tpa * 120.0 + net / dd * 80.0 - neg_months * 20.0


def portfolio_score(row: dict[str, Any]) -> float:
    pf = float(row.get("profit_factor") or 0.0)
    wr = float(row.get("win_rate_pct") or 0.0)
    net = float(row.get("net_usd") or 0.0)
    active = float(row.get("active_days") or 0.0)
    tpa = float(row.get("trades_per_active_day") or 0.0)
    positive_day_pct = float(row.get("positive_day_pct") or 0.0)
    three_plus_pct = float(row.get("three_plus_trade_day_pct") or 0.0)
    median_day = float(row.get("median_day_usd") or 0.0)
    dd = max(float(row.get("max_closed_drawdown_usd") or 1.0), 1.0)
    worst_day = min(float(row.get("worst_day_usd") or 0.0), 0.0)
    worst_month = min(float(row.get("worst_month_usd") or 0.0), 0.0)
    top25 = float(row.get("top25_removed_usd") or 0.0)
    top100 = float(row.get("top100_removed_usd") or 0.0)
    split_pf = min(float(row.get("older_profit_factor") or 0.0), float(row.get("newer_profit_factor") or 0.0))
    duplicate_pct = float(row.get("raw_duplicate_like_trade_pct") or 0.0)
    neg_months = float(row.get("negative_months") or 0.0)
    return (
        pf * 900.0
        + split_pf * 700.0
        + wr * 10.0
        + positive_day_pct * 18.0
        + three_plus_pct * 8.0
        + active * 0.8
        + tpa * 130.0
        + net / dd * 120.0
        + top25 / 20.0
        + top100 / 35.0
        + median_day * 16.0
        + worst_day * 1.5
        + worst_month
        - neg_months * 18.0
        - duplicate_pct * 20.0
    )


def decision_for(row: dict[str, Any]) -> str:
    if row["trades"] < 1800:
        return "FAIL_SAMPLE"
    if row["active_days"] < 550:
        return "FAIL_ACTIVE_DAY_COVERAGE"
    if row["trades_per_active_day"] < 3.0:
        return "FAIL_DAILY_TRADE_FREQUENCY"
    if row["three_plus_trade_day_pct"] < 55.0:
        return "FAIL_THREE_PLUS_DAY_COVERAGE"
    if row["win_rate_pct"] < 60.0:
        return "FAIL_TRADE_WIN_RATE"
    if row["positive_day_pct"] < 52.0:
        return "FAIL_POSITIVE_DAY_RATE"
    if row["profit_factor"] is None or row["profit_factor"] < 1.25:
        return "FAIL_PROFIT_FACTOR"
    if row["net_usd"] < 1200:
        return "FAIL_NET"
    if row["top25_removed_usd"] <= 0 or row["top100_removed_usd"] <= 0:
        return "FAIL_TOP_WINNER_ROBUSTNESS"
    if row["negative_months"] > 16:
        return "FAIL_MONTH_STABILITY"
    if row["worst_month_usd"] < -90:
        return "FAIL_WORST_MONTH"
    if row["max_closed_drawdown_usd"] > 180:
        return "FAIL_DRAWDOWN"
    if row["raw_duplicate_like_trade_pct"] > 12.0:
        return "FAIL_STACKING_OVERLAP"
    if row["older_net_usd"] <= 0 or row["newer_net_usd"] <= 0:
        return "FAIL_SPLIT_NET"
    if row["older_profit_factor"] < 1.15 or row["newer_profit_factor"] < 1.15:
        return "REVIEW_WITH_SPLIT_CAVEAT"
    return "DAILY_FIT_REVIEW_CANDIDATE"


def build_pool(variants: dict[str, dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    pool: list[dict[str, Any]] = []
    for item in variants.values():
        summary = item["summary"]
        if summary["trades"] < 100:
            continue
        if summary["net_usd"] <= 0:
            continue
        if summary["profit_factor"] is None or summary["profit_factor"] < 1.04:
            continue
        if summary["win_rate_pct"] < 50.0:
            continue
        candidate = dict(item)
        candidate["single_score"] = single_score(summary)
        pool.append(candidate)
    return sorted(pool, key=lambda row: row["single_score"], reverse=True)[:limit]


def evaluate_combo(combo: tuple[dict[str, Any], ...], priority: dict[str, int]) -> dict[str, Any]:
    raw_trades: list[dict[str, Any]] = []
    for item in combo:
        raw_trades.extend(item["trades"])
    raw_dups = duplicate_like_stats(raw_trades)
    deduped = dedupe_trades(raw_trades, priority)
    deduped = sorted(deduped, key=lambda row: (row["entry_time"], row["exit_time"], row["variant"]))
    name = " + ".join(str(item["name"]) for item in combo)
    summary = summarize(name, deduped)
    day = daily_metrics(deduped)
    older = window_summary(name + "_older", deduped, None, SPLIT_DATE)
    newer = window_summary(name + "_newer", deduped, SPLIT_DATE, None)
    summary.update(day)
    summary.update(
        {
            "members": [str(item["name"]) for item in combo],
            "raw_trades": len(raw_trades),
            "raw_duplicate_like_trade_pct": raw_dups["duplicate_like_trade_pct"],
            "dedupe_removed_trades": len(raw_trades) - len(deduped),
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
            "top100_removed_usd": round(
                sum(float(row["profit"]) for row in deduped)
                - sum(sorted((float(row["profit"]) for row in deduped), reverse=True)[:100]),
                2,
            ),
        }
    )
    summary["decision"] = decision_for(summary)
    summary["score"] = round(portfolio_score(summary), 2)
    return summary


def search(pool: list[dict[str, Any]], max_size: int) -> list[dict[str, Any]]:
    priority = {str(item["name"]): index for index, item in enumerate(pool)}
    rows: list[dict[str, Any]] = []
    for size in range(1, max_size + 1):
        for combo in itertools.combinations(pool, size):
            rows.append(evaluate_combo(combo, priority))
    preferred = {"DAILY_FIT_REVIEW_CANDIDATE": 0, "REVIEW_WITH_SPLIT_CAVEAT": 1}
    rows.sort(key=lambda row: (preferred.get(row["decision"], 9), -row["score"]))
    return rows


def compact(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "decision",
        "score",
        "name",
        "members",
        "raw_trades",
        "trades",
        "win_rate_pct",
        "net_usd",
        "profit_factor",
        "active_days",
        "trades_per_active_day",
        "positive_day_pct",
        "three_plus_trade_days",
        "three_plus_trade_day_pct",
        "five_plus_trade_days",
        "five_plus_trade_day_pct",
        "avg_day_usd",
        "median_day_usd",
        "worst_day_usd",
        "best_day_usd",
        "positive_months",
        "negative_months",
        "worst_month_usd",
        "top25_removed_usd",
        "top100_removed_usd",
        "max_closed_drawdown_usd",
        "raw_duplicate_like_trade_pct",
        "dedupe_removed_trades",
        "older_trades",
        "older_net_usd",
        "older_profit_factor",
        "older_win_rate_pct",
        "older_trades_per_active_day",
        "newer_trades",
        "newer_net_usd",
        "newer_profit_factor",
        "newer_win_rate_pct",
        "newer_trades_per_active_day",
    ]
    return {key: row.get(key) for key in keys}


def render_markdown(rows: list[dict[str, Any]], reports: list[Path], output_json: Path) -> str:
    review = [
        row for row in rows if row["decision"] in {"DAILY_FIT_REVIEW_CANDIDATE", "REVIEW_WITH_SPLIT_CAVEAT"}
    ]
    top = review[:30] if review else rows[:30]
    lines = [
        "# A1 XAU M5 Momentum Daily-Fit Portfolio Search",
        "",
        "Generated: 2026-07-02",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV analysis only. No MT5 runtime, charts, presets, orders, or positions were changed.",
        "",
        "## Purpose",
        "",
        "The owner rejected sparse strategies as primary lanes. This search scores portfolios by daily business fit: enough trades per active day, enough 3+ trade days, positive-day rate, PF/net, split-period health, and duplicate-stack control.",
        "",
        "The search still uses deterministic same-minute same-direction de-duplication before scoring, so the result is not allowed to win by clone stacking.",
        "",
        "## Daily-Fit Gates",
        "",
        "| Gate | Requirement |",
        "|---|---:|",
        "| Trades | >= 1800 |",
        "| Active days | >= 550 |",
        "| Trades / active day | >= 3.0 |",
        "| 3+ trade active days | >= 55% |",
        "| Trade win rate | >= 60% |",
        "| Positive active days | >= 52% |",
        "| Profit factor | >= 1.25 |",
        "| Net USD | >= 1200 |",
        "| Top 25 and top 100 winners removed | still positive |",
        "| Raw duplicate-like overlap | <= 12% |",
        "",
        "## Source reports",
        "",
    ]
    for report in reports:
        lines.append(f"- `{report}`")
    lines.extend(
        [
            "",
            "## Top Daily-Fit Candidates",
            "",
            "| Rank | Decision | Score | Members | Trades | WR % | Net | PF | Active | T/active | 3+ day % | Pos day % | Median day | Worst day | +M/-M | Top100 removed | DD | Dup % | Older net/PF | Newer net/PF |",
            "|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for index, row in enumerate(top, 1):
        lines.append(
            "| {rank} | `{decision}` | {score:.2f} | {members} | {trades} | {wr:.2f} | {net:.2f} | {pf} | {active} | {tpa:.2f} | {three:.2f} | {pos:.2f} | {median:.2f} | {worst_day:.2f} | {pm}/{nm} | {top100:.2f} | {dd:.2f} | {dup:.2f} | {older_net:.2f}/{older_pf:.2f} | {newer_net:.2f}/{newer_pf:.2f} |".format(
                rank=index,
                decision=row["decision"],
                score=row["score"],
                members="<br>".join(row["members"]),
                trades=row["trades"],
                wr=row["win_rate_pct"],
                net=row["net_usd"],
                pf=row["profit_factor"],
                active=row["active_days"],
                tpa=row["trades_per_active_day"],
                three=row["three_plus_trade_day_pct"],
                pos=row["positive_day_pct"],
                median=row["median_day_usd"],
                worst_day=row["worst_day_usd"],
                pm=row["positive_months"],
                nm=row["negative_months"],
                top100=row["top100_removed_usd"],
                dd=row["max_closed_drawdown_usd"],
                dup=row["raw_duplicate_like_trade_pct"],
                older_net=row["older_net_usd"],
                older_pf=row["older_profit_factor"],
                newer_net=row["newer_net_usd"],
                newer_pf=row["newer_profit_factor"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This is still a diagnostic search, not attachment approval. A daily-fit candidate is useful because it matches the desired operating shape better than sparse monthly lanes, but it still needs independent review and frozen forward demo testing.",
            "",
            "If the top candidate fails review, the next repair should target the exact failing gate rather than loosening everything for more trades.",
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
            compacted["members"] = " + ".join(compacted["members"] or [])
            writer.writerow(compacted)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="append", type=Path, default=[])
    parser.add_argument("--pool-limit", type=int, default=35)
    parser.add_argument("--max-size", type=int, default=4)
    parser.add_argument(
        "--output-md",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_SEARCH_2026_07_02.md",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_SEARCH_2026_07_02.json",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_SEARCH_2026_07_02.csv",
    )
    args = parser.parse_args()

    reports = args.report or sorted(REPORTS_DIR.glob("A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_*FOUR_YEAR*.json"))
    reports = [path for path in reports if path.exists() and is_four_year_report(path)]
    variants = load_variants(reports)
    pool = build_pool(variants, args.pool_limit)
    rows = search(pool, args.max_size)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(rows, reports, args.output_json), encoding="utf-8")
    args.output_json.write_text(
        json.dumps(
            {
                "status": "DAILY_FIT_PORTFOLIO_SEARCH_COMPLETE",
                "boundary": "offline_exact_mt5_trade_csv_analysis_only_no_runtime_change",
                "source_reports": [str(path) for path in reports],
                "pool_size": len(pool),
                "searched_portfolios": len(rows),
                "top_candidates": [compact(row) for row in rows[:50]],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    write_csv(args.output_csv, rows)
    print(args.output_md)
    print(args.output_json)
    print(args.output_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
