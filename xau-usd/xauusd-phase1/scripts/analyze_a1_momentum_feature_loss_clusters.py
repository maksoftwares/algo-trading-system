from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_momentum_broad_portfolio_search import is_four_year_report, load_variants
from analyze_a1_momentum_daily_guard_search import apply_daily_guard, load_base_trades
from analyze_a1_momentum_daily_state_guard_search import REPAIRED_BLOCKS, top_removed_usd
from analyze_a1_momentum_portfolio_combinations import summarize


PHASE1_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PHASE1_ROOT / "outputs" / "reports"

FEATURES = (
    "spread_points",
    "atr",
    "body_fraction",
    "close_location",
    "three_bar_move_atr",
    "break_distance_atr",
    "estimated_cost_r",
    "signal_range",
    "recent_range",
    "close_to_recent_extreme",
    "against_wick_points",
    "against_wick_body_ratio",
)


def parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y.%m.%d %H:%M:%S")


def as_float(value: Any, default: float = math.nan) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def source_variants() -> dict[str, dict[str, Any]]:
    reports = sorted(
        path
        for path in REPORTS_DIR.glob("A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_*FOUR_YEAR*.json")
        if is_four_year_report(path)
    )
    return load_variants(reports)


def signal_csv_for_trade_csv(path: Path) -> Path:
    return path.with_name(path.name.replace("_trades.csv", "_signals.csv"))


def wanted_signal_keys(trades: list[dict[str, Any]]) -> dict[str, set[tuple[str, str]]]:
    wanted: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for row in trades:
        wanted[row["variant"]].add((row["entry_time"].strftime("%Y.%m.%d %H:%M:%S"), row["direction"]))
    return wanted


def load_signal_features(variants: dict[str, dict[str, Any]], trades: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, float]]:
    wanted = wanted_signal_keys(trades)
    features: dict[tuple[str, str, str], dict[str, float]] = {}
    for variant, keys in wanted.items():
        item = variants.get(variant)
        if not item:
            continue
        signal_path = signal_csv_for_trade_csv(Path(item["trade_csv"]))
        if not signal_path.exists():
            continue
        with signal_path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            for row in reader:
                if row.get("stage") != "WOULD_SIGNAL":
                    continue
                key = (row.get("timestamp_broker", ""), row.get("direction", ""))
                if key not in keys:
                    continue
                open_ = as_float(row.get("signal_open"))
                high = as_float(row.get("signal_high"))
                low = as_float(row.get("signal_low"))
                close = as_float(row.get("signal_close"))
                recent_high = as_float(row.get("recent_high"))
                recent_low = as_float(row.get("recent_low"))
                direction = row.get("direction", "")
                body = abs(close - open_) if all(not math.isnan(v) for v in (close, open_)) else math.nan
                upper_wick = high - max(open_, close) if all(not math.isnan(v) for v in (high, open_, close)) else math.nan
                lower_wick = min(open_, close) - low if all(not math.isnan(v) for v in (low, open_, close)) else math.nan
                against_wick = upper_wick if direction == "LONG" else lower_wick
                close_to_extreme = (
                    close - recent_high
                    if direction == "LONG"
                    else recent_low - close
                    if direction == "SHORT"
                    else math.nan
                )
                parsed = {
                    "spread_points": as_float(row.get("spread_points")),
                    "atr": as_float(row.get("atr")),
                    "body_fraction": as_float(row.get("body_fraction")),
                    "close_location": as_float(row.get("close_location")),
                    "three_bar_move_atr": as_float(row.get("three_bar_move_atr")),
                    "break_distance_atr": as_float(row.get("break_distance_atr")),
                    "estimated_cost_r": as_float(row.get("estimated_cost_r")),
                    "signal_range": high - low if all(not math.isnan(v) for v in (high, low)) else math.nan,
                    "recent_range": recent_high - recent_low
                    if all(not math.isnan(v) for v in (recent_high, recent_low))
                    else math.nan,
                    "close_to_recent_extreme": close_to_extreme,
                    "against_wick_points": against_wick,
                    "against_wick_body_ratio": against_wick / body if body and body > 0 else math.nan,
                }
                features[(variant, key[0], key[1])] = parsed
    return features


