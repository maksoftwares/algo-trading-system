from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_momentum_risk_normalized_component_stress import (
    REPO_ROOT,
    REPORTS_DIR,
    dedupe,
    load_variants,
    summarize,
)
from analyze_a1_momentum_risk_normalized_feature_ranker import FEATURES, enrich_rows


OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_WALKFORWARD_FEATURE_MODEL_2026_07_03"

TEST_PERIODS = (
    (datetime(2025, 1, 1), datetime(2025, 4, 1)),
    (datetime(2025, 4, 1), datetime(2025, 7, 1)),
    (datetime(2025, 7, 1), datetime(2025, 10, 1)),
    (datetime(2025, 10, 1), datetime(2026, 1, 1)),
    (datetime(2026, 1, 1), datetime(2026, 4, 1)),
    (datetime(2026, 4, 1), datetime(2026, 7, 1)),
)

CATEGORICAL_FEATURES = ("variant", "direction", "entry_session", "entry_hour")


@dataclass(frozen=True)
class ModelConfig:
    name: str
    numeric_features: tuple[str, ...]
    categorical_features: tuple[str, ...]
    bin_count: int
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


def raw_enriched_rows() -> list[dict[str, Any]]:
    variants = load_variants()
    raw: list[dict[str, Any]] = []
    for rows in variants.values():
        raw.extend(rows)
    enriched = enrich_rows(raw)
    for row in enriched:
        row["entry_hour"] = row["entry_time"].hour
    return enriched


def quantile_edges(values: list[float], bins: int) -> list[float]:
    clean = sorted(value for value in values if not math.isnan(value))
    if len(clean) < 50:
        return []
    edges: list[float] = []
    for index in range(1, bins):
        pct = index / bins
        pos = max(0, min(len(clean) - 1, round((len(clean) - 1) * pct)))
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


def bucket_key(row: dict[str, Any], feature: str, edges_by_feature: dict[str, list[float]]) -> tuple[str, str] | None:
    if feature in CATEGORICAL_FEATURES:
        return feature, str(row.get(feature, ""))
    bucket = numeric_bucket(as_float(row.get(feature)), edges_by_feature.get(feature, []))
    if bucket is None:
        return None
    return feature, bucket


def train_model(rows: list[dict[str, Any]], config: ModelConfig) -> dict[str, Any]:
    numeric_edges = {
        feature: quantile_edges([as_float(row.get(feature)) for row in rows], config.bin_count)
        for feature in config.numeric_features
    }
    features = tuple(config.categorical_features) + tuple(config.numeric_features)
    bucket_stats: dict[tuple[str, str], dict[str, float]] = {}
    overall_mean = sum(float(row["profit"]) for row in rows) / len(rows)
    for feature in features:
        grouped: dict[tuple[str, str], list[float]] = {}
        for row in rows:
            key = bucket_key(row, feature, numeric_edges)
            if key is None:
                continue
            grouped.setdefault(key, []).append(float(row["profit"]))
        for key, profits in grouped.items():
            count = len(profits)
            raw_mean = sum(profits) / count
            shrink_weight = count / (count + config.shrink)
            edge = shrink_weight * raw_mean + (1.0 - shrink_weight) * overall_mean
            bucket_stats[key] = {
                "count": float(count),
                "edge": edge if count >= config.min_bucket_count else overall_mean,
                "raw_mean": raw_mean,
            }
    return {"edges": numeric_edges, "bucket_stats": bucket_stats, "features": features, "overall_mean": overall_mean}


def score_row(row: dict[str, Any], model: dict[str, Any]) -> float:
    values: list[float] = []
    for feature in model["features"]:
        key = bucket_key(row, feature, model["edges"])
        if key is None:
            continue
        values.append(float(model["bucket_stats"].get(key, {}).get("edge", model["overall_mean"])))
    if not values:
        return float(model["overall_mean"])
    return sum(values) / len(values)


