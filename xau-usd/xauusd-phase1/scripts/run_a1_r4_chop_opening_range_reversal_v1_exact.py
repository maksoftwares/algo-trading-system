from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_a1_r1_pullback_long_v1_exact as r1
import run_a1_r4_chop_failed_break_v1_exact as r4
import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR, rel
from analyze_a1_xau_source_monthly_firewall import read_ledger
from run_a1_h4_d1_geometry_v2_weekly_shape import FROM_DATE, TO_DATE, sha256_file, write_signal_csv
from run_a1_h4_d1_review_repair_exact import guard_counts


PHASE1_ROOT = Path(__file__).resolve().parents[1]
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_R4_CHOP_OPENING_RANGE_REVERSAL_V1_EXACT_PREREG_2026_07_09.md"
OUTPUT_STEM = "A1_XAU_R4_CHOP_OPENING_RANGE_REVERSAL_V1_EXACT_20260709"
TAG = "OWNER_GOAL_R4_CHOP_ORREV_V1_EXACT_202207_202606"
FAMILY_GROUP = "xau_r4_chop_opening_range_reversal"

CURRENT_R1_R2_BOOK = (
    REPORTS_DIR
    / "A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10_KEPT.csv"
)

BASE_INPUTS = {
    **r4.R4_INPUTS,
    "InpRegimeRouterMode": "4",
    "InpSignalMode": "6",
    "InpRiskReward": "2.00",
    "InpMaxEstimatedCostR": "0.08",
    "InpMaxSpreadPoints": "75",
    "InpMaxTradesPerDay": "24",
    "InpCooldownMinutes": "0",
    "InpOnePositionPerMagic": "true",
    "InpMaxOpenPositionsPerMagic": "1",
    "InpUseDirectionalSessionFilter": "false",
    "InpUseH1TrendFilter": "false",
    "InpUseH4TrendFilter": "false",
    "InpProfitProtectionEnabled": "false",
    "InpPartialCloseEnabled": "false",
    "InpSplitEntryEnabled": "false",
    "InpOpeningRangeStartHour": "7",
    "InpOpeningRangeMinutes": "60",
    "InpOpeningTradeWindowHours": "5",
    "InpOpeningBreakAtrMultiple": "0.10",
    "InpReclaimAtrMultiple": "0.05",
    "InpMinRangeAtr": "0.40",
    "InpMinBodyFraction": "0.35",
    "InpLongCloseLocation": "0.60",
    "InpShortCloseLocation": "0.40",
    "InpStopAtrMultiple": "1.50",
    "InpStopFloorPoints": "250",
    "InpStopCeilingPoints": "1400",
    "InpStopCapPoints": "0",
}


def build_variants() -> list[a1.Variant]:
    specs: list[tuple[str, str, str]] = [
        ("r4_chop_orrev_london_firm_both", "both directions", "0"),
        ("r4_chop_orrev_london_firm_long", "long-only", "1"),
        ("r4_chop_orrev_london_firm_short", "short-only", "2"),
    ]
    return [
        a1.Variant(
            name=name,
            label=f"R4 chop-only London opening-range reversal, {label}, fixed 2R",
            run_id=f"BT_A1_XAU_R4_CHOP_ORREV_{name.upper()}",
            tester_inputs={**BASE_INPUTS, "InpDirectionMode": direction_mode},
        )
        for name, label, direction_mode in specs
    ]


def static_checks(variants: list[a1.Variant]) -> dict[str, bool]:
    return {
        "variant_count_eq_3": len(variants) == 3,
        "all_r4_router": all(variant.tester_inputs.get("InpRegimeRouterMode") == "4" for variant in variants),
        "all_signal_6": all(variant.tester_inputs.get("InpSignalMode") == "6" for variant in variants),
        "all_rr_2": all(variant.tester_inputs.get("InpRiskReward") == "2.00" for variant in variants),
        "direction_split_exact": [variant.tester_inputs.get("InpDirectionMode") for variant in variants] == ["0", "1", "2"],
        "all_london_or": all(
            variant.tester_inputs.get("InpOpeningRangeStartHour") == "7"
            and variant.tester_inputs.get("InpOpeningRangeMinutes") == "60"
            and variant.tester_inputs.get("InpOpeningTradeWindowHours") == "5"
            for variant in variants
        ),
        "no_management_layers": all(
            variant.tester_inputs.get("InpProfitProtectionEnabled") == "false"
            and variant.tester_inputs.get("InpPartialCloseEnabled") == "false"
            and variant.tester_inputs.get("InpSplitEntryEnabled") == "false"
            for variant in variants
        ),
    }


def mt5_rows(result: dict[str, Any], priority: int) -> list[dict[str, Any]]:
    rows = r1.mt5_rows(result, source_priority=priority)
    for row in rows:
        row["component"] = result["name"]
        row["source_id"] = result["name"]
        row["upstream_source_id"] = result["name"]
        row["upstream_component"] = result["name"]
        row["family_group"] = FAMILY_GROUP
        row["cell_id"] = result["name"]
    return rows


