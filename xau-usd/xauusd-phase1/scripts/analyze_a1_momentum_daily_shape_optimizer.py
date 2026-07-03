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
from analyze_a1_momentum_daily_fit_repair import MEMBERS, block_key, candidate_blocks, summarize_pockets
from analyze_a1_momentum_daily_guard_search import apply_daily_guard
from analyze_a1_momentum_deep_portfolio_search import dedupe_trades
from analyze_a1_momentum_portfolio_combinations import summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
SPLIT_DATE = datetime(2024, 7, 1)


def top_removed_usd(trades: list[dict[str, Any]], count: int) -> float:
    profits = [float(row["profit"]) for row in trades]
    return round(sum(profits) - sum(sorted(profits, reverse=True)[:count]), 2)


def month_stats(trades: list[dict[str, Any]]) -> dict[str, Any]:
    by_month: dict[str, float] = defaultdict(float)
    for row in trades:
        by_month[row["entry_time"].strftime("%Y-%m")] += float(row["profit"])
    values = [round(value, 2) for value in by_month.values()]
    return {
        "positive_months": sum(1 for value in values if value > 0),
        "negative_months": sum(1 for value in values if value < 0),
        "worst_month_usd": min(values) if values else 0.0,
        "best_month_usd": max(values) if values else 0.0,
    }


def day_tail_stats(trades: list[dict[str, Any]]) -> dict[str, Any]:
    by_day: dict[str, float] = defaultdict(float)
    for row in trades:
        by_day[row["entry_date"]] += float(row["profit"])
    totals = sorted(round(value, 2) for value in by_day.values())
    if not totals:
        return {"p10_day_usd": 0.0, "p25_day_usd": 0.0, "positive_day_after_top10_removed_pct": 0.0}

    def percentile(pct: float) -> float:
        index = max(0, min(len(totals) - 1, round((len(totals) - 1) * pct)))
        return totals[index]

    top10_days = set(sorted(by_day, key=lambda day: by_day[day], reverse=True)[:10])
    rest = [value for day, value in by_day.items() if day not in top10_days]
    return {
        "p10_day_usd": percentile(0.10),
        "p25_day_usd": percentile(0.25),
        "positive_day_after_top10_removed_pct": round(
            100.0 * sum(1 for value in rest if value > 0) / len(rest), 2
        )
        if rest
        else 0.0,
    }