def threshold_from_train(rows: list[dict[str, Any]], model: dict[str, Any], keep_quantile: float) -> float:
    scores = sorted(score_row(row, model) for row in rows)
    if not scores:
        return -math.inf
    pos = max(0, min(len(scores) - 1, round((len(scores) - 1) * keep_quantile)))
    return scores[pos]


def config_grid() -> list[ModelConfig]:
    return [
        ModelConfig(
            name=f"{name}_bins{bins}_shrink{int(shrink)}_keep{int(keep * 100)}",
            numeric_features=features,
            categorical_features=CATEGORICAL_FEATURES,
            bin_count=bins,
            shrink=shrink,
            keep_quantile=keep,
            min_bucket_count=min_count,
        )
        for name, features in (
            (
                "execution",
                ("spread_points", "estimated_cost_r", "against_wick_points", "against_wick_body_ratio"),
            ),
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
            (
                "full",
                FEATURES,
            ),
        )
        for bins in (4, 5)
        for shrink in (25.0, 60.0)
        for min_count in (20, 50)
        for keep in (0.0, 0.10, 0.20, 0.30, 0.40)
    ]


def walkforward_rows(raw_rows: list[dict[str, Any]], config: ModelConfig) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected: list[dict[str, Any]] = []
    scored_rows: list[dict[str, Any]] = []
    for start, end in TEST_PERIODS:
        train = [row for row in raw_rows if row["entry_time"] < start]
        test = [row for row in raw_rows if start <= row["entry_time"] < end]
        if len(train) < 200 or not test:
            continue
        model = train_model(train, config)
        threshold = threshold_from_train(train, model, config.keep_quantile)
        for row in test:
            score = score_row(row, model)
            copied = dict(row)
            copied["wf_period"] = f"{start.date()}_{end.date()}"
            copied["wf_score"] = round(score, 6)
            copied["wf_threshold"] = round(threshold, 6)
            copied["wf_decision"] = "keep" if score >= threshold else "skip"
            scored_rows.append(copied)
            if score >= threshold:
                selected.append(copied)
    return selected, scored_rows


def decision(row: dict[str, Any]) -> str:
    if row["trades"] < 900:
        return "FAIL_SAMPLE"
    if row["trades_per_market_day"] < 3.0:
        return "FAIL_CADENCE"
    if row["win_rate_pct"] < 60.0:
        return "FAIL_WIN_RATE"
    if (row["profit_factor"] or 0.0) < 1.30:
        return "FAIL_PF"
    if row["top100_removed_usd"] <= 0:
        return "FAIL_TOP100"
    if row["top200_removed_usd"] <= 0:
        return "FAIL_TOP200"
    if row["rolling100"].get("negative_windows", 0) > 0:
        return "REVISE_ROLLING100"
    return "WALKFORWARD_REVIEW_CANDIDATE"


def score(summary: dict[str, Any]) -> float:
    return round(
        float(summary.get("profit_factor") or 0.0) * 1000.0
        + float(summary.get("win_rate_pct") or 0.0) * 10.0
        + float(summary.get("trades_per_market_day") or 0.0) * 160.0
        + float(summary.get("top100_removed_usd") or 0.0) * 0.25
        + float(summary.get("top200_removed_usd") or 0.0) * 0.25
        - float(summary.get("rolling100", {}).get("negative_windows", 0)) * 8.0,
        2,
    )