def enrich_trades(trades: list[dict[str, Any]], signal_features: dict[tuple[str, str, str], dict[str, float]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for row in trades:
        copied = dict(row)
        key = (row["variant"], row["entry_time"].strftime("%Y.%m.%d %H:%M:%S"), row["direction"])
        for name, value in signal_features.get(key, {}).items():
            copied[name] = value
        enriched.append(copied)
    return enriched


def quantiles(values: list[float]) -> list[float]:
    clean = sorted(value for value in values if not math.isnan(value))
    if len(clean) < 20:
        return []
    thresholds = []
    for pct in (0.10, 0.15, 0.20, 0.25, 0.30, 0.70, 0.75, 0.80, 0.85, 0.90):
        index = max(0, min(len(clean) - 1, round((len(clean) - 1) * pct)))
        thresholds.append(round(clean[index], 6))
    return sorted(set(thresholds))


def trade_matches(row: dict[str, Any], *, feature: str, op: str, threshold: float, direction: str) -> bool:
    if direction != "ANY" and row.get("direction") != direction:
        return False
    value = as_float(row.get(feature))
    if math.isnan(value):
        return False
    return value <= threshold if op == "<=" else value >= threshold


def apply_feature_filter(
    trades: list[dict[str, Any]], *, feature: str, op: str, threshold: float, direction: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    kept = []
    blocked = []
    for row in trades:
        if trade_matches(row, feature=feature, op=op, threshold=threshold, direction=direction):
            blocked.append(row)
        else:
            kept.append(row)
    return kept, blocked


def with_daily_guard(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    guarded, _stats = apply_daily_guard(
        trades,
        profit_target_usd=None,
        loss_stop_usd=-25.0,
        max_trades_per_day=6,
        max_losses_per_day=None,
    )
    return guarded


def daily_shape(summary: dict[str, Any], trades: list[dict[str, Any]]) -> dict[str, Any]:
    by_day: dict[str, list[float]] = defaultdict(list)
    for row in trades:
        by_day[row["entry_date"]].append(float(row["profit"]))
    active_days = len(by_day)
    positive_days = sum(1 for values in by_day.values() if sum(values) > 0)
    three_plus = sum(1 for values in by_day.values() if len(values) >= 3)
    summary.update(
        {
            "positive_day_pct": round(100.0 * positive_days / active_days, 2) if active_days else 0.0,
            "three_plus_trade_day_pct": round(100.0 * three_plus / active_days, 2) if active_days else 0.0,
            "top100_removed_usd": top_removed_usd(trades, 100),
        }
    )
    return summary


def evaluate(name: str, trades: list[dict[str, Any]]) -> dict[str, Any]:
    summary = summarize(name, trades)
    return daily_shape(summary, trades)


def decision(row: dict[str, Any], base: dict[str, Any]) -> str:
    if row["trades"] < 1800:
        return "FAIL_SAMPLE"
    if row["active_days"] < 540:
        return "FAIL_ACTIVE_DAYS"
    if row["trades_per_active_day"] < 3.0:
        return "FAIL_TRADES_PER_ACTIVE_DAY"
    if row["three_plus_trade_day_pct"] < 55.0:
        return "FAIL_THREE_PLUS_DAY_COVERAGE"
    if row["win_rate_pct"] < 60.0:
        return "FAIL_WIN_RATE"
    if row["profit_factor"] is None or row["profit_factor"] < 1.25:
        return "FAIL_PROFIT_FACTOR"
    if row["net_usd"] < 1100:
        return "FAIL_NET"
    if row["top100_removed_usd"] <= 0:
        return "FAIL_TOP100_ROBUSTNESS"
    if row["positive_day_pct"] <= base["positive_day_pct"]:
        return "FAIL_NO_DAY_RATE_IMPROVEMENT"
    if row["positive_day_pct"] < 57.0:
        return "REVIEW_DAY_RATE"
    return "FEATURE_FILTER_REVIEW_CANDIDATE"


def score(row: dict[str, Any], base: dict[str, Any]) -> float:
    pf = float(row.get("profit_factor") or 0.0)
    return round(
        pf * 900
        + float(row["win_rate_pct"]) * 10
        + float(row["positive_day_pct"]) * 45
        + float(row["three_plus_trade_day_pct"]) * 10
        + float(row["trades_per_active_day"]) * 150
        + (float(row["net_usd"]) / max(float(row["max_closed_drawdown_usd"] or 1), 1)) * 100
        + (float(row["positive_day_pct"]) - float(base["positive_day_pct"])) * 160,
        2,
    )


def filter_candidates(trades: list[dict[str, Any]], base_guarded: list[dict[str, Any]]) -> list[dict[str, Any]]:
    base = evaluate("daily_guard_base", base_guarded)
    rows: list[dict[str, Any]] = []
    for feature in FEATURES:
        values = [as_float(row.get(feature)) for row in trades]
        for threshold in quantiles(values):
            for op in ("<=", ">="):
                for direction in ("ANY", "LONG", "SHORT"):
                    pre_guard, blocked_raw = apply_feature_filter(
                        trades, feature=feature, op=op, threshold=threshold, direction=direction
                    )
                    if len(blocked_raw) < 30:
                        continue
                    guarded = with_daily_guard(pre_guard)
                    row = evaluate(f"block_{direction}_{feature}_{op}_{threshold}", guarded)
                    row.update(
                        {
                            "feature": feature,
                            "op": op,
                            "threshold": threshold,
                            "direction_filter": direction,
                            "blocked_raw_trades": len(blocked_raw),
                            "raw_retention_pct": round(100.0 * len(pre_guard) / len(trades), 2),
                            "guarded_retention_pct": round(100.0 * len(guarded) / len(base_guarded), 2)
                            if base_guarded
                            else 0.0,
                            "positive_day_delta": round(row["positive_day_pct"] - base["positive_day_pct"], 2),
                            "pf_delta": round(float(row.get("profit_factor") or 0.0) - float(base.get("profit_factor") or 0.0), 2),
                            "net_delta": round(float(row["net_usd"]) - float(base["net_usd"]), 2),
                        }
                    )
                    row["decision"] = decision(row, base)
                    row["score"] = score(row, base)
                    rows.append(row)
    preferred = {"FEATURE_FILTER_REVIEW_CANDIDATE": 0, "REVIEW_DAY_RATE": 1}
    rows.sort(key=lambda row: (preferred.get(row["decision"], 9), -row["score"]))
    return rows


def bin_stats(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for feature in FEATURES:
        values = [as_float(row.get(feature)) for row in trades]
        thresholds = quantiles(values)
        if not thresholds:
            continue
        edges = [-math.inf] + thresholds + [math.inf]
        for direction in ("ANY", "LONG", "SHORT"):
            scoped = [row for row in trades if direction == "ANY" or row["direction"] == direction]
            for left, right in zip(edges, edges[1:]):
                bucket = [
                    row
                    for row in scoped
                    if not math.isnan(as_float(row.get(feature))) and left < as_float(row.get(feature)) <= right
                ]
                if len(bucket) < 20:
                    continue
                summary = evaluate(f"{direction}_{feature}_{left}_{right}", bucket)
                rows.append(
                    {
                        "feature": feature,
                        "direction": direction,
                        "min_exclusive": None if left == -math.inf else left,
                        "max_inclusive": None if right == math.inf else right,
                        "trades": summary["trades"],
                        "win_rate_pct": summary["win_rate_pct"],
                        "net_usd": summary["net_usd"],
                        "profit_factor": summary["profit_factor"],
                        "positive_day_pct": summary["positive_day_pct"],
                    }
                )
    rows.sort(key=lambda row: (row["net_usd"], row["profit_factor"] or 0))
    return rows


def compact_filter(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "decision",
        "score",
        "feature",
        "op",
        "threshold",
        "direction_filter",
        "blocked_raw_trades",
        "raw_retention_pct",
        "guarded_retention_pct",
        "trades",
        "win_rate_pct",
        "net_usd",
        "profit_factor",
        "active_days",
        "trades_per_active_day",
        "three_plus_trade_day_pct",
        "positive_day_pct",
        "positive_day_delta",
        "pf_delta",
        "net_delta",
        "top100_removed_usd",
        "max_closed_drawdown_usd",
    ]
    return {key: row.get(key) for key in keys}


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def render_markdown(
    base_raw: dict[str, Any],
    base_guarded: dict[str, Any],
    filters: list[dict[str, Any]],
    bins: list[dict[str, Any]],
    output_json: Path,
    filter_csv: Path,
    bin_csv: Path,
) -> str:
    top = filters[:25]
    worst_bins = bins[:20]
    lines = [
        "# A1 XAU M5 Momentum Feature Loss-Cluster Analysis",
        "",
        "Generated: 2026-07-02",
        "",
        "Scope: offline MT5 tester trade/signal CSV analysis only. No MT5 runtime, charts, presets, orders, or positions were changed.",
        "",
        "## Purpose",
        "",
        "The sparse pocket path failed the owner's trade-frequency requirement, and daily-state pruning did not solve the positive-day problem. This report joins the frequent daily-guard candidate back to MT5 signal features and checks whether a measurable setup feature can block losing trades while preserving cadence.",
        "",
        "## Baselines",
        "",
        "| Baseline | Trades | WR % | Net | PF | Active days | T/active | 3+ day % | Pos day % | Top100 removed |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        "| Repaired raw before daily guard | {trades} | {wr:.2f} | {net:.2f} | {pf:.2f} | {active} | {tpa:.2f} | {three:.2f} | {pos:.2f} | {top100:.2f} |".format(
            trades=base_raw["trades"],
            wr=base_raw["win_rate_pct"],
            net=base_raw["net_usd"],
            pf=float(base_raw["profit_factor"] or 0),
            active=base_raw["active_days"],
            tpa=base_raw["trades_per_active_day"],
            three=base_raw["three_plus_trade_day_pct"],
            pos=base_raw["positive_day_pct"],
            top100=base_raw["top100_removed_usd"],
        ),
        "| Repaired daily guard | {trades} | {wr:.2f} | {net:.2f} | {pf:.2f} | {active} | {tpa:.2f} | {three:.2f} | {pos:.2f} | {top100:.2f} |".format(
            trades=base_guarded["trades"],
            wr=base_guarded["win_rate_pct"],
            net=base_guarded["net_usd"],
            pf=float(base_guarded["profit_factor"] or 0),
            active=base_guarded["active_days"],
            tpa=base_guarded["trades_per_active_day"],
            three=base_guarded["three_plus_trade_day_pct"],
            pos=base_guarded["positive_day_pct"],
            top100=base_guarded["top100_removed_usd"],
        ),
        "",
        "## Best Single Feature Filters",
        "",
        "| Rank | Decision | Block rule | Raw blocked | Guarded trades | WR % | Net | PF | Active | T/active | 3+ day % | Pos day % | Delta day % | Top100 removed |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(top, 1):
        rule = f"{row['direction_filter']} {row['feature']} {row['op']} {row['threshold']}"
        lines.append(
            "| {rank} | `{decision}` | `{rule}` | {blocked} | {trades} | {wr:.2f} | {net:.2f} | {pf:.2f} | {active} | {tpa:.2f} | {three:.2f} | {pos:.2f} | {delta:.2f} | {top100:.2f} |".format(
                rank=index,
                decision=row["decision"],
                rule=rule,
                blocked=row["blocked_raw_trades"],
                trades=row["trades"],
                wr=row["win_rate_pct"],
                net=row["net_usd"],
                pf=float(row["profit_factor"] or 0),
                active=row["active_days"],
                tpa=row["trades_per_active_day"],
                three=row["three_plus_trade_day_pct"],
                pos=row["positive_day_pct"],
                delta=row["positive_day_delta"],
                top100=row["top100_removed_usd"],
            )
        )
    lines.extend(
        [
            "",
            "## Worst Feature Buckets",
            "",
            "| Rank | Feature | Direction | Range | Trades | WR % | Net | PF | Pos day % |",
            "|---:|---|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for index, row in enumerate(worst_bins, 1):
        range_label = f"({row['min_exclusive']}, {row['max_inclusive']}]"
        lines.append(
            "| {rank} | `{feature}` | `{direction}` | `{range}` | {trades} | {wr:.2f} | {net:.2f} | {pf:.2f} | {pos:.2f} |".format(
                rank=index,
                feature=row["feature"],
                direction=row["direction"],
                range=range_label,
                trades=row["trades"],
                wr=row["win_rate_pct"],
                net=row["net_usd"],
                pf=float(row["profit_factor"] or 0),
                pos=row["positive_day_pct"],
            )
        )
    review = [row for row in filters if row["decision"] == "FEATURE_FILTER_REVIEW_CANDIDATE"]
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "At least one single-feature filter reached the review bar."
                if review
                else "No single-feature filter crossed the full review bar. The useful output is the ranked list of bad setup buckets; any runtime change should be a newly pre-registered entry rule, not a quick threshold tweak."
            ),
            "",
            f"Machine-readable output: `{output_json}`",
            f"Filter CSV: `{filter_csv}`",
            f"Feature-bin CSV: `{bin_csv}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool-limit", type=int, default=35)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_LOSS_CLUSTERS_2026_07_02.json",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_LOSS_CLUSTERS_2026_07_02.md",
    )
    parser.add_argument(
        "--filter-csv",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_LOSS_FILTERS_2026_07_02.csv",
    )
    parser.add_argument(
        "--bin-csv",
        type=Path,
        default=REPORTS_DIR / "A1_XAU_M5_MOMENTUM_FEATURE_LOSS_BINS_2026_07_02.csv",
    )
    args = parser.parse_args()

    variants = source_variants()
    raw_trades, _priority = load_base_trades(args.pool_limit, REPAIRED_BLOCKS)
    signal_features = load_signal_features(variants, raw_trades)
    enriched_raw = enrich_trades(raw_trades, signal_features)
    enriched_count = sum(1 for row in enriched_raw if "estimated_cost_r" in row)
    base_guarded = with_daily_guard(enriched_raw)
    base_raw_summary = evaluate("repaired_raw_before_daily_guard", enriched_raw)
    base_guarded_summary = evaluate("repaired_daily_guard", base_guarded)
    filters = filter_candidates(enriched_raw, base_guarded)
    bins = bin_stats(base_guarded)

    payload = {
        "status": "FEATURE_LOSS_CLUSTER_ANALYSIS_COMPLETE",
        "boundary": "offline_mt5_tester_trade_signal_csv_analysis_only_no_runtime_change",
        "base": "daily_fit_repair_no_v13_18_22",
        "daily_guard": {"loss_stop_usd": -25.0, "max_trades_per_day": 6, "profit_target_usd": None},
        "raw_trade_count": len(raw_trades),
        "enriched_trade_count": enriched_count,
        "enriched_trade_pct": round(100.0 * enriched_count / len(raw_trades), 2) if raw_trades else 0.0,
        "base_raw_summary": base_raw_summary,
        "base_guarded_summary": base_guarded_summary,
        "top_filters": [compact_filter(row) for row in filters[:100]],
        "worst_bins": bins[:100],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    write_csv(args.filter_csv, [compact_filter(row) for row in filters], list(compact_filter(filters[0]).keys()))
    write_csv(
        args.bin_csv,
        bins,
        [
            "feature",
            "direction",
            "min_exclusive",
            "max_inclusive",
            "trades",
            "win_rate_pct",
            "net_usd",
            "profit_factor",
            "positive_day_pct",
        ],
    )
    args.output_md.write_text(
        render_markdown(
            base_raw_summary,
            base_guarded_summary,
            filters,
            bins,
            args.output_json,
            args.filter_csv,
            args.bin_csv,
        ),
        encoding="utf-8",
    )
    print(args.output_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
