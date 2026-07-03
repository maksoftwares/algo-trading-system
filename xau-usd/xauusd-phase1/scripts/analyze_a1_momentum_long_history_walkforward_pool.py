from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from analyze_a1_momentum_feature_loss_clusters import FEATURES, load_signal_features, source_variants
from analyze_a1_momentum_risk_normalized_component_stress import REPO_ROOT, REPORTS_DIR, dedupe, profit_factor


OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_LONG_HISTORY_WALKFORWARD_POOL_2026_07_03"

TEST_PERIODS = (
    (datetime(2023, 1, 1), datetime(2023, 4, 1)),
    (datetime(2023, 4, 1), datetime(2023, 7, 1)),
    (datetime(2023, 7, 1), datetime(2023, 10, 1)),
    (datetime(2023, 10, 1), datetime(2024, 1, 1)),
    (datetime(2024, 1, 1), datetime(2024, 4, 1)),
    (datetime(2024, 4, 1), datetime(2024, 7, 1)),
    (datetime(2024, 7, 1), datetime(2024, 10, 1)),
    (datetime(2024, 10, 1), datetime(2025, 1, 1)),
    (datetime(2025, 1, 1), datetime(2025, 4, 1)),
    (datetime(2025, 4, 1), datetime(2025, 7, 1)),
    (datetime(2025, 7, 1), datetime(2025, 10, 1)),
    (datetime(2025, 10, 1), datetime(2026, 1, 1)),
    (datetime(2026, 1, 1), datetime(2026, 4, 1)),
    (datetime(2026, 4, 1), datetime(2026, 7, 1)),
)

CATEGORICAL_FEATURES = ("variant", "direction", "entry_session", "entry_hour")
MAX_VARIANTS = 12


@dataclass(frozen=True)
class Config:
    name: str
    numeric_features: tuple[str, ...]
    bins: int
    shrink: float
    keep_quantile: float
    min_bucket_count: int


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def as_float(value: Any, default: float = math.nan) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def market_days(start: date, end: date) -> int:
    days = 0
    current = start
    while current <= end:
        if current.weekday() < 5:
            days += 1
        current += timedelta(days=1)
    return days


def max_drawdown(values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    drawdown = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return round(drawdown, 2)


def top_removed(values: list[float], count: int) -> float:
    wins = sorted((value for value in values if value > 0), reverse=True)
    return round(sum(values) - sum(wins[:count]), 2)


def rolling_stats(rows: list[dict[str, Any]], window: int) -> dict[str, Any]:
    values = [row["profit"] for row in sorted(rows, key=lambda item: (item["exit_time"], item["entry_time"], item["variant"]))]
    if len(values) < window:
        return {"window": window, "available": False}
    nets = [sum(values[index : index + window]) for index in range(0, len(values) - window + 1)]
    return {
        "window": window,
        "available": True,
        "count": len(nets),
        "worst_net": round(min(nets), 2),
        "negative_windows": sum(value < 0 for value in nets),
    }


def summarize(name: str, rows: list[dict[str, Any]], duplicate_drops: int = 0) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda item: (item["exit_time"], item["entry_time"], item["variant"]))
    values = [float(row["profit"]) for row in ordered]
    if not ordered:
        return {"name": name, "trades": 0}
    start = min(row["entry_time"].date() for row in ordered)
    end = max(row["entry_time"].date() for row in ordered)
    market_day_count = market_days(start, end)
    by_day: dict[date, list[float]] = defaultdict(list)
    by_half: dict[str, list[float]] = defaultdict(list)
    by_variant: dict[str, list[float]] = defaultdict(list)
    for row in ordered:
        day = row["entry_time"].date()
        by_day[day].append(float(row["profit"]))
        half = "H1" if row["entry_time"].month <= 6 else "H2"
        by_half[f"{row['entry_time'].year}-{half}"].append(float(row["profit"]))
        by_variant[str(row["variant"])].append(float(row["profit"]))
    wins = sum(value > 0 for value in values)
    return {
        "name": name,
        "trades": len(values),
        "wins": wins,
        "losses": sum(value < 0 for value in values),
        "win_rate_pct": round(100.0 * wins / len(values), 2),
        "profit_factor": profit_factor(values),
        "net_usd": round(sum(values), 2),
        "max_closed_drawdown_usd": max_drawdown(values),
        "duplicate_drops": duplicate_drops,
        "date_start": start.isoformat(),
        "date_end": end.isoformat(),
        "market_days": market_day_count,
        "active_days": len(by_day),
        "trades_per_market_day": round(len(values) / market_day_count, 2),
        "active_market_day_pct": round(100.0 * len(by_day) / market_day_count, 2),
        "three_plus_market_day_pct": round(100.0 * sum(len(day_values) >= 3 for day_values in by_day.values()) / market_day_count, 2),
        "positive_active_day_pct": round(100.0 * sum(sum(day_values) > 0 for day_values in by_day.values()) / len(by_day), 2),
        "top50_removed_usd": top_removed(values, 50),
        "top100_removed_usd": top_removed(values, 100),
        "top200_removed_usd": top_removed(values, 200),
        "top300_removed_usd": top_removed(values, 300),
        "rolling100": rolling_stats(ordered, 100),
        "rolling250": rolling_stats(ordered, 250),
        "half_year": {
            key: {"trades": len(period_values), "net_usd": round(sum(period_values), 2), "profit_factor": profit_factor(period_values)}
            for key, period_values in sorted(by_half.items())
        },
        "top_variants": [
            {"variant": key, "trades": len(period_values), "net_usd": round(sum(period_values), 2)}
            for key, period_values in sorted(by_variant.items(), key=lambda item: -abs(sum(item[1])))[:10]
        ],
    }


