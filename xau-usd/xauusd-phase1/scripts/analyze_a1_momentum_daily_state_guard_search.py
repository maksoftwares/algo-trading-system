from __future__ import annotations

import argparse
import csv
import itertools
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from analyze_a1_momentum_daily_fit_portfolio_search import daily_metrics, window_summary
from analyze_a1_momentum_daily_guard_search import load_base_trades
from analyze_a1_momentum_portfolio_combinations import summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
SPLIT_DATE = datetime(2024, 7, 1)

REPAIRED_BLOCKS = (
    "v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning@18",
    "v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning@22",
)


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
    without_top10 = [value for day, value in by_day.items() if day not in top10_days]
    return {
        "p10_day_usd": percentile(0.10),
        "p25_day_usd": percentile(0.25),
        "positive_day_after_top10_removed_pct": round(
            100.0 * sum(1 for value in without_top10 if value > 0) / len(without_top10), 2
        )
        if without_top10
        else 0.0,
    }


def apply_state_guard(
    trades: list[dict[str, Any]],
    *,
    state_rule: str,
    profit_target_usd: float | None,
    loss_stop_usd: float | None,
    max_trades_per_day: int | None,
    max_losses_per_day: int | None,
    cooldown_after_loss_minutes: int,
    early_trade_count: int,
    early_pnl_threshold: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_day: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in trades:
        by_day[row["entry_date"]].append(row)

    kept: list[dict[str, Any]] = []
    stats = {
        "guard_model": "event_time_causal_v2",
        "skipped_trades": 0,
        "profit_target_days": 0,
        "loss_stop_days": 0,
        "trade_cap_days": 0,
        "loss_count_days": 0,
        "state_stop_days": 0,
        "cooldown_skipped_trades": 0,
        "closed_trades_processed": 0,
    }

    for day, day_trades in sorted(by_day.items()):
        ordered = sorted(day_trades, key=lambda row: (row["entry_time"], row["exit_time"], row["variant"]))
        day_pnl = 0.0
        day_losses = 0
        opened_count = 0
        closed_count = 0
        first_trade_profit: float | None = None
        closed_profits: list[float] = []
        consecutive_losses = 0
        stopped_reason = ""
        cooldown_until: datetime | None = None
        pending_exits: list[dict[str, Any]] = []

        def process_exits(up_to: datetime) -> None:
            nonlocal day_pnl
            nonlocal day_losses
            nonlocal closed_count
            nonlocal first_trade_profit
            nonlocal consecutive_losses
            nonlocal stopped_reason
            nonlocal cooldown_until

            pending_exits.sort(key=lambda pending: (pending["exit_time"], pending["entry_time"], pending["variant"]))
            while pending_exits and pending_exits[0]["exit_time"] <= up_to:
                closed = pending_exits.pop(0)
                profit = float(closed["profit"])
                day_pnl += profit
                closed_count += 1
                closed_profits.append(profit)
                stats["closed_trades_processed"] += 1
                if first_trade_profit is None:
                    first_trade_profit = profit
                if profit < 0:
                    day_losses += 1
                    consecutive_losses += 1
                    if cooldown_after_loss_minutes > 0:
                        cooldown_until = closed["exit_time"] + timedelta(minutes=cooldown_after_loss_minutes)
                else:
                    consecutive_losses = 0

                if stopped_reason:
                    continue
                if state_rule == "first_trade_loss_stop" and closed_count == 1 and profit < 0:
                    stopped_reason = "first_trade_loss_stop"
                    stats["state_stop_days"] += 1
                elif state_rule == "first_two_net_negative_stop" and closed_count == 2 and sum(closed_profits[:2]) <= early_pnl_threshold:
                    stopped_reason = "first_two_net_negative_stop"
                    stats["state_stop_days"] += 1
                elif state_rule == "first_three_net_negative_stop" and closed_count == 3 and sum(closed_profits[:3]) <= early_pnl_threshold:
                    stopped_reason = "first_three_net_negative_stop"
                    stats["state_stop_days"] += 1
                elif state_rule == "two_consecutive_losses_stop" and consecutive_losses >= 2:
                    stopped_reason = "two_consecutive_losses_stop"
                    stats["state_stop_days"] += 1
                elif state_rule == "early_window_net_negative_stop" and closed_count >= early_trade_count and day_pnl <= early_pnl_threshold:
                    stopped_reason = "early_window_net_negative_stop"
                    stats["state_stop_days"] += 1

                if not stopped_reason:
                    if profit_target_usd is not None and day_pnl >= profit_target_usd:
                        stopped_reason = "profit_target"
                        stats["profit_target_days"] += 1
                    elif loss_stop_usd is not None and day_pnl <= loss_stop_usd:
                        stopped_reason = "loss_stop"
                        stats["loss_stop_days"] += 1
                    elif max_losses_per_day is not None and day_losses >= max_losses_per_day:
                        stopped_reason = "max_losses_per_day"
                        stats["loss_count_days"] += 1

        for row in ordered:
            process_exits(row["entry_time"])
            if stopped_reason:
                stats["skipped_trades"] += 1
                continue
            if cooldown_until is not None and row["entry_time"] < cooldown_until:
                stats["skipped_trades"] += 1
                stats["cooldown_skipped_trades"] += 1
                continue
            if max_trades_per_day is not None and opened_count >= max_trades_per_day:
                stopped_reason = "max_trades_per_day"
                stats["trade_cap_days"] += 1
                stats["skipped_trades"] += 1
                continue
            if max_losses_per_day is not None and day_losses >= max_losses_per_day:
                stopped_reason = "max_losses_per_day"
                stats["loss_count_days"] += 1
                stats["skipped_trades"] += 1
                continue
            if profit_target_usd is not None and day_pnl >= profit_target_usd:
                stopped_reason = "profit_target"
                stats["profit_target_days"] += 1
                stats["skipped_trades"] += 1
                continue
            if loss_stop_usd is not None and day_pnl <= loss_stop_usd:
                stopped_reason = "loss_stop"
                stats["loss_stop_days"] += 1
                stats["skipped_trades"] += 1
                continue

            copied = dict(row)
            copied["daily_state_rule"] = state_rule
            kept.append(copied)
            opened_count += 1
            pending_exits.append(row)
            if max_trades_per_day is not None and opened_count >= max_trades_per_day:
                stopped_reason = "max_trades_per_day"
                stats["trade_cap_days"] += 1

        process_exits(datetime.max)

    return kept, stats


def evaluate(
    name: str,
    base_trades: list[dict[str, Any]],
    *,
    state_rule: str,
    profit_target_usd: float | None,
    loss_stop_usd: float | None,
    max_trades_per_day: int | None,
    max_losses_per_day: int | None,
    cooldown_after_loss_minutes: int,
    early_trade_count: int,
    early_pnl_threshold: float,
) -> dict[str, Any]:
    guarded, guard_stats = apply_state_guard(
        base_trades,
        state_rule=state_rule,
        profit_target_usd=profit_target_usd,
        loss_stop_usd=loss_stop_usd,
        max_trades_per_day=max_trades_per_day,
        max_losses_per_day=max_losses_per_day,
        cooldown_after_loss_minutes=cooldown_after_loss_minutes,
        early_trade_count=early_trade_count,
        early_pnl_threshold=early_pnl_threshold,
    )
    summary = summarize(name, guarded)
    summary.update(daily_metrics(guarded))
    summary.update(month_stats(guarded))
    summary.update(day_tail_stats(guarded))
    older = window_summary(name + "_older", guarded, None, SPLIT_DATE)
    newer = window_summary(name + "_newer", guarded, SPLIT_DATE, None)
    summary.update(
        {
            "state_rule": state_rule,
            "profit_target_usd": profit_target_usd,
            "loss_stop_usd": loss_stop_usd,
            "max_trades_per_day_guard": max_trades_per_day,
            "max_losses_per_day_guard": max_losses_per_day,
            "cooldown_after_loss_minutes": cooldown_after_loss_minutes,
            "early_trade_count": early_trade_count,
            "early_pnl_threshold": early_pnl_threshold,
            "base_trades": len(base_trades),
            "retention_pct": round(100.0 * len(guarded) / len(base_trades), 2) if base_trades else 0.0,
            "top10_removed_usd": top_removed_usd(guarded, 10),
            "top25_removed_usd": top_removed_usd(guarded, 25),
            "top100_removed_usd": top_removed_usd(guarded, 100),
            "older_trades": older.get("trades", 0),
            "older_net_usd": older.get("net_usd", 0.0),
            "older_profit_factor": older.get("profit_factor") or 0.0,
            "newer_trades": newer.get("trades", 0),
            "newer_net_usd": newer.get("net_usd", 0.0),
            "newer_profit_factor": newer.get("profit_factor") or 0.0,
        }
    )
    summary.update(guard_stats)
    summary["decision"] = decision(summary)
    summary["score"] = round(score(summary), 2)
    return summary


def decision(row: dict[str, Any]) -> str:
    if int(row.get("trades") or 0) < 1800:
        return "FAIL_SAMPLE"
    if float(row.get("retention_pct") or 0.0) < 70.0:
        return "FAIL_RETENTION"
    if int(row.get("active_days") or 0) < 540:
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
    if float(row.get("positive_day_pct") or 0.0) < 56.0:
        return "REVIEW_DAY_RATE"
    if float(row.get("median_day_usd") or 0.0) <= 0.0:
        return "REVIEW_MEDIAN_DAY"
    if float(row.get("top100_removed_usd") or 0.0) <= 0.0:
        return "FAIL_TOP100_ROBUSTNESS"
    if float(row.get("older_net_usd") or 0.0) <= 0.0 or float(row.get("newer_net_usd") or 0.0) <= 0.0:
        return "FAIL_SPLIT_NET"
    if float(row.get("older_profit_factor") or 0.0) < 1.15 or float(row.get("newer_profit_factor") or 0.0) < 1.15:
        return "REVIEW_SPLIT_PF"
    return "DAILY_STATE_GUARD_REVIEW_CANDIDATE"


def score(row: dict[str, Any]) -> float:
    pf = float(row.get("profit_factor") or 0.0)
    split_pf = min(float(row.get("older_profit_factor") or 0.0), float(row.get("newer_profit_factor") or 0.0))
    wr = float(row.get("win_rate_pct") or 0.0)
    pos_day = float(row.get("positive_day_pct") or 0.0)
    pos_day_no_top = float(row.get("positive_day_after_top10_removed_pct") or 0.0)
    tpa = float(row.get("trades_per_active_day") or 0.0)
    three_plus = float(row.get("three_plus_trade_day_pct") or 0.0)
    net = float(row.get("net_usd") or 0.0)
    dd = max(float(row.get("max_closed_drawdown_usd") or 1.0), 1.0)
    median_day = float(row.get("median_day_usd") or 0.0)
    p25_day = float(row.get("p25_day_usd") or 0.0)
    worst_day = min(float(row.get("worst_day_usd") or 0.0), 0.0)
    top100 = float(row.get("top100_removed_usd") or 0.0)
    retention = float(row.get("retention_pct") or 0.0)
    return (
        pf * 900.0
        + split_pf * 650.0
        + wr * 8.0
        + pos_day * 44.0
        + pos_day_no_top * 14.0
        + three_plus * 10.0
        + tpa * 160.0
        + net / dd * 130.0
        + median_day * 45.0
        + p25_day * 14.0
        + worst_day * 1.2
        + top100 / 38.0
        + retention * 3.0
    )


def compact(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "decision",
        "score",
        "state_rule",
        "profit_target_usd",
        "loss_stop_usd",
        "max_trades_per_day_guard",
        "max_losses_per_day_guard",
        "cooldown_after_loss_minutes",
        "early_trade_count",
        "early_pnl_threshold",
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
        "positive_day_after_top10_removed_pct",
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
        "state_stop_days",
        "cooldown_skipped_trades",
        "profit_target_days",
        "loss_stop_days",
        "trade_cap_days",
        "loss_count_days",
    ]
    return {key: row.get(key) for key in keys}


def search(base_trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    state_rules = [
        "none",
        "first_trade_loss_stop",
        "first_two_net_negative_stop",
        "first_three_net_negative_stop",
        "two_consecutive_losses_stop",
        "early_window_net_negative_stop",
    ]
    for state_rule, profit_target, loss_stop, max_trades, max_losses, cooldown in itertools.product(
        state_rules,
        [None, 8.0, 10.0, 12.0],
        [None, -15.0, -20.0, -25.0],
        [None, 5, 6, 8],
        [None, 2, 3],
        [0, 60],
    ):
        early_options = [(2, 0.0)]
        if state_rule == "first_two_net_negative_stop":
            early_options = [(2, 0.0), (2, -5.0)]
        elif state_rule == "first_three_net_negative_stop":
            early_options = [(3, 0.0), (3, -5.0)]
        elif state_rule == "early_window_net_negative_stop":
            early_options = [(2, 0.0), (2, -5.0), (3, 0.0), (3, -5.0)]

        for early_count, early_threshold in early_options:
            if state_rule in {"first_trade_loss_stop", "two_consecutive_losses_stop"} and max_losses is not None:
                continue
            if state_rule == "none" and cooldown:
                continue
            if state_rule == "none" and profit_target is None and loss_stop is None and max_trades is None and max_losses is None:
                continue
            name = f"{state_rule}_target{profit_target}_stop{loss_stop}_max{max_trades}_losses{max_losses}_cool{cooldown}_early{early_count}_{early_threshold}"
            rows.append(
                evaluate(
                    name,
                    base_trades,
                    state_rule=state_rule,
                    profit_target_usd=profit_target,
                    loss_stop_usd=loss_stop,
                    max_trades_per_day=max_trades,
                    max_losses_per_day=max_losses,
                    cooldown_after_loss_minutes=cooldown,
                    early_trade_count=early_count,
                    early_pnl_threshold=early_threshold,
                )
            )
    preferred = {
        "DAILY_STATE_GUARD_REVIEW_CANDIDATE": 0,
        "REVIEW_DAY_RATE": 1,
        "REVIEW_MEDIAN_DAY": 2,
        "REVIEW_SPLIT_PF": 3,
    }
    rows.sort(key=lambda row: (preferred.get(row["decision"], 9), -row["score"]))
    return rows


def render_markdown(rows: list[dict[str, Any]], base_summary: dict[str, Any], output_json: Path, output_csv: Path) -> str:
    review = [
        row
        for row in rows
        if row["decision"] in {"DAILY_STATE_GUARD_REVIEW_CANDIDATE", "REVIEW_DAY_RATE", "REVIEW_MEDIAN_DAY", "REVIEW_SPLIT_PF"}
    ]
    top = review[:30] if review else rows[:30]
    lines = [
        "# A1 XAU M5 Momentum Daily-State Guard Search",
        "",
        "Generated: 2026-07-02",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV analysis only. No MT5 runtime, charts, presets, orders, or positions were changed.",
        "",
        "## Purpose",
        "",
        "The owner wants a frequent intraday engine, not sparse high-PF pockets. The current daily-guard candidate has enough cadence but only about 55% positive active days. This search tests causal daily-state rules, such as stopping after a bad opening sequence or pausing after losses, to see whether daily positivity can improve without killing trade count.",
        "",
        "## Base Before Daily-State Rules",
        "",
        "| Trades | WR % | Net | PF | Active days | T/active | 3+ day % | Pos day % | Top100 removed |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        "| {trades} | {wr:.2f} | {net:.2f} | {pf:.2f} | {active} | {tpa:.2f} | {three:.2f} | {pos:.2f} | {top100:.2f} |".format(
            trades=base_summary.get("trades", 0),
            wr=float(base_summary.get("win_rate_pct") or 0.0),
            net=float(base_summary.get("net_usd") or 0.0),
            pf=float(base_summary.get("profit_factor") or 0.0),
            active=base_summary.get("active_days", 0),
            tpa=float(base_summary.get("trades_per_active_day") or 0.0),
            three=float(base_summary.get("three_plus_trade_day_pct") or 0.0),
            pos=float(base_summary.get("positive_day_pct") or 0.0),
            top100=float(base_summary.get("top100_removed_usd") or 0.0),
        ),
        "",
        "## Top Daily-State Rules",
        "",
        "| Rank | Decision | Rule | Trades | WR % | Net | PF | Active | T/active | 3+ day % | Pos day % | Median day | Worst day | Top100 removed | Older PF | Newer PF | Guard details |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for index, row in enumerate(top, 1):
        details = "target={}; stop={}; max_trades={}; max_losses={}; cooldown={}; early={}/{}".format(
            row.get("profit_target_usd"),
            row.get("loss_stop_usd"),
            row.get("max_trades_per_day_guard"),
            row.get("max_losses_per_day_guard"),
            row.get("cooldown_after_loss_minutes"),
            row.get("early_trade_count"),
            row.get("early_pnl_threshold"),
        )
        lines.append(
            "| {rank} | `{decision}` | `{rule}` | {trades} | {wr:.2f} | {net:.2f} | {pf:.2f} | {active} | {tpa:.2f} | {three:.2f} | {pos:.2f} | {median:.2f} | {worst:.2f} | {top100:.2f} | {older_pf:.2f} | {newer_pf:.2f} | {details} |".format(
                rank=index,
                decision=row["decision"],
                rule=row["state_rule"],
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
                details=details,
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A daily-state rule is only useful if it preserves the active-day cadence. If it improves PF but drops below the 3+ trades/day requirement, it is not a primary solution for this project.",
            "",
            f"Machine-readable output: `{output_json}`",
            f"CSV output: `{output_csv}`",
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
    parser.add_argument("--pool-limit", type=int, default=35)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_DAILY_STATE_GUARD_SEARCH_2026_07_02.json",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_DAILY_STATE_GUARD_SEARCH_2026_07_02.md",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_DAILY_STATE_GUARD_SEARCH_2026_07_02.csv",
    )
    args = parser.parse_args()

    base_trades, _priority = load_base_trades(args.pool_limit, REPAIRED_BLOCKS)
    base_summary = summarize("daily_fit_repair_base", base_trades)
    base_summary.update(daily_metrics(base_trades))
    base_summary.update(month_stats(base_trades))
    base_summary.update(day_tail_stats(base_trades))
    base_summary["top100_removed_usd"] = top_removed_usd(base_trades, 100)

    rows = search(base_trades)
    payload = {
        "status": "DAILY_STATE_GUARD_SEARCH_COMPLETE",
        "boundary": "offline_exact_mt5_trade_csv_analysis_only_no_runtime_change",
        "base": "daily_fit_repair_no_v13_18_22",
        "blocks": list(REPAIRED_BLOCKS),
        "base_summary": base_summary,
        "searched_rules": len(rows),
        "top_candidates": [compact(row) for row in rows[:100]],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    write_csv(args.output_csv, rows)
    args.output_md.write_text(render_markdown(rows, base_summary, args.output_json, args.output_csv), encoding="utf-8")
    print(args.output_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
