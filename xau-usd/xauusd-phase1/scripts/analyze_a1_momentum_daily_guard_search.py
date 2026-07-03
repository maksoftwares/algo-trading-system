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

from analyze_a1_momentum_broad_portfolio_search import duplicate_like_stats, is_four_year_report, load_variants
from analyze_a1_momentum_daily_fit_portfolio_search import build_pool, daily_metrics, window_summary
from analyze_a1_momentum_daily_fit_repair import MEMBERS, block_key
from analyze_a1_momentum_deep_portfolio_search import dedupe_trades
from analyze_a1_momentum_portfolio_combinations import summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
SPLIT_DATE = datetime(2024, 7, 1)


BASES = {
    "daily_fit_baseline": (),
    "daily_fit_repair_no_v13_18_22": (
        "v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning@18",
        "v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning@22",
    ),
}


def load_base_trades(pool_limit: int, blocks: tuple[str, ...]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    reports = sorted(
        path for path in REPORTS_DIR.glob("A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_*FOUR_YEAR*.json")
        if is_four_year_report(path)
    )
    variants = load_variants(reports)
    pool = build_pool(variants, pool_limit)
    by_name = {str(item["name"]): item for item in pool}
    missing = [name for name in MEMBERS if name not in by_name]
    if missing:
        raise SystemExit(f"Missing members from pool: {missing}")

    raw: list[dict[str, Any]] = []
    for name in MEMBERS:
        raw.extend(by_name[name]["trades"])
    blocked = set(blocks)
    filtered = [row for row in raw if block_key(row) not in blocked]
    priority = {str(item["name"]): index for index, item in enumerate(pool)}
    deduped = dedupe_trades(filtered, priority)
    deduped.sort(key=lambda row: (row["entry_time"], row["exit_time"], row["variant"]))
    return deduped, priority


def apply_daily_guard(
    trades: list[dict[str, Any]],
    *,
    profit_target_usd: float | None,
    loss_stop_usd: float | None,
    max_trades_per_day: int | None,
    max_losses_per_day: int | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_day: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in trades:
        by_day[row["entry_date"]].append(row)

    kept: list[dict[str, Any]] = []
    skipped = 0
    hit_profit_target = 0
    hit_loss_stop = 0
    hit_trade_cap = 0
    hit_loss_count = 0

    for day, day_trades in sorted(by_day.items()):
        day_trades.sort(key=lambda row: (row["entry_time"], row["exit_time"], row["variant"]))
        day_pnl = 0.0
        day_losses = 0
        day_count = 0
        stopped_reason = ""

        for row in day_trades:
            if stopped_reason:
                skipped += 1
                continue
            if max_trades_per_day is not None and day_count >= max_trades_per_day:
                stopped_reason = "max_trades_per_day"
                hit_trade_cap += 1
                skipped += 1
                continue
            if max_losses_per_day is not None and day_losses >= max_losses_per_day:
                stopped_reason = "max_losses_per_day"
                hit_loss_count += 1
                skipped += 1
                continue
            if profit_target_usd is not None and day_pnl >= profit_target_usd:
                stopped_reason = "profit_target"
                hit_profit_target += 1
                skipped += 1
                continue
            if loss_stop_usd is not None and day_pnl <= loss_stop_usd:
                stopped_reason = "loss_stop"
                hit_loss_stop += 1
                skipped += 1
                continue

            copied = dict(row)
            copied["daily_guard_day"] = day
            kept.append(copied)
            profit = float(row["profit"])
            day_pnl += profit
            day_count += 1
            if profit < 0:
                day_losses += 1

            if profit_target_usd is not None and day_pnl >= profit_target_usd:
                stopped_reason = "profit_target"
                hit_profit_target += 1
            elif loss_stop_usd is not None and day_pnl <= loss_stop_usd:
                stopped_reason = "loss_stop"
                hit_loss_stop += 1
            elif max_losses_per_day is not None and day_losses >= max_losses_per_day:
                stopped_reason = "max_losses_per_day"
                hit_loss_count += 1
            elif max_trades_per_day is not None and day_count >= max_trades_per_day:
                stopped_reason = "max_trades_per_day"
                hit_trade_cap += 1

    return kept, {
        "skipped_trades": skipped,
        "profit_target_days": hit_profit_target,
        "loss_stop_days": hit_loss_stop,
        "trade_cap_days": hit_trade_cap,
        "loss_count_days": hit_loss_count,
    }


def top_removed(trades: list[dict[str, Any]], count: int) -> float:
    profits = [float(row["profit"]) for row in trades]
    return round(sum(profits) - sum(sorted(profits, reverse=True)[:count]), 2)


def month_stability(trades: list[dict[str, Any]]) -> dict[str, Any]:
    by_month: dict[str, float] = defaultdict(float)
    for row in trades:
        key = row["entry_time"].strftime("%Y-%m")
        by_month[key] += float(row["profit"])
    values = [round(value, 2) for value in by_month.values()]
    return {
        "positive_months": sum(1 for value in values if value > 0),
        "negative_months": sum(1 for value in values if value < 0),
        "worst_month_usd": min(values) if values else 0.0,
        "best_month_usd": max(values) if values else 0.0,
    }


def daily_ledger_stats(trades: list[dict[str, Any]]) -> dict[str, Any]:
    by_day: dict[str, float] = defaultdict(float)
    for row in trades:
        by_day[row["entry_date"]] += float(row["profit"])
    totals = [round(value, 2) for value in by_day.values()]
    if not totals:
        return {
            "positive_day_after_top5_removed_pct": 0.0,
            "positive_day_after_top10_removed_pct": 0.0,
            "p10_day_usd": 0.0,
            "p25_day_usd": 0.0,
        }
    sorted_totals = sorted(totals)
    def percentile(pct: float) -> float:
        index = max(0, min(len(sorted_totals) - 1, round((len(sorted_totals) - 1) * pct)))
        return round(sorted_totals[index], 2)

    top5_days = set(sorted(by_day, key=lambda key: by_day[key], reverse=True)[:5])
    top10_days = set(sorted(by_day, key=lambda key: by_day[key], reverse=True)[:10])
    without_top5 = [value for key, value in by_day.items() if key not in top5_days]
    without_top10 = [value for key, value in by_day.items() if key not in top10_days]
    return {
        "positive_day_after_top5_removed_pct": round(
            100.0 * sum(1 for value in without_top5 if value > 0) / len(without_top5), 2
        ) if without_top5 else 0.0,
        "positive_day_after_top10_removed_pct": round(
            100.0 * sum(1 for value in without_top10 if value > 0) / len(without_top10), 2
        ) if without_top10 else 0.0,
        "p10_day_usd": percentile(0.10),
        "p25_day_usd": percentile(0.25),
    }


def evaluate_guard(
    base_name: str,
    base_trades: list[dict[str, Any]],
    *,
    profit_target_usd: float | None,
    loss_stop_usd: float | None,
    max_trades_per_day: int | None,
    max_losses_per_day: int | None,
) -> dict[str, Any]:
    guarded, guard_hits = apply_daily_guard(
        base_trades,
        profit_target_usd=profit_target_usd,
        loss_stop_usd=loss_stop_usd,
        max_trades_per_day=max_trades_per_day,
        max_losses_per_day=max_losses_per_day,
    )
    summary = summarize(base_name, guarded)
    summary.update(daily_metrics(guarded))
    summary.update(month_stability(guarded))
    summary.update(daily_ledger_stats(guarded))
    older = window_summary(base_name + "_older", guarded, None, SPLIT_DATE)
    newer = window_summary(base_name + "_newer", guarded, SPLIT_DATE, None)
    summary.update(
        {
            "base": base_name,
            "profit_target_usd": profit_target_usd,
            "loss_stop_usd": loss_stop_usd,
            "max_trades_per_day_guard": max_trades_per_day,
            "max_losses_per_day_guard": max_losses_per_day,
            "kept_trades": len(guarded),
            "skipped_trades": guard_hits["skipped_trades"],
            "retention_pct": round(100.0 * len(guarded) / len(base_trades), 2) if base_trades else 0.0,
            "top10_removed_usd": top_removed(guarded, 10),
            "top25_removed_usd": top_removed(guarded, 25),
            "top100_removed_usd": top_removed(guarded, 100),
            "older_net_usd": older.get("net_usd", 0.0),
            "older_profit_factor": older.get("profit_factor") or 0.0,
            "newer_net_usd": newer.get("net_usd", 0.0),
            "newer_profit_factor": newer.get("profit_factor") or 0.0,
        }
    )
    summary.update(guard_hits)
    summary["decision"] = decision_for_guard(summary)
    summary["score"] = round(score_guard(summary), 2)
    return summary


def decision_for_guard(row: dict[str, Any]) -> str:
    if int(row.get("trades") or 0) < 1800:
        return "FAIL_SAMPLE"
    if float(row.get("retention_pct") or 0.0) < 72.0:
        return "FAIL_RETENTION"
    if int(row.get("active_days") or 0) < 540:
        return "FAIL_ACTIVE_DAY_COVERAGE"
    if float(row.get("trades_per_active_day") or 0.0) < 3.0:
        return "FAIL_DAILY_TRADE_FREQUENCY"
    if float(row.get("three_plus_trade_day_pct") or 0.0) < 55.0:
        return "FAIL_THREE_PLUS_DAY_COVERAGE"
    if float(row.get("win_rate_pct") or 0.0) < 60.0:
        return "FAIL_WIN_RATE"
    if float(row.get("positive_day_pct") or 0.0) < 55.0:
        return "REVIEW_POSITIVE_DAY_RATE"
    if float(row.get("profit_factor") or 0.0) < 1.25:
        return "FAIL_PROFIT_FACTOR"
    if float(row.get("net_usd") or 0.0) < 1200.0:
        return "FAIL_NET"
    if float(row.get("top100_removed_usd") or 0.0) <= 0.0:
        return "FAIL_TOP_WINNER_ROBUSTNESS"
    if float(row.get("older_profit_factor") or 0.0) < 1.15 or float(row.get("newer_profit_factor") or 0.0) < 1.15:
        return "REVIEW_SPLIT_CAVEAT"
    return "DAILY_GUARD_REVIEW_CANDIDATE"


def score_guard(row: dict[str, Any]) -> float:
    pf = float(row.get("profit_factor") or 0.0)
    wr = float(row.get("win_rate_pct") or 0.0)
    net = float(row.get("net_usd") or 0.0)
    dd = max(float(row.get("max_closed_drawdown_usd") or 1.0), 1.0)
    active = float(row.get("active_days") or 0.0)
    tpa = float(row.get("trades_per_active_day") or 0.0)
    pos_day = float(row.get("positive_day_pct") or 0.0)
    three_plus = float(row.get("three_plus_trade_day_pct") or 0.0)
    median_day = float(row.get("median_day_usd") or 0.0)
    p25 = float(row.get("p25_day_usd") or 0.0)
    worst_day = min(float(row.get("worst_day_usd") or 0.0), 0.0)
    retention = float(row.get("retention_pct") or 0.0)
    split_pf = min(float(row.get("older_profit_factor") or 0.0), float(row.get("newer_profit_factor") or 0.0))
    return (
        pf * 1000.0
        + split_pf * 650.0
        + wr * 8.0
        + pos_day * 36.0
        + three_plus * 12.0
        + active * 0.6
        + tpa * 140.0
        + net / dd * 130.0
        + median_day * 30.0
        + p25 * 8.0
        + worst_day * 1.2
        + retention * 4.0
    )


def compact(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "decision",
        "score",
        "base",
        "profit_target_usd",
        "loss_stop_usd",
        "max_trades_per_day_guard",
        "max_losses_per_day_guard",
        "trades",
        "retention_pct",
        "win_rate_pct",
        "net_usd",
        "profit_factor",
        "active_days",
        "trades_per_active_day",
        "positive_day_pct",
        "three_plus_trade_day_pct",
        "five_plus_trade_day_pct",
        "median_day_usd",
        "p25_day_usd",
        "worst_day_usd",
        "positive_day_after_top5_removed_pct",
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
        "skipped_trades",
        "profit_target_days",
        "loss_stop_days",
        "trade_cap_days",
        "loss_count_days",
    ]
    return {key: row.get(key) for key in keys}


def render_markdown(rows: list[dict[str, Any]], output_json: Path) -> str:
    lines = [
        "# A1 XAU M5 Momentum Daily Guard Search",
        "",
        "Generated: 2026-07-02",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV simulation only. No MT5 runtime, charts, presets, orders, or positions were changed.",
        "",
        "Purpose: test whether daily profit/loss/trade-count lifecycle rules improve the daily-income shape without starving the owner's required intraday frequency.",
        "",
        "## Top Guard Permutations",
        "",
        "| Rank | Decision | Base | Target | Stop | Max trades | Max losses | Trades | Retention | WR | Net | PF | Active | T/active | Positive day | 3+ day | Median day | Worst day | Older PF | Newer PF |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(rows[:30], 1):
        lines.append(
            f"| {index} | `{row.get('decision')}` | `{row.get('base')}` | {row.get('profit_target_usd')} | {row.get('loss_stop_usd')} | {row.get('max_trades_per_day_guard')} | {row.get('max_losses_per_day_guard')} | {row.get('trades')} | {row.get('retention_pct')}% | {row.get('win_rate_pct')}% | {row.get('net_usd')} | {row.get('profit_factor')} | {row.get('active_days')} | {row.get('trades_per_active_day')} | {row.get('positive_day_pct')}% | {row.get('three_plus_trade_day_pct')}% | {row.get('median_day_usd')} | {row.get('worst_day_usd')} | {row.get('older_profit_factor')} | {row.get('newer_profit_factor')} |"
        )
    best = rows[0] if rows else {}
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- A daily guard is useful only if it improves positive-day rate or drawdown while preserving at least 3 trades per active day and enough 3+ trade days.",
            "- Strong-looking guard settings that remove too many trades are not aligned with the owner's goal.",
            "- This search is not a runtime approval. It is a review packet for choosing whether the forward demo should include a daily lifecycle layer.",
            "",
            "## Current Best",
            "",
            f"- Decision: `{best.get('decision', 'MISSING')}`",
            f"- Base: `{best.get('base', '')}`",
            f"- Guard: target `{best.get('profit_target_usd')}`, stop `{best.get('loss_stop_usd')}`, max trades `{best.get('max_trades_per_day_guard')}`, max losses `{best.get('max_losses_per_day_guard')}`",
            f"- Result: `{best.get('trades')}` trades, WR `{best.get('win_rate_pct')}%`, PF `{best.get('profit_factor')}`, net `{best.get('net_usd')}`, positive days `{best.get('positive_day_pct')}%`, trades/active day `{best.get('trades_per_active_day')}`.",
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
            writer.writerow(compact(row))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool-limit", type=int, default=24)
    parser.add_argument(
        "--output-md",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_DAILY_GUARD_SEARCH_2026_07_02.md",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_DAILY_GUARD_SEARCH_2026_07_02.json",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_DAILY_GUARD_SEARCH_2026_07_02.csv",
    )
    args = parser.parse_args()

    profit_targets: list[float | None] = [None, 6.0, 8.0, 10.0, 12.0, 15.0, 20.0]
    loss_stops: list[float | None] = [None, -8.0, -10.0, -12.0, -15.0, -20.0, -25.0, -30.0]
    max_trades: list[int | None] = [None, 4, 5, 6, 8, 10, 12]
    max_losses: list[int | None] = [None, 2, 3, 4]

    rows: list[dict[str, Any]] = []
    for base_name, blocks in BASES.items():
        base_trades, _priority = load_base_trades(args.pool_limit, blocks)
        for profit_target, loss_stop, max_trade_count, max_loss_count in itertools.product(
            profit_targets, loss_stops, max_trades, max_losses
        ):
            rows.append(
                evaluate_guard(
                    base_name,
                    base_trades,
                    profit_target_usd=profit_target,
                    loss_stop_usd=loss_stop,
                    max_trades_per_day=max_trade_count,
                    max_losses_per_day=max_loss_count,
                )
            )

    preferred = {
        "DAILY_GUARD_REVIEW_CANDIDATE": 0,
        "REVIEW_POSITIVE_DAY_RATE": 1,
        "REVIEW_SPLIT_CAVEAT": 2,
    }
    rows.sort(key=lambda row: (preferred.get(row["decision"], 9), -float(row.get("score") or 0.0)))

    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "DAILY_GUARD_SEARCH_COMPLETE",
        "boundary": "offline_exact_mt5_trade_csv_daily_lifecycle_simulation_only_no_runtime_change",
        "bases": BASES,
        "grid": {
            "profit_targets_usd": profit_targets,
            "loss_stops_usd": loss_stops,
            "max_trades_per_day": max_trades,
            "max_losses_per_day": max_losses,
        },
        "top_results": [compact(row) for row in rows[:100]],
    }
    args.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    args.output_md.write_text(render_markdown(rows, args.output_json), encoding="utf-8")
    write_csv(args.output_csv, rows)
    print(args.output_md)
    print(args.output_json)
    print(args.output_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
