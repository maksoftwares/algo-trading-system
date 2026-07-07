from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_hybrid_f67_h16_no_f33_composition import read_raw_rows
from analyze_a1_hybrid_weekly_exit_anatomy import enrich_exit_times
from analyze_a1_owner_goal_step3_portfolio_composition import (
    LAST12_MARKET_DAYS,
    LAST12_START,
    MARKET_DAYS,
    REPORTS_DIR,
    dedupe_signals,
    parse_dt,
    rel,
    summary_metrics,
)
from run_a1_h4_d1_geometry_v2_weekly_shape import (
    BASELINE_KEPT,
    BASELINE_RAW,
    FROM_DATE,
    TO_DATE,
    parse_date,
    read_composition_csv,
    remove_top_winners,
    result_row,
    sha256_file,
    weekly_exit_shape,
    write_signal_csv,
)
from run_a1_v9_v10_rr2_stretch_probe import read_trade_csv


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_H4_D1_REVIEW_REPAIR_PREREG_2026_07_07.md"
OUTPUT_STEM = "A1_XAU_H4_D1_REVIEW_REPAIR_EXACT_202207_202606"
TAG = "OWNER_GOAL_H4_D1_REVIEW_REPAIR_202207_202606"
REMOVED_SOURCE = "step1_f33_r30_be_never"
H4_SOURCES = {"h4_d1_long_best_box2_atr80", "h4_d1_long_broad_box3_atr60"}
RECENT3_START = date(2026, 4, 1)
RECENT3_END = date(2026, 6, 30)
MAY_START = date(2026, 5, 1)
MAY_END = date(2026, 5, 31)


BASE_H4_INPUTS = {
    "InpSignalMode": "7",
    "InpDirectionMode": "1",
    "InpUseH1TrendFilter": "false",
    "InpUseH4TrendFilter": "false",
    "InpRiskReward": "2.00",
    "InpMaxEstimatedCostR": "0.15",
    "InpStopCeilingPoints": "0",
    "InpStopCapPoints": "0",
    "InpMaxTradesPerDay": "6",
    "InpCooldownMinutes": "0",
    "InpOnePositionPerMagic": "false",
    "InpMaxOpenPositionsPerMagic": "32",
    "InpBlockedLongEntryHoursCsv": "3,10,13,14",
}

COMPONENTS = {
    "box2": {
        "source_id": "h4_d1_long_best_box2_atr80",
        "source_priority": 80,
        "inputs": {
            "InpD1CompressionAtrPercentileMax": "80.00",
            "InpD1CompressionBoxDays": "2",
            "InpD1CompressionRangeMedianMax": "1.50",
            "InpD1CompressionH4MinBodyFraction": "0.35",
        },
    },
    "broad": {
        "source_id": "h4_d1_long_broad_box3_atr60",
        "source_priority": 81,
        "inputs": {
            "InpD1CompressionAtrPercentileMax": "60.00",
            "InpD1CompressionBoxDays": "3",
            "InpD1CompressionRangeMedianMax": "1.25",
            "InpD1CompressionH4MinBodyFraction": "0.35",
        },
    },
}

