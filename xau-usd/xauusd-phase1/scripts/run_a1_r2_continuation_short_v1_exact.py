from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_r1_pullback_long_v1_exact as r1
import run_a1_r2_pullback_rejection_short_v1_exact as r2v1
import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR, rel
from analyze_a1_xau_source_monthly_firewall import read_ledger
from run_a1_h4_d1_geometry_v2_weekly_shape import FROM_DATE, TO_DATE, sha256_file, write_signal_csv
from run_a1_h4_d1_review_repair_exact import guard_counts


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_R2_CONTINUATION_SHORT_V1_PREREG_2026_07_09.md"
OUTPUT_STEM = "A1_XAU_R2_CONTINUATION_SHORT_V1_EXACT_20260709"
TAG = "OWNER_GOAL_R2_CONTINUATION_SHORT_V1_EXACT_202207_202606"

BEST_R2_PULLBACK_BOOK = (
    REPORTS_DIR
    / "A1_XAU_R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_EXACT_20260709_r2_h1_m5_body58_hours05_18_NORMALIZED_TRADES.csv"
)

R2_CONT_SOURCE = "r2_continuation_short_v1"


COMMON_CONT_INPUTS = {
    **r2v1.R2_BASE_INPUTS,
    "InpSignalMode": "19",
    "InpMaxTradesPerDay": "12",
    "InpBearRetestLookbackBars": "10",
    "InpBearRetestSupportLookbackBars": "12",
    "InpBearRetestBreakAtr": "0.10",
    "InpBearRetestTouchAtr": "0.05",
    "InpBearRetestReclaimAtr": "0.05",
    "InpBearRetestStopBufferAtr": "0.25",
    "InpBearRetestMinBodyFraction": "0.45",
    "InpShortCloseLocation": "0.30",
    "InpBearImpulseRetestImpulseBars": "3",
    "InpBearImpulseRetestMinImpulseAtr": "1.20",
    "InpBearImpulseRetestBreakMinBodyFraction": "0.45",
}


def build_variants() -> list[a1.Variant]:
    return [
        a1.Variant(
            name="r2_break_retest_body45",
            label="Strict R2 M5 bear breakdown/retest, body >= 0.45, fixed 2R",
            run_id="BT_A1_XAU_R2_BREAK_RETEST_BODY45",
            tester_inputs={
                **COMMON_CONT_INPUTS,
                "InpSignalMode": "15",
            },
        ),
        a1.Variant(
            name="r2_impulse_retest_body45",
            label="Strict R2 M5 downside impulse/retest, body >= 0.45, fixed 2R",
            run_id="BT_A1_XAU_R2_IMPULSE_RETEST_BODY45",
            tester_inputs={
                **COMMON_CONT_INPUTS,
                "InpSignalMode": "19",
            },
        ),
        a1.Variant(
            name="r2_impulse_retest_q55",
            label="Strict R2 M5 downside impulse/retest quality, body >= 0.55, close <= 0.25, fixed 2R",
            run_id="BT_A1_XAU_R2_IMPULSE_RETEST_Q55",
            tester_inputs={
                **COMMON_CONT_INPUTS,
                "InpSignalMode": "19",
                "InpBearRetestMinBodyFraction": "0.55",
                "InpShortCloseLocation": "0.25",
                "InpBearImpulseRetestMinImpulseAtr": "1.50",
                "InpBearImpulseRetestBreakMinBodyFraction": "0.55",
            },
        ),
    ]


def continuation_rows(result: dict[str, Any], source_priority: int) -> list[dict[str, Any]]:
    rows = r1.mt5_rows(result, source_priority=source_priority)
    for row in rows:
        row["component"] = R2_CONT_SOURCE
        row["source_id"] = R2_CONT_SOURCE
        row["upstream_source_id"] = R2_CONT_SOURCE
        row["upstream_component"] = result["name"]
        row["family_group"] = "xau_r2_continuation_short"
        row["cell_id"] = "r2_continuation_short_v1"
    return rows


