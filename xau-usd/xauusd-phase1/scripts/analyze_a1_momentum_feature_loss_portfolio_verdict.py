from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_momentum_broad_portfolio_search import duplicate_like_stats, is_four_year_report, load_variants
from analyze_a1_momentum_daily_fit_portfolio_search import daily_metrics, window_summary
from analyze_a1_momentum_daily_guard_search import apply_daily_guard
from analyze_a1_momentum_deep_portfolio_search import dedupe_trades
from analyze_a1_momentum_portfolio_combinations import summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
SPLIT_DATE = datetime(2024, 7, 1)

LONG_MEMBER = "freq_h1_h4_long_rr0p7_cost005_block_weak_hours_v1"
OLD_V13_MEMBER = "v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning"
FEATURE_MEMBERS = [
    ("m1p25", "v13_feature_loss_short_extreme_m1p25_rr0p6"),
    ("m1p0", "v13_feature_loss_short_extreme_m1p0_rr0p6"),
    ("m0p75", "v13_feature_loss_short_extreme_rr0p6"),
    ("band_m2p51_m0p75", "v13_feature_loss_short_extreme_band_m2p51_rr0p6"),
    ("m0p5", "v13_feature_loss_short_extreme_m0p5_rr0p6"),
    ("m0p25", "v13_feature_loss_short_extreme_m0p25_rr0p6"),
]


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