PROBES = {
    "supportive_guard": {
        "label": "H4/D1 supportive-state guard: D1 close[1] > EMA20[1] and EMA20[1] >= EMA20[6]",
        "inputs": {
            "InpH4D1SupportiveStateGuardEnabled": "true",
            "InpH4D1SupportiveEmaPeriod": "20",
            "InpH4D1SupportiveSlopeLagBars": "5",
        },
    },
    "weekly_loss_governor": {
        "label": "H4/D1 weekly loss governor: block after closed weekly component PnL <= -150 USD",
        "inputs": {
            "InpH4D1WeeklyLossGovernorEnabled": "true",
            "InpH4D1WeeklyLossLimitUsd": "150.00",
        },
    },
}


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def build_variants() -> tuple[list[a1.Variant], dict[str, dict[str, Any]]]:
    variants: list[a1.Variant] = []
    metadata: dict[str, dict[str, Any]] = {}
    for probe_name, probe in PROBES.items():
        for component_key, component in COMPONENTS.items():
            name = f"{probe_name}_{component_key}"
            inputs = {
                **BASE_H4_INPUTS,
                **component["inputs"],
                **probe["inputs"],
            }
            variant = a1.Variant(
                name=name,
                label=f"{probe['label']} on {component['source_id']}",
                run_id=f"BT_A1_XAU_H4_D1_REPAIR_{probe_name.upper()}_{component_key.upper()}",
                tester_inputs=inputs,
            )
            variants.append(variant)
            metadata[name] = {
                "probe": probe_name,
                "component_key": component_key,
                "source_id": component["source_id"],
                "source_priority": component["source_priority"],
                "family_group": "h4_d1_core_shape",
                "label": variant.label,
            }
    return variants, metadata


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def guard_counts(result: dict[str, Any]) -> dict[str, Any]:
    rows = read_tsv(Path(result["order_csv"]))
    reasons = Counter(row.get("reason", "") for row in rows if row.get("action") == "GUARD_BLOCK")
    actions = Counter(row.get("action", "") for row in rows)
    return {
        "order_rows": len(rows),
        "actions": dict(actions),
        "guard_reasons": dict(reasons),
    }


