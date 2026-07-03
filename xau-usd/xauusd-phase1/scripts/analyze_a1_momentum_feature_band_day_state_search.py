from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_momentum_daily_fit_portfolio_search import daily_metrics, window_summary
from analyze_a1_momentum_daily_state_guard_search import apply_state_guard, day_tail_stats, top_removed_usd
from analyze_a1_momentum_feature_loss_daily_guard_optimizer import build_base, load_variant_trades
from analyze_a1_momentum_feature_loss_portfolio_verdict import FEATURE_MEMBERS
from analyze_a1_momentum_portfolio_combinations import summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAY_STATE_SEARCH_2026_07_02"
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


def load_base_feature_band_trades() -> list[dict[str, Any]]:
    variants = load_variant_trades()
    feature_member = dict(FEATURE_MEMBERS)["band_m2p51_m0p75"]
    base, _info = build_base(variants, "band_m2p51_m0p75", feature_member)
    return base


def summarize_trades(name: str, selected: list[dict[str, Any]], base_count: int, state: dict[str, Any]) -> dict[str, Any]:
    older = window_summary("older", selected, None, SPLIT_DATE)
    newer = window_summary("newer", selected, SPLIT_DATE, None)
    summary = summarize(name, selected)
    summary.update(daily_metrics(selected))
    summary.update(day_tail_stats(selected))
    summary.update(month_stats(selected))
    summary.update(
        {
            "base_trades": base_count,
            "retention_pct": round(100.0 * len(selected) / base_count, 2) if base_count else 0.0,
            "top10_removed_usd": top_removed_usd(selected, 10),
            "top25_removed_usd": top_removed_usd(selected, 25),
            "top100_removed_usd": top_removed_usd(selected, 100),
            "older_net_usd": older.get("net_usd", 0.0),
            "older_profit_factor": older.get("profit_factor") or 0.0,
            "newer_net_usd": newer.get("net_usd", 0.0),
            "newer_profit_factor": newer.get("profit_factor") or 0.0,
        }
    )
    summary.update(state)
    summary["decision"] = decision(summary)
    summary["score"] = round(score(summary), 2)
    return summary