def standalone_checks(row: dict[str, Any]) -> dict[str, bool]:
    return {
        "wr_ge_50": row["wr"] >= 50.0,
        "wl_ge_1p90": (row["wl"] or 0.0) >= 1.90,
        "pf_ge_1p50": (row["pf"] or 0.0) >= 1.50,
        "net_gt_0": row["net"] > 0.0,
        "stress_net_gt_0": row["stress_030_net"] > 0.0,
        "stress_pf_ge_1p15": (row["stress_030_pf"] or 0.0) >= 1.15,
        "recent3_nonnegative_if_exposed": row["recent3_signals"] == 0 or row["recent3_net"] >= 0.0,
        "top10_removed_net_gt_0": row["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": row["top3_days_removed_net"] > 0.0,
    }


def combined_checks(row: dict[str, Any], baseline: dict[str, Any]) -> dict[str, bool]:
    return {
        "net_gt_r1_plus_best_r2_pullback": row["net"] > baseline["net"],
        "wr_ge_50": row["wr"] >= 50.0,
        "pf_ge_2": (row["pf"] or 0.0) >= 2.00,
        "recent3_net_ge_0": row["recent3_net"] >= 0.0,
        "dd_not_worse_10pct": row["max_closed_dd"] <= baseline["max_closed_dd"] * 1.10,
        "top10_removed_net_gt_0": row["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": row["top3_days_removed_net"] > 0.0,
    }


def decide(standalone_rows: list[dict[str, Any]], combined_rows: list[dict[str, Any]]) -> tuple[str, str]:
    for standalone, combined in zip(standalone_rows, combined_rows, strict=True):
        if all(standalone["standalone_checks"].values()) and all(combined["combined_checks"].values()):
            return (
                "R2_CONTINUATION_SHORT_V1_REVIEW_CANDIDATE",
                f"`{standalone['name']}` passed standalone quality checks and improved the current R1 plus repaired R2 pullback book. Keep research-only and send to review.",
            )
    if any(row["net"] > 0.0 and row["recent3_net"] >= 0.0 for row in standalone_rows):
        return (
            "R2_CONTINUATION_SHORT_V1_SHADOW_ONLY",
            "At least one R2 continuation variant was profitable and recent-period safe, but no variant cleared both standalone and combined gates.",
        )
    return (
        "R2_CONTINUATION_SHORT_V1_NO_SURVIVOR",
        "The strict-R2 continuation specialist did not produce a robust standalone or combined improvement.",
    )


def static_checks(variants: list[a1.Variant]) -> dict[str, bool]:
    blocked_fields = {
        "InpBlockedEntryHoursCsv",
        "InpBlockedEntryDayHoursCsv",
        "InpBlockedLongEntryHoursCsv",
        "InpBlockedShortEntryHoursCsv",
    }
    return {
        "variant_count_eq_3": len(variants) == 3,
        "all_strict_r2_router": all(variant.tester_inputs.get("InpRegimeRouterMode") == "2" for variant in variants),
        "all_short_only": all(variant.tester_inputs.get("InpDirectionMode") == "2" for variant in variants),
        "all_signal_15_or_19": all(variant.tester_inputs.get("InpSignalMode") in {"15", "19"} for variant in variants),
        "all_rr_2": all(variant.tester_inputs.get("InpRiskReward") == "2.00" for variant in variants),
        "no_session_filter": all(variant.tester_inputs.get("InpUseDirectionalSessionFilter") == "false" for variant in variants),
        "no_hour_day_filters": all(all(variant.tester_inputs.get(field, "") == "" for field in blocked_fields) for variant in variants),
        "no_breakeven_partial_trailing": all(
            variant.tester_inputs.get("InpProfitProtectionEnabled") == "false"
            and variant.tester_inputs.get("InpPartialCloseEnabled") == "false"
            and variant.tester_inputs.get("InpSplitEntryEnabled") == "false"
            for variant in variants
        ),
    }


def strip_heavy(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in r2v1.strip_heavy(row).items()
        if key not in {"yearly_rows", "monthly_rows"}
    }


def render_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = ["| Book | Period | Trades | WR% | W/L | PF | Net |", "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for row in rows:
        lines.append(
            f"| `{row['name']}` | `{row['period']}` | {row['signals']} | {row['wr']:.2f} | "
            f"{row['wl'] or 0.0:.4f} | {row['pf'] or 0.0:.4f} | {row['net']:.2f} |"
        )
    return lines


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU R2 Continuation Short V1 Exact-MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Scope: exact-MT5 research-only test for a second strict-R2 short specialist. No demo/live runtime, chart, preset, order, position, account, or broker state was changed.",
        "",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        f"Current R1 book: `{payload['current_r1_book']}`",
        f"Best repaired R2 pullback book: `{payload['best_r2_pullback_book']}`",
        f"MT5 component evidence: `{payload['outputs']['mt5_components_md']}`",
        "",
        "## Baseline Book",
        "",
        "| Book | Trades | WR% | W/L | PF | Net | Recent3 trades | Recent3 WR% | Recent3 PF | Recent3 net | Max DD |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    base = payload["baseline_row"]
    lines.append(
        f"| `{base['name']}` | {base['signals']} | {base['wr']:.2f} | {base['wl'] or 0.0:.4f} | "
        f"{base['pf'] or 0.0:.4f} | {base['net']:.2f} | {base['recent3_signals']} | {base['recent3_wr']:.2f} | "
        f"{base['recent3_pf'] or 0.0:.4f} | {base['recent3_net']:.2f} | {base['max_closed_dd']:.2f} |"
    )

    lines.extend(
        [
            "",
            "## Standalone Continuation Full Window",
            "",
            "| Variant | Trades | Wins | Losses | WR% | W/L | PF | Net | Stress W/L | Stress PF | Stress net | Max DD | Top10 rem | Top3 days rem | Best month% | Pass |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in payload["standalone_rows"]:
        share = row["best_month_share_pct"] if row["best_month_share_pct"] is not None else 0.0
        lines.append(
            f"| `{row['name']}` | {row['signals']} | {row['wins']} | {row['losses']} | {row['wr']:.2f} | "
            f"{row['wl'] or 0.0:.4f} | {row['pf'] or 0.0:.4f} | {row['net']:.2f} | "
            f"{row['stress_030_wl'] or 0.0:.4f} | {row['stress_030_pf'] or 0.0:.4f} | {row['stress_030_net']:.2f} | "
            f"{row['max_closed_dd']:.2f} | {row['top10_removed_net']:.2f} | {row['top3_days_removed_net']:.2f} | "
            f"{share:.2f} | {all(row['standalone_checks'].values())} |"
        )

    lines.extend(
        [
            "",
            "## Standalone Continuation Last Three Months",
            "",
            "| Variant | Recent3 trades | Recent3 WR% | Recent3 W/L | Recent3 PF | Recent3 net | June trades | June WR% | June PF | June net |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload["standalone_rows"]:
        lines.append(
            f"| `{row['name']}` | {row['recent3_signals']} | {row['recent3_wr']:.2f} | {row['recent3_wl'] or 0.0:.4f} | "
            f"{row['recent3_pf'] or 0.0:.4f} | {row['recent3_net']:.2f} | {row['june2026_signals']} | "
            f"{row['june2026_wr']:.2f} | {row['june2026_pf'] or 0.0:.4f} | {row['june2026_net']:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Combined With Current R1 Plus Best R2 Pullback",
            "",
            "| Book | Trades | WR% | W/L | PF | Net | Recent3 trades | Recent3 WR% | Recent3 PF | Recent3 net | Max DD | Dropped | Pass |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in payload["combined_rows"]:
        lines.append(
            f"| `{row['name']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['pf'] or 0.0:.4f} | {row['net']:.2f} | {row['recent3_signals']} | {row['recent3_wr']:.2f} | "
            f"{row['recent3_pf'] or 0.0:.4f} | {row['recent3_net']:.2f} | {row['max_closed_dd']:.2f} | "
            f"{row['dropped_signals']} | {all(row['combined_checks'].values())} |"
        )

    lines.extend(["", "## Yearly Table", ""])
    yearly_rows: list[dict[str, Any]] = []
    for row in payload["standalone_rows"] + payload["combined_rows"]:
        yearly_rows.extend(row["yearly_rows"])
    lines.extend(render_table(yearly_rows))

    lines.extend(["", "## Failed Checks", ""])
    for row in payload["standalone_rows"]:
        failed = [key for key, value in row["standalone_checks"].items() if not value]
        lines.append(f"- `{row['name']}` standalone: {', '.join(failed) if failed else 'none'}")
    for row in payload["combined_rows"]:
        failed = [key for key, value in row["combined_checks"].items() if not value]
        lines.append(f"- `{row['name']}` combined: {', '.join(failed) if failed else 'none'}")

    lines.extend(["", "## Guard Summary", ""])
    for item in payload["mt5_component_details"]:
        lines.append(f"### `{item['variant']}`")
        for reason, count in sorted(item["guard_counts"]["guard_reasons"].items()):
            if reason.startswith("regime_router_block") or reason in {"pass", "stop_ceiling_exceeded", "spread_too_high", "estimated_cost_r_too_high"}:
                lines.append(f"- `{reason}`: {count}")
        lines.append("")

    lines.extend(["## Static Validation", ""])
    for key, value in payload["static_checks"].items():
        lines.append(f"- `{key}`: {value}")

    lines.extend(["", "## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for key, path in payload["outputs"].items():
        lines.append(f"- {key}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 R2 continuation short V1.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    r2v1.require_file(PREREG)
    r2v1.require_file(r2v1.CURRENT_R1_BOOK)
    r2v1.require_file(BEST_R2_PULLBACK_BOOK)

    variants = build_variants()
    checks = static_checks(variants)
    if not all(checks.values()):
        raise RuntimeError(f"Invalid static runner configuration: {checks}")

    a1.VARIANTS = variants

    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    standalone_csv = REPORTS_DIR / f"{OUTPUT_STEM}_STANDALONE.csv"
    combined_csv = REPORTS_DIR / f"{OUTPUT_STEM}_COMBINED.csv"
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

    r1_rows = read_ledger(r2v1.CURRENT_R1_BOOK)
    pullback_rows = read_ledger(BEST_R2_PULLBACK_BOOK)
    baseline_rows = r1_rows + pullback_rows
    baseline = r2v1.evaluate_book("current_r1_plus_best_r2_pullback", baseline_rows, dedupe=True)

    standalone_rows: list[dict[str, Any]] = []
    combined_rows: list[dict[str, Any]] = []
    mt5_component_details: list[dict[str, Any]] = []

    for index, result in enumerate(mt5_payload["variants"], start=1):
        rows = continuation_rows(result, source_priority=96 + index)
        normalized_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{result['name']}_NORMALIZED_TRADES.csv"
        write_signal_csv(normalized_csv, rows)

        standalone = r2v1.evaluate_book(result["name"], rows)
        standalone["standalone_checks"] = standalone_checks(standalone)
        standalone_rows.append(standalone)

        combined = r2v1.evaluate_book(f"current_r1_best_r2_pullback_plus_{result['name']}", baseline_rows + rows, dedupe=True)
        combined["combined_checks"] = combined_checks(combined, baseline)
        combined_rows.append(combined)
        write_signal_csv(REPORTS_DIR / f"{OUTPUT_STEM}_{combined['name']}_KEPT.csv", combined["data"])
        write_signal_csv(REPORTS_DIR / f"{OUTPUT_STEM}_{combined['name']}_DROPPED.csv", combined["dropped_data"])

        mt5_component_details.append(
            {
                "variant": result["name"],
                "mt5_result": result,
                "guard_counts": guard_counts(result),
                "normalized_trades": len(rows),
                "tester_input_sha256": r2v1.stable_hash(variants[index - 1].tester_inputs),
            }
        )

    status, interpretation = decide(standalone_rows, combined_rows)
    r1.write_csv(standalone_csv, [strip_heavy(row) for row in standalone_rows])
    r1.write_csv(combined_csv, [strip_heavy(row) for row in combined_rows])

    outputs = {
        "report_md": rel(report_md),
        "report_json": rel(report_json),
        "standalone_csv": rel(standalone_csv),
        "combined_csv": rel(combined_csv),
        "mt5_components_md": rel(mt5_report_md),
        "mt5_components_json": rel(mt5_report_json),
    }
    for row in standalone_rows:
        outputs[f"{row['name']}_normalized_trades_csv"] = rel(REPORTS_DIR / f"{OUTPUT_STEM}_{row['name']}_NORMALIZED_TRADES.csv")
    for row in combined_rows:
        outputs[f"{row['name']}_kept_csv"] = rel(REPORTS_DIR / f"{OUTPUT_STEM}_{row['name']}_KEPT.csv")
        outputs[f"{row['name']}_dropped_csv"] = rel(REPORTS_DIR / f"{OUTPUT_STEM}_{row['name']}_DROPPED.csv")

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": rel(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "current_r1_book": rel(r2v1.CURRENT_R1_BOOK),
        "current_r1_book_sha256": sha256_file(r2v1.CURRENT_R1_BOOK),
        "best_r2_pullback_book": rel(BEST_R2_PULLBACK_BOOK),
        "best_r2_pullback_book_sha256": sha256_file(BEST_R2_PULLBACK_BOOK),
        "mt5_scope": mt5_payload["scope"],
        "compile_log": mt5_payload["compile_log"],
        "baseline_row": strip_heavy(baseline),
        "standalone_rows": [
            strip_heavy(row) | {"standalone_checks": row["standalone_checks"], "yearly_rows": row["yearly_rows"], "monthly_rows": row["monthly_rows"]}
            for row in standalone_rows
        ],
        "combined_rows": [
            strip_heavy(row) | {"combined_checks": row["combined_checks"], "yearly_rows": row["yearly_rows"], "monthly_rows": row["monthly_rows"]}
            for row in combined_rows
        ],
        "mt5_component_details": mt5_component_details,
        "static_checks": checks,
        "interpretation": interpretation,
        "outputs": outputs,
    }

    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "baseline": strip_heavy(baseline),
                "standalone": [strip_heavy(row) | {"standalone_checks": row["standalone_checks"]} for row in standalone_rows],
                "combined": [strip_heavy(row) | {"combined_checks": row["combined_checks"]} for row in combined_rows],
                "report": str(report_md),
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