def replacement_rows(result: dict[str, Any], meta: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    trade_csv = Path(result["trade_csv"])
    for ordinal, row in enumerate(read_trade_csv(trade_csv), start=2):
        entry_time = parse_dt(row["entry_time"])
        rows.append(
            {
                "component": meta["source_id"],
                "source_id": meta["source_id"],
                "upstream_source_id": meta["source_id"],
                "upstream_component": f"h4_d1_review_repair_{meta['probe']}",
                "family_group": meta["family_group"],
                "source_priority": int(meta["source_priority"]),
                "cell_id": meta["probe"],
                "component_priority": 0,
                "variant_name": result["name"],
                "entry_time": entry_time,
                "entry_date": parse_date(row.get("entry_date") or entry_time.date().isoformat()),
                "exit_time": row.get("exit_time", ""),
                "direction": str(row.get("direction", "")).upper(),
                "pnl_usd": float(row.get("profit_float") or 0.0),
                "tickets": 1,
                "lots": float(row.get("volume") or 0.0),
                "source_csv": str(trade_csv),
                "source_row": ordinal,
            }
        )
    return rows


def remove_f33_and_h4_sources(raw: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    kept: list[dict[str, Any]] = []
    counts = {"removed_f33": 0, "removed_h4_d1": 0}
    for row in raw:
        source = row.get("source_id", "")
        upstream = row.get("upstream_source_id", "")
        if source == REMOVED_SOURCE or upstream == REMOVED_SOURCE:
            counts["removed_f33"] += 1
            continue
        if source in H4_SOURCES or upstream in H4_SOURCES:
            counts["removed_h4_d1"] += 1
            continue
        kept.append(row)
    return kept, counts


def period_stats(rows: list[dict[str, Any]], start: date, end: date) -> dict[str, Any]:
    selected = [row for row in rows if start <= row["entry_date"] <= end]
    profits = [float(row.get("pnl_usd") or 0.0) for row in selected]
    wins = [value for value in profits if value > 0.0]
    losses = [-value for value in profits if value < 0.0]
    gross_profit = sum(wins)
    gross_loss = sum(losses)
    avg_win = gross_profit / len(wins) if wins else 0.0
    avg_loss = gross_loss / len(losses) if losses else 0.0
    return {
        "signals": len(selected),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round(100.0 * len(wins) / len(selected), 2) if selected else 0.0,
        "net_usd": round(sum(profits), 2),
        "profit_factor": round(gross_profit / gross_loss, 4) if gross_loss else None,
        "avg_win_loss": round(avg_win / avg_loss, 4) if avg_loss else None,
    }


def pass_fail(
    metrics: dict[str, Any],
    stress_030: dict[str, Any],
    shape: dict[str, Any],
    baseline_row: dict[str, Any],
    baseline_recent3: dict[str, Any],
    baseline_may: dict[str, Any],
    recent3: dict[str, Any],
    may: dict[str, Any],
) -> tuple[bool, dict[str, bool], str]:
    worst_week_target = baseline_row["worst_week"] * 0.80
    checks = {
        "wr_ge_50": metrics["win_rate_pct"] >= 50.0,
        "wl_ge_2": (metrics["avg_win_loss"] or 0.0) >= 2.0,
        "active_ge_84": metrics["active_weekday_pct"] >= 84.0,
        "stress_wl_ge_1p90": (stress_030["avg_win_loss"] or 0.0) >= 1.90,
        "recent3_improves_750": recent3["net_usd"] - baseline_recent3["net_usd"] >= 750.0,
        "may_improves_500": may["net_usd"] - baseline_may["net_usd"] >= 500.0,
        "positive_weeks_plus_3pp": shape["positive_week_pct"] - baseline_row["positive_week_pct"] >= 3.0,
        "net_ge_17500": metrics["net_usd"] >= 17500.0,
        "worst_week_improves_20pct": shape["worst_week_usd"] >= worst_week_target,
    }
    passed = all(checks.values())
    if passed:
        return True, checks, "PASS_REVIEW_REPAIR_CANDIDATE"
    if not checks["wr_ge_50"] or not checks["wl_ge_2"]:
        return False, checks, "FAIL_CORE_WR_WL"
    if not checks["recent3_improves_750"] and not checks["may_improves_500"]:
        return False, checks, "FAIL_RECENT_DECAY_REPAIR"
    if not checks["positive_weeks_plus_3pp"]:
        return False, checks, "FAIL_WEEKLY_SHAPE"
    return False, checks, "FAIL_REPAIR_GATE"


def source_contributions(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["source_id"], []).append(row)
    return {
        source: {
            "signals": len(items),
            "net_usd": round(sum(float(row.get("pnl_usd") or 0.0) for row in items), 2),
        }
        for source, items in sorted(grouped.items())
    }


def row_for_probe(
    probe: str,
    metrics: dict[str, Any],
    stress_030: dict[str, Any],
    shape: dict[str, Any],
    recent3: dict[str, Any],
    may: dict[str, Any],
    decision: str,
) -> dict[str, Any]:
    row = result_row(probe, metrics, stress_030, shape, decision)
    row.update(
        {
            "recent3_signals": recent3["signals"],
            "recent3_wr": recent3["win_rate_pct"],
            "recent3_wl": recent3["avg_win_loss"],
            "recent3_net": recent3["net_usd"],
            "may_net": may["net_usd"],
        }
    )
    return row


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU H4/D1 Review Repair Exact MT5 Probe",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: two preregistered H4/D1-only exact-MT5 repair probes, recomposed into the current F67-H16 no-f33 frontier. Frequency rows are unchanged. No live/demo runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Status: `{payload['status']}`",
        f"Preregistration: `{rel(Path(payload['preregistration']))}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        "",
        "## Results",
        "",
        "| Probe | Signals | WR% | W/L | Active% | PF | Net | Stress -0.30 W/L | Positive weeks% | Worst week | Recent3 net | May net | Decision |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in [payload["baseline_row"], *payload["result_rows"]]:
        lines.append(
            f"| `{row['variant']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['active']:.2f} | {row['pf'] or 0.0:.4f} | {row['net']:.2f} | "
            f"{row['stress_030_wl'] or 0.0:.4f} | {row['positive_week_pct']:.2f} | {row['worst_week']:.2f} | "
            f"{row.get('recent3_net', 0.0):.2f} | {row.get('may_net', 0.0):.2f} | `{row['decision']}` |"
        )

    lines.extend(["", "## Pass-Fail Checks", ""])
    for item in payload["probe_details"]:
        lines.append(f"### `{item['probe']}`")
        lines.append("")
        for key, value in item["pass_fail_checks"].items():
            lines.append(f"- `{key}`: `{value}`")
        lines.append("")

    lines.extend(
        [
            "## H4/D1 MT5 Guard Counts",
            "",
            "| Variant | Orders | h4_d1_supportive_state_guard | h4_d1_weekly_loss_governor | Other guard blocks |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in payload["mt5_component_details"]:
        reasons = item["guard_counts"]["guard_reasons"]
        support = reasons.get("h4_d1_supportive_state_guard", 0)
        governor = reasons.get("h4_d1_weekly_loss_governor", 0)
        other = sum(count for reason, count in reasons.items() if reason not in {"h4_d1_supportive_state_guard", "h4_d1_weekly_loss_governor"})
        lines.append(f"| `{item['variant']}` | {item['guard_counts']['order_rows']} | {support} | {governor} | {other} |")

    lines.extend(["", "## Source Contributions", ""])
    for item in payload["probe_details"]:
        lines.extend(["", f"### `{item['probe']}`", "", "| Source | Signals | Net USD |", "| --- | ---: | ---: |"])
        for source, contribution in item["source_contributions"].items():
            lines.append(f"| `{source}` | {contribution['signals']} | {contribution['net_usd']:.2f} |")

    lines.extend(["", "## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for label, path in payload["outputs"].items():
        lines.append(f"- {label}: `{rel(Path(path))}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 H4/D1 review repair probes.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    for path in (PREREG, BASELINE_KEPT, BASELINE_RAW):
        require_file(path)

    variants, metadata = build_variants()
    a1.VARIANTS = variants
    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    mt5_report_md = REPORTS_DIR / f"{OUTPUT_STEM}_MT5_COMPONENTS.md"
    mt5_report_json = REPORTS_DIR / f"{OUTPUT_STEM}_MT5_COMPONENTS.json"
    mt5_payload = a1.run_variants(
        from_date=FROM_DATE,
        to_date=TO_DATE,
        tag=a1.safe_name(TAG),
        report_md=mt5_report_md,
        report_json=mt5_report_json,
        variant_timeout_seconds=args.variant_timeout_seconds,
        deposit="1000",
        currency="USD",
    )

    baseline_rows = read_composition_csv(BASELINE_KEPT)
    baseline_metrics = summary_metrics(baseline_rows, market_days=MARKET_DAYS)
    baseline_stress_030 = summary_metrics(baseline_rows, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    baseline_shape = weekly_exit_shape(baseline_rows)
    baseline_recent3 = period_stats(baseline_rows, RECENT3_START, RECENT3_END)
    baseline_may = period_stats(baseline_rows, MAY_START, MAY_END)
    baseline_row = row_for_probe(
        "baseline_f67_h16_no_f33",
        baseline_metrics,
        baseline_stress_030,
        baseline_shape,
        baseline_recent3,
        baseline_may,
        "BASELINE",
    )

    raw = read_raw_rows(BASELINE_RAW)
    filtered_raw, removal_counts = remove_f33_and_h4_sources(raw)
    replacements_by_probe: dict[str, list[dict[str, Any]]] = {probe: [] for probe in PROBES}
    mt5_component_details: list[dict[str, Any]] = []
    result_by_name = {result["name"]: result for result in mt5_payload["variants"]}
    for variant_name, result in result_by_name.items():
        meta = metadata[variant_name]
        rows = replacement_rows(result, meta)
        replacements_by_probe[meta["probe"]].extend(rows)
        mt5_component_details.append(
            {
                "variant": variant_name,
                "probe": meta["probe"],
                "source_id": meta["source_id"],
                "replacement_rows": len(rows),
                "mt5_result": result,
                "guard_counts": guard_counts(result),
            }
        )

    result_rows: list[dict[str, Any]] = []
    probe_details: list[dict[str, Any]] = []
    outputs = {
        "md": str(report_md),
        "json": str(report_json),
        "results_csv": str(REPORTS_DIR / f"{OUTPUT_STEM}_RESULTS.csv"),
        "mt5_components_md": str(mt5_report_md),
        "mt5_components_json": str(mt5_report_json),
    }

    for probe_name in PROBES:
        recomposed_raw = filtered_raw + replacements_by_probe[probe_name]
        kept, dropped = dedupe_signals(recomposed_raw)
        metrics = summary_metrics(kept, market_days=MARKET_DAYS)
        last12 = summary_metrics([row for row in kept if row["entry_date"] >= LAST12_START], market_days=LAST12_MARKET_DAYS)
        metrics.update(
            {
                "last12_win_rate_pct": last12["win_rate_pct"],
                "last12_avg_win_loss": last12["avg_win_loss"],
                "last12_active_weekday_pct": last12["active_weekday_pct"],
                "last12_net_usd": last12["net_usd"],
            }
        )
        stress_030 = summary_metrics(kept, cost_per_ticket=0.30, market_days=MARKET_DAYS)
        shape = weekly_exit_shape(kept)
        recent3 = period_stats(kept, RECENT3_START, RECENT3_END)
        may = period_stats(kept, MAY_START, MAY_END)
        passed, checks, decision = pass_fail(
            metrics,
            stress_030,
            shape,
            baseline_row,
            baseline_recent3,
            baseline_may,
            recent3,
            may,
        )
        result_rows.append(row_for_probe(probe_name, metrics, stress_030, shape, recent3, may, decision))

        enriched_kept, kept_exit_stats = enrich_exit_times(kept)
        kept_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{probe_name}_KEPT.csv"
        dropped_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{probe_name}_DROPPED.csv"
        write_signal_csv(kept_csv, enriched_kept)
        write_signal_csv(dropped_csv, dropped)
        outputs[f"{probe_name}_kept_csv"] = str(kept_csv)
        outputs[f"{probe_name}_dropped_csv"] = str(dropped_csv)

        probe_details.append(
            {
                "probe": probe_name,
                "passed": passed,
                "pass_fail_checks": checks,
                "metrics": metrics,
                "stress_030": stress_030,
                "shape": shape,
                "recent3": recent3,
                "may": may,
                "recent3_improvement_usd": round(recent3["net_usd"] - baseline_recent3["net_usd"], 2),
                "may_improvement_usd": round(may["net_usd"] - baseline_may["net_usd"], 2),
                "positive_week_delta_pp": round(shape["positive_week_pct"] - baseline_shape["positive_week_pct"], 2),
                "kept_exit_match_stats": kept_exit_stats,
                "source_contributions": source_contributions(kept),
                "kept_csv": str(kept_csv),
                "dropped_csv": str(dropped_csv),
            }
        )

    with Path(outputs["results_csv"]).open("w", newline="", encoding="utf-8") as handle:
        fieldnames = list(result_rows[0].keys()) if result_rows else []
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(result_rows)

    passes = [item for item in probe_details if item["passed"]]
    if passes:
        status = "H4_D1_REVIEW_REPAIR_PASS_REVIEW_REQUIRED"
        best = max(passes, key=lambda item: (item["positive_week_delta_pp"], item["recent3_improvement_usd"], item["metrics"]["net_usd"]))
        interpretation = (
            f"`{best['probe']}` passed the preregistered repair gates. This is not auto-demo-ready; freeze it and request review before any demo spec."
        )
    else:
        status = "NO_H4_D1_REVIEW_REPAIR_SURVIVOR"
        best = max(probe_details, key=lambda item: (item["recent3_improvement_usd"], item["positive_week_delta_pp"], item["metrics"]["avg_win_loss"] or 0.0))
        interpretation = (
            f"No preregistered H4/D1 repair probe passed. Best diagnostic by recent repair was `{best['probe']}` "
            f"with recent3 improvement {best['recent3_improvement_usd']:.2f} USD and positive-week delta "
            f"{best['positive_week_delta_pp']:.2f}pp. Per preregistration, if both fail this repair path should be frozen "
            "and the next work should be a genuinely new red-week source class, not more H4/D1 masking."
        )

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": str(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "period": f"{FROM_DATE} -> {TO_DATE}",
        "mt5_scope": mt5_payload["scope"],
        "compile_log": mt5_payload["compile_log"],
        "removal_counts": removal_counts,
        "baseline_metrics": baseline_metrics,
        "baseline_stress_030": baseline_stress_030,
        "baseline_shape": baseline_shape,
        "baseline_recent3": baseline_recent3,
        "baseline_may": baseline_may,
        "baseline_row": baseline_row,
        "baseline_ex_top_1pct": remove_top_winners(baseline_rows, 0.01),
        "baseline_ex_top_2pct": remove_top_winners(baseline_rows, 0.02),
        "result_rows": result_rows,
        "probe_details": probe_details,
        "mt5_component_details": mt5_component_details,
        "outputs": outputs,
        "interpretation": interpretation,
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "baseline": baseline_row,
                "results": result_rows,
                "report": str(report_md),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