def evaluate(
    base_trades: list[dict[str, Any]],
    *,
    name: str,
    state_rule: str,
    profit_target_usd: float | None = 50.0,
    loss_stop_usd: float | None = None,
    max_trades_per_day: int | None = 6,
    max_losses_per_day: int | None = None,
    cooldown_after_loss_minutes: int = 0,
    early_trade_count: int = 2,
    early_pnl_threshold: float = 0.0,
) -> dict[str, Any]:
    selected, guard_stats = apply_state_guard(
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
    state = {
        "state_rule": state_rule,
        "profit_target_usd": profit_target_usd,
        "loss_stop_usd": loss_stop_usd,
        "max_trades_per_day_guard": max_trades_per_day,
        "max_losses_per_day_guard": max_losses_per_day,
        "cooldown_after_loss_minutes": cooldown_after_loss_minutes,
        "early_trade_count": early_trade_count,
        "early_pnl_threshold": early_pnl_threshold,
    }
    state.update(guard_stats)
    return summarize_trades(name, selected, len(base_trades), state)


def decision(row: dict[str, Any]) -> str:
    if row["trades"] < 1800:
        return "FAIL_SAMPLE"
    if row["active_days"] < 560:
        return "FAIL_ACTIVE_DAYS"
    if row["trades_per_active_day"] < 3.0:
        return "FAIL_TRADES_PER_ACTIVE_DAY"
    if row["three_plus_trade_day_pct"] < 50.0:
        return "FAIL_THREE_PLUS_DAY_COVERAGE"
    if row["win_rate_pct"] < 60.0:
        return "FAIL_WIN_RATE"
    if (row["profit_factor"] or 0.0) < 1.25:
        return "FAIL_PROFIT_FACTOR"
    if row["net_usd"] < 1000.0:
        return "FAIL_NET"
    if row["top100_removed_usd"] <= 0:
        return "FAIL_TOP100_ROBUSTNESS"
    if row["older_net_usd"] <= 0 or row["newer_net_usd"] <= 0:
        return "FAIL_SPLIT_NET"
    if row["positive_day_pct"] < 58.0:
        return "REVIEW_DAY_RATE"
    if row["three_plus_trade_day_pct"] < 53.0:
        return "DAILY_RELIABILITY_REVIEW_CANDIDATE_WITH_CADENCE_NOTE"
    return "FREQUENCY_FIRST_DAY_STATE_REVIEW_CANDIDATE"


def score(row: dict[str, Any]) -> float:
    pf = float(row.get("profit_factor") or 0.0)
    split_pf = min(float(row.get("older_profit_factor") or 0.0), float(row.get("newer_profit_factor") or 0.0))
    return (
        pf * 900.0
        + split_pf * 550.0
        + float(row.get("win_rate_pct") or 0.0) * 9.0
        + float(row.get("positive_day_pct") or 0.0) * 48.0
        + float(row.get("three_plus_trade_day_pct") or 0.0) * 10.0
        + float(row.get("trades_per_active_day") or 0.0) * 130.0
        + float(row.get("net_usd") or 0.0) / max(float(row.get("max_closed_drawdown_usd") or 1.0), 1.0) * 110.0
        + float(row.get("top100_removed_usd") or 0.0) / 45.0
        - max(0.0, -float(row.get("worst_month_usd") or 0.0)) * 0.75
    )


def generate_rows(base_trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        evaluate(base_trades, name="owner_target_50_max6_baseline", state_rule="none"),
    ]
    for loss_stop in [None, -10.0, -15.0, -20.0, -25.0, -30.0]:
        for max_losses in [None, 2, 3, 4]:
            rows.append(
                evaluate(
                    base_trades,
                    name=f"owner_target_50_max6_lossstop_{loss_stop}_maxloss_{max_losses}",
                    state_rule="none",
                    loss_stop_usd=loss_stop,
                    max_losses_per_day=max_losses,
                )
            )
    for rule in [
        "first_trade_loss_stop",
        "two_consecutive_losses_stop",
    ]:
        rows.append(evaluate(base_trades, name=f"owner_target_50_max6_{rule}", state_rule=rule))
    for threshold in [0.0, -2.5, -5.0, -7.5, -10.0]:
        rows.append(
            evaluate(
                base_trades,
                name=f"owner_target_50_max6_first2_threshold_{threshold}",
                state_rule="first_two_net_negative_stop",
                early_trade_count=2,
                early_pnl_threshold=threshold,
            )
        )
        rows.append(
            evaluate(
                base_trades,
                name=f"owner_target_50_max6_first3_threshold_{threshold}",
                state_rule="first_three_net_negative_stop",
                early_trade_count=3,
                early_pnl_threshold=threshold,
            )
        )
    for early_count in [2, 3, 4]:
        for threshold in [0.0, -5.0, -10.0, -15.0]:
            rows.append(
                evaluate(
                    base_trades,
                    name=f"owner_target_50_max6_early{early_count}_pnl_{threshold}",
                    state_rule="early_window_net_negative_stop",
                    early_trade_count=early_count,
                    early_pnl_threshold=threshold,
                )
            )
    for cooldown in [15, 30, 60, 90, 120]:
        rows.append(
            evaluate(
                base_trades,
                name=f"owner_target_50_max6_cooldown_after_loss_{cooldown}",
                state_rule="none",
                cooldown_after_loss_minutes=cooldown,
            )
        )
    decision_rank = {
        "FREQUENCY_FIRST_DAY_STATE_REVIEW_CANDIDATE": 0,
        "DAILY_RELIABILITY_REVIEW_CANDIDATE_WITH_CADENCE_NOTE": 0,
        "REVIEW_DAY_RATE": 2,
    }
    rows.sort(key=lambda row: (decision_rank.get(row["decision"], 9), -row["score"]))
    return rows


def compact(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "name",
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
        "win_rate_pct",
        "net_usd",
        "profit_factor",
        "active_days",
        "trades_per_active_day",
        "three_plus_trade_day_pct",
        "positive_day_pct",
        "median_day_usd",
        "p10_day_usd",
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
        "retention_pct",
        "skipped_trades",
        "profit_target_days",
        "loss_stop_days",
        "trade_cap_days",
        "loss_count_days",
        "state_stop_days",
        "cooldown_skipped_trades",
    ]
    return {key: row.get(key) for key in keys}


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    fields = list(compact(rows[0]).keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(compact(row))


def render(rows: list[dict[str, Any]], output_json: Path, output_csv: Path) -> str:
    baseline = next(row for row in rows if row["name"] == "owner_target_50_max6_baseline")
    review = [
        row
        for row in rows
        if row["decision"]
        in {
            "FREQUENCY_FIRST_DAY_STATE_REVIEW_CANDIDATE",
            "DAILY_RELIABILITY_REVIEW_CANDIDATE_WITH_CADENCE_NOTE",
        }
    ]
    top = review[:20] if review else rows[:20]
    best = top[0] if top else baseline
    lines = [
        "# A1 XAU M5 Momentum Feature-Band Day-State Search - 2026-07-02",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV analysis only. No MT5 runtime, charts, presets, orders, or positions were changed.",
        "",
        "## Purpose",
        "",
        "The +50/max6 feature-band package matches the owner's frequency requirement, but positive active days are still below 60%. This search tests causal day-state overlays on the exact same trade stream to see whether daily reliability can improve without making the system sparse.",
        "",
        "Baseline:",
        "",
        f"`{baseline['trades']}` trades / WR `{baseline['win_rate_pct']}%` / PF `{baseline['profit_factor']}` / net `{baseline['net_usd']}` / `{baseline['trades_per_active_day']}` trades per active day / `{baseline['positive_day_pct']}%` positive active days.",
        "",
        f"Best row: `{best['name']}`",
        "",
        "## Top Rows",
        "",
        "| Rank | Decision | Rule | Loss stop | Max losses | Cooldown | Early | Trades | WR % | Net | PF | T/active | 3+ day % | Pos day % | +M/-M | Top100 | DD | Older PF/net | Newer PF/net |",
        "|---:|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(top, 1):
        early = f"{row['early_trade_count']} @ {row['early_pnl_threshold']}"
        lines.append(
            "| {rank} | `{decision}` | `{rule}` | {loss_stop} | {max_losses} | {cooldown} | `{early}` | {trades} | {wr:.2f} | {net:.2f} | {pf} | {tpa:.2f} | {three:.2f} | {pos:.2f} | {pm}/{nm} | {top100:.2f} | {dd:.2f} | {opf:.2f} / {onet:.2f} | {npf:.2f} / {nnet:.2f} |".format(
                rank=index,
                decision=row["decision"],
                rule=row["state_rule"],
                loss_stop=row["loss_stop_usd"],
                max_losses=row["max_losses_per_day_guard"],
                cooldown=row["cooldown_after_loss_minutes"],
                early=early,
                trades=row["trades"],
                wr=row["win_rate_pct"],
                net=row["net_usd"],
                pf=row["profit_factor"],
                tpa=row["trades_per_active_day"],
                three=row["three_plus_trade_day_pct"],
                pos=row["positive_day_pct"],
                pm=row["positive_months"],
                nm=row["negative_months"],
                top100=row["top100_removed_usd"],
                dd=row["max_closed_drawdown_usd"],
                opf=row["older_profit_factor"],
                onet=row["older_net_usd"],
                npf=row["newer_profit_factor"],
                nnet=row["newer_net_usd"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Any improvement here is a day-management overlay, not a new entry edge.",
            "- A row is only useful if it preserves at least 1800 trades, at least 3 trades per active day, PF >= 1.25, WR >= 60%, positive older/newer splits, and positive top-100 removal.",
            "- `DAILY_RELIABILITY_REVIEW_CANDIDATE_WITH_CADENCE_NOTE` means the row keeps the owner's multiple-trades/day shape, but the 3+ trade-day rate is between 50% and 53%; this is reviewable because it can materially improve PF, win rate, positive-day rate, drawdown, and top-100 robustness.",
            "- If the best overlay only improves positive-day rate by reducing cadence or net too far, keep the current +50/max6 package and look for another entry/feature improvement instead.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{output_json}`",
            f"- CSV: `{output_csv}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    base = load_base_feature_band_trades()
    rows = generate_rows(base)
    payload = {
        "status": "FEATURE_BAND_DAY_STATE_SEARCH_COMPLETE",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "baseline": compact(next(row for row in rows if row["name"] == "owner_target_50_max6_baseline")),
        "best": compact(rows[0]),
        "review_candidates": [
            compact(row)
            for row in rows
            if row["decision"]
            in {
                "FREQUENCY_FIRST_DAY_STATE_REVIEW_CANDIDATE",
                "DAILY_RELIABILITY_REVIEW_CANDIDATE_WITH_CADENCE_NOTE",
            }
        ],
        "top_rows": [compact(row) for row in rows[:25]],
    }
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    write_csv(rows, output_csv)
    output_md.write_text(render(rows, output_json, output_csv), encoding="utf-8")
    print(output_md)
    print(json.dumps({"status": payload["status"], "best": payload["best"]}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
