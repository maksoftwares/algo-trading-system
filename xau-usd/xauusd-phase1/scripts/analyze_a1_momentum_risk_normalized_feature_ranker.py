from __future__ import annotations

import csv
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

from analyze_a1_momentum_risk_normalized_component_stress import (
    BACKTEST_DIR,
    PHASE1_ROOT,
    REPO_ROOT,
    REPORTS_DIR,
    dedupe,
    load_variants,
    summarize,
)


OUTPUT_STEM = "A1_XAU_M5_MOMENTUM_RISK_NORMALIZED_FEATURE_RANKER_2026_07_03"

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


def signal_csv_for_variant(variant: str) -> Path | None:
    matches = sorted(BACKTEST_DIR.glob(f"*_XAUUSD_M5_{variant}_signals.csv"))
    return matches[0] if matches else None


def wanted_signal_keys(rows: list[dict[str, Any]]) -> dict[str, set[tuple[str, str]]]:
    wanted: dict[str, set[tuple[str, str]]] = {}
    for row in rows:
        wanted.setdefault(row["variant"], set()).add((row["entry_time"].strftime("%Y.%m.%d %H:%M:%S"), row["direction"]))
    return wanted


def load_signal_features(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, float]]:
    wanted = wanted_signal_keys(rows)
    features: dict[tuple[str, str, str], dict[str, float]] = {}
    for variant, keys in wanted.items():
        signal_path = signal_csv_for_variant(variant)
        if signal_path is None or not signal_path.exists():
            continue
        with signal_path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            for signal in reader:
                if signal.get("stage") != "WOULD_SIGNAL":
                    continue
                key = (signal.get("timestamp_broker", ""), signal.get("direction", ""))
                if key not in keys:
                    continue
                open_ = as_float(signal.get("signal_open"))
                high = as_float(signal.get("signal_high"))
                low = as_float(signal.get("signal_low"))
                close = as_float(signal.get("signal_close"))
                recent_high = as_float(signal.get("recent_high"))
                recent_low = as_float(signal.get("recent_low"))
                direction = signal.get("direction", "")
                body = abs(close - open_) if all(not math.isnan(value) for value in (close, open_)) else math.nan
                upper_wick = high - max(open_, close) if all(not math.isnan(value) for value in (high, open_, close)) else math.nan
                lower_wick = min(open_, close) - low if all(not math.isnan(value) for value in (low, open_, close)) else math.nan
                against_wick = upper_wick if direction == "LONG" else lower_wick
                close_to_extreme = (
                    close - recent_high
                    if direction == "LONG"
                    else recent_low - close
                    if direction == "SHORT"
                    else math.nan
                )
                parsed = {
                    "spread_points": as_float(signal.get("spread_points")),
                    "atr": as_float(signal.get("atr")),
                    "body_fraction": as_float(signal.get("body_fraction")),
                    "close_location": as_float(signal.get("close_location")),
                    "three_bar_move_atr": as_float(signal.get("three_bar_move_atr")),
                    "break_distance_atr": as_float(signal.get("break_distance_atr")),
                    "estimated_cost_r": as_float(signal.get("estimated_cost_r")),
                    "signal_range": high - low if all(not math.isnan(value) for value in (high, low)) else math.nan,
                    "recent_range": recent_high - recent_low
                    if all(not math.isnan(value) for value in (recent_high, recent_low))
                    else math.nan,
                    "close_to_recent_extreme": close_to_extreme,
                    "against_wick_points": against_wick,
                    "against_wick_body_ratio": against_wick / body if body and body > 0 else math.nan,
                }
                features[(variant, key[0], key[1])] = parsed
    return features


def enrich_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    features = load_signal_features(rows)
    enriched: list[dict[str, Any]] = []
    for row in rows:
        copied = dict(row)
        key = (row["variant"], row["entry_time"].strftime("%Y.%m.%d %H:%M:%S"), row["direction"])
        copied.update(features.get(key, {}))
        enriched.append(copied)
    return enriched