def daily_guard(trades: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    return apply_daily_guard(
        trades,
        profit_target_usd=None,
        loss_stop_usd=-25.0,
        max_trades_per_day=6,
        max_losses_per_day=None,
    )


def load_member_trades(member_names: tuple[str, ...]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    reports = sorted(
        path
        for path in REPORTS_DIR.glob("A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_*FOUR_YEAR*.json")
        if is_four_year_report(path)
    )
    variants = load_variants(reports)
    missing = [name for name in member_names if name not in variants]
    if missing:
        raise SystemExit(f"Missing variants: {missing}")

    raw: list[dict[str, Any]] = []
    for name in member_names:
        for row in variants[name]["trades"]:
            copied = dict(row)
            copied["portfolio_member"] = name
            raw.append(copied)
    priority = {name: index for index, name in enumerate(member_names)}
    return raw, priority


def evaluate(name: str, member_names: tuple[str, ...], *, use_daily_guard: bool) -> dict[str, Any]:
    raw, priority = load_member_trades(member_names)
    duplicate_like = duplicate_like_stats(raw)
    deduped = dedupe_trades(raw, priority)
    deduped.sort(key=lambda row: (row["entry_time"], row["exit_time"], row["variant"]))
    guarded_stats: dict[str, Any] = {}
    if use_daily_guard:
        selected, guarded_stats = daily_guard(deduped)
    else:
        selected = deduped

    older = window_summary("older", selected, None, SPLIT_DATE)
    newer = window_summary("newer", selected, SPLIT_DATE, None)
    summary = summarize(name, selected)
    summary.update(daily_metrics(selected))
    summary.update(month_stats(selected))
    summary.update(
        {
            "members": list(member_names),
            "raw_trades": len(raw),
            "deduped_before_guard": len(deduped),
            "dedupe_removed_trades": len(raw) - len(deduped),
            "raw_duplicate_like_trade_pct": duplicate_like["duplicate_like_trade_pct"],
            "daily_guard_enabled": use_daily_guard,
            "daily_guard": guarded_stats,
            "older": older,
            "newer": newer,
            "top10_removed_usd": top_removed_usd(selected, 10),
            "top25_removed_usd": top_removed_usd(selected, 25),
            "top100_removed_usd": top_removed_usd(selected, 100),
        }
    )
    return summary


def decision(summary: dict[str, Any]) -> str:
    if summary["trades"] < 1200:
        return "FAIL_SAMPLE"
    if summary["trades_per_active_day"] < 3.0:
        return "FAIL_TRADES_PER_ACTIVE_DAY"
    if summary["win_rate_pct"] < 60.0:
        return "FAIL_WIN_RATE"
    if (summary["profit_factor"] or 0.0) < 1.25:
        return "FAIL_PROFIT_FACTOR"
    if summary["net_usd"] <= 0:
        return "FAIL_NET"
    if summary["top100_removed_usd"] <= 0:
        return "FAIL_TOP100_ROBUSTNESS"
    if summary["older"]["net_usd"] <= 0 or summary["newer"]["net_usd"] <= 0:
        return "FAIL_SPLIT_STABILITY"
    if summary["positive_day_pct"] < 55.0:
        return "REVIEW_DAY_RATE"
    return "REVIEW_READY_NOT_PROMOTED"


def row(summary: dict[str, Any]) -> str:
    return (
        f"| `{summary['name']}` | `{summary['decision']}` | {summary['trades']} | "
        f"{summary['win_rate_pct']} | {summary['net_usd']} | {summary['profit_factor']} | "
        f"{summary['active_days']} | {summary['trades_per_active_day']} | "
        f"{summary['positive_day_pct']} | {summary['three_plus_trade_day_pct']} | "
        f"{summary['positive_months']}/{summary['negative_months']} | {summary['top100_removed_usd']} | "
        f"{summary['older']['net_usd']} / {summary['older']['profit_factor']} | "
        f"{summary['newer']['net_usd']} / {summary['newer']['profit_factor']} |"
    )


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU M5 Momentum Feature-Loss Portfolio Verdict",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV analysis only. No MT5 runtime, charts, presets, orders, or positions were changed.",
        "",
        "## Purpose",
        "",
        "The standalone feature-loss V13 lane improved WR/PF but did not meet the owner's multiple-trades-per-active-day target. This report combines the existing frequency-first long lane with the new MT5-confirmed feature-loss V13 lane, de-duplicates same-minute overlap, and replays the existing daily guard.",
        "",
        f"Best frequency-first candidate: `{payload.get('best_frequency_first_candidate')}`",
        "",
        "## Result Table",
        "",
        "| Portfolio | Decision | Trades | WR % | Net | PF | Active | T/active | Pos day % | 3+ day % | Pos/neg months | Top100 removed | Older net/PF | Newer net/PF |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in payload["summaries"]:
        lines.append(row(item))
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The feature-loss V13 filter is a real MT5-tested improvement over old V13, but as a single lane it is still too sparse for the project objective.",
            "- The owner's business rule is now frequency-first: a candidate must remain profitable while producing multiple trades per active day.",
            "- The portfolio-shaped question is whether the long weak-hour lane plus feature-filtered V13 can preserve at least 3 trades per active day while improving positive-day rate.",
            "- Threshold variants are shown as diagnostic candidates, not as promoted demo presets. The preferred setting should be stable across nearby thresholds, not a one-threshold accident.",
            "- This report is still diagnostic. It does not authorize demo attachment or replacement without reviewer/owner approval.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    old_members = (LONG_MEMBER, OLD_V13_MEMBER)
    summaries = [
        evaluate("old_daily_guard_long_plus_v13", old_members, use_daily_guard=True),
    ]
    for label, member in FEATURE_MEMBERS:
        feature_members = (LONG_MEMBER, member)
        summaries.append(evaluate(f"feature_daily_guard_long_plus_feature_v13_{label}", feature_members, use_daily_guard=True))
    summaries.append(evaluate("feature_raw_long_plus_feature_v13_m0p75", (LONG_MEMBER, "v13_feature_loss_short_extreme_rr0p6"), use_daily_guard=False))
    for item in summaries:
        item["decision"] = decision(item)
    eligible = [
        item
        for item in summaries
        if item["decision"] in {"REVIEW_READY_NOT_PROMOTED", "REVIEW_DAY_RATE"}
        and item["daily_guard_enabled"]
        and item["name"].startswith("feature_daily_guard")
    ]
    best = max(
        eligible,
        key=lambda item: (
            item["decision"] == "REVIEW_READY_NOT_PROMOTED",
            item["positive_day_pct"],
            item["profit_factor"] or 0,
            item["net_usd"],
            item["trades_per_active_day"],
        ),
        default=None,
    )
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "FEATURE_LOSS_PORTFOLIO_VERDICT_COMPLETE",
        "best_frequency_first_candidate": best["name"] if best else None,
        "summaries": summaries,
    }
    report_md = REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_LOSS_PORTFOLIO_VERDICT_2026_07_02.md"
    report_json = report_md.with_suffix(".json")
    report_md.write_text(render(payload), encoding="utf-8")
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(report_md)
    print(json.dumps({"status": payload["status"], "summaries": summaries}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