def evaluate_config(raw_rows: list[dict[str, Any]], config: ModelConfig) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    selected, scored = walkforward_rows(raw_rows, config)
    deduped, drops = dedupe(selected)
    summary = summarize(config.name, deduped, duplicate_drops=drops)
    summary["decision"] = decision(summary)
    summary["score"] = score(summary)
    summary["raw_selected"] = len(selected)
    summary["raw_scored"] = len(scored)
    summary["config"] = {
        "name": config.name,
        "numeric_features": config.numeric_features,
        "categorical_features": config.categorical_features,
        "bin_count": config.bin_count,
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
        "# A1 XAU M5 Momentum Walk-Forward Feature Model - 2026-07-03",
        "",
        "Scope: offline analysis only. The model trains on prior exact MT5 trade exports and scores later quarters. No MT5 runtime, chart, preset, order, or position was touched.",
        "",
        "## Out-Of-Sample Baseline",
        "",
        "| Field | Value |",
        "|---|---:|",
        f"| Trades | {baseline['trades']} |",
        f"| Win rate | {baseline['win_rate_pct']}% |",
        f"| Profit factor | {baseline['profit_factor']} |",
        f"| Net USD | {baseline['net_usd']} |",
        f"| Trades / market day | {baseline['trades_per_market_day']} |",
        f"| Top100 removed USD | {baseline['top100_removed_usd']} |",
        f"| Top200 removed USD | {baseline['top200_removed_usd']} |",
        f"| Rolling100 negative windows | {baseline['rolling100'].get('negative_windows')} |",
        "",
        "## Best Walk-Forward Model",
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
        f"| Top100 removed USD | {best.get('top100_removed_usd')} |",
        f"| Top200 removed USD | {best.get('top200_removed_usd')} |",
        f"| Rolling100 negative windows | {best.get('rolling100', {}).get('negative_windows')} |",
        "",
        "## Top Rows",
        "",
        "| Rank | Decision | Config | Trades | WR | PF | Net | T/market day | Top200 | Roll100 neg |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(payload["top_results"][:25], start=1):
        lines.append(
            "| {rank} | `{decision}` | `{name}` | {trades} | {wr:.2f}% | {pf} | {net:.2f} | {tmd:.2f} | {top200:.2f} | {roll} |".format(
                rank=index,
                decision=row.get("decision"),
                name=row.get("name"),
                trades=row.get("trades"),
                wr=row.get("win_rate_pct", 0.0),
                pf=row.get("profit_factor"),
                net=row.get("net_usd", 0.0),
                tmd=row.get("trades_per_market_day", 0.0),
                top200=row.get("top200_removed_usd", 0.0),
                roll=row.get("rolling100", {}).get("negative_windows"),
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
            "This report is deliberately stricter than an in-sample feature filter: every kept trade is from a period scored by older data only.",
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
    raw = raw_enriched_rows()
    baseline_raw = [row for row in raw if TEST_PERIODS[0][0] <= row["entry_time"] < TEST_PERIODS[-1][1]]
    baseline_rows, baseline_drops = dedupe(baseline_raw)
    baseline = summarize("oos_baseline_all_components_deduped", baseline_rows, duplicate_drops=baseline_drops)
    baseline["decision"] = "BASELINE"
    rows: list[dict[str, Any]] = []
    scored_by_name: dict[str, list[dict[str, Any]]] = {}
    for config in config_grid():
        summary, scored = evaluate_config(raw, config)
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
        "FOUND_WALKFORWARD_REVIEW_CANDIDATE"
        if str(best.get("decision", "")).endswith("CANDIDATE")
        else "NO_WALKFORWARD_FEATURE_MODEL_CANDIDATE"
    )
    next_action = (
        "port_walkforward_logic_to_static_rule_or_exact_mt5_shadow_test"
        if verdict == "FOUND_WALKFORWARD_REVIEW_CANDIDATE"
        else "continue_new_entry_design_or_longer_history_model"
    )
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    output_scored = REPORTS_DIR / f"{OUTPUT_STEM}_BEST_SCORED_ROWS.csv"
    payload = {
        "status": "PASS_WALKFORWARD_MODEL_READY",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "offline_exact_mt5_export_walkforward_only_no_runtime_change",
        "test_periods": [(start.date().isoformat(), end.date().isoformat()) for start, end in TEST_PERIODS],
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
            "rolling100",
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
                "top200_removed_usd": best.get("top200_removed_usd"),
                "rolling100_negative": best.get("rolling100", {}).get("negative_windows"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
