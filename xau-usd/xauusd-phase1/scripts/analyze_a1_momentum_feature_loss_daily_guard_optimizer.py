from __future__ import annotations

import csv
import itertools
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_momentum_broad_portfolio_search import duplicate_like_stats, is_four_year_report, load_variants
from analyze_a1_momentum_daily_fit_portfolio_search import daily_metrics, window_summary
from analyze_a1_momentum_daily_guard_search import apply_daily_guard
from analyze_a1_momentum_daily_shape_optimizer import day_tail_stats
from analyze_a1_momentum_deep_portfolio_search import dedupe_trades
from analyze_a1_momentum_feature_loss_portfolio_verdict import FEATURE_MEMBERS, LONG_MEMBER
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


def load_variant_trades() -> dict[str, dict[str, Any]]:
    reports = sorted(
        path
        for path in REPORTS_DIR.glob("A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_*FOUR_YEAR*.json")
        if is_four_year_report(path)
    )
    variants = load_variants(reports)
    required = [LONG_MEMBER] + [member for _, member in FEATURE_MEMBERS]
    missing = [name for name in required if name not in variants]
    if missing:
        raise SystemExit(f"Missing required MT5-tested variants: {missing}")
    return variants


def build_base(
    variants: dict[str, dict[str, Any]],
    label: str,
    feature_member: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw: list[dict[str, Any]] = []
    priority_names = [LONG_MEMBER, feature_member]
    for name in priority_names:
        for row in variants[name]["trades"]:
            copied = dict(row)
            copied["portfolio_member"] = name
            raw.append(copied)
    priority = {name: index for index, name in enumerate(priority_names)}
    raw_dups = duplicate_like_stats(raw)
    deduped = dedupe_trades(raw, priority)
    deduped.sort(key=lambda row: (row["entry_time"], row["exit_time"], row["variant"]))
    return deduped, {
        "threshold_label": label,
        "members": priority_names,
        "raw_trades": len(raw),
        "deduped_before_guard": len(deduped),
        "dedupe_removed_trades": len(raw) - len(deduped),
        "raw_duplicate_like_trade_pct": raw_dups["duplicate_like_trade_pct"],
    }


def evaluate(
    base_trades: list[dict[str, Any]],
    base_info: dict[str, Any],
    *,
    profit_target_usd: float | None,
    loss_stop_usd: float | None,
    max_trades_per_day: int | None,
    max_losses_per_day: int | None,
) -> dict[str, Any]:
    selected, guard = apply_daily_guard(
        base_trades,
        profit_target_usd=profit_target_usd,
        loss_stop_usd=loss_stop_usd,
        max_trades_per_day=max_trades_per_day,
        max_losses_per_day=max_losses_per_day,
    )
    name = (
        f"{base_info['threshold_label']}|target={profit_target_usd}|loss={loss_stop_usd}|"
        f"max_trades={max_trades_per_day}|max_losses={max_losses_per_day}"
    )
    older = window_summary("older", selected, None, SPLIT_DATE)
    newer = window_summary("newer", selected, SPLIT_DATE, None)
    summary = summarize(name, selected)
    summary.update(daily_metrics(selected))
    summary.update(day_tail_stats(selected))
    summary.update(month_stats(selected))
    summary.update(base_info)
    summary.update(
        {
            "profit_target_usd": profit_target_usd,
            "loss_stop_usd": loss_stop_usd,
            "max_trades_per_day_guard": max_trades_per_day,
            "max_losses_per_day_guard": max_losses_per_day,
            "retention_pct": round(100.0 * len(selected) / len(base_trades), 2) if base_trades else 0.0,
            "guard": guard,
            "older": older,
            "newer": newer,
            "top10_removed_usd": top_removed_usd(selected, 10),
            "top25_removed_usd": top_removed_usd(selected, 25),
            "top50_removed_usd": top_removed_usd(selected, 50),
            "top100_removed_usd": top_removed_usd(selected, 100),
        }
    )
    summary["decision"] = decision(summary)
    summary["score"] = round(score(summary), 2)
    return summary


def decision(row: dict[str, Any]) -> str:
    if row["trades"] < 1800:
        return "FAIL_SAMPLE"
    if row["active_days"] < 560:
        return "FAIL_ACTIVE_DAYS"
    if row["trades_per_active_day"] < 3.0:
        return "FAIL_TRADES_PER_ACTIVE_DAY"
    if row["three_plus_trade_day_pct"] < 53.0:
        return "FAIL_THREE_PLUS_DAYS"
    if row["win_rate_pct"] < 63.0:
        return "FAIL_WIN_RATE"
    if (row["profit_factor"] or 0.0) < 1.28:
        return "FAIL_PROFIT_FACTOR"
    if row["net_usd"] < 1250.0:
        return "FAIL_NET"
    if row["positive_day_pct"] < 56.0:
        return "REVIEW_DAY_RATE"
    if row["median_day_usd"] <= 0:
        return "REVIEW_MEDIAN_DAY"
    if row["top100_removed_usd"] <= 0:
        return "FAIL_TOP100_ROBUSTNESS"
    if row["older"]["net_usd"] <= 0 or row["newer"]["net_usd"] <= 0:
        return "FAIL_SPLIT_NET"
    if (row["older"]["profit_factor"] or 0.0) < 1.15 or (row["newer"]["profit_factor"] or 0.0) < 1.25:
        return "REVIEW_SPLIT_PF"
    if row["max_closed_drawdown_usd"] > 125:
        return "REVIEW_DRAWDOWN"
    return "FREQUENCY_FIRST_REVIEW_CANDIDATE"


def score(row: dict[str, Any]) -> float:
    pf = float(row["profit_factor"] or 0.0)
    split_pf = min(float(row["older"]["profit_factor"] or 0.0), float(row["newer"]["profit_factor"] or 0.0))
    wr = float(row["win_rate_pct"])
    pos_day = float(row["positive_day_pct"])
    three_plus = float(row["three_plus_trade_day_pct"])
    tpa = float(row["trades_per_active_day"])
    net = float(row["net_usd"])
    dd = max(float(row["max_closed_drawdown_usd"] or 1.0), 1.0)
    median_day = float(row["median_day_usd"])
    p25_day = float(row["p25_day_usd"])
    top100 = float(row["top100_removed_usd"])
    retention = float(row["retention_pct"])
    guard_complexity = sum(
        1
        for value in [
            row["profit_target_usd"],
            row["loss_stop_usd"],
            row["max_trades_per_day_guard"],
            row["max_losses_per_day_guard"],
        ]
        if value is not None
    )
    return (
        pf * 1000.0
        + split_pf * 600.0
        + wr * 10.0
        + pos_day * 40.0
        + three_plus * 11.0
        + tpa * 140.0
        + net / dd * 130.0
        + median_day * 45.0
        + p25_day * 15.0
        + top100 / 35.0
        + retention * 2.5
        - guard_complexity * 45.0
        - max(0.0, -float(row["worst_month_usd"])) * 0.8
    )


def compact(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "decision",
        "score",
        "threshold_label",
        "members",
        "trades",
        "win_rate_pct",
        "net_usd",
        "profit_factor",
        "active_days",
        "trades_per_active_day",
        "three_plus_trade_day_pct",
        "positive_day_pct",
        "median_day_usd",
        "p25_day_usd",
        "positive_months",
        "negative_months",
        "worst_month_usd",
        "top25_removed_usd",
        "top100_removed_usd",
        "max_closed_drawdown_usd",
        "older",
        "newer",
        "profit_target_usd",
        "loss_stop_usd",
        "max_trades_per_day_guard",
        "max_losses_per_day_guard",
        "retention_pct",
        "guard",
        "raw_trades",
        "deduped_before_guard",
        "dedupe_removed_trades",
        "raw_duplicate_like_trade_pct",
    ]
    return {key: row.get(key) for key in keys}


def render(rows: list[dict[str, Any]], output_json: Path, output_csv: Path) -> str:
    review = [row for row in rows if row["decision"] == "FREQUENCY_FIRST_REVIEW_CANDIDATE"]
    top = review[:25] if review else rows[:25]
    lines = [
        "# A1 XAU M5 Momentum Feature-Loss Daily Guard Optimizer",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV analysis only. No MT5 runtime, charts, presets, orders, or positions were changed.",
        "",
        "## Purpose",
        "",
        "The owner rejected sparse monthly strategies. This optimizer keeps the entry family fixed and searches only portfolio-level daily controls around the feature-loss threshold family: profit target, loss stop, max trades/day, and max losses/day.",
        "",
        "A useful result must keep at least 3 trades per active day, preserve a win rate above 50%, keep PF/net positive after de-duplication, and improve day-to-day reliability without turning the system sparse.",
        "",
        "## Top Frequency-First Candidates",
        "",
        "| Rank | Decision | Score | Threshold | Guard | Trades | WR % | Net | PF | Active | T/active | 3+ day % | Pos day % | Median day | +M/-M | Top100 removed | DD | Older PF/net | Newer PF/net |",
        "|---:|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(top, 1):
        guard = (
            f"target={row['profit_target_usd']}, loss={row['loss_stop_usd']}, "
            f"max_trades={row['max_trades_per_day_guard']}, max_losses={row['max_losses_per_day_guard']}"
        )
        lines.append(
            "| {rank} | `{decision}` | {score:.2f} | `{threshold}` | `{guard}` | {trades} | {wr:.2f} | {net:.2f} | {pf} | {active} | {tpa:.2f} | {three:.2f} | {pos:.2f} | {median:.2f} | {pm}/{nm} | {top100:.2f} | {dd:.2f} | {opf} / {onet:.2f} | {npf} / {nnet:.2f} |".format(
                rank=index,
                decision=row["decision"],
                score=row["score"],
                threshold=row["threshold_label"],
                guard=guard,
                trades=row["trades"],
                wr=row["win_rate_pct"],
                net=row["net_usd"],
                pf=row["profit_factor"],
                active=row["active_days"],
                tpa=row["trades_per_active_day"],
                three=row["three_plus_trade_day_pct"],
                pos=row["positive_day_pct"],
                median=row["median_day_usd"],
                pm=row["positive_months"],
                nm=row["negative_months"],
                top100=row["top100_removed_usd"],
                dd=row["max_closed_drawdown_usd"],
                opf=row["older"]["profit_factor"],
                onet=row["older"]["net_usd"],
                npf=row["newer"]["profit_factor"],
                nnet=row["newer"]["net_usd"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This is a diagnostic search over daily controls, not an approval to attach runtime.",
            "- If the top row only improves by over-pruning, reject it. The frequency requirement remains hard.",
            "- A promoted demo candidate still needs reviewer/owner approval and a frozen forward-test spec.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{output_json}`",
            f"- CSV: `{output_csv}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "decision",
        "score",
        "threshold_label",
        "trades",
        "win_rate_pct",
        "net_usd",
        "profit_factor",
        "active_days",
        "trades_per_active_day",
        "three_plus_trade_day_pct",
        "positive_day_pct",
        "median_day_usd",
        "p25_day_usd",
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
        "profit_target_usd",
        "loss_stop_usd",
        "max_trades_per_day_guard",
        "max_losses_per_day_guard",
        "retention_pct",
        "raw_duplicate_like_trade_pct",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "decision": row["decision"],
                    "score": row["score"],
                    "threshold_label": row["threshold_label"],
                    "trades": row["trades"],
                    "win_rate_pct": row["win_rate_pct"],
                    "net_usd": row["net_usd"],
                    "profit_factor": row["profit_factor"],
                    "active_days": row["active_days"],
                    "trades_per_active_day": row["trades_per_active_day"],
                    "three_plus_trade_day_pct": row["three_plus_trade_day_pct"],
                    "positive_day_pct": row["positive_day_pct"],
                    "median_day_usd": row["median_day_usd"],
                    "p25_day_usd": row["p25_day_usd"],
                    "positive_months": row["positive_months"],
                    "negative_months": row["negative_months"],
                    "worst_month_usd": row["worst_month_usd"],
                    "top25_removed_usd": row["top25_removed_usd"],
                    "top100_removed_usd": row["top100_removed_usd"],
                    "max_closed_drawdown_usd": row["max_closed_drawdown_usd"],
                    "older_net_usd": row["older"]["net_usd"],
                    "older_profit_factor": row["older"]["profit_factor"],
                    "newer_net_usd": row["newer"]["net_usd"],
                    "newer_profit_factor": row["newer"]["profit_factor"],
                    "profit_target_usd": row["profit_target_usd"],
                    "loss_stop_usd": row["loss_stop_usd"],
                    "max_trades_per_day_guard": row["max_trades_per_day_guard"],
                    "max_losses_per_day_guard": row["max_losses_per_day_guard"],
                    "retention_pct": row["retention_pct"],
                    "raw_duplicate_like_trade_pct": row["raw_duplicate_like_trade_pct"],
                }
            )


def main() -> int:
    variants = load_variant_trades()
    rows: list[dict[str, Any]] = []
    profit_targets = [None, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0, 75.0, 100.0]
    loss_stops = [None, -15.0, -20.0, -25.0, -30.0, -35.0, -40.0]
    max_trades = [None, 4, 5, 6, 7, 8, 10]
    max_losses = [None, 1, 2, 3, 4]
    for label, feature_member in FEATURE_MEMBERS:
        base_trades, base_info = build_base(variants, label, feature_member)
        for profit_target, loss_stop, max_trade_count, max_loss_count in itertools.product(
            profit_targets,
            loss_stops,
            max_trades,
            max_losses,
        ):
            rows.append(
                evaluate(
                    base_trades,
                    base_info,
                    profit_target_usd=profit_target,
                    loss_stop_usd=loss_stop,
                    max_trades_per_day=max_trade_count,
                    max_losses_per_day=max_loss_count,
                )
            )
    rows.sort(key=lambda row: (row["decision"] != "FREQUENCY_FIRST_REVIEW_CANDIDATE", -row["score"]))
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "FEATURE_LOSS_DAILY_GUARD_OPTIMIZER_COMPLETE",
        "searched_rows": len(rows),
        "best_frequency_first_candidate": compact(rows[0]) if rows else {},
        "top_rows": [compact(row) for row in rows[:100]],
    }
    output_md = REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_LOSS_DAILY_GUARD_OPTIMIZER_2026_07_02.md"
    output_json = output_md.with_suffix(".json")
    output_csv = output_md.with_suffix(".csv")
    output_md.write_text(render(rows, output_json, output_csv), encoding="utf-8")
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    write_csv(output_csv, rows)
    print(output_md)
    print(json.dumps({"status": payload["status"], "searched_rows": len(rows), "best": payload["best_frequency_first_candidate"]}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
