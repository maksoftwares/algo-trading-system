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
from analyze_a1_momentum_daily_fit_portfolio_search import daily_metrics, window_summary
from analyze_a1_momentum_daily_guard_search import apply_daily_guard
from analyze_a1_momentum_deep_portfolio_search import dedupe_trades
from analyze_a1_momentum_portfolio_combinations import summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
SPLIT_DATE = datetime(2024, 7, 1)


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


def top_removed_usd(trades: list[dict[str, Any]], count: int) -> float:
    profits = [float(row["profit"]) for row in trades]
    return round(sum(profits) - sum(sorted(profits, reverse=True)[:count]), 2)


def day_tail_stats(trades: list[dict[str, Any]]) -> dict[str, Any]:
    by_day: dict[str, float] = defaultdict(float)
    for row in trades:
        by_day[row["entry_date"]] += float(row["profit"])
    totals = sorted(round(value, 2) for value in by_day.values())
    if not totals:
        return {
            "p10_day_usd": 0.0,
            "p25_day_usd": 0.0,
            "positive_day_after_top10_removed_pct": 0.0,
        }

    def percentile(pct: float) -> float:
        index = max(0, min(len(totals) - 1, round((len(totals) - 1) * pct)))
        return totals[index]

    top10_days = set(sorted(by_day, key=lambda key: by_day[key], reverse=True)[:10])
    rest = [value for key, value in by_day.items() if key not in top10_days]
    return {
        "p10_day_usd": percentile(0.10),
        "p25_day_usd": percentile(0.25),
        "positive_day_after_top10_removed_pct": round(
            100.0 * sum(1 for value in rest if value > 0) / len(rest), 2
        )
        if rest
        else 0.0,
    }


def pocket_key(row: dict[str, Any]) -> tuple[str, str, int]:
    return (str(row["variant"]), str(row.get("direction", "")), int(row.get("entry_hour") or 0))


def pocket_name(key: tuple[str, str, int]) -> str:
    return f"{key[0]}|{key[1]}|h{key[2]:02d}"


def summarize_pocket(name: str, trades: list[dict[str, Any]]) -> dict[str, Any]:
    summary = summarize(name, trades)
    summary.update(month_stats(trades))
    summary.update(day_tail_stats(trades))
    summary["top10_removed_usd"] = top_removed_usd(trades, 10)
    summary["top25_removed_usd"] = top_removed_usd(trades, 25)
    return summary


def pocket_decision(row: dict[str, Any]) -> str:
    if row["trades"] < 45:
        return "FAIL_SAMPLE"
    if row["win_rate_pct"] < 57.0:
        return "FAIL_WR"
    if row["profit_factor"] is None or row["profit_factor"] < 1.12:
        return "FAIL_PF"
    if row["net_usd"] <= 0:
        return "FAIL_NET"
    if row["top10_removed_usd"] <= -80:
        return "FAIL_TOP10_FRAGILE"
    return "POCKET_CANDIDATE"


def pocket_score(row: dict[str, Any]) -> float:
    pf = float(row.get("profit_factor") or 0.0)
    wr = float(row.get("win_rate_pct") or 0.0)
    net = float(row.get("net_usd") or 0.0)
    trades = float(row.get("trades") or 0.0)
    active = float(row.get("active_days") or 0.0)
    top10 = float(row.get("top10_removed_usd") or 0.0)
    worst_month = min(float(row.get("worst_month_usd") or 0.0), 0.0)
    return pf * 650.0 + wr * 8.0 + net * 0.22 + trades * 0.08 + active * 0.2 + top10 * 0.08 + worst_month * 0.7