def variant_score(item: dict[str, Any]) -> float:
    summary = item.get("summary", {})
    return (
        float(summary.get("profit_factor") or 0.0) * 1000.0
        + float(summary.get("net_usd") or 0.0) * 0.25
        + float(summary.get("trades") or 0.0) * 0.05
        + float(summary.get("active_days") or 0.0) * 0.25
    )


def selected_variants() -> dict[str, dict[str, Any]]:
    variants = source_variants()
    ranked = sorted(variants.items(), key=lambda item: -variant_score(item[1]))
    return dict(ranked[:MAX_VARIANTS])


def raw_enriched_rows(variants: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in variants.values():
        for row in item["trades"]:
            copied = dict(row)
            copied["volume"] = copied.get("volume", 0.01)
            rows.append(copied)
    signal_features = load_signal_features(variants, rows)
    enriched: list[dict[str, Any]] = []
    for row in rows:
        copied = dict(row)
        key = (row["variant"], row["entry_time"].strftime("%Y.%m.%d %H:%M:%S"), row["direction"])
        copied.update(signal_features.get(key, {}))
        copied["entry_hour"] = int(copied.get("entry_hour") or copied["entry_time"].hour)
        enriched.append(copied)
    return enriched


def quantile_edges(values: list[float], bins: int) -> list[float]:
    clean = sorted(value for value in values if not math.isnan(value))
    if len(clean) < 100:
        return []
    edges: list[float] = []
    for index in range(1, bins):
        pos = max(0, min(len(clean) - 1, round((len(clean) - 1) * index / bins)))
        edges.append(clean[pos])
    return sorted(set(edges))


def numeric_bucket(value: float, edges: list[float]) -> str | None:
    if math.isnan(value):
        return None
    bucket = 0
    for edge in edges:
        if value > edge:
            bucket += 1
    return str(bucket)


def bucket_key(row: dict[str, Any], feature: str, edges: dict[str, list[float]]) -> tuple[str, str] | None:
    if feature in CATEGORICAL_FEATURES:
        return feature, str(row.get(feature, ""))
    bucket = numeric_bucket(as_float(row.get(feature)), edges.get(feature, []))
    return (feature, bucket) if bucket is not None else None


def config_grid() -> list[Config]:
    families = (
        ("execution", ("spread_points", "estimated_cost_r", "against_wick_points", "against_wick_body_ratio")),
        (
            "shape",
            (
                "body_fraction",
                "close_location",
                "three_bar_move_atr",
                "break_distance_atr",
                "close_to_recent_extreme",
                "against_wick_body_ratio",
            ),
        ),
        ("full", FEATURES),
    )
    return [
        Config(
            name=f"{name}_bins{bins}_shrink{int(shrink)}_keep{int(keep * 100)}",
            numeric_features=features,
            bins=bins,
            shrink=shrink,
            keep_quantile=keep,
            min_bucket_count=min_count,
        )
        for name, features in families
        for bins in (4,)
        for shrink in (60.0,)
        for min_count in (50,)
        for keep in (0.0, 0.15, 0.30, 0.45, 0.60)
    ]


def train_model(rows: list[dict[str, Any]], config: Config) -> dict[str, Any]:
    edges = {
        feature: quantile_edges([as_float(row.get(feature)) for row in rows], config.bins)
        for feature in config.numeric_features
    }
    features = CATEGORICAL_FEATURES + config.numeric_features
    overall_mean = sum(float(row["profit"]) for row in rows) / len(rows)
    stats: dict[tuple[str, str], dict[str, float]] = {}
    for feature in features:
        grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
        for row in rows:
            key = bucket_key(row, feature, edges)
            if key is not None:
                grouped[key].append(float(row["profit"]))
        for key, values in grouped.items():
            count = len(values)
            mean = sum(values) / count
            shrink_weight = count / (count + config.shrink)
            stats[key] = {
                "count": float(count),
                "edge": (shrink_weight * mean + (1.0 - shrink_weight) * overall_mean)
                if count >= config.min_bucket_count
                else overall_mean,
            }
    return {"edges": edges, "features": features, "stats": stats, "overall_mean": overall_mean}


def score_row(row: dict[str, Any], model: dict[str, Any]) -> float:
    scores: list[float] = []
    for feature in model["features"]:
        key = bucket_key(row, feature, model["edges"])
        if key is not None:
            scores.append(float(model["stats"].get(key, {}).get("edge", model["overall_mean"])))
    return sum(scores) / len(scores) if scores else float(model["overall_mean"])


def threshold(train: list[dict[str, Any]], model: dict[str, Any], keep_quantile: float) -> float:
    scores = sorted(score_row(row, model) for row in train)
    if not scores:
        return -math.inf
    pos = max(0, min(len(scores) - 1, round((len(scores) - 1) * keep_quantile)))
    return scores[pos]


def walkforward(raw: list[dict[str, Any]], config: Config) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected: list[dict[str, Any]] = []
    scored: list[dict[str, Any]] = []
    for start, end in TEST_PERIODS:
        train = [row for row in raw if row["entry_time"] < start]
        test = [row for row in raw if start <= row["entry_time"] < end]
        if len(train) < 500 or not test:
            continue
        model = train_model(train, config)
        limit = threshold(train, model, config.keep_quantile)
        for row in test:
            value = score_row(row, model)
            copied = dict(row)
            copied["wf_period"] = f"{start.date()}_{end.date()}"
            copied["wf_score"] = round(value, 6)
            copied["wf_threshold"] = round(limit, 6)
            copied["wf_decision"] = "keep" if value >= limit else "skip"
            scored.append(copied)
            if value >= limit:
                selected.append(copied)
    return selected, scored


def decision(row: dict[str, Any]) -> str:
    if row.get("trades", 0) < 2200:
        return "FAIL_SAMPLE"
    if row["trades_per_market_day"] < 3.0:
        return "FAIL_CADENCE"
    if row["win_rate_pct"] < 60.0:
        return "FAIL_WIN_RATE"
    if (row["profit_factor"] or 0.0) < 1.30:
        return "FAIL_PF"
    if row["top200_removed_usd"] <= 0:
        return "FAIL_TOP200"
    if row["top300_removed_usd"] <= 0:
        return "FAIL_TOP300"
    if row["rolling250"].get("negative_windows", 1) > 0:
        return "REVISE_ROLLING250"
    return "LONG_HISTORY_WALKFORWARD_REVIEW_CANDIDATE"


def rank_score(row: dict[str, Any]) -> float:
    return round(
        float(row.get("profit_factor") or 0.0) * 1000.0
        + float(row.get("win_rate_pct") or 0.0) * 10.0
        + float(row.get("trades_per_market_day") or 0.0) * 200.0
        + float(row.get("top200_removed_usd") or 0.0) * 0.2
        + float(row.get("top300_removed_usd") or 0.0) * 0.2
        - float(row.get("rolling250", {}).get("negative_windows", 0)) * 10.0,
        2,
    )


def evaluate(raw: list[dict[str, Any]], config: Config) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    selected, scored = walkforward(raw, config)
    deduped, drops = dedupe(selected)
    summary = summarize(config.name, deduped, drops)
    summary["decision"] = decision(summary)
    summary["score"] = rank_score(summary)
    summary["raw_selected"] = len(selected)
    summary["raw_scored"] = len(scored)
    summary["config"] = {
        "name": config.name,
        "numeric_features": config.numeric_features,
        "categorical_features": CATEGORICAL_FEATURES,
        "bins": config.bins,
        "shrink": config.shrink,
        "keep_quantile": config.keep_quantile,
        "min_bucket_count": config.min_bucket_count,
    }
    return summary, scored


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def render(payload: dict[str, Any]) -> str:
    baseline = payload["baseline"]
    best = payload["best_result"]
    lines = [
        "# A1 XAU M5 Momentum Long-History Walk-Forward Pool - 2026-07-03",
        "",
        "Scope: offline analysis only. It uses four-year exact MT5 trade/signal exports and tests future quarters with models trained only on older data. No MT5 runtime was touched.",
        "",
        "## Baseline Pool",
        "",
        "| Field | Value |",
        "|---|---:|",
        f"| Variants | {payload['variant_count']} |",
        f"| Raw rows | {payload['raw_rows']} |",
        f"| Deduped trades | {baseline['trades']} |",
        f"| Win rate | {baseline['win_rate_pct']}% |",
        f"| Profit factor | {baseline['profit_factor']} |",
        f"| Net USD | {baseline['net_usd']} |",
        f"| Trades / market day | {baseline['trades_per_market_day']} |",
        f"| Top300 removed USD | {baseline['top300_removed_usd']} |",
        f"| Rolling250 negative windows | {baseline['rolling250'].get('negative_windows')} |",
        "",
        "## Best Model",
        "",
        "| Field | Value |",
        "|---|---:|",
        f"| Decision | `{best.get('decision')}` |",
        f"| Config | `{best.get('name')}` |",
        f"| Trades | {best.get('trades')} |",
        f"| Win rate | {best.get('win_rate_pct')}% |",
        f"| Profit factor | {best.get('profit_factor')} |",
        f"| Net USD | {best.get('net_usd')} |",
        f"| Trades / market day | {best.get('trades_per_market_day')} |",
        f"| Top200 removed USD | {best.get('top200_removed_usd')} |",
        f"| Top300 removed USD | {best.get('top300_removed_usd')} |",
        f"| Rolling250 negative windows | {best.get('rolling250', {}).get('negative_windows')} |",
        "",
        "## Top Rows",
        "",
        "| Rank | Decision | Config | Trades | WR | PF | Net | T/market day | Top300 | Roll250 neg |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(payload["top_results"][:25], start=1):
        lines.append(
            "| {rank} | `{decision}` | `{name}` | {trades} | {wr:.2f}% | {pf} | {net:.2f} | {tmd:.2f} | {top300:.2f} | {roll} |".format(
                rank=index,
                decision=row.get("decision"),
                name=row.get("name"),
                trades=row.get("trades"),
                wr=row.get("win_rate_pct", 0.0),
                pf=row.get("profit_factor"),
                net=row.get("net_usd", 0.0),
                tmd=row.get("trades_per_market_day", 0.0),
                top300=row.get("top300_removed_usd", 0.0),
                roll=row.get("rolling250", {}).get("negative_windows"),
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Verdict: `{payload['verdict']}`",
            f"- Next action: `{payload['next_action']}`",
            "",
            "If this still cannot clear robustness, the current momentum-family pool is not enough by itself and the next candidate must add a truly different source of trades.",
            "",
            "## Artifacts",
            "",
            f"- Report: `{payload['report']}`",
            f"- JSON: `{payload['json']}`",
            f"- CSV: `{payload['csv']}`",
            f"- Best scored rows CSV: `{payload['best_scored_csv']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    variants = selected_variants()
    raw = raw_enriched_rows(variants)
    baseline_raw = [row for row in raw if TEST_PERIODS[0][0] <= row["entry_time"] < TEST_PERIODS[-1][1]]
    baseline_deduped, baseline_drops = dedupe(baseline_raw)
    baseline = summarize("long_history_pool_oos_baseline_deduped", baseline_deduped, baseline_drops)
    baseline["decision"] = "BASELINE"
    rows: list[dict[str, Any]] = []
    scored_by_name: dict[str, list[dict[str, Any]]] = {}
    for config in config_grid():
        summary, scored = evaluate(raw, config)
        rows.append(summary)
        scored_by_name[config.name] = scored
    rows.sort(
        key=lambda row: (
            row["decision"].startswith("FAIL"),
            row["decision"].startswith("REVISE"),
            -float(row.get("score") or 0.0),
        )
    )
    best = rows[0]
    verdict = (
        "FOUND_LONG_HISTORY_WALKFORWARD_CANDIDATE"
        if str(best.get("decision", "")).endswith("CANDIDATE")
        else "NO_LONG_HISTORY_WALKFORWARD_CANDIDATE"
    )
    next_action = (
        "freeze_and_review_static_implementation_plan"
        if verdict == "FOUND_LONG_HISTORY_WALKFORWARD_CANDIDATE"
        else "continue_new_non_momentum_entry_research"
    )
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    output_scored = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_SCORED_ROWS.csv"
    payload = {
        "status": "PASS_LONG_HISTORY_WALKFORWARD_READY",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "offline_four_year_exact_mt5_export_walkforward_only_no_runtime_change",
        "test_periods": [(start.date().isoformat(), end.date().isoformat()) for start, end in TEST_PERIODS],
        "variant_count": len(variants),
        "variant_pool": list(variants),
        "raw_rows": len(raw),
        "baseline": baseline,
        "verdict": verdict,
        "next_action": next_action,
        "best_result": best,
        "top_results": rows[:50],
        "report": rel(output_md),
        "json": rel(output_json),
        "csv": rel(output_csv),
        "best_scored_csv": rel(output_scored),
    }
    output_md.write_text(render(payload), encoding="utf-8")
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    write_csv(
        output_csv,
        rows,
        [
            "decision",
            "score",
            "name",
            "trades",
            "win_rate_pct",
            "profit_factor",
            "net_usd",
            "trades_per_market_day",
            "top100_removed_usd",
            "top200_removed_usd",
            "top300_removed_usd",
            "rolling250",
            "raw_selected",
            "duplicate_drops",
        ],
    )
    write_csv(
        output_scored,
        scored_by_name.get(str(best.get("name")), []),
        [
            "wf_period",
            "wf_decision",
            "wf_score",
            "wf_threshold",
            "variant",
            "entry_time",
            "exit_time",
            "direction",
            "profit",
            "entry_session",
            "entry_hour",
            "spread_points",
            "body_fraction",
            "close_location",
            "three_bar_move_atr",
            "break_distance_atr",
            "estimated_cost_r",
            "against_wick_body_ratio",
        ],
    )
    print(output_md)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "verdict": verdict,
                "decision": best.get("decision"),
                "config": best.get("name"),
                "trades": best.get("trades"),
                "win_rate_pct": best.get("win_rate_pct"),
                "profit_factor": best.get("profit_factor"),
                "net_usd": best.get("net_usd"),
                "trades_per_market_day": best.get("trades_per_market_day"),
                "top300_removed_usd": best.get("top300_removed_usd"),
                "rolling250_negative": best.get("rolling250", {}).get("negative_windows"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
