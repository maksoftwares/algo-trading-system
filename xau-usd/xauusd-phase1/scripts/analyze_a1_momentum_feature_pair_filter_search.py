from __future__ import annotations

import csv
import itertools
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_momentum_daily_fit_portfolio_search import daily_metrics, window_summary
from analyze_a1_momentum_daily_guard_search import apply_daily_guard
from analyze_a1_momentum_daily_shape_optimizer import day_tail_stats
from analyze_a1_momentum_deep_portfolio_search import dedupe_trades
from analyze_a1_momentum_feature_loss_clusters import (
    FEATURES,
    as_float,
    enrich_trades,
    load_signal_features,
    quantiles,
    source_variants,
)
from analyze_a1_momentum_feature_loss_daily_guard_optimizer import month_stats, top_removed_usd
from analyze_a1_momentum_feature_loss_portfolio_verdict import LONG_MEMBER
from analyze_a1_momentum_portfolio_combinations import summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"
SPLIT_DATE = datetime(2024, 7, 1)

FEATURE_MEMBER = "v13_feature_loss_short_extreme_rr0p6"
OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_FEATURE_PAIR_FILTER_SEARCH_2026_07_02"


def build_base_trades() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    variants = source_variants()
    missing = [name for name in (LONG_MEMBER, FEATURE_MEMBER) if name not in variants]
    if missing:
        raise SystemExit(f"Missing required MT5-tested variants: {missing}")

    raw: list[dict[str, Any]] = []
    members = [LONG_MEMBER, FEATURE_MEMBER]
    for name in members:
        for row in variants[name]["trades"]:
            copied = dict(row)
            copied["portfolio_member"] = name
            raw.append(copied)

    priority = {name: index for index, name in enumerate(members)}
    deduped = dedupe_trades(raw, priority)
    deduped.sort(key=lambda row: (row["entry_time"], row["exit_time"], row["variant"]))
    features = load_signal_features(variants, deduped)
    enriched = enrich_trades(deduped, features)
    return enriched, {
        "members": members,
        "raw_trades": len(raw),
        "deduped_before_extra_filters": len(deduped),
        "enriched_trades": sum(1 for row in enriched if "estimated_cost_r" in row),
    }