def build_pockets(variants: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    source_reports: dict[str, str] = {}
    for item in variants.values():
        source_reports[str(item["name"])] = str(item["report"])
        for row in item["trades"]:
            grouped[pocket_key(row)].append(row)

    pockets: list[dict[str, Any]] = []
    for key, trades in grouped.items():
        name = pocket_name(key)
        summary = summarize_pocket(name, trades)
        summary.update(
            {
                "pocket": name,
                "variant": key[0],
                "direction": key[1],
                "entry_hour": key[2],
                "source_report": source_reports.get(key[0], ""),
                "decision": "",
                "score": 0.0,
                "trades_data": sorted(trades, key=lambda row: (row["entry_time"], row["exit_time"], row["variant"])),
            }
        )
        summary["decision"] = pocket_decision(summary)
        summary["score"] = round(pocket_score(summary), 2)
        pockets.append(summary)
    pockets.sort(key=lambda row: (row["decision"] != "POCKET_CANDIDATE", -row["score"]))
    return pockets


def portfolio_metrics(
    name: str,
    trades: list[dict[str, Any]],
    raw_trades_count: int,
    raw_duplicate_pct: float,
    dedupe_removed: int,
) -> dict[str, Any]:
    ordered = sorted(trades, key=lambda row: (row["entry_time"], row["exit_time"], row["variant"]))
    summary = summarize(name, ordered)
    summary.update(daily_metrics(ordered))
    summary.update(month_stats(ordered))
    summary.update(day_tail_stats(ordered))
    older = window_summary(name + "_older", ordered, None, SPLIT_DATE)
    newer = window_summary(name + "_newer", ordered, SPLIT_DATE, None)
    summary.update(
        {
            "raw_trades": raw_trades_count,
            "raw_duplicate_like_trade_pct": raw_duplicate_pct,
            "dedupe_removed_trades": dedupe_removed,
            "top10_removed_usd": top_removed_usd(ordered, 10),
            "top25_removed_usd": top_removed_usd(ordered, 25),
            "top100_removed_usd": top_removed_usd(ordered, 100),
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
    return summary


def portfolio_decision(row: dict[str, Any]) -> str:
    if int(row.get("trades") or 0) < 1700:
        return "FAIL_SAMPLE"
    if int(row.get("active_days") or 0) < 560:
        return "FAIL_ACTIVE_DAYS"
    if float(row.get("trades_per_active_day") or 0.0) < 3.0:
        return "FAIL_TRADES_PER_ACTIVE_DAY"
    if float(row.get("three_plus_trade_day_pct") or 0.0) < 55.0:
        return "FAIL_THREE_PLUS_DAY_COVERAGE"
    if float(row.get("win_rate_pct") or 0.0) < 60.0:
        return "FAIL_WIN_RATE"
    if float(row.get("profit_factor") or 0.0) < 1.25:
        return "FAIL_PROFIT_FACTOR"
    if float(row.get("net_usd") or 0.0) < 1100.0:
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
    if float(row.get("raw_duplicate_like_trade_pct") or 0.0) > 10.0:
        return "REVIEW_DUPLICATE_OVERLAP"
    return "POCKET_PORTFOLIO_REVIEW_CANDIDATE"


def portfolio_score(row: dict[str, Any]) -> float:
    pf = float(row.get("profit_factor") or 0.0)
    split_pf = min(float(row.get("older_profit_factor") or 0.0), float(row.get("newer_profit_factor") or 0.0))
    wr = float(row.get("win_rate_pct") or 0.0)
    pos_day = float(row.get("positive_day_pct") or 0.0)
    three_plus = float(row.get("three_plus_trade_day_pct") or 0.0)
    tpa = float(row.get("trades_per_active_day") or 0.0)
    median_day = float(row.get("median_day_usd") or 0.0)
    p25_day = float(row.get("p25_day_usd") or 0.0)
    net = float(row.get("net_usd") or 0.0)
    trades = float(row.get("trades") or 0.0)
    active = float(row.get("active_days") or 0.0)
    dd = max(float(row.get("max_closed_drawdown_usd") or 1.0), 1.0)
    top100 = float(row.get("top100_removed_usd") or 0.0)
    worst_day = min(float(row.get("worst_day_usd") or 0.0), 0.0)
    dup = float(row.get("raw_duplicate_like_trade_pct") or 0.0)
    pocket_count = float(row.get("pocket_count") or 0.0)
    return (
        pf * 930.0
        + split_pf * 680.0
        + wr * 9.0
        + pos_day * 36.0
        + three_plus * 10.0
        + min(trades, 2200.0) * 0.9
        + active * 0.55
        + tpa * 170.0
        + median_day * 45.0
        + p25_day * 12.0
        + net / dd * 135.0
        + top100 / 38.0
        + worst_day * 1.2
        - dup * 22.0
        - pocket_count * 10.0
    )


def evaluate_combo(combo: tuple[dict[str, Any], ...], priority: dict[str, int]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    raw_trades: list[dict[str, Any]] = []
    for pocket in combo:
        raw_trades.extend(pocket["trades_data"])
    raw_dups = duplicate_like_stats(raw_trades)
    deduped = dedupe_trades(raw_trades, priority)
    members = [str(pocket["pocket"]) for pocket in combo]
    summary = portfolio_metrics(
        " + ".join(members),
        deduped,
        len(raw_trades),
        raw_dups["duplicate_like_trade_pct"],
        len(raw_trades) - len(deduped),
    )
    summary.update(
        {
            "members": members,
            "pocket_count": len(combo),
            "source_variants": sorted({str(pocket["variant"]) for pocket in combo}),
            "hours": sorted({int(pocket["entry_hour"]) for pocket in combo}),
            "directions": sorted({str(pocket["direction"]) for pocket in combo}),
        }
    )
    summary["decision"] = portfolio_decision(summary)
    summary["score"] = round(portfolio_score(summary), 2)
    return summary, deduped


def beam_search(
    pockets: list[dict[str, Any]],
    *,
    max_size: int,
    beam_width: int,
) -> list[tuple[dict[str, Any], list[dict[str, Any]]]]:
    candidates = [pocket for pocket in pockets if pocket["decision"] == "POCKET_CANDIDATE"]
    priority: dict[str, int] = {}
    for index, pocket in enumerate(candidates):
        for row in pocket["trades_data"]:
            priority.setdefault(str(row.get("variant", "")), index)
    beams: list[tuple[tuple[int, ...], dict[str, Any], list[dict[str, Any]]]] = []
    results: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []

    for index, pocket in enumerate(candidates):
        summary, trades = evaluate_combo((pocket,), priority)
        beams.append(((index,), summary, trades))
        results.append((summary, trades))
    beams.sort(key=lambda item: item[1]["score"], reverse=True)
    beams = beams[:beam_width]

    for _size in range(2, max_size + 1):
        next_beams: list[tuple[tuple[int, ...], dict[str, Any], list[dict[str, Any]]]] = []
        seen: set[tuple[int, ...]] = set()
        for indexes, _summary, _trades in beams:
            last = indexes[-1]
            for next_index in range(last + 1, len(candidates)):
                combo_indexes = indexes + (next_index,)
                if combo_indexes in seen:
                    continue
                seen.add(combo_indexes)
                combo = tuple(candidates[i] for i in combo_indexes)
                summary, trades = evaluate_combo(combo, priority)
                next_beams.append((combo_indexes, summary, trades))
                results.append((summary, trades))
        next_beams.sort(key=lambda item: item[1]["score"], reverse=True)
        beams = next_beams[:beam_width]
        if not beams:
            break

    deduped_results: dict[str, tuple[dict[str, Any], list[dict[str, Any]]]] = {}
    for summary, trades in results:
        deduped_results[summary["name"]] = (summary, trades)
    return sorted(deduped_results.values(), key=lambda item: item[0]["score"], reverse=True)


def evaluate_guard(
    base: dict[str, Any],
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
    row = portfolio_metrics(
        base["name"],
        guarded,
        base["raw_trades"],
        base["raw_duplicate_like_trade_pct"],
        base["dedupe_removed_trades"],
    )
    row.update(
        {
            "members": base["members"],
            "pocket_count": base["pocket_count"],
            "source_variants": base["source_variants"],
            "hours": base["hours"],
            "directions": base["directions"],
            "profit_target_usd": profit_target_usd,
            "loss_stop_usd": loss_stop_usd,
            "max_trades_per_day_guard": max_trades_per_day,
            "max_losses_per_day_guard": max_losses_per_day,
            "retention_pct": round(100.0 * len(guarded) / len(base_trades), 2) if base_trades else 0.0,
        }
    )
    row.update(guard_hits)
    row["decision"] = portfolio_decision(row)
    row["score"] = round(portfolio_score(row), 2)
    return row


def guarded_search(
    combo_results: list[tuple[dict[str, Any], list[dict[str, Any]]]],
    *,
    base_limit: int,
) -> list[dict[str, Any]]:
    guard_grid = list(
        itertools.product(
            [None, 6.0, 8.0, 10.0, 12.0],
            [None, -20.0, -25.0, -30.0],
            [None, 5, 6, 8, 10],
            [None, 3, 4],
        )
    )
    rows: list[dict[str, Any]] = []
    preferred = {
        "POCKET_PORTFOLIO_REVIEW_CANDIDATE": 0,
        "REVIEW_DAY_RATE": 1,
        "REVIEW_MEDIAN_DAY": 2,
        "REVIEW_SPLIT_PF": 3,
        "REVIEW_DUPLICATE_OVERLAP": 4,
        "FAIL_TOP100_ROBUSTNESS": 5,
        "FAIL_PROFIT_FACTOR": 6,
        "FAIL_WIN_RATE": 7,
        "FAIL_TRADES_PER_ACTIVE_DAY": 8,
        "FAIL_SAMPLE": 9,
    }
    base_candidates = sorted(
        combo_results,
        key=lambda item: (
            preferred.get(item[0]["decision"], 99),
            -int(item[0].get("trades") or 0),
            -float(item[0].get("active_days") or 0.0),
            -float(item[0].get("score") or 0.0),
        ),
    )
    for base, trades in base_candidates[:base_limit]:
        for profit_target, loss_stop, max_trades, max_losses in guard_grid:
            rows.append(
                evaluate_guard(
                    base,
                    trades,
                    profit_target_usd=profit_target,
                    loss_stop_usd=loss_stop,
                    max_trades_per_day=max_trades,
                    max_losses_per_day=max_losses,
                )
            )
    preferred = {
        "POCKET_PORTFOLIO_REVIEW_CANDIDATE": 0,
        "REVIEW_DAY_RATE": 1,
        "REVIEW_MEDIAN_DAY": 2,
        "REVIEW_SPLIT_PF": 3,
        "REVIEW_DUPLICATE_OVERLAP": 4,
    }
    rows.sort(key=lambda row: (preferred.get(row["decision"], 9), -row["score"]))
    return rows


def compact_portfolio(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "decision",
        "score",
        "name",
        "members",
        "pocket_count",
        "source_variants",
        "hours",
        "directions",
        "profit_target_usd",
        "loss_stop_usd",
        "max_trades_per_day_guard",
        "max_losses_per_day_guard",
        "trades",
        "raw_trades",
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
        "positive_day_after_top10_removed_pct",
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
        "newer_trades",
        "newer_net_usd",
        "newer_profit_factor",
        "skipped_trades",
        "profit_target_days",
        "loss_stop_days",
        "trade_cap_days",
        "loss_count_days",
    ]
    return {key: row.get(key) for key in keys}


def compact_pocket(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "decision",
        "score",
        "pocket",
        "variant",
        "direction",
        "entry_hour",
        "trades",
        "win_rate_pct",
        "net_usd",
        "profit_factor",
        "active_days",
        "trades_per_active_day",
        "positive_months",
        "negative_months",
        "worst_month_usd",
        "top10_removed_usd",
        "top25_removed_usd",
        "source_report",
    ]
    return {key: row.get(key) for key in keys}


def write_csv(path: Path, rows: list[dict[str, Any]], compact_func) -> None:
    fieldnames = list(compact_func(rows[0]).keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            compacted = compact_func(row)
            for key in ("members", "source_variants", "hours", "directions"):
                if key in compacted and isinstance(compacted[key], list):
                    compacted[key] = " | ".join(str(value) for value in compacted[key])
            writer.writerow(compacted)


def render_markdown(
    *,
    rows: list[dict[str, Any]],
    pockets: list[dict[str, Any]],
    source_reports: list[Path],
    output_json: Path,
    output_csv: Path,
    pockets_csv: Path,
    baseline: dict[str, Any] | None,
) -> str:
    review = [
        row
        for row in rows
        if row["decision"]
        in {
            "POCKET_PORTFOLIO_REVIEW_CANDIDATE",
            "REVIEW_DAY_RATE",
            "REVIEW_MEDIAN_DAY",
            "REVIEW_SPLIT_PF",
            "REVIEW_DUPLICATE_OVERLAP",
        }
    ]
    top = review[:30] if review else rows[:30]
    pocket_candidates = [row for row in pockets if row["decision"] == "POCKET_CANDIDATE"][:25]
    lines = [
        "# A1 XAU M5 Momentum Pocket Portfolio Search",
        "",
        "Generated: 2026-07-02",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV analysis only. No MT5 runtime, charts, presets, orders, or positions were changed.",
        "",
        "## Purpose",
        "",
        "The owner clarified that sparse strategies do not match the project goal. This search treats intraday frequency as a hard business requirement: a candidate must deliver multiple trades on active days, not just attractive monthly PF from rare trades.",
        "",
        "Instead of only combining whole variants, it mines smaller pockets by `variant + direction + entry hour`, then combines the strongest pockets and tests daily guards. This is diagnostic and intentionally not deployment approval.",
        "",
        "## Hard Frequency Shape",
        "",
        "| Requirement | Gate |",
        "|---|---:|",
        "| Trades | >= 1700 |",
        "| Active days | >= 560 |",
        "| Trades / active day | >= 3.0 |",
        "| 3+ trade active days | >= 55% |",
        "| Trade win rate | >= 60% |",
        "| Profit factor | >= 1.25 |",
        "| Net USD | >= 1100 |",
        "| Top 100 winners removed | still positive |",
        "| Positive active day rate | review if <55% |",
        "",
    ]
    if baseline:
        lines.extend(
            [
                "## Current Daily-Shape Baseline",
                "",
                "| Candidate | Trades | WR % | Net | PF | Active | T/active | 3+ day % | Pos day % | Top100 removed | Decision |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
                "| Current best daily-shape guard | {trades} | {wr:.2f} | {net:.2f} | {pf:.2f} | {active} | {tpa:.2f} | {three:.2f} | {pos:.2f} | {top100:.2f} | `{decision}` |".format(
                    trades=baseline.get("trades", 0),
                    wr=float(baseline.get("win_rate_pct") or 0.0),
                    net=float(baseline.get("net_usd") or 0.0),
                    pf=float(baseline.get("profit_factor") or 0.0),
                    active=baseline.get("active_days", 0),
                    tpa=float(baseline.get("trades_per_active_day") or 0.0),
                    three=float(baseline.get("three_plus_trade_day_pct") or 0.0),
                    pos=float(baseline.get("positive_day_pct") or 0.0),
                    top100=float(baseline.get("top100_removed_usd") or 0.0),
                    decision=baseline.get("decision", ""),
                ),
                "",
            ]
        )
    lines.extend(
        [
            "## Top Pocket Portfolio Candidates",
            "",
            "| Rank | Decision | Score | Pockets | Trades | WR % | Net | PF | Active | T/active | 3+ day % | Pos day % | Median day | Worst day | Top100 removed | Older PF | Newer PF | Guard |",
            "|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for index, row in enumerate(top, 1):
        guard = "target={}; stop={}; max_trades={}; max_losses={}".format(
            row.get("profit_target_usd"),
            row.get("loss_stop_usd"),
            row.get("max_trades_per_day_guard"),
            row.get("max_losses_per_day_guard"),
        )
        lines.append(
            "| {rank} | `{decision}` | {score:.2f} | {pockets} | {trades} | {wr:.2f} | {net:.2f} | {pf:.2f} | {active} | {tpa:.2f} | {three:.2f} | {pos:.2f} | {median:.2f} | {worst:.2f} | {top100:.2f} | {older_pf:.2f} | {newer_pf:.2f} | {guard} |".format(
                rank=index,
                decision=row["decision"],
                score=row["score"],
                pockets=row["pocket_count"],
                trades=row["trades"],
                wr=row["win_rate_pct"],
                net=row["net_usd"],
                pf=float(row["profit_factor"] or 0.0),
                active=row["active_days"],
                tpa=row["trades_per_active_day"],
                three=row["three_plus_trade_day_pct"],
                pos=row["positive_day_pct"],
                median=row["median_day_usd"],
                worst=row["worst_day_usd"],
                top100=row["top100_removed_usd"],
                older_pf=row["older_profit_factor"],
                newer_pf=row["newer_profit_factor"],
                guard=guard,
            )
        )
    lines.extend(
        [
            "",
            "## Top Individual Pockets",
            "",
            "| Rank | Pocket | Trades | WR % | Net | PF | Active | T/active | +M/-M | Top10 removed |",
            "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for index, row in enumerate(pocket_candidates, 1):
        lines.append(
            "| {rank} | `{pocket}` | {trades} | {wr:.2f} | {net:.2f} | {pf:.2f} | {active} | {tpa:.2f} | {pm}/{nm} | {top10:.2f} |".format(
                rank=index,
                pocket=row["pocket"],
                trades=row["trades"],
                wr=row["win_rate_pct"],
                net=row["net_usd"],
                pf=float(row["profit_factor"] or 0.0),
                active=row["active_days"],
                tpa=row["trades_per_active_day"],
                pm=row["positive_months"],
                nm=row["negative_months"],
                top10=row["top10_removed_usd"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "If this report does not beat the current daily-shape guard, the honest conclusion is that the current two-lane daily guard remains the best available frequent-trade candidate, but it is still weak on positive-day rate. That means the next improvement should target day-level selectivity, not sparse high-PF variants.",
            "",
            "Any candidate here is diagnostic. The search surface is wide, so independent review and a frozen forward-test spec are required before touching demo runtime.",
            "",
            "## Source reports",
            "",
        ]
    )
    for report in source_reports:
        lines.append(f"- `{report}`")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: `{output_json}`",
            f"- Portfolio CSV: `{output_csv}`",
            f"- Pocket CSV: `{pockets_csv}`",
        ]
    )
    return "\n".join(lines) + "\n"


def load_daily_shape_baseline() -> dict[str, Any] | None:
    path = REPORTS_DIR / "A1_XAU_M5_MOMENTUM_DAILY_SHAPE_OPTIMIZER_2026_07_02.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    rows = payload.get("top_candidates") or payload.get("top_results") or []
    return rows[0] if rows else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool-limit", type=int, default=36)
    parser.add_argument("--max-size", type=int, default=8)
    parser.add_argument("--beam-width", type=int, default=350)
    parser.add_argument("--guard-base-limit", type=int, default=220)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_POCKET_PORTFOLIO_SEARCH_2026_07_02.json",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_POCKET_PORTFOLIO_SEARCH_2026_07_02.md",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_POCKET_PORTFOLIO_SEARCH_2026_07_02.csv",
    )
    parser.add_argument(
        "--pockets-csv",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_POCKET_PORTFOLIO_POCKETS_2026_07_02.csv",
    )
    args = parser.parse_args()

    source_reports = sorted(
        path
        for path in REPORTS_DIR.glob("A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_*FOUR_YEAR*.json")
        if is_four_year_report(path)
    )
    variants = load_variants(source_reports)
    pockets_all = build_pockets(variants)
    pockets = pockets_all[: args.pool_limit]
    combo_results = beam_search(pockets, max_size=args.max_size, beam_width=args.beam_width)
    rows = guarded_search(combo_results, base_limit=args.guard_base_limit)

    payload = {
        "status": "POCKET_PORTFOLIO_SEARCH_COMPLETE",
        "boundary": "offline_exact_mt5_trade_csv_analysis_only_no_runtime_change",
        "source_reports": [str(path) for path in source_reports],
        "variant_count": len(variants),
        "pocket_count": len(pockets_all),
        "pocket_pool_limit": args.pool_limit,
        "searched_combo_count": len(combo_results),
        "guarded_candidate_count": len(rows),
        "top_candidates": [compact_portfolio(row) for row in rows[:100]],
        "top_pockets": [compact_pocket(row) for row in pockets_all[:100]],
        "daily_shape_baseline": load_daily_shape_baseline(),
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    write_csv(args.output_csv, rows, compact_portfolio)
    write_csv(args.pockets_csv, pockets_all, compact_pocket)
    args.output_md.write_text(
        render_markdown(
            rows=rows,
            pockets=pockets_all,
            source_reports=source_reports,
            output_json=args.output_json,
            output_csv=args.output_csv,
            pockets_csv=args.pockets_csv,
            baseline=payload["daily_shape_baseline"],
        ),
        encoding="utf-8",
    )
    print(args.output_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
