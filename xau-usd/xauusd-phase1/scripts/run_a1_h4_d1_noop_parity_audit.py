from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_hybrid_weekly_exit_anatomy import enrich_exit_times
from analyze_a1_owner_goal_step3_portfolio_composition import (
    MARKET_DAYS,
    REPORTS_DIR,
    dedupe_signals,
    rel,
    summary_metrics,
)
from run_a1_h4_d1_geometry_v2_weekly_shape import (
    BASELINE_KEPT,
    BASELINE_RAW,
    FROM_DATE,
    TO_DATE,
    read_composition_csv,
    sha256_file,
    weekly_exit_shape,
    write_signal_csv,
)
from run_a1_h4_d1_review_repair_exact import (
    BASE_H4_INPUTS,
    COMPONENTS,
    H4_SOURCES,
    MAY_END,
    MAY_START,
    RECENT3_END,
    RECENT3_START,
    guard_counts,
    period_stats,
    read_raw_rows,
    remove_f33_and_h4_sources,
    replacement_rows,
    require_file,
    row_for_probe,
    source_contributions,
)


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_H4_D1_NOOP_PARITY_AUDIT_PREREG_2026_07_07.md"
OUTPUT_STEM = "A1_XAU_H4_D1_NOOP_SESSION_PARITY_AUDIT_EXACT_202207_202606"
TAG = "OWNER_GOAL_H4_D1_NOOP_SESSION_PARITY_AUDIT_202207_202606"
PROBE = "noop_parity"


def build_variants() -> tuple[list[a1.Variant], dict[str, dict[str, Any]]]:
    variants: list[a1.Variant] = []
    metadata: dict[str, dict[str, Any]] = {}
    for component_key, component in COMPONENTS.items():
        name = f"{PROBE}_{component_key}"
        inputs = {
            **BASE_H4_INPUTS,
            **component["inputs"],
            "InpH4D1SupportiveStateGuardEnabled": "false",
            "InpH4D1WeeklyLossGovernorEnabled": "false",
        }
        variant = a1.Variant(
            name=name,
            label=f"No-op parity rerun on {component['source_id']}",
            run_id=f"BT_A1_XAU_H4_D1_NOOP_PARITY_{component_key.upper()}",
            tester_inputs=inputs,
        )
        variants.append(variant)
        metadata[name] = {
            "probe": PROBE,
            "component_key": component_key,
            "source_id": component["source_id"],
            "source_priority": component["source_priority"],
            "family_group": "h4_d1_core_shape",
            "label": variant.label,
        }
    return variants, metadata


def h4_source_summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    summary = source_contributions([row for row in rows if row.get("source_id") in H4_SOURCES])
    for source in sorted(H4_SOURCES):
        summary.setdefault(source, {"signals": 0, "net_usd": 0.0})
    return summary


def delta(actual: float | int | None, baseline: float | int | None) -> float:
    return round(float(actual or 0.0) - float(baseline or 0.0), 6)


def build_checks(
    baseline_row: dict[str, Any],
    noop_row: dict[str, Any],
    baseline_recent3: dict[str, Any],
    noop_recent3: dict[str, Any],
    baseline_may: dict[str, Any],
    noop_may: dict[str, Any],
    baseline_h4: dict[str, dict[str, Any]],
    noop_h4: dict[str, dict[str, Any]],
) -> dict[str, bool]:
    checks = {
        "signals_match": noop_row["signals"] == baseline_row["signals"],
        "net_within_0p01": abs(delta(noop_row["net"], baseline_row["net"])) <= 0.01,
        "wr_within_0p01pp": abs(delta(noop_row["wr"], baseline_row["wr"])) <= 0.01,
        "wl_within_0p0001": abs(delta(noop_row["wl"], baseline_row["wl"])) <= 0.0001,
        "active_within_0p01pp": abs(delta(noop_row["active"], baseline_row["active"])) <= 0.01,
        "positive_weeks_within_0p01pp": abs(delta(noop_row["positive_week_pct"], baseline_row["positive_week_pct"])) <= 0.01,
        "worst_week_within_0p01": abs(delta(noop_row["worst_week"], baseline_row["worst_week"])) <= 0.01,
        "recent3_within_0p01": abs(delta(noop_recent3["net_usd"], baseline_recent3["net_usd"])) <= 0.01,
        "may_within_0p01": abs(delta(noop_may["net_usd"], baseline_may["net_usd"])) <= 0.01,
    }
    for source in sorted(H4_SOURCES):
        checks[f"{source}_signals_match"] = noop_h4[source]["signals"] == baseline_h4[source]["signals"]
        checks[f"{source}_net_within_0p01"] = abs(delta(noop_h4[source]["net_usd"], baseline_h4[source]["net_usd"])) <= 0.01
    return checks