def daily_guard(trades: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    return apply_daily_guard(
        trades,
        profit_target_usd=None,
        loss_stop_usd=-20.0,
        max_trades_per_day=6,
        max_losses_per_day=None,
    )


def daily_shape(trades: list[dict[str, Any]]) -> dict[str, Any]:
    by_day: dict[str, list[float]] = defaultdict(list)
    for row in trades:
        by_day[row["entry_date"]].append(float(row["profit"]))
    active_days = len(by_day)
    positive_days = sum(1 for values in by_day.values() if sum(values) > 0)
    three_plus = sum(1 for values in by_day.values() if len(values) >= 3)
    return {
        "positive_day_pct": round(100.0 * positive_days / active_days, 2) if active_days else 0.0,
        "three_plus_trade_day_pct": round(100.0 * three_plus / active_days, 2) if active_days else 0.0,
        "active_days": active_days,
    }


def evaluate(name: str, pre_guard: list[dict[str, Any]], base_count: int) -> dict[str, Any]:
    selected, guard = daily_guard(pre_guard)
    summary = summarize(name, selected)
    summary.update(daily_metrics(selected))
    summary.update(day_tail_stats(selected))
    summary.update(month_stats(selected))
    summary.update(
        {
            "pre_guard_trades": len(pre_guard),
            "retention_pct": round(100.0 * len(selected) / base_count, 2) if base_count else 0.0,
            "guard": guard,
            "older": window_summary("older", selected, None, SPLIT_DATE),
            "newer": window_summary("newer", selected, SPLIT_DATE, None),
            "top10_removed_usd": top_removed_usd(selected, 10),
            "top25_removed_usd": top_removed_usd(selected, 25),
            "top50_removed_usd": top_removed_usd(selected, 50),
            "top100_removed_usd": top_removed_usd(selected, 100),
        }
    )
    return summary


def candidate_filters(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    filters: list[dict[str, Any]] = []
    seen: set[tuple[str, str, float, str]] = set()
    for feature in FEATURES:
        values = [as_float(row.get(feature)) for row in trades]
        for threshold in quantiles(values):
            for op in ("<=", ">="):
                for direction in ("ANY", "LONG", "SHORT"):
                    key = (feature, op, threshold, direction)
                    if key in seen:
                        continue
                    seen.add(key)
                    filters.append(
                        {
                            "feature": feature,
                            "op": op,
                            "threshold": threshold,
                            "direction_filter": direction,
                        }
                    )
    return filters


def matches_filter(row: dict[str, Any], item: dict[str, Any]) -> bool:
    direction = item["direction_filter"]
    if direction != "ANY" and row.get("direction") != direction:
        return False
    value = as_float(row.get(item["feature"]))
    if math.isnan(value):
        return False
    if item["op"] == "<=":
        return value <= float(item["threshold"])
    return value >= float(item["threshold"])


def apply_filters(trades: list[dict[str, Any]], filters: tuple[dict[str, Any], ...]) -> tuple[list[dict[str, Any]], int]:
    kept: list[dict[str, Any]] = []
    blocked = 0
    for row in trades:
        if any(matches_filter(row, item) for item in filters):
            blocked += 1
        else:
            kept.append(row)
    return kept, blocked


def filter_label(filters: tuple[dict[str, Any], ...]) -> str:
    return " + ".join(
        f"{item['direction_filter']} {item['feature']} {item['op']} {item['threshold']}" for item in filters
    )


def decision(row: dict[str, Any], base: dict[str, Any]) -> str:
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
    if (row["profit_factor"] or 0.0) < 1.30:
        return "FAIL_PROFIT_FACTOR"
    if row["net_usd"] < 1250.0:
        return "FAIL_NET"
    if row["positive_day_pct"] <= base["positive_day_pct"]:
        return "FAIL_NO_DAY_RATE_IMPROVEMENT"
    if row["positive_day_pct"] < 58.0:
        return "REVIEW_DAY_RATE"
    if row["top100_removed_usd"] <= 0:
        return "FAIL_TOP100_ROBUSTNESS"
    if row["older"]["net_usd"] <= 0 or row["newer"]["net_usd"] <= 0:
        return "FAIL_SPLIT_NET"
    if (row["older"]["profit_factor"] or 0.0) < 1.15 or (row["newer"]["profit_factor"] or 0.0) < 1.25:
        return "REVIEW_SPLIT_PF"
    if row["max_closed_drawdown_usd"] > 120:
        return "REVIEW_DRAWDOWN"
    return "FEATURE_PAIR_REVIEW_CANDIDATE"


def score(row: dict[str, Any], base: dict[str, Any]) -> float:
    pf = float(row["profit_factor"] or 0.0)
    split_pf = min(float(row["older"]["profit_factor"] or 0.0), float(row["newer"]["profit_factor"] or 0.0))
    return round(
        pf * 1000.0
        + split_pf * 550.0
        + float(row["win_rate_pct"]) * 10.0
        + float(row["positive_day_pct"]) * 55.0
        + (float(row["positive_day_pct"]) - float(base["positive_day_pct"])) * 180.0
        + float(row["three_plus_trade_day_pct"]) * 10.0
        + float(row["trades_per_active_day"]) * 130.0
        + float(row["net_usd"]) / max(float(row["max_closed_drawdown_usd"] or 1.0), 1.0) * 125.0
        + float(row["top100_removed_usd"]) / 35.0
        + float(row["retention_pct"]) * 2.0
        - max(0.0, -float(row["worst_month_usd"])) * 0.7,
        2,
    )


def compact(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "decision",
        "score",
        "filter_count",
        "filter_rule",
        "blocked_raw_trades",
        "pre_guard_trades",
        "trades",
        "retention_pct",
        "win_rate_pct",
        "net_usd",
        "profit_factor",
        "active_days",
        "trades_per_active_day",
        "three_plus_trade_day_pct",
        "positive_day_pct",
        "positive_day_delta",
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
        "guard",
    ]
    return {key: row.get(key) for key in keys}


def search(trades: list[dict[str, Any]], *, single_pool_limit: int, pair_limit: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    base = evaluate("feature_loss_daily_guard_optimizer_baseline", trades, len(trades))
    filters = candidate_filters(trades)
    singles: list[dict[str, Any]] = []
    for item in filters:
        kept, blocked = apply_filters(trades, (item,))
        if blocked < 35:
            continue
        row = evaluate(filter_label((item,)), kept, len(trades))
        row.update(
            {
                "filter_count": 1,
                "filters": [item],
                "filter_rule": filter_label((item,)),
                "blocked_raw_trades": blocked,
                "positive_day_delta": round(row["positive_day_pct"] - base["positive_day_pct"], 2),
            }
        )
        row["decision"] = decision(row, base)
        row["score"] = score(row, base)
        singles.append(row)

    singles.sort(key=lambda row: (row["decision"] == "FEATURE_PAIR_REVIEW_CANDIDATE", row["score"]), reverse=True)
    pool = singles[:single_pool_limit]
    pairs: list[dict[str, Any]] = []
    for left, right in itertools.combinations(pool, 2):
        left_filter = left["filters"][0]
        right_filter = right["filters"][0]
        if left_filter == right_filter:
            continue
        kept, blocked = apply_filters(trades, (left_filter, right_filter))
        if blocked < 60:
            continue
        row = evaluate(filter_label((left_filter, right_filter)), kept, len(trades))
        row.update(
            {
                "filter_count": 2,
                "filters": [left_filter, right_filter],
                "filter_rule": filter_label((left_filter, right_filter)),
                "blocked_raw_trades": blocked,
                "positive_day_delta": round(row["positive_day_pct"] - base["positive_day_pct"], 2),
            }
        )
        row["decision"] = decision(row, base)
        row["score"] = score(row, base)
        pairs.append(row)
        if len(pairs) >= pair_limit:
            break

    rows = singles + pairs
    preferred = {"FEATURE_PAIR_REVIEW_CANDIDATE": 0, "REVIEW_DAY_RATE": 1, "REVIEW_SPLIT_PF": 2, "REVIEW_DRAWDOWN": 3}
    rows.sort(key=lambda row: (preferred.get(row["decision"], 9), -row["score"]))
    return base, rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(compact(rows[0]).keys()) if rows else []
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(compact(row))


def render_markdown(base: dict[str, Any], rows: list[dict[str, Any]], payload: dict[str, Any]) -> str:
    review = [row for row in rows if row["decision"] == "FEATURE_PAIR_REVIEW_CANDIDATE"]
    top = review[:20] if review else rows[:25]
    lines = [
        "# A1 XAU M5 Momentum Feature Pair Filter Search",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "Scope: offline exact MT5 Strategy Tester trade/signal CSV analysis only. No MT5 runtime, charts, presets, orders, or positions were changed.",
        "",
        "## Purpose",
        "",
        "The owner rejected sparse strategies. This search keeps the current frequent feature-loss portfolio fixed, then tests whether one or two additional signal-feature blocks can improve positive active-day rate while preserving at least three trades per active day.",
        "",
        "## Baseline",
        "",
        "| Field | Value |",
        "|---|---:|",
        f"| Trades | {base['trades']} |",
        f"| Win rate | {base['win_rate_pct']}% |",
        f"| Net USD | {base['net_usd']} |",
        f"| Profit factor | {base['profit_factor']} |",
        f"| Active days | {base['active_days']} |",
        f"| Trades / active day | {base['trades_per_active_day']} |",
        f"| 3+ trade active days | {base['three_plus_trade_day_pct']}% |",
        f"| Positive active days | {base['positive_day_pct']}% |",
        f"| Positive / negative months | {base['positive_months']} / {base['negative_months']} |",
        f"| Top100 removed | {base['top100_removed_usd']} |",
        "",
        "## Top Search Results",
        "",
        "| Rank | Decision | Filters | Blocked | Trades | WR % | Net | PF | Active | T/active | 3+ day % | Pos day % | Delta | +M/-M | Top100 removed | DD | Older PF/net | Newer PF/net |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(top, 1):
        lines.append(
            "| {rank} | `{decision}` | `{rule}` | {blocked} | {trades} | {wr:.2f} | {net:.2f} | {pf:.2f} | {active} | {tpa:.2f} | {three:.2f} | {pos:.2f} | {delta:.2f} | {pm}/{nm} | {top100:.2f} | {dd:.2f} | {opf:.2f}/{onet:.2f} | {npf:.2f}/{nnet:.2f} |".format(
                rank=index,
                decision=row["decision"],
                rule=row["filter_rule"],
                blocked=row["blocked_raw_trades"],
                trades=row["trades"],
                wr=row["win_rate_pct"],
                net=row["net_usd"],
                pf=float(row["profit_factor"] or 0.0),
                active=row["active_days"],
                tpa=row["trades_per_active_day"],
                three=row["three_plus_trade_day_pct"],
                pos=row["positive_day_pct"],
                delta=row["positive_day_delta"],
                pm=row["positive_months"],
                nm=row["negative_months"],
                top100=row["top100_removed_usd"],
                dd=row["max_closed_drawdown_usd"],
                opf=float(row["older"]["profit_factor"] or 0.0),
                onet=row["older"]["net_usd"],
                npf=float(row["newer"]["profit_factor"] or 0.0),
                nnet=row["newer"]["net_usd"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
        ]
    )
    if review:
        best = review[0]
        lines.extend(
            [
                "At least one feature-combination candidate crossed the review bar without becoming sparse.",
                "",
                f"Best candidate: `{best['filter_rule']}`.",
                "",
                "This is not a runtime approval. It is a next-review candidate that must be independently checked and then converted into an exact MT5 tester variant before any demo replacement.",
            ]
        )
    else:
        lines.extend(
            [
                "No additional one/two-feature block crossed the full review bar. This means the current feature-loss daily guard candidate remains the best frequent package from this feature set.",
                "",
                "Do not keep pruning this same entry blindly. The next improvement would need a new entry feature, exit/management layer, or a different momentum variant, not just another threshold on the same data.",
            ]
        )
    lines.extend(
        [
            "",
            f"CSV: `{payload['csv_path']}`",
            f"JSON: `{payload['json_path']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    trades, base_info = build_base_trades()
    base, rows = search(trades, single_pool_limit=45, pair_limit=2000)
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "FEATURE_PAIR_FILTER_SEARCH_COMPLETE",
        "boundary": "offline_mt5_tester_trade_signal_csv_analysis_only_no_runtime_change",
        "base_info": base_info,
        "base_summary": compact(base),
        "review_candidate_count": sum(1 for row in rows if row["decision"] == "FEATURE_PAIR_REVIEW_CANDIDATE"),
        "top_rows": [compact(row) for row in rows[:100]],
        "json_path": str(output_json),
        "csv_path": str(output_csv),
    }
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    output_md.write_text(render_markdown(base, rows, payload), encoding="utf-8")
    write_csv(output_csv, rows[:500])
    print(output_md)
    print(json.dumps({"status": payload["status"], "review_candidate_count": payload["review_candidate_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
