from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_hybrid_weekly_exit_anatomy import enrich_exit_times
from analyze_a1_owner_goal_step3_portfolio_composition import MARKET_DAYS, REPORTS_DIR, dedupe_signals, rel, summary_metrics
from analyze_a1_xau_previous_month_source_health_gate import LONG_PLUS_V2
from analyze_a1_xau_source_monthly_firewall import max_closed_drawdown, month_shape, read_ledger, weekly_shape
from run_a1_h4_d1_geometry_v2_weekly_shape import BASELINE_RAW, FROM_DATE, TO_DATE, read_composition_csv, write_signal_csv
from run_a1_h4_d1_review_repair_exact import (
    BASE_H4_INPUTS,
    COMPONENTS,
    H4_SOURCES,
    guard_counts,
    read_raw_rows,
    remove_f33_and_h4_sources,
    replacement_rows,
    require_file,
    sha256_file,
    source_contributions,
)


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_H4_PREVIOUS_MONTH_HEALTH_GATE_EXACT_PREREG_2026_07_08.md"
OUTPUT_STEM = "A1_XAU_H4_PREVIOUS_MONTH_HEALTH_GATE_EXACT_202207_202606"
TAG = "OWNER_GOAL_H4_PREV_MONTH_HEALTH_GATE_EXACT_202207_202606"
PROBE = "h4_prev_month_health_gate"
SHORT_V2_KEPT = REPORTS_DIR / "A1_XAU_SHORT_HEDGE_EXACT_202207_202606_short_hedge_v2_breakdown_retest_KEPT.csv"
SHORT_V2_DROPPED = REPORTS_DIR / "A1_XAU_SHORT_HEDGE_EXACT_202207_202606_short_hedge_v2_breakdown_retest_DROPPED.csv"
SHORT_SOURCE_ID = "short_hedge_v2_breakdown_retest"


def build_variants() -> tuple[list[a1.Variant], dict[str, dict[str, Any]]]:
    variants: list[a1.Variant] = []
    metadata: dict[str, dict[str, Any]] = {}
    for component_key, component in COMPONENTS.items():
        name = f"{PROBE}_{component_key}"
        inputs = {
            **BASE_H4_INPUTS,
            **component["inputs"],
            "InpH4D1SupportiveStateGuardEnabled": "true",
            "InpH4D1SupportiveEmaPeriod": "20",
            "InpH4D1SupportiveSlopeLagBars": "5",
            "InpH4D1WeeklyLossGovernorEnabled": "false",
            "InpH4D1PrevMonthHealthGateEnabled": "true",
            "InpH4D1PrevMonthNetMinUsd": "-50.00",
        }
        variant = a1.Variant(
            name=name,
            label=f"H4 previous-month health gate on {component['source_id']}",
            run_id=f"BT_A1_XAU_H4_PREV_MONTH_HEALTH_{component_key.upper()}",
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


def short_v2_raw_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, int]] = set()
    for path in (SHORT_V2_KEPT, SHORT_V2_DROPPED):
        for row in read_composition_csv(path):
            if row.get("source_id") != SHORT_SOURCE_ID:
                continue
            key = (row["source_id"], row["entry_time"].strftime("%Y-%m-%d %H:%M:%S"), int(row.get("source_row") or 0))
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
    return rows


def evaluate(name: str, rows: list[dict[str, Any]], dropped: list[dict[str, Any]], baseline: dict[str, Any] | None) -> dict[str, Any]:
    enriched, exit_stats = enrich_exit_times(rows)
    metrics = summary_metrics(enriched, market_days=MARKET_DAYS)
    stress = summary_metrics(enriched, cost_per_ticket=0.30, market_days=MARKET_DAYS)
    months = month_shape(enriched)
    weeks = weekly_shape(enriched)
    row = {
        "name": name,
        "signals": metrics["signals"],
        "wins": metrics["wins"],
        "losses": metrics["losses"],
        "wr": metrics["win_rate_pct"],
        "wl": metrics["avg_win_loss"],
        "pf": metrics["profit_factor"],
        "net": metrics["net_usd"],
        "stress_030_wl": stress["avg_win_loss"],
        "stress_030_net": stress["net_usd"],
        "active_weekday_pct": metrics["active_weekday_pct"],
        "max_closed_dd": max_closed_drawdown(enriched),
        "positive_week_pct": weeks["positive_week_pct"],
        "worst_week": weeks["worst_week"],
        "blocked_signals": len(dropped),
        "exit_stats": exit_stats,
        "kept_rows": enriched,
        "dropped_rows": dropped,
        **months,
    }
    row["decision"] = "BASELINE" if baseline is None else decide(row, baseline)
    return row


