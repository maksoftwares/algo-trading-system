from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR, dedupe_signals, rel
from analyze_a1_xau_source_monthly_firewall import read_ledger
from run_a1_h4_box2_health_daily_stack_cap_exact import evaluate, strip_heavy, write_results
from run_a1_h4_d1_geometry_v2_weekly_shape import BASELINE_RAW, FROM_DATE, TO_DATE, write_signal_csv
from run_a1_h4_d1_review_repair_exact import (
    BASE_H4_INPUTS,
    COMPONENTS,
    guard_counts,
    read_raw_rows,
    remove_f33_and_h4_sources,
    replacement_rows,
    require_file,
    sha256_file,
    source_contributions,
)
from run_a1_h4_previous_month_health_gate_exact import short_v2_raw_rows


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_H4_BOX2_HEALTH_THIRD_ENTRY_QUALITY_EXACT_PREREG_2026_07_08.md"
OUTPUT_STEM = "A1_XAU_H4_BOX2_HEALTH_THIRD_ENTRY_QUALITY_EXACT_202207_202606"
TAG = "OWNER_GOAL_H4_BOX2_HEALTH_THIRD_ENTRY_QUALITY_EXACT_202207_202606"
BASE_CANDIDATE_KEPT = REPORTS_DIR / "A1_XAU_H4_BOX2_HEALTH_BROAD_QUARANTINE_202207_202606_prevhealth_box2_broad_quarantined_KEPT.csv"


def build_variant() -> tuple[a1.Variant, dict[str, Any]]:
    component = COMPONENTS["box2"]
    inputs = {
        **BASE_H4_INPUTS,
        **component["inputs"],
        "InpMaxTradesPerDay": "6",
        "InpOnePositionPerMagic": "false",
        "InpMaxOpenPositionsPerMagic": "32",
        "InpH4D1SupportiveStateGuardEnabled": "true",
        "InpH4D1SupportiveEmaPeriod": "20",
        "InpH4D1SupportiveSlopeLagBars": "5",
        "InpH4D1PrevMonthHealthGateEnabled": "true",
        "InpH4D1PrevMonthNetMinUsd": "-50.00",
        "InpH4D1WeeklyLossGovernorEnabled": "false",
        "InpH4D1NegativeStackGuardEnabled": "false",
        "InpH4D1ThirdEntryQualityGateEnabled": "true",
        "InpH4D1ThirdEntryQualityNormalEntries": "2",
        "InpH4D1ThirdEntryMinH4BodyFraction": "0.50",
        "InpH4D1ThirdEntryMinBreakDistanceAtr": "0.10",
    }
    variant = a1.Variant(
        name="prevhealth_box2_third_entry_quality",
        label="H4/D1 box2 supportive + previous-month health gate + third-entry H4 quality gate",
        run_id="BT_A1_XAU_H4_BOX2_HEALTH_THIRD_ENTRY_QUALITY",
        tester_inputs=inputs,
    )
    metadata = {
        "probe": "prevhealth_third_entry_quality",
        "component_key": "box2",
        "source_id": component["source_id"],
        "source_priority": component["source_priority"],
        "family_group": "h4_d1_core_shape",
        "label": variant.label,
    }
    return variant, metadata