def quantiles(values: list[float]) -> list[float]:
    clean = sorted(value for value in values if not math.isnan(value))
    if len(clean) < 50:
        return []
    thresholds = []
    for pct in (0.10, 0.15, 0.20, 0.25, 0.30, 0.70, 0.75, 0.80, 0.85, 0.90):
        index = max(0, min(len(clean) - 1, round((len(clean) - 1) * pct)))
        thresholds.append(round(clean[index], 6))
    return sorted(set(thresholds))


def row_matches(row: dict[str, Any], *, feature: str, op: str, threshold: float, direction: str) -> bool:
    if direction != "ANY" and row.get("direction") != direction:
        return False
    value = as_float(row.get(feature))
    if math.isnan(value):
        return False
    return value <= threshold if op == "<=" else value >= threshold


def apply_filter(
    rows: list[dict[str, Any]], *, feature: str, op: str, threshold: float, direction: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    kept: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for row in rows:
        if row_matches(row, feature=feature, op=op, threshold=threshold, direction=direction):
            blocked.append(row)
        else:
            kept.append(row)
    return kept, blocked


def decision(row: dict[str, Any]) -> str:
    if row["trades_per_market_day"] < 3.0:
        return "FAIL_CADENCE"
    if row["win_rate_pct"] < 60.0:
        return "FAIL_WIN_RATE"
    if (row["profit_factor"] or 0.0) < 1.30:
        return "FAIL_PF"
    if row["top200_removed_usd"] <= 0:
        return "FAIL_TOP200"
    if row["top300_removed_usd"] <= 0:
        return "REVISE_TOP300"
    if row["rolling100"].get("negative_windows", 0) > 0:
        return "REVISE_ROLLING100"
    return "FEATURE_FILTER_REVIEW_CANDIDATE"


def score(row: dict[str, Any], baseline: dict[str, Any]) -> float:
    pf = float(row.get("profit_factor") or 0.0)
    return round(
        pf * 1000.0
        + float(row.get("win_rate_pct") or 0.0) * 12.0
        + float(row.get("trades_per_market_day") or 0.0) * 200.0
        + float(row.get("top200_removed_usd") or 0.0) * 0.5
        + float(row.get("top300_removed_usd") or 0.0) * 0.5
        + max(0.0, float(row.get("net_usd") or 0.0)) * 0.08
        - float(row.get("rolling100", {}).get("negative_windows", 0)) * 6.0
        + (float(row.get("net_usd") or 0.0) - float(baseline.get("net_usd") or 0.0)) * 0.05,
        2,
    )


def evaluate(name: str, rows: list[dict[str, Any]], duplicate_drops: int, baseline: dict[str, Any]) -> dict[str, Any]:
    summary = summarize(name, rows, duplicate_drops=duplicate_drops)
    summary["decision"] = decision(summary)
    summary["score"] = score(summary, baseline)
    summary["delta_net_usd"] = round(summary["net_usd"] - baseline["net_usd"], 2)
    summary["delta_top300_removed_usd"] = round(summary["top300_removed_usd"] - baseline["top300_removed_usd"], 2)
    summary["delta_rolling100_negative"] = summary["rolling100"].get("negative_windows", 0) - baseline["rolling100"].get(
        "negative_windows", 0
    )
    return summary


def build_rows(raw_rows: list[dict[str, Any]], baseline_rows: list[dict[str, Any]], baseline: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    specs: list[dict[str, Any]] = []
    for feature in FEATURES:
        values = [as_float(row.get(feature)) for row in raw_rows]
        for threshold in quantiles(values):
            for op in ("<=", ">="):
                for direction in ("ANY", "LONG", "SHORT"):
                    filtered_raw, blocked_raw = apply_filter(
                        raw_rows, feature=feature, op=op, threshold=threshold, direction=direction
                    )
                    if len(blocked_raw) < 25:
                        continue
                    deduped, drops = dedupe(filtered_raw)
                    summary = evaluate(
                        f"block_{direction}_{feature}_{op}_{threshold}",
                        deduped,
                        drops,
                        baseline,
                    )
                    summary.update(
                        {
                            "filter_type": "single_feature",
                            "feature": feature,
                            "op": op,
                            "threshold": threshold,
                            "direction_filter": direction,
                            "raw_blocked": len(blocked_raw),
                            "raw_blocked_net_usd": round(sum(float(row["profit"]) for row in blocked_raw), 2),
                            "baseline_trades": len(baseline_rows),
                        }
                    )
                    rows.append(summary)
                    specs.append(
                        {
                            "feature": feature,
                            "op": op,
                            "threshold": threshold,
                            "direction": direction,
                            "score": summary["score"],
                            "decision": summary["decision"],
                        }
                    )
    top_specs = sorted(specs, key=lambda item: -float(item["score"]))[:30]
    for left_index, left in enumerate(top_specs):
        for right in top_specs[left_index + 1 :]:
            if left == right:
                continue
            kept_raw: list[dict[str, Any]] = []
            blocked_raw: list[dict[str, Any]] = []
            for row in raw_rows:
                left_match = row_matches(
                    row,
                    feature=left["feature"],
                    op=left["op"],
                    threshold=left["threshold"],
                    direction=left["direction"],
                )
                right_match = row_matches(
                    row,
                    feature=right["feature"],
                    op=right["op"],
                    threshold=right["threshold"],
                    direction=right["direction"],
                )
                if left_match or right_match:
                    blocked_raw.append(row)
                else:
                    kept_raw.append(row)
            if len(blocked_raw) < 50:
                continue
            deduped, drops = dedupe(kept_raw)
            summary = evaluate(
                (
                    f"pair_block_{left['direction']}_{left['feature']}_{left['op']}_{left['threshold']}"
                    f"__{right['direction']}_{right['feature']}_{right['op']}_{right['threshold']}"
                ),
                deduped,
                drops,
                baseline,
            )
            summary.update(
                {
                    "filter_type": "pair_feature",
                    "feature": f"{left['feature']} + {right['feature']}",
                    "op": f"{left['op']} + {right['op']}",
                    "threshold": f"{left['threshold']} + {right['threshold']}",
                    "direction_filter": f"{left['direction']} + {right['direction']}",
                    "raw_blocked": len(blocked_raw),
                    "raw_blocked_net_usd": round(sum(float(row["profit"]) for row in blocked_raw), 2),
                    "baseline_trades": len(baseline_rows),
                }
            )
            rows.append(summary)
    rows.sort(
        key=lambda row: (
            row["decision"].startswith("FAIL"),
            row["decision"].startswith("REVISE"),
            -row["score"],
        )
    )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "decision",
        "score",
        "name",
        "feature",
        "op",
        "threshold",
        "direction_filter",
        "trades",
        "win_rate_pct",
        "profit_factor",
        "net_usd",
        "delta_net_usd",
        "trades_per_market_day",
        "top200_removed_usd",
        "top300_removed_usd",
        "delta_top300_removed_usd",
        "delta_rolling100_negative",
        "raw_blocked",
        "raw_blocked_net_usd",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def render(payload: dict[str, Any]) -> str:
    best = payload["best_result"]
    baseline = payload["baseline"]
    lines = [
        "# A1 XAU M5 Momentum Risk-Normalized Feature Ranker - 2026-07-03",
        "",
        "Scope: offline analysis of exact MT5 Strategy Tester component trade exports. No MT5 runtime, chart, preset, order, or position was touched.",
        "",
        "## Baseline",
        "",
        "| Field | Value |",
        "|---|---:|",
        f"| Trades | {baseline['trades']} |",
        f"| Win rate | {baseline['win_rate_pct']}% |",
        f"| Profit factor | {baseline['profit_factor']} |",
        f"| Net USD | {baseline['net_usd']} |",
        f"| Trades / market day | {baseline['trades_per_market_day']} |",
        f"| Top200 removed USD | {baseline['top200_removed_usd']} |",
        f"| Top300 removed USD | {baseline['top300_removed_usd']} |",
        f"| Rolling100 negative windows | {baseline['rolling100'].get('negative_windows')} |",
        "",
        "## Best Filter",
        "",
        "| Field | Value |",
        "|---|---:|",
        f"| Decision | `{best.get('decision')}` |",
        f"| Filter | `{best.get('name')}` |",
        f"| Trades | {best.get('trades')} |",
        f"| Win rate | {best.get('win_rate_pct')}% |",
        f"| Profit factor | {best.get('profit_factor')} |",
        f"| Net USD | {best.get('net_usd')} |",
        f"| Trades / market day | {best.get('trades_per_market_day')} |",
        f"| Top200 removed USD | {best.get('top200_removed_usd')} |",
        f"| Top300 removed USD | {best.get('top300_removed_usd')} |",
        f"| Rolling100 negative delta | {best.get('delta_rolling100_negative')} |",
        "",
        "## Top Rows",
        "",
        "| Rank | Decision | Filter | Trades | WR | PF | Net | T/market day | Top300 | Roll100 delta |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(payload["top_results"][:25], start=1):
        lines.append(
            "| {rank} | `{decision}` | `{name}` | {trades} | {wr:.2f}% | {pf} | {net:.2f} | {tmd:.2f} | {top300:.2f} | {roll_delta} |".format(
                rank=index,
                decision=row.get("decision"),
                name=row.get("name"),
                trades=row.get("trades"),
                wr=row.get("win_rate_pct", 0.0),
                pf=row.get("profit_factor"),
                net=row.get("net_usd", 0.0),
                tmd=row.get("trades_per_market_day", 0.0),
                top300=row.get("top300_removed_usd", 0.0),
                roll_delta=row.get("delta_rolling100_negative"),
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
            "A filter is not demo-ready unless it clears cadence, PF, top-winner robustness, and rolling-window robustness together.",
            "",
            "## Artifacts",
            "",
            f"- Report: `{payload['report']}`",
            f"- JSON: `{payload['json']}`",
            f"- CSV: `{payload['csv']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    variants = load_variants()
    raw_rows: list[dict[str, Any]] = []
    for rows in variants.values():
        raw_rows.extend(rows)
    raw_rows = enrich_rows(raw_rows)
    baseline_rows, baseline_drops = dedupe(raw_rows)
    baseline = evaluate("baseline_all_components_deduped", baseline_rows, baseline_drops, {"net_usd": 0.0, "top300_removed_usd": 0.0, "rolling100": {"negative_windows": 0}})
    baseline["decision"] = "BASELINE"
    rows = build_rows(raw_rows, baseline_rows, baseline)
    best = rows[0] if rows else {}
    verdict = (
        "FOUND_FEATURE_FILTER_REVIEW_CANDIDATE"
        if str(best.get("decision", "")).endswith("CANDIDATE")
        else "NO_FEATURE_FILTER_CANDIDATE"
    )
    next_action = (
        "port_best_filter_to_exact_mt5_variant_and_backtest"
        if verdict == "FOUND_FEATURE_FILTER_REVIEW_CANDIDATE"
        else "do_not_promote_feature_filter_continue_new_entry_design"
    )
    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    output_csv = REPORTS_DIR / f"{OUTPUT_STEM}.csv"
    payload = {
        "status": "PASS_FEATURE_RANKER_READY",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "boundary": "offline_exact_mt5_export_analysis_only_no_runtime_change",
        "source_backtest_dir": rel(BACKTEST_DIR),
        "variant_count": len(variants),
        "raw_rows": len(raw_rows),
        "baseline": baseline,
        "verdict": verdict,
        "next_action": next_action,
        "best_result": best,
        "top_results": rows[:50],
        "report": rel(output_md),
        "json": rel(output_json),
        "csv": rel(output_csv),
    }
    output_md.write_text(render(payload), encoding="utf-8")
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    write_csv(output_csv, rows)
    print(output_md)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "verdict": verdict,
                "decision": best.get("decision"),
                "filter": best.get("name"),
                "trades": best.get("trades"),
                "win_rate_pct": best.get("win_rate_pct"),
                "profit_factor": best.get("profit_factor"),
                "net_usd": best.get("net_usd"),
                "trades_per_market_day": best.get("trades_per_market_day"),
                "top300_removed_usd": best.get("top300_removed_usd"),
                "rolling100_negative_delta": best.get("delta_rolling100_negative"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