def decide(row: dict[str, Any], baseline: dict[str, Any]) -> str:
    wl = row.get("wl") or 0.0
    stress_wl = row.get("stress_030_wl") or 0.0
    core_ok = (
        row["net"] >= 19000.0
        and row["wr"] >= 48.0
        and wl >= 2.0
        and stress_wl >= 1.90
        and row["active_weekday_pct"] >= 84.0
    )
    review_ok = (
        row["positive_months"] >= 32
        and core_ok
        and row["max_closed_dd"] <= baseline["max_closed_dd"] * 0.90
    )
    if review_ok:
        return "EXACT_SOURCE_HEALTH_REVIEW_CANDIDATE"
    if row["positive_months"] >= baseline["positive_months"] + 2 and core_ok:
        return "EXACT_SOURCE_HEALTH_WATCHLIST"
    if row["positive_months"] > baseline["positive_months"] and not core_ok:
        return "EXACT_MONTHLY_IMPROVES_CORE_BREAKS"
    return "EXACT_REJECT_NO_MONTHLY_REPAIR"


def strip_heavy(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in {"kept_rows", "dropped_rows"}}


def write_results(path: Path, rows: list[dict[str, Any]]) -> None:
    keys = list(strip_heavy(rows[0]).keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(strip_heavy(row))


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU H4 Previous-Month Health Gate Exact MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: exact-MT5 H4 component rerun with previous-month health gate, recomposed with existing exact-MT5 frequency and V2 short ledgers. No live/demo runtime, chart, preset, order, position, or broker state was changed.",
        "",
        f"Status: `{payload['status']}`",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        "",
        "## Results",
        "",
        "| Row | Decision | Signals | Blocked | WR% | W/L | Stress W/L | Active% | Net | Max DD | +Months | -Months | Pos weeks% | Worst month | Worst month net | Worst week |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |",
    ]
    for row in [payload["baseline"], payload["result"]]:
        lines.append(
            f"| `{row['name']}` | `{row['decision']}` | {row['signals']} | {row['blocked_signals']} | "
            f"{row['wr']:.2f} | {row['wl'] or 0.0:.4f} | {row['stress_030_wl'] or 0.0:.4f} | "
            f"{row['active_weekday_pct']:.2f} | {row['net']:.2f} | {row['max_closed_dd']:.2f} | "
            f"{row['positive_months']} | {row['negative_months']} | {row['positive_week_pct']:.2f} | "
            f"`{row['worst_month']}` | {row['worst_month_net']:.2f} | {row['worst_week']:.2f} |"
        )

    lines.extend(
        [
            "",
            "## MT5 Guard Counts",
            "",
            "| Variant | Trades | Orders | previous-month health blocks | supportive-state blocks | other guard blocks |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in payload["mt5_component_details"]:
        reasons = item["guard_counts"]["guard_reasons"]
        health = reasons.get("h4_d1_previous_month_health_gate", 0)
        support = reasons.get("h4_d1_supportive_state_guard", 0)
        other = sum(count for reason, count in reasons.items() if reason not in {"h4_d1_previous_month_health_gate", "h4_d1_supportive_state_guard"})
        lines.append(f"| `{item['variant']}` | {item['replacement_rows']} | {item['guard_counts']['order_rows']} | {health} | {support} | {other} |")

    lines.extend(["", "## Source Contributions", "", "| Source | Signals | Net USD |", "| --- | ---: | ---: |"])
    for source, contribution in payload["source_contributions"].items():
        lines.append(f"| `{source}` | {contribution['signals']} | {contribution['net_usd']:.2f} |")

    lines.extend(["", "## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for key, path in payload["outputs"].items():
        lines.append(f"- {key}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 H4 previous-month health gate probe.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    for path in (PREREG, BASELINE_RAW, LONG_PLUS_V2, SHORT_V2_KEPT, SHORT_V2_DROPPED):
        require_file(path)

    variants, metadata = build_variants()
    a1.VARIANTS = variants
    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    results_csv = REPORTS_DIR / f"{OUTPUT_STEM}_RESULTS.csv"
    kept_csv = REPORTS_DIR / f"{OUTPUT_STEM}_KEPT.csv"
    dropped_csv = REPORTS_DIR / f"{OUTPUT_STEM}_DROPPED.csv"
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

    baseline = evaluate("long_plus_short_v2_no_source_health_gate", read_ledger(LONG_PLUS_V2), [], None)

    raw = read_raw_rows(BASELINE_RAW)
    filtered_raw, removal_counts = remove_f33_and_h4_sources(raw)
    short_raw = short_v2_raw_rows()

    h4_rows: list[dict[str, Any]] = []
    mt5_component_details: list[dict[str, Any]] = []
    for result in mt5_payload["variants"]:
        meta = metadata[result["name"]]
        rows = replacement_rows(result, meta)
        h4_rows.extend(rows)
        mt5_component_details.append(
            {
                "variant": result["name"],
                "source_id": meta["source_id"],
                "replacement_rows": len(rows),
                "mt5_result": result,
                "guard_counts": guard_counts(result),
            }
        )

    recomposed_raw = filtered_raw + h4_rows + short_raw
    kept, dropped = dedupe_signals(recomposed_raw)
    result = evaluate("h4_prev_month_health_gate_exact", kept, dropped, baseline)

    write_signal_csv(kept_csv, result["kept_rows"])
    write_signal_csv(dropped_csv, dropped)
    write_results(results_csv, [baseline, result])

    if result["decision"] == "EXACT_SOURCE_HEALTH_REVIEW_CANDIDATE":
        status = "EXACT_SOURCE_HEALTH_REVIEW_CANDIDATE"
        interpretation = "The exact-MT5 component-local previous-month H4 health gate reached the review-candidate gate. Keep research-only and request review before demo discussion."
    elif result["decision"] == "EXACT_SOURCE_HEALTH_WATCHLIST":
        status = "EXACT_SOURCE_HEALTH_WATCHLIST"
        interpretation = "The exact-MT5 component-local previous-month H4 health gate preserved the core and improved monthly consistency enough for watchlist. Next step is reviewer review or a true combined-H4 runtime if exact group-gating is required."
    elif result["decision"] == "EXACT_MONTHLY_IMPROVES_CORE_BREAKS":
        status = "EXACT_SOURCE_HEALTH_SMOOTHING_ONLY"
        interpretation = "The exact-MT5 gate improved month count but broke the core. Do not promote."
    else:
        status = "NO_EXACT_SOURCE_HEALTH_SURVIVOR"
        interpretation = "The exact-MT5 component-local gate did not reproduce a useful monthly repair. Do not promote this gate."

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": rel(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "boundary": "exact_mt5_h4_components_recomposed_with_existing_exact_ledgers",
        "inputs": {
            "baseline_raw": rel(BASELINE_RAW),
            "long_plus_v2_baseline": rel(LONG_PLUS_V2),
            "short_v2_kept": rel(SHORT_V2_KEPT),
            "short_v2_dropped": rel(SHORT_V2_DROPPED),
        },
        "removal_counts": removal_counts,
        "short_v2_raw_rows": len(short_raw),
        "baseline": strip_heavy(baseline),
        "result": strip_heavy(result),
        "source_contributions": source_contributions(result["kept_rows"]),
        "mt5_scope": mt5_payload["scope"],
        "compile_log": mt5_payload["compile_log"],
        "mt5_component_details": mt5_component_details,
        "interpretation": interpretation,
        "outputs": {
            "report_md": rel(report_md),
            "report_json": rel(report_json),
            "results_csv": rel(results_csv),
            "kept_csv": rel(kept_csv),
            "dropped_csv": rel(dropped_csv),
            "mt5_components_md": rel(mt5_report_md),
            "mt5_components_json": rel(mt5_report_json),
        },
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "decision": result["decision"],
                "signals": result["signals"],
                "wr": result["wr"],
                "wl": result["wl"],
                "stress_030_wl": result["stress_030_wl"],
                "net": result["net"],
                "max_closed_dd": result["max_closed_dd"],
                "positive_months": result["positive_months"],
                "negative_months": result["negative_months"],
                "report": str(report_md),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