def standalone_checks(row: dict[str, Any]) -> dict[str, bool]:
    return {
        "trades_ge_150": row["signals"] >= 150,
        "wr_ge_45": row["wr"] >= 45.0,
        "wl_ge_1p80": (row["wl"] or 0.0) >= 1.80,
        "pf_ge_1p30": (row["pf"] or 0.0) >= 1.30,
        "stress_pf_ge_1p15": (row["stress_030_pf"] or 0.0) >= 1.15,
        "stress_wl_ge_1p65": (row["stress_030_wl"] or 0.0) >= 1.65,
        "net_gt_0": row["net"] > 0.0,
        "recent3_trades_ge_20": row["recent3_signals"] >= 20,
        "recent3_net_gt_0": row["recent3_net"] > 0.0,
        "net_2023_2024_ge_0": row["net_2023_2024"] >= 0.0,
        "top10_removed_net_gt_0": row["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": row["top3_days_removed_net"] > 0.0,
    }


def combined_checks(row: dict[str, Any], baseline: dict[str, Any]) -> dict[str, bool]:
    return {
        "net_gt_current_r1_r2": row["net"] > baseline["net"],
        "recent3_net_gt_current_r1_r2": row["recent3_net"] > baseline["recent3_net"],
        "wr_ge_50": row["wr"] >= 50.0,
        "wl_or_stress_wl_ok": (row["wl"] or 0.0) >= 2.00 or (row["stress_030_wl"] or 0.0) >= 1.90,
        "pf_ge_2": (row["pf"] or 0.0) >= 2.00,
        "stress_net_gt_0": row["stress_030_net"] > 0.0,
        "dd_not_worse_15pct": row["max_closed_dd"] <= baseline["max_closed_dd"] * 1.15,
        "top10_removed_net_gt_0": row["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": row["top3_days_removed_net"] > 0.0,
    }


def decide(standalones: list[dict[str, Any]], combineds: list[dict[str, Any]], baseline: dict[str, Any]) -> tuple[str, str]:
    paired = list(zip(standalones, combineds, strict=True))
    if any(all(standalone["checks"].values()) and all(combined["checks"].values()) for standalone, combined in paired):
        return (
            "R4_CHOP_ORREV_V1_REVIEW_CANDIDATE",
            "At least one R4 opening-range reversal variant passed standalone and combined checks. Keep research-only and send for reviewer approval.",
        )
    if any(standalone["net"] > 0.0 and combined["recent3_net"] > baseline["recent3_net"] for standalone, combined in paired):
        return (
            "R4_CHOP_ORREV_V1_SHADOW_ONLY",
            "At least one variant added recent-three-month value but did not clear the full standalone and combined promotion checks.",
        )
    return (
        "R4_CHOP_ORREV_V1_NO_SURVIVOR",
        "The R4 opening-range reversal direction split did not produce a deployable improvement over the current R1+R2 baseline.",
    )


def _result_row(row: dict[str, Any]) -> str:
    return (
        f"| `{row['name']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
        f"{row['pf'] or 0.0:.4f} | {row['net']:.2f} | {row['stress_030_wl'] or 0.0:.4f} | "
        f"{row['stress_030_pf'] or 0.0:.4f} | {row['recent3_signals']} | {row['recent3_net']:.2f} | "
        f"{row['max_closed_dd']:.2f} | {row['top10_removed_net']:.2f} | {row['top3_days_removed_net']:.2f} | "
        f"{all(row['checks'].values())} |"
    )


def render(payload: dict[str, Any]) -> str:
    baseline = payload["baseline"]
    lines = [
        "# A1 XAU R4 Chop Opening-Range Reversal V1 Exact-MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Scope: exact-MT5 run using the EA-side R4 chop-only router and opening-range reversal signal. Research-only.",
        "",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        "",
        "## Current R1+R2 Baseline",
        "",
        f"Current R1+R2 book: {baseline['signals']} trades, WR {baseline['wr']:.2f}%, W/L {baseline['wl'] or 0.0:.4f}, "
        f"PF {baseline['pf'] or 0.0:.4f}, net {baseline['net']:.2f}, recent3 trades {baseline['recent3_signals']}, "
        f"recent3 net {baseline['recent3_net']:.2f}, max DD {baseline['max_closed_dd']:.2f}.",
        "",
        "## Standalone R4 Results",
        "",
        "| Variant | Trades | WR% | W/L | PF | Net | Stress W/L | Stress PF | Recent3 trades | Recent3 net | Max DD | Top10 rem | Top3 days rem | Pass |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["standalones"]:
        lines.append(_result_row(row))

    lines.extend(
        [
            "",
            "## Combined With Current R1+R2",
            "",
            "| Book | Trades | WR% | W/L | PF | Net | Stress W/L | Stress PF | Recent3 trades | Recent3 net | Max DD | Top10 rem | Top3 days rem | Pass |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in payload["combineds"]:
        lines.append(_result_row(row))

    lines.extend(["", "## Failed Checks", ""])
    for section in ("standalones", "combineds"):
        for row in payload[section]:
            failed = [key for key, value in row["checks"].items() if not value]
            lines.append(f"- `{row['name']}`: {', '.join(failed) if failed else 'none'}")

    lines.extend(["", "## Router / Guard Notes", ""])
    for name, counts in payload["guard_counts"].items():
        lines.append(f"### `{name}`")
        for reason, count in sorted(counts["guard_reasons"].items()):
            if reason.startswith("regime_router_block") or reason in {
                "pass",
                "stop_ceiling_exceeded",
                "spread_too_high",
                "estimated_cost_r_too_high",
                "max_open_positions_reached",
                "daily_trade_cap_reached",
            }:
                lines.append(f"- `{reason}`: {count}")
        lines.append("")

    lines.extend(["## Interpretation", "", payload["interpretation"], "", "## Artifacts", ""])
    for key, path in payload["outputs"].items():
        lines.append(f"- {key}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-MT5 R4 chop opening-range reversal V1.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    r4.require_file(PREREG)
    r4.require_file(CURRENT_R1_R2_BOOK)

    variants = build_variants()
    checks = static_checks(variants)
    if not all(checks.values()):
        raise RuntimeError(f"Invalid static runner configuration: {checks}")

    a1.VARIANTS = variants
    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    standalone_csv = REPORTS_DIR / f"{OUTPUT_STEM}_STANDALONE.csv"
    combined_csv = REPORTS_DIR / f"{OUTPUT_STEM}_COMBINED.csv"
    mt5_report_md = REPORTS_DIR / f"{OUTPUT_STEM}_MT5.md"
    mt5_report_json = REPORTS_DIR / f"{OUTPUT_STEM}_MT5.json"

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

    baseline_rows = read_ledger(CURRENT_R1_R2_BOOK)
    baseline = r4.enriched_book("current_r1_r2_best", baseline_rows)
    standalones: list[dict[str, Any]] = []
    combineds: list[dict[str, Any]] = []
    guards: dict[str, Any] = {}
    outputs: dict[str, str] = {
        "report_md": rel(report_md),
        "report_json": rel(report_json),
        "standalone_csv": rel(standalone_csv),
        "combined_csv": rel(combined_csv),
        "mt5_report_md": rel(mt5_report_md),
        "mt5_report_json": rel(mt5_report_json),
    }

    for index, result in enumerate(mt5_payload["variants"], start=1):
        rows = mt5_rows(result, priority=150 + index)
        standalone = r4.enriched_book(result["name"], rows)
        combined = r4.enriched_book(f"current_r1_r2_plus_{result['name']}", baseline_rows + rows, dedupe=True)
        standalone["checks"] = standalone_checks(standalone)
        combined["checks"] = combined_checks(combined, baseline)
        standalones.append(standalone)
        combineds.append(combined)
        guards[result["name"]] = guard_counts(result)

        normalized_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{result['name']}_NORMALIZED_TRADES.csv"
        combined_kept_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{combined['name']}_KEPT.csv"
        combined_dropped_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{combined['name']}_DROPPED.csv"
        write_signal_csv(normalized_csv, rows)
        write_signal_csv(combined_kept_csv, combined["data"])
        write_signal_csv(combined_dropped_csv, combined["dropped_data"])
        outputs[f"{result['name']}_normalized_trades_csv"] = rel(normalized_csv)
        outputs[f"{result['name']}_combined_kept_csv"] = rel(combined_kept_csv)
        outputs[f"{result['name']}_combined_dropped_csv"] = rel(combined_dropped_csv)

    status, interpretation = decide(standalones, combineds, baseline)
    r1.write_csv(standalone_csv, [r1.strip_heavy(row) for row in standalones])
    r1.write_csv(combined_csv, [r1.strip_heavy(row) for row in combineds])

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": rel(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "current_r1_r2_book": rel(CURRENT_R1_R2_BOOK),
        "current_r1_r2_book_sha256": sha256_file(CURRENT_R1_R2_BOOK),
        "mt5_scope": mt5_payload["scope"],
        "compile_log": mt5_payload["compile_log"],
        "mt5_results": mt5_payload["variants"],
        "static_checks": checks,
        "guard_counts": guards,
        "baseline": r1.strip_heavy(baseline),
        "standalones": [r1.strip_heavy(row) | {"checks": row["checks"]} for row in standalones],
        "combineds": [r1.strip_heavy(row) | {"checks": row["checks"]} for row in combineds],
        "interpretation": interpretation,
        "outputs": outputs,
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "baseline": payload["baseline"],
                "standalones": payload["standalones"],
                "combineds": payload["combineds"],
                "report": str(report_md),
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