def base_raw_trades(pool_limit: int) -> tuple[list[dict[str, Any]], dict[str, int], list[dict[str, Any]]]:
    reports = sorted(
        path
        for path in REPORTS_DIR.glob("A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_*FOUR_YEAR*.json")
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
    priority = {str(item["name"]): index for index, item in enumerate(pool)}
    return raw, priority, pool


def filtered_deduped(
    raw_trades: list[dict[str, Any]],
    priority: dict[str, int],
    blocks: tuple[str, ...],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    blocked = set(blocks)
    filtered = [row for row in raw_trades if block_key(row) not in blocked]
    raw_dups = duplicate_like_stats(filtered)
    deduped = dedupe_trades(filtered, priority)
    deduped.sort(key=lambda row: (row["entry_time"], row["exit_time"], row["variant"]))
    return deduped, {
        "blocked_raw_trades": len(raw_trades) - len(filtered),
        "raw_duplicate_like_trade_pct": raw_dups["duplicate_like_trade_pct"],
        "dedupe_removed_trades": len(filtered) - len(deduped),
    }


def evaluate(
    raw_trades: list[dict[str, Any]],
    priority: dict[str, int],
    blocks: tuple[str, ...],
    *,
    profit_target_usd: float | None,
    loss_stop_usd: float | None,
    max_trades_per_day: int | None,
    max_losses_per_day: int | None,
) -> dict[str, Any]:
    base_trades, base_info = filtered_deduped(raw_trades, priority, blocks)
    return evaluate_guarded_base(
        base_trades,
        base_info,
        len(raw_trades),
        blocks,
        profit_target_usd=profit_target_usd,
        loss_stop_usd=loss_stop_usd,
        max_trades_per_day=max_trades_per_day,
        max_losses_per_day=max_losses_per_day,
    )


def evaluate_guarded_base(
    base_trades: list[dict[str, Any]],
    base_info: dict[str, Any],
    raw_trade_count: int,
    blocks: tuple[str, ...],
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
    name = "daily_shape_optimizer"
    summary = summarize(name, guarded)
    summary.update(daily_metrics(guarded))
    summary.update(month_stats(guarded))
    summary.update(day_tail_stats(guarded))
    older = window_summary(name + "_older", guarded, None, SPLIT_DATE)
    newer = window_summary(name + "_newer", guarded, SPLIT_DATE, None)
    summary.update(
        {
            "blocks": list(blocks),
            "block_count": len(blocks),
            "profit_target_usd": profit_target_usd,
            "loss_stop_usd": loss_stop_usd,
            "max_trades_per_day_guard": max_trades_per_day,
            "max_losses_per_day_guard": max_losses_per_day,
            "base_trades_after_blocks": len(base_trades),
            "retention_pct": round(100.0 * len(guarded) / len(base_trades), 2) if base_trades else 0.0,
            "overall_retention_pct": round(100.0 * len(guarded) / raw_trade_count, 2) if raw_trade_count else 0.0,
            "top10_removed_usd": top_removed_usd(guarded, 10),
            "top25_removed_usd": top_removed_usd(guarded, 25),
            "top100_removed_usd": top_removed_usd(guarded, 100),
            "older_trades": older.get("trades", 0),
            "older_net_usd": older.get("net_usd", 0.0),
            "older_profit_factor": older.get("profit_factor") or 0.0,
            "older_win_rate_pct": older.get("win_rate_pct", 0.0),
            "newer_trades": newer.get("trades", 0),
            "newer_net_usd": newer.get("net_usd", 0.0),
            "newer_profit_factor": newer.get("profit_factor") or 0.0,
            "newer_win_rate_pct": newer.get("win_rate_pct", 0.0),
        }
    )
    summary.update(base_info)
    summary.update(guard_hits)
    summary["decision"] = decision(summary)
    summary["score"] = round(score(summary), 2)
    return summary


def decision(row: dict[str, Any]) -> str:
    if int(row.get("trades") or 0) < 1900:
        return "FAIL_SAMPLE"
    if int(row.get("active_days") or 0) < 560:
        return "FAIL_ACTIVE_DAYS"
    if float(row.get("retention_pct") or 0.0) < 72.0:
        return "FAIL_GUARD_RETENTION"
    if float(row.get("trades_per_active_day") or 0.0) < 3.0:
        return "FAIL_TRADES_PER_ACTIVE_DAY"
    if float(row.get("three_plus_trade_day_pct") or 0.0) < 55.0:
        return "FAIL_THREE_PLUS_DAY_COVERAGE"
    if float(row.get("win_rate_pct") or 0.0) < 60.0:
        return "FAIL_WIN_RATE"
    if float(row.get("profit_factor") or 0.0) < 1.25:
        return "FAIL_PROFIT_FACTOR"
    if float(row.get("net_usd") or 0.0) < 1200.0:
        return "FAIL_NET"
    if float(row.get("positive_day_pct") or 0.0) < 55.0:
        return "REVIEW_DAY_RATE"
    if float(row.get("median_day_usd") or 0.0) <= 0.0:
        return "REVIEW_MEDIAN_DAY"
    if float(row.get("top100_removed_usd") or 0.0) <= 0.0:
        return "FAIL_TOP100_ROBUSTNESS"
    if float(row.get("older_net_usd") or 0.0) <= 0.0 or float(row.get("newer_net_usd") or 0.0) <= 0.0:
        return "FAIL_SPLIT_NET"
    if float(row.get("older_profit_factor") or 0.0) < 1.15 or float(row.get("newer_profit_factor") or 0.0) < 1.15:
        return "REVIEW_SPLIT_PF"
    if float(row.get("raw_duplicate_like_trade_pct") or 0.0) > 8.0:
        return "REVIEW_DUPLICATE_OVERLAP"
    return "DAILY_SHAPE_REVIEW_CANDIDATE"


def score(row: dict[str, Any]) -> float:
    pf = float(row.get("profit_factor") or 0.0)
    split_pf = min(float(row.get("older_profit_factor") or 0.0), float(row.get("newer_profit_factor") or 0.0))
    wr = float(row.get("win_rate_pct") or 0.0)
    pos_day = float(row.get("positive_day_pct") or 0.0)
    pos_day_no_top = float(row.get("positive_day_after_top10_removed_pct") or 0.0)
    three_plus = float(row.get("three_plus_trade_day_pct") or 0.0)
    tpa = float(row.get("trades_per_active_day") or 0.0)
    median_day = float(row.get("median_day_usd") or 0.0)
    p25_day = float(row.get("p25_day_usd") or 0.0)
    worst_day = min(float(row.get("worst_day_usd") or 0.0), 0.0)
    dd = max(float(row.get("max_closed_drawdown_usd") or 1.0), 1.0)
    net = float(row.get("net_usd") or 0.0)
    top100 = float(row.get("top100_removed_usd") or 0.0)
    retention = float(row.get("retention_pct") or 0.0)
    duplicate_pct = float(row.get("raw_duplicate_like_trade_pct") or 0.0)
    blocks = float(row.get("block_count") or 0.0)
    return (
        pf * 900.0
        + split_pf * 650.0
        + wr * 9.0
        + pos_day * 35.0
        + pos_day_no_top * 12.0
        + three_plus * 8.0
        + tpa * 160.0
        + median_day * 45.0
        + p25_day * 12.0
        + worst_day * 1.3
        + net / dd * 120.0
        + top100 / 40.0
        + retention * 3.0
        - duplicate_pct * 25.0
        - blocks * 35.0
    )


def compact(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "decision",
        "score",
        "blocks",
        "block_count",
        "profit_target_usd",
        "loss_stop_usd",
        "max_trades_per_day_guard",
        "max_losses_per_day_guard",
        "base_trades_after_blocks",
        "trades",
        "retention_pct",
        "overall_retention_pct",
        "win_rate_pct",
        "net_usd",
        "profit_factor",
        "active_days",
        "trades_per_active_day",
        "positive_day_pct",
        "positive_day_after_top10_removed_pct",
        "three_plus_trade_day_pct",
        "five_plus_trade_day_pct",
        "median_day_usd",
        "p25_day_usd",
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
        "raw_duplicate_like_trade_pct",
        "blocked_raw_trades",
        "dedupe_removed_trades",
        "profit_target_days",
        "loss_stop_days",
        "trade_cap_days",
        "loss_count_days",
    ]
    return {key: row.get(key) for key in keys}


def render_markdown(rows: list[dict[str, Any]], candidate_block_keys: list[str], output_json: Path) -> str:
    preferred = [row for row in rows if row["decision"] == "DAILY_SHAPE_REVIEW_CANDIDATE"]
    top = (preferred or rows)[:30]
    lines = [
        "# A1 XAU M5 Momentum Daily-Shape Optimizer",
        "",
        "Generated: 2026-07-02",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV analysis only. No MT5 runtime, charts, presets, orders, or positions were changed.",
        "",
        "## Purpose",
        "",
        "The owner rejected sparse strategies. This optimizer searches weak member-hour blocks plus shared daily lifecycle guards to improve day-by-day behavior while preserving the active intraday cadence.",
        "",
        "Unlike the sparse RR2 path, this search requires thousands of trades, at least 3 trades per active day, at least 55% 3+ trade active days, WR above 60%, PF above 1.25, and positive split-period evidence.",
        "",
        "## Candidate Block Universe",
        "",
    ]
    for key in candidate_block_keys:
        lines.append(f"- `{key}`")
    lines.extend(
        [
            "",
            "## Top Daily-Shape Results",
            "",
            "| Rank | Decision | Score | Blocks | Target | Stop | Max trades | Max losses | Trades | Ret% | WR | Net | PF | Active | T/active | Pos day | 3+ day | Median | P25 day | Worst day | Top100 | DD | Older PF | Newer PF |",
            "|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for index, row in enumerate(top, 1):
        blocks = "<br>".join(row.get("blocks") or []) or "None"
        lines.append(
            "| {rank} | `{decision}` | {score:.2f} | {blocks} | {target} | {stop} | {max_trades} | {max_losses} | {trades} | {ret:.2f}% | {wr:.2f}% | {net:.2f} | {pf} | {active} | {tpa:.2f} | {pos:.2f}% | {three:.2f}% | {median:.2f} | {p25:.2f} | {worst:.2f} | {top100:.2f} | {dd:.2f} | {older_pf:.2f} | {newer_pf:.2f} |".format(
                rank=index,
                decision=row.get("decision", ""),
                score=float(row.get("score") or 0.0),
                blocks=blocks,
                target=row.get("profit_target_usd"),
                stop=row.get("loss_stop_usd"),
                max_trades=row.get("max_trades_per_day_guard"),
                max_losses=row.get("max_losses_per_day_guard"),
                trades=row.get("trades"),
                ret=float(row.get("retention_pct") or 0.0),
                wr=float(row.get("win_rate_pct") or 0.0),
                net=float(row.get("net_usd") or 0.0),
                pf=row.get("profit_factor"),
                active=row.get("active_days"),
                tpa=float(row.get("trades_per_active_day") or 0.0),
                pos=float(row.get("positive_day_pct") or 0.0),
                three=float(row.get("three_plus_trade_day_pct") or 0.0),
                median=float(row.get("median_day_usd") or 0.0),
                p25=float(row.get("p25_day_usd") or 0.0),
                worst=float(row.get("worst_day_usd") or 0.0),
                top100=float(row.get("top100_removed_usd") or 0.0),
                dd=float(row.get("max_closed_drawdown_usd") or 0.0),
                older_pf=float(row.get("older_profit_factor") or 0.0),
                newer_pf=float(row.get("newer_profit_factor") or 0.0),
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This is a diagnostic optimizer, not runtime approval. A candidate only matters if its daily shape improves without starving trade count. Any selected result must be reviewed before attaching and then forward-tested unchanged.",
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
            item = compact(row)
            item["blocks"] = " + ".join(item["blocks"] or [])
            writer.writerow(item)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool-limit", type=int, default=35)
    parser.add_argument("--candidate-block-limit", type=int, default=14)
    parser.add_argument("--max-blocks", type=int, default=3)
    parser.add_argument(
        "--output-md",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_DAILY_SHAPE_OPTIMIZER_2026_07_02.md",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_DAILY_SHAPE_OPTIMIZER_2026_07_02.json",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_DAILY_SHAPE_OPTIMIZER_2026_07_02.csv",
    )
    args = parser.parse_args()

    raw, priority, _pool = base_raw_trades(args.pool_limit)
    pockets = summarize_pockets(raw)
    block_candidates = candidate_blocks(pockets)[: args.candidate_block_limit]
    block_sets: list[tuple[str, ...]] = [()]
    for size in range(1, args.max_blocks + 1):
        block_sets.extend(itertools.combinations(block_candidates, size))

    profit_targets = [None, 6.0, 8.0, 10.0, 12.0]
    loss_stops = [None, -20.0, -25.0, -30.0]
    max_trades = [None, 5, 6, 8, 10]
    max_losses = [None, 3, 4]

    rows: list[dict[str, Any]] = []
    for blocks in block_sets:
        base_trades, base_info = filtered_deduped(raw, priority, blocks)
        for target, stop, trade_cap, loss_cap in itertools.product(
            profit_targets, loss_stops, max_trades, max_losses
        ):
            rows.append(
                evaluate_guarded_base(
                    base_trades,
                    base_info,
                    len(raw),
                    blocks,
                    profit_target_usd=target,
                    loss_stop_usd=stop,
                    max_trades_per_day=trade_cap,
                    max_losses_per_day=loss_cap,
                )
            )

    decision_rank = {
        "DAILY_SHAPE_REVIEW_CANDIDATE": 0,
        "REVIEW_DAY_RATE": 1,
        "REVIEW_MEDIAN_DAY": 2,
        "REVIEW_SPLIT_PF": 3,
        "REVIEW_DUPLICATE_OVERLAP": 4,
    }
    rows.sort(key=lambda row: (decision_rank.get(row["decision"], 9), -float(row["score"] or 0.0)))

    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(
            {
                "status": "DAILY_SHAPE_OPTIMIZER_COMPLETE",
                "boundary": "offline_exact_mt5_trade_csv_analysis_only_no_runtime_change",
                "members": MEMBERS,
                "candidate_block_keys": block_candidates,
                "searched_block_sets": len(block_sets),
                "searched_permutations": len(rows),
                "top_results": [compact(row) for row in rows[:80]],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    args.output_md.write_text(render_markdown(rows, block_candidates, args.output_json), encoding="utf-8")
    write_csv(args.output_csv, rows)
    print(args.output_md)
    print(args.output_json)
    print(args.output_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