def status_for(decision: str) -> tuple[str, str]:
    if decision == "H4_BOX2_DAILY_STACK_CAP_REVIEW_CANDIDATE":
        return (
            "H4_BOX2_THIRD_ENTRY_QUALITY_REVIEW_CANDIDATE",
            "The third-entry quality gate repaired the weekly tail without breaking the monthly/core candidate. Keep research-only and send for review.",
        )
    if decision == "H4_BOX2_DAILY_STACK_CAP_WATCHLIST_PARTIAL_TAIL_REPAIR":
        return (
            "H4_BOX2_THIRD_ENTRY_QUALITY_WATCHLIST_PARTIAL_TAIL_REPAIR",
            "The third-entry quality gate partially improved the weekly tail but did not pass the full preregistered review gate. Keep watchlist-only.",
        )
    if decision == "H4_BOX2_DAILY_STACK_CAP_CORE_ONLY":
        return (
            "H4_BOX2_THIRD_ENTRY_QUALITY_CORE_ONLY",
            "The third-entry quality gate preserved the core but did not repair the weekly tail. Same-day third-entry H4 quality is not enough.",
        )
    return "NO_H4_BOX2_THIRD_ENTRY_QUALITY_SURVIVOR", "The third-entry quality gate broke the core candidate. Do not promote."


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU H4 Box2 Health Gate + Third-Entry Quality Exact MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        "",
        "Scope: one exact-MT5 H4/D1 box2 rerun with supportive guard, previous-month health gate, and a third-entry H4 quality gate; broad H4/D1 is quarantined. No live/demo runtime, chart, preset, order, position, or broker state was changed.",
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

    lines.extend(["", "## Source Contributions", "", "| Source | Signals | Net USD |", "| --- | ---: | ---: |"])
    for source, contribution in payload["source_contributions"].items():
        lines.append(f"| `{source}` | {contribution['signals']} | {contribution['net_usd']:.2f} |")

    reasons = payload["guard_counts"]["guard_reasons"]
    lines.extend(
        [
            "",
            "## MT5 Guard Counts",
            "",
            f"- Orders: `{payload['guard_counts']['order_rows']}`",
            f"- Third-entry quality blocks: `{reasons.get('h4_d1_third_entry_quality_gate', 0)}`",
            f"- Previous-month health blocks: `{reasons.get('h4_d1_previous_month_health_gate', 0)}`",
            f"- Supportive-state blocks: `{reasons.get('h4_d1_supportive_state_guard', 0)}`",
            "",
            "## Interpretation",
            "",
            payload["interpretation"],
            "",
            "## Artifacts",
            "",
        ]
    )
    for key, path in payload["outputs"].items():
        lines.append(f"- {key}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 H4 box2 health gate with third-entry quality gate.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    for path in (PREREG, BASELINE_RAW, BASE_CANDIDATE_KEPT):
        require_file(path)

    variant, metadata = build_variant()
    a1.VARIANTS = [variant]
    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    results_csv = REPORTS_DIR / f"{OUTPUT_STEM}_RESULTS.csv"
    kept_csv = REPORTS_DIR / f"{OUTPUT_STEM}_KEPT.csv"
    dropped_csv = REPORTS_DIR / f"{OUTPUT_STEM}_DROPPED.csv"
    mt5_report_md = REPORTS_DIR / f"{OUTPUT_STEM}_MT5_COMPONENT.md"
    mt5_report_json = REPORTS_DIR / f"{OUTPUT_STEM}_MT5_COMPONENT.json"

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

    baseline = evaluate("prevhealth_box2_broad_quarantined", read_ledger(BASE_CANDIDATE_KEPT), [], None)
    filtered_raw, removal_counts = remove_f33_and_h4_sources(read_raw_rows(BASELINE_RAW))
    short_raw = short_v2_raw_rows()
    box2_rows = replacement_rows(mt5_payload["variants"][0], metadata)
    kept, dropped = dedupe_signals(filtered_raw + box2_rows + short_raw)
    result = evaluate("prevhealth_box2_third_entry_quality_broad_quarantined", kept, dropped, baseline)
    status, interpretation = status_for(result["decision"])
    result["decision"] = status

    write_signal_csv(kept_csv, result["kept_rows"])
    write_signal_csv(dropped_csv, dropped)
    write_results(results_csv, [baseline, result])

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": rel(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "inputs": {
            "baseline_candidate_kept": rel(BASE_CANDIDATE_KEPT),
            "baseline_raw": rel(BASELINE_RAW),
        },
        "removal_counts": removal_counts,
        "short_v2_raw_rows": len(short_raw),
        "box2_replacement_rows": len(box2_rows),
        "baseline": strip_heavy(baseline),
        "result": strip_heavy(result),
        "source_contributions": source_contributions(result["kept_rows"]),
        "guard_counts": guard_counts(mt5_payload["variants"][0]),
        "mt5_scope": mt5_payload["scope"],
        "compile_log": mt5_payload["compile_log"],
        "interpretation": interpretation,
        "outputs": {
            "report_md": rel(report_md),
            "report_json": rel(report_json),
            "results_csv": rel(results_csv),
            "kept_csv": rel(kept_csv),
            "dropped_csv": rel(dropped_csv),
            "mt5_component_md": rel(mt5_report_md),
            "mt5_component_json": rel(mt5_report_json),
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
                "worst_week": result["worst_week"],
                "report": str(report_md),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
