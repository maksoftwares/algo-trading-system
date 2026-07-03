from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_momentum_daily_fit_portfolio_search import daily_metrics, window_summary
from analyze_a1_momentum_daily_state_guard_search import apply_state_guard, day_tail_stats, top_removed_usd
from analyze_a1_momentum_feature_band_day_state_search import load_base_feature_band_trades, month_stats
from analyze_a1_momentum_feature_loss_clusters import (
    FEATURES,
    apply_feature_filter,
    load_signal_features,
    quantiles,
    source_variants,
)
from analyze_a1_momentum_portfolio_combinations import summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_FEATURE_BAND_RELIABILITY_RESIDUAL_SEARCH_2026_07_02"
SPLIT_DATE = datetime(2024, 7, 1)


def enrich_base_trades() -> list[dict[str, Any]]:
    base = load_base_feature_band_trades()
    variants = source_variants()
    signal_features = load_signal_features(variants, base)
    enriched: list[dict[str, Any]] = []
    for row in base:
        copied = dict(row)
        key = (row["variant"], row["entry_time"].strftime("%Y.%m.%d %H:%M:%S"), row["direction"])
        copied.update(signal_features.get(key, {}))
        enriched.append(copied)
    return enriched


def apply_reliability_guard(trades: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    return apply_state_guard(
        trades,
        state_rule="none",
        profit_target_usd=50.0,
        loss_stop_usd=None,
        max_trades_per_day=6,
        max_losses_per_day=None,
        cooldown_after_loss_minutes=15,
        early_trade_count=2,
        early_pnl_threshold=0.0,
    )


def summarize_candidate(
    name: str,
    selected: list[dict[str, Any]],
    *,
    base_count: int,
    guard_stats: dict[str, Any],
    filter_info: dict[str, Any],
    baseline: dict[str, Any] | None = None,
) -> dict[str, Any]:
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
    summary.update(guard_stats)
    summary.update(filter_info)
    if baseline:
        summary["delta_net_usd"] = round(summary["net_usd"] - baseline["net_usd"], 2)
        summary["delta_positive_day_pct"] = round(summary["positive_day_pct"] - baseline["positive_day_pct"], 2)
        summary["delta_profit_factor"] = round((summary["profit_factor"] or 0.0) - (baseline["profit_factor"] or 0.0), 3)
        summary["delta_win_rate_pct"] = round(summary["win_rate_pct"] - baseline["win_rate_pct"], 2)
        summary["delta_trades"] = summary["trades"] - baseline["trades"]
        summary["delta_top100_removed_usd"] = round(summary["top100_removed_usd"] - baseline["top100_removed_usd"], 2)
        summary["delta_drawdown_usd"] = round(summary["max_closed_drawdown_usd"] - baseline["max_closed_drawdown_usd"], 2)
    else:
        summary["delta_net_usd"] = 0.0
        summary["delta_positive_day_pct"] = 0.0
        summary["delta_profit_factor"] = 0.0
        summary["delta_win_rate_pct"] = 0.0
        summary["delta_trades"] = 0
        summary["delta_top100_removed_usd"] = 0.0
        summary["delta_drawdown_usd"] = 0.0
    summary["decision"] = decision(summary, baseline)
    summary["score"] = round(score(summary), 2)
    return summary


def decision(row: dict[str, Any], baseline: dict[str, Any] | None) -> str:
    if row["trades"] < 1800:
        return "FAIL_SAMPLE"
    if row["active_days"] < 560:
        return "FAIL_ACTIVE_DAYS"
    if row["trades_per_active_day"] < 3.0:
        return "FAIL_TRADES_PER_ACTIVE_DAY"
    if row["three_plus_trade_day_pct"] < 50.0:
        return "FAIL_THREE_PLUS_DAY_COVERAGE"
    if row["win_rate_pct"] < 65.0:
        return "FAIL_WIN_RATE"
    if (row["profit_factor"] or 0.0) < 1.35:
        return "FAIL_PROFIT_FACTOR"
    if row["net_usd"] < 1400.0:
        return "FAIL_NET"
    if row["top100_removed_usd"] <= 0:
        return "FAIL_TOP100_ROBUSTNESS"
    if row["older_net_usd"] <= 0 or row["newer_net_usd"] <= 0:
        return "FAIL_SPLIT_NET"
    if not baseline:
        return "BASELINE"
    if row["positive_day_pct"] < baseline["positive_day_pct"]:
        return "FAIL_DAY_RATE_REGRESSION"
    if row["net_usd"] < baseline["net_usd"] and row["positive_day_pct"] <= baseline["positive_day_pct"] + 0.5:
        return "FAIL_NO_USEFUL_TRADEOFF"
    if row["positive_day_pct"] >= 61.0 and row["profit_factor"] >= baseline["profit_factor"]:
        return "RELIABILITY_UPGRADE_REVIEW_CANDIDATE"
    return "REVIEW_TRADEOFF"


def score(row: dict[str, Any]) -> float:
    pf = float(row.get("profit_factor") or 0.0)
    split_pf = min(float(row.get("older_profit_factor") or 0.0), float(row.get("newer_profit_factor") or 0.0))
    return (
        pf * 900.0
        + split_pf * 600.0
        + float(row.get("win_rate_pct") or 0.0) * 9.0
        + float(row.get("positive_day_pct") or 0.0) * 55.0
        + float(row.get("three_plus_trade_day_pct") or 0.0) * 10.0
        + float(row.get("trades_per_active_day") or 0.0) * 140.0
        + float(row.get("net_usd") or 0.0) / max(float(row.get("max_closed_drawdown_usd") or 1.0), 1.0) * 115.0
        + float(row.get("top100_removed_usd") or 0.0) / 40.0
        + float(row.get("delta_positive_day_pct") or 0.0) * 210.0
        + float(row.get("delta_profit_factor") or 0.0) * 650.0
        - max(0.0, -float(row.get("worst_month_usd") or 0.0)) * 0.75
    )


def as_float(value: Any) -> float:
    try:
        if value in (None, ""):
            return math.nan
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def block_by_category(
    trades: list[dict[str, Any]], *, field: str, value: Any, direction: str | None = None
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    kept: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for row in trades:
        direction_ok = direction is None or row.get("direction") == direction
        if direction_ok and row.get(field) == value:
            blocked.append(row)
        else:
            kept.append(row)
    return kept, blocked


def evaluate_filtered(
    base_trades: list[dict[str, Any]],
    *,
    name: str,
    kept_raw: list[dict[str, Any]],
    blocked_raw: list[dict[str, Any]],
    filter_info: dict[str, Any],
    baseline: dict[str, Any],
) -> dict[str, Any]:
    selected, guard_stats = apply_reliability_guard(kept_raw)
    info = {
        "filter_name": name,
        "blocked_raw_trades": len(blocked_raw),
        "blocked_raw_net_usd": round(sum(float(row["profit"]) for row in blocked_raw), 2),
        "blocked_raw_win_rate_pct": round(
            100.0 * sum(1 for row in blocked_raw if float(row["profit"]) > 0) / len(blocked_raw), 2
        )
        if blocked_raw
        else 0.0,
    }
    info.update(filter_info)
    return summarize_candidate(
        name,
        selected,
        base_count=len(base_trades),
        guard_stats=guard_stats,
        filter_info=info,
        baseline=baseline,
    )


def single_feature_rows(base_trades: list[dict[str, Any]], baseline: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for feature in FEATURES:
        values = [as_float(row.get(feature)) for row in base_trades]
        for threshold in quantiles(values):
            for op in ("<=", ">="):
                for direction in ("ANY", "LONG", "SHORT"):
                    kept, blocked = apply_feature_filter(
                        base_trades, feature=feature, op=op, threshold=threshold, direction=direction
                    )
                    if len(blocked) < 25:
                        continue
                    rows.append(
                        evaluate_filtered(
                            base_trades,
                            name=f"block_{direction}_{feature}_{op}_{threshold}",
                            kept_raw=kept,
                            blocked_raw=blocked,
                            filter_info={
                                "filter_type": "single_feature",
                                "feature": feature,
                                "op": op,
                                "threshold": threshold,
                                "direction_filter": direction,
                            },
                            baseline=baseline,
                        )
                    )
    return rows


def category_rows(base_trades: list[dict[str, Any]], baseline: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for field in ("entry_hour", "entry_session", "portfolio_member"):
        values = sorted({row.get(field) for row in base_trades})
        for value in values:
            for direction in (None, "LONG", "SHORT"):
                kept, blocked = block_by_category(base_trades, field=field, value=value, direction=direction)
                if len(blocked) < 25:
                    continue
                direction_label = direction or "ANY"
                rows.append(
                    evaluate_filtered(
                        base_trades,
                        name=f"block_{direction_label}_{field}_{value}",
                        kept_raw=kept,
                        blocked_raw=blocked,
                        filter_info={
                            "filter_type": "category",
                            "category_field": field,
                            "category_value": value,
                            "direction_filter": direction_label,
                        },
                        baseline=baseline,
                    )
                )
    return rows


def combo_rows(base_trades: list[dict[str, Any]], baseline: dict[str, Any], singles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seed = [
        row
        for row in singles
        if row["decision"] in {"RELIABILITY_UPGRADE_REVIEW_CANDIDATE", "REVIEW_TRADEOFF"}
        and row["trades"] >= 1850
        and row["positive_day_pct"] >= baseline["positive_day_pct"]
    ]
    seed = sorted(seed, key=lambda row: -row["score"])[:12]
    rows: list[dict[str, Any]] = []
    for left_index, left in enumerate(seed):
        for right in seed[left_index + 1 :]:
            kept = []
            blocked = []
            for row in base_trades:
                left_block = row_is_blocked_by_summary(row, left)
                right_block = row_is_blocked_by_summary(row, right)
                if left_block or right_block:
                    blocked.append(row)
                else:
                    kept.append(row)
            if len(blocked) < 50:
                continue
            rows.append(
                evaluate_filtered(
                    base_trades,
                    name=f"combo__{left['filter_name']}__{right['filter_name']}",
                    kept_raw=kept,
                    blocked_raw=blocked,
                    filter_info={
                        "filter_type": "combo",
                        "combo_left": left["filter_name"],
                        "combo_right": right["filter_name"],
                    },
                    baseline=baseline,
                )
            )
    return rows


def row_is_blocked_by_summary(row: dict[str, Any], summary: dict[str, Any]) -> bool:
    filter_type = summary.get("filter_type")
    direction_filter = summary.get("direction_filter", "ANY")
    if direction_filter not in ("", "ANY") and row.get("direction") != direction_filter:
        return False
    if filter_type == "single_feature":
        value = as_float(row.get(summary.get("feature")))
        if math.isnan(value):
            return False
        threshold = float(summary["threshold"])
        return value <= threshold if summary["op"] == "<=" else value >= threshold
    if filter_type == "category":
        return row.get(summary.get("category_field")) == summary.get("category_value")
    return False


def compact(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "filter_name",
        "decision",
        "score",
        "filter_type",
        "feature",
        "op",
        "threshold",
        "category_field",
        "category_value",
        "direction_filter",
        "combo_left",
        "combo_right",
        "blocked_raw_trades",
        "blocked_raw_net_usd",
        "blocked_raw_win_rate_pct",
        "trades",
        "win_rate_pct",
        "net_usd",
        "profit_factor",
        "active_days",
        "trades_per_active_day",
        "three_plus_trade_day_pct",
        "positive_day_pct",
        "delta_positive_day_pct",
        "delta_net_usd",
        "delta_profit_factor",
        "delta_win_rate_pct",
        "top100_removed_usd",
        "delta_top100_removed_usd",
        "max_closed_drawdown_usd",
        "delta_drawdown_usd",
        "older_net_usd",
        "older_profit_factor",
        "newer_net_usd",
        "newer_profit_factor",
        "positive_months",
        "negative_months",
        "worst_month_usd",
        "trade_cap_days",
        "cooldown_skipped_trades",
        "retention_pct",
    ]
    return {key: row.get(key) for key in keys}


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    fields = list(compact(rows[0]).keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(compact(row))


def render(rows: list[dict[str, Any]], baseline: dict[str, Any], output_json: Path, output_csv: Path) -> str:
    review = [row for row in rows if row["decision"] == "RELIABILITY_UPGRADE_REVIEW_CANDIDATE"]
    tradeoffs = [row for row in rows if row["decision"] == "REVIEW_TRADEOFF"]
    top = (review or tradeoffs or rows)[:25]
    lines = [
        "# A1 XAU M5 Momentum Feature-Band Reliability Residual Search - 2026-07-02",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Scope: offline exact MT5 Strategy Tester trade CSV and signal-log analysis only. No MT5 runtime, charts, presets, orders, or positions were changed.",
        "",
        "## Baseline",
        "",
        "Baseline is the current frequent daily-reliability package: +50 USD target, max 6 package trades/day, and 15-minute package cooldown after any package loss.",
        "",
        f"`{baseline['trades']}` trades / WR `{baseline['win_rate_pct']}%` / PF `{baseline['profit_factor']}` / net `{baseline['net_usd']}` / `{baseline['trades_per_active_day']}` trades per active day / `{baseline['positive_day_pct']}%` positive active days.",
        "",
        "## Top Residual Rules",
        "",
        "| Rank | Decision | Filter | Blocked | Blocked net | Trades | WR % | Net | PF | T/active | 3+ day % | Pos day % | Delta pos day | Top100 | DD | Older PF/net | Newer PF/net |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(top, 1):
        lines.append(
            "| {rank} | `{decision}` | `{filter_name}` | {blocked} | {blocked_net:.2f} | {trades} | {wr:.2f} | {net:.2f} | {pf} | {tpa:.2f} | {three:.2f} | {pos:.2f} | {dpos:.2f} | {top100:.2f} | {dd:.2f} | {opf:.2f} / {onet:.2f} | {npf:.2f} / {nnet:.2f} |".format(
                rank=index,
                decision=row["decision"],
                filter_name=row["filter_name"],
                blocked=row["blocked_raw_trades"],
                blocked_net=row["blocked_raw_net_usd"],
                trades=row["trades"],
                wr=row["win_rate_pct"],
                net=row["net_usd"],
                pf=row["profit_factor"],
                tpa=row["trades_per_active_day"],
                three=row["three_plus_trade_day_pct"],
                pos=row["positive_day_pct"],
                dpos=row["delta_positive_day_pct"],
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
            "- `RELIABILITY_UPGRADE_REVIEW_CANDIDATE` requires at least 1800 trades, at least 3 trades per active day, at least 50% 3+ trade active days, positive split net, and a positive-day improvement versus the current daily-reliability baseline.",
            "- `REVIEW_TRADEOFF` means the rule may improve some quality metrics but does not clearly improve the daily-reliability target enough to replace the baseline.",
            "- This is a residual search over an already-selected candidate. Any winner must be treated as a new review candidate, not as proof.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{output_json}`",
            f"- CSV: `{output_csv}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    base_trades = enrich_base_trades()
    baseline_selected, baseline_guard = apply_reliability_guard(base_trades)
    baseline = summarize_candidate(
        "daily_reliability_baseline",
        baseline_selected,
        base_count=len(base_trades),
        guard_stats=baseline_guard,
        filter_info={"filter_name": "none", "filter_type": "baseline", "blocked_raw_trades": 0},
    )

    singles = single_feature_rows(base_trades, baseline)
    categories = category_rows(base_trades, baseline)
    combos = combo_rows(base_trades, baseline, singles + categories)
    rows = singles + categories + combos
    decision_rank = {
        "RELIABILITY_UPGRADE_REVIEW_CANDIDATE": 0,
        "REVIEW_TRADEOFF": 1,
    }
    rows.sort(key=lambda row: (decision_rank.get(row["decision"], 9), -row["score"]))

    payload = {
        "status": "FEATURE_BAND_RELIABILITY_RESIDUAL_SEARCH_COMPLETE",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "baseline": compact(baseline),
        "best": compact(rows[0]) if rows else {},
        "review_candidates": [
            compact(row) for row in rows if row["decision"] == "RELIABILITY_UPGRADE_REVIEW_CANDIDATE"
        ],
        "top_rows": [compact(row) for row in rows[:50]],
    }
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    write_csv(rows, output_csv)
    output_md.write_text(render(rows, baseline, output_json, output_csv), encoding="utf-8")
    print(output_md)
    print(json.dumps({"status": payload["status"], "best": payload["best"]}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