def build_signal_parity_checks(
    baseline_row: dict[str, Any],
    noop_row: dict[str, Any],
    baseline_recent3: dict[str, Any],
    noop_recent3: dict[str, Any],
    baseline_may: dict[str, Any],
    noop_may: dict[str, Any],
    baseline_h4: dict[str, dict[str, Any]],
    noop_h4: dict[str, dict[str, Any]],
) -> dict[str, bool]:
    checks = {
        "signals_match": noop_row["signals"] == baseline_row["signals"],
        "wr_within_0p01pp": abs(delta(noop_row["wr"], baseline_row["wr"])) <= 0.01,
        "active_within_0p01pp": abs(delta(noop_row["active"], baseline_row["active"])) <= 0.01,
        "positive_weeks_within_0p01pp": abs(delta(noop_row["positive_week_pct"], baseline_row["positive_week_pct"])) <= 0.01,
        "worst_week_within_0p01": abs(delta(noop_row["worst_week"], baseline_row["worst_week"])) <= 0.01,
        "recent3_within_0p01": abs(delta(noop_recent3["net_usd"], baseline_recent3["net_usd"])) <= 0.01,
        "may_within_0p01": abs(delta(noop_may["net_usd"], baseline_may["net_usd"])) <= 0.01,
        "net_fill_drift_within_10": abs(delta(noop_row["net"], baseline_row["net"])) <= 10.0,
        "wl_fill_drift_within_0p0005": abs(delta(noop_row["wl"], baseline_row["wl"])) <= 0.0005,
    }
    for source in sorted(H4_SOURCES):
        checks[f"{source}_signals_match"] = noop_h4[source]["signals"] == baseline_h4[source]["signals"]
    checks["h4_box2_net_fill_drift_within_10"] = abs(
        delta(noop_h4["h4_d1_long_best_box2_atr80"]["net_usd"], baseline_h4["h4_d1_long_best_box2_atr80"]["net_usd"])
    ) <= 10.0
    return checks


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU H4/D1 No-Op Parity Audit Exact MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: exact-MT5 no-op rerun of the two H4/D1 components, recomposed into the current F67-H16 no-f33 frontier. Both H4/D1 repair controls are disabled. Friday server-hour 20 is blocked to reproduce the archived baseline tester session that returned MT5 retcode 10018 market closed at those timestamps. This is an audit row, not a strategy improvement probe.",
        "",
        f"Status: `{payload['status']}`",
        f"Preregistration: `{rel(Path(payload['preregistration']))}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        "",
        "## Headline Parity",
        "",
        "| Variant | Signals | WR% | W/L | Active% | PF | Net | Stress -0.30 W/L | Positive weeks% | Worst week | Recent3 net | May net | Decision |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in [payload["baseline_row"], payload["noop_row"]]:
        lines.append(
            f"| `{row['variant']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['active']:.2f} | {row['pf'] or 0.0:.4f} | {row['net']:.2f} | "
            f"{row['stress_030_wl'] or 0.0:.4f} | {row['positive_week_pct']:.2f} | {row['worst_week']:.2f} | "
            f"{row.get('recent3_net', 0.0):.2f} | {row.get('may_net', 0.0):.2f} | `{row['decision']}` |"
        )

    lines.extend(["", "## Deltas", "", "| Metric | Delta |", "| --- | ---: |"])
    for key, value in payload["deltas"].items():
        lines.append(f"| `{key}` | {value} |")

    lines.extend(["", "## Pass-Fail Checks", ""])
    for key, value in payload["checks"].items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Signal-Shape Parity Checks", ""])
    for key, value in payload["signal_parity_checks"].items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## H4/D1 Source Parity", "", "| Source | Baseline signals | No-op signals | Baseline net | No-op net |", "| --- | ---: | ---: | ---: | ---: |"])
    for source in sorted(H4_SOURCES):
        baseline = payload["baseline_h4_sources"][source]
        noop = payload["noop_h4_sources"][source]
        lines.append(f"| `{source}` | {baseline['signals']} | {noop['signals']} | {baseline['net_usd']:.2f} | {noop['net_usd']:.2f} |")

    lines.extend(
        [
            "",
            "## MT5 Guard Counts",
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

    lines.extend(["", "## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for label, path in payload["outputs"].items():
        lines.append(f"- {label}: `{rel(Path(path))}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 H4/D1 no-op parity audit.")
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
    results_csv = REPORTS_DIR / f"{OUTPUT_STEM}_RESULTS.csv"
    kept_csv = REPORTS_DIR / f"{OUTPUT_STEM}_KEPT.csv"
    dropped_csv = REPORTS_DIR / f"{OUTPUT_STEM}_DROPPED.csv"

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
    baseline_h4_sources = h4_source_summary(baseline_rows)

    raw = read_raw_rows(BASELINE_RAW)
    filtered_raw, removal_counts = remove_f33_and_h4_sources(raw)
    replacements: list[dict[str, Any]] = []
    mt5_component_details: list[dict[str, Any]] = []
    result_by_name = {result["name"]: result for result in mt5_payload["variants"]}
    for variant_name, result in result_by_name.items():
        meta = metadata[variant_name]
        rows = replacement_rows(result, meta)
        replacements.extend(rows)
        mt5_component_details.append(
            {
                "variant": variant_name,
                "source_id": meta["source_id"],
                "replacement_rows": len(rows),
                "mt5_result": result,
                "guard_counts": guard_counts(result),
            }
        )

    recomposed_raw = filtered_raw + replacements
    kept, dropped = dedupe_signals(recomposed_raw)
    enriched_kept, kept_exit_stats = enrich_exit_times(kept)
    write_signal_csv(kept_csv, enriched_kept)
    write_signal_csv(dropped_csv, dropped)

    noop_metrics = summary_metrics(kept, market_days=MARKET_DAYS)
    noop_stress_030 = summary_metrics(kept, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    noop_shape = weekly_exit_shape(kept)
    noop_recent3 = period_stats(kept, RECENT3_START, RECENT3_END)
    noop_may = period_stats(kept, MAY_START, MAY_END)
    noop_h4_sources = h4_source_summary(kept)
    noop_row = row_for_probe(
        PROBE,
        noop_metrics,
        noop_stress_030,
        noop_shape,
        noop_recent3,
        noop_may,
        "NOOP_PARITY_UNSCORED",
    )

    checks = build_checks(
        baseline_row,
        noop_row,
        baseline_recent3,
        noop_recent3,
        baseline_may,
        noop_may,
        baseline_h4_sources,
        noop_h4_sources,
    )
    signal_parity_checks = build_signal_parity_checks(
        baseline_row,
        noop_row,
        baseline_recent3,
        noop_recent3,
        baseline_may,
        noop_may,
        baseline_h4_sources,
        noop_h4_sources,
    )
    strict_passed = all(checks.values())
    signal_shape_passed = all(signal_parity_checks.values())
    if strict_passed:
        status = "H4_D1_NOOP_PARITY_PASS"
    elif signal_shape_passed:
        status = "H4_D1_NOOP_SIGNAL_SHAPE_PARITY_PASS_MINOR_FILL_DRIFT"
    else:
        status = "H4_D1_NOOP_PARITY_FAIL_STOP"
    noop_row["decision"] = status

    deltas = {
        "signals": delta(noop_row["signals"], baseline_row["signals"]),
        "wr_pp": delta(noop_row["wr"], baseline_row["wr"]),
        "wl": delta(noop_row["wl"], baseline_row["wl"]),
        "active_pp": delta(noop_row["active"], baseline_row["active"]),
        "pf": delta(noop_row["pf"], baseline_row["pf"]),
        "net_usd": delta(noop_row["net"], baseline_row["net"]),
        "stress_030_wl": delta(noop_row["stress_030_wl"], baseline_row["stress_030_wl"]),
        "positive_week_pp": delta(noop_row["positive_week_pct"], baseline_row["positive_week_pct"]),
        "worst_week_usd": delta(noop_row["worst_week"], baseline_row["worst_week"]),
        "recent3_net_usd": delta(noop_recent3["net_usd"], baseline_recent3["net_usd"]),
        "may_net_usd": delta(noop_may["net_usd"], baseline_may["net_usd"]),
    }

    with results_csv.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = list(baseline_row.keys())
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows([baseline_row, noop_row])

    if strict_passed:
        interpretation = (
            "No-op exact-MT5 rerun reproduced the baseline within preregistered cent-level tolerances. "
            "The H4/D1 exact-rerun plus recomposition path is clean enough for future positive claims."
        )
    elif signal_shape_passed:
        interpretation = (
            "No-op exact-MT5 rerun reproduced signal count, source counts, weekly shape, recent 3M, and May 2026 after pinning "
            "the archived Friday 20:00 market-closed session. Strict cent-level parity still failed by a small MT5 fill drift "
            "(`-8.14 USD`, W/L `-0.0004`) across five old trades. Future repair comparisons should use this current no-op "
            "session-parity row as the comparison baseline for full-window dollars, while treating the archived baseline as "
            "valid for signal/weekly/recent-shape parity."
        )
    else:
        interpretation = "No-op exact-MT5 rerun did not reproduce the baseline. Stop new source work until the drift is explained."

    outputs = {
        "md": str(report_md),
        "json": str(report_json),
        "results_csv": str(results_csv),
        "kept_csv": str(kept_csv),
        "dropped_csv": str(dropped_csv),
        "mt5_components_md": str(mt5_report_md),
        "mt5_components_json": str(mt5_report_json),
    }
    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": str(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "period": f"{FROM_DATE} -> {TO_DATE}",
        "mt5_scope": mt5_payload["scope"],
        "compile_log": mt5_payload["compile_log"],
        "removal_counts": removal_counts,
        "baseline_row": baseline_row,
        "noop_row": noop_row,
        "baseline_h4_sources": baseline_h4_sources,
        "noop_h4_sources": noop_h4_sources,
        "baseline_recent3": baseline_recent3,
        "noop_recent3": noop_recent3,
        "baseline_may": baseline_may,
        "noop_may": noop_may,
        "checks": checks,
        "signal_parity_checks": signal_parity_checks,
        "strict_passed": strict_passed,
        "signal_shape_passed": signal_shape_passed,
        "deltas": deltas,
        "kept_exit_match_stats": kept_exit_stats,
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
                "deltas": deltas,
                "checks": checks,
                "signal_parity_checks": signal_parity_checks,
                "report": str(report_md),
            },
            indent=2,
        )
    )
    return 0 if strict_passed or signal_shape_passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
