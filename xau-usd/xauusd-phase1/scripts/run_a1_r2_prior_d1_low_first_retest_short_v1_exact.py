from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import analyze_a1_r2_prior_d1_low_first_retest_episode_audit as episode_audit
import run_a1_r1_pullback_long_v1_exact as r1
import run_a1_r2_pullback_rejection_short_v1_exact as r2_common
import run_a1_xau_m5_momentum_backtest_variants as a1
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR, rel
from run_a1_h4_d1_geometry_v2_weekly_shape import FROM_DATE, TO_DATE, sha256_file, write_signal_csv
from run_a1_h4_d1_review_repair_exact import guard_counts


PHASE1_ROOT = Path(__file__).resolve().parents[1]
EA_SOURCE = PHASE1_ROOT / "mt5" / "Experts" / "A1XauM5MomentumContinuationExecutor.mq5"
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_R2_PRIOR_D1_LOW_FIRST_RETEST_SHORT_V1_PREREG_2026_07_10.md"
OUTPUT_STEM = "A1_XAU_R2_PRIOR_D1_LOW_FIRST_RETEST_SHORT_V1_EXACT_20260710"
TAG = "OWNER_GOAL_R2_PRIOR_D1_LOW_FIRST_RETEST_SHORT_V1_EXACT_202207_202606"
SOURCE_ID = "r2_prior_d1_low_first_retest_short_v1"
VARIANT_NAME = "r2_pdl_first_retest_structural_v1"
HISTORICAL_RUN_AUTHORIZED = True


FROZEN_INPUTS = {
    **r2_common.R2_BASE_INPUTS,
    "InpSignalMode": "22",
    "InpRegimeRouterMode": "2",
    "InpDirectionMode": "2",
    "InpRiskReward": "2.00",
    "InpR2PdlAtrPeriod": "14",
    "InpR2PdlH1AtrPercentileLookback": "480",
    "InpR2PdlH1AtrPercentileMin": "40.00",
    "InpR2PdlH1AtrPercentileMax": "90.00",
    "InpR2PdlBreakMarginH1Atr": "0.10",
    "InpR2PdlBreakMinRangeH1Atr": "1.00",
    "InpR2PdlBreakMinBodyFraction": "0.50",
    "InpR2PdlBreakCloseLocationMax": "0.25",
    "InpR2PdlRetestWindowM15Bars": "8",
    "InpR2PdlRetestTouchM15Atr": "0.25",
    "InpR2PdlInvalidReclaimH1Atr": "0.10",
    "InpR2PdlRejectDistanceM15Atr": "0.10",
    "InpR2PdlRejectMinBodyFraction": "0.50",
    "InpR2PdlRejectCloseLocationMax": "0.25",
    "InpR2PdlStopBufferM15Atr": "0.20",
    "InpR2PdlMaxStopH1Atr": "1.00",
    "InpMinAtrAbsoluteForEntry": "0.00",
    "InpStopFloorPoints": "0",
    "InpStopCeilingPoints": "0",
    "InpStopCapPoints": "0",
    "InpMaxEstimatedCostR": "0.10",
    "InpUseRiskNormalizedLots": "true",
    "InpRiskAmountUsd": "50.00",
    "InpMaxRiskLots": "0.10",
    "InpRejectRiskOvershootEnabled": "true",
    "InpMaxRiskOvershootPct": "10.00",
    "InpOnePositionPerMagic": "true",
    "InpMaxOpenPositionsPerMagic": "1",
    "InpMaxTradesPerDay": "0",
    "InpCooldownMinutes": "0",
    "InpPortfolioDailyGuardEnabled": "false",
    "InpBlockedEntryHoursCsv": "",
    "InpBlockedEntryDayHoursCsv": "",
    "InpBlockedLongEntryHoursCsv": "",
    "InpBlockedShortEntryHoursCsv": "",
    "InpUseDirectionalSessionFilter": "false",
    "InpProfitProtectionEnabled": "false",
    "InpPartialCloseEnabled": "false",
    "InpSplitEntryEnabled": "false",
}


def build_variants() -> list[a1.Variant]:
    return [
        a1.Variant(
            name=VARIANT_NAME,
            label="Strict-R2 prior-D1-low H1 acceptance and first M15 failed-reclaim short, fixed 2R",
            run_id="BT_A1_XAU_R2_PDL_FIRST_RETEST_STRUCTURAL_V1",
            tester_inputs=dict(FROZEN_INPUTS),
        )
    ]


def static_checks(variants: list[a1.Variant] | None = None) -> dict[str, bool]:
    variants = variants or build_variants()
    expected = dict(FROZEN_INPUTS)
    variant = variants[0] if len(variants) == 1 else None
    inputs = variant.tester_inputs if variant is not None else {}
    ea_source = EA_SOURCE.read_text(encoding="utf-8") if EA_SOURCE.exists() else ""
    forbidden_calendar_fields = (
        "InpBlockedEntryHoursCsv",
        "InpBlockedEntryDayHoursCsv",
        "InpBlockedLongEntryHoursCsv",
        "InpBlockedShortEntryHoursCsv",
    )
    return {
        "exactly_one_variant": len(variants) == 1,
        "variant_name_frozen": variant is not None and variant.name == VARIANT_NAME,
        "tester_inputs_exactly_frozen": inputs == expected,
        "signal_mode_22": inputs.get("InpSignalMode") == "22",
        "completed_m15_counter_runtime": all(
            token in ea_source
            for token in (
                "g_r2_pdl_last_counted_m15_bar",
                "g_r2_pdl_retest_m15_bars_observed",
                "R2PdlTakeDistinctCompletedM15Bar",
                "final_retest_bar",
            )
        )
        and "g_r2_pdl_break_expiry" not in ea_source,
        "strict_r2_router": inputs.get("InpRegimeRouterMode") == "2",
        "short_only": inputs.get("InpDirectionMode") == "2",
        "fixed_rr2": inputs.get("InpRiskReward") == "2.00",
        "normalized_h1_volatility_40_90": (
            inputs.get("InpR2PdlH1AtrPercentileLookback") == "480"
            and inputs.get("InpR2PdlH1AtrPercentileMin") == "40.00"
            and inputs.get("InpR2PdlH1AtrPercentileMax") == "90.00"
        ),
        "absolute_atr_disabled": inputs.get("InpMinAtrAbsoluteForEntry") == "0.00",
        "absolute_stop_filters_disabled": all(
            inputs.get(field) == "0" for field in ("InpStopFloorPoints", "InpStopCeilingPoints", "InpStopCapPoints")
        ),
        "calendar_masks_empty": all(inputs.get(field, "") == "" for field in forbidden_calendar_fields),
        "session_filter_disabled": inputs.get("InpUseDirectionalSessionFilter") == "false",
        "risk_normalized_50usd": (
            inputs.get("InpUseRiskNormalizedLots") == "true"
            and inputs.get("InpRiskAmountUsd") == "50.00"
            and inputs.get("InpMaxRiskLots") == "0.10"
        ),
        "risk_overshoot_guard_10pct": (
            inputs.get("InpRejectRiskOvershootEnabled") == "true"
            and inputs.get("InpMaxRiskOvershootPct") == "10.00"
        ),
        "one_position_one_episode": (
            inputs.get("InpOnePositionPerMagic") == "true"
            and inputs.get("InpMaxOpenPositionsPerMagic") == "1"
        ),
        "no_daily_or_cooldown_filter": (
            inputs.get("InpMaxTradesPerDay") == "0"
            and inputs.get("InpCooldownMinutes") == "0"
            and inputs.get("InpPortfolioDailyGuardEnabled") == "false"
        ),
        "no_trade_management_overlay": (
            inputs.get("InpProfitProtectionEnabled") == "false"
            and inputs.get("InpPartialCloseEnabled") == "false"
            and inputs.get("InpSplitEntryEnabled") == "false"
        ),
    }


def normalized_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows = r1.mt5_rows(result, source_priority=94)
    for row in rows:
        row["component"] = SOURCE_ID
        row["source_id"] = SOURCE_ID
        row["upstream_source_id"] = SOURCE_ID
        row["upstream_component"] = VARIANT_NAME
        row["family_group"] = "xau_r2_prior_d1_low_first_retest_short"
        row["cell_id"] = SOURCE_ID
    return rows


def standalone_checks(row: dict[str, Any]) -> dict[str, bool]:
    share = row.get("best_month_share_pct")
    return {
        "trades_ge_80": row["signals"] >= 80,
        "wr_ge_50": row["wr"] >= 50.0,
        "wl_ge_1p90": (row["wl"] or 0.0) >= 1.90,
        "pf_ge_2": (row["pf"] or 0.0) >= 2.00,
        "stress_pf_ge_1p90": (row["stress_030_pf"] or 0.0) >= 1.90,
        "stress_net_gt_0": row["stress_030_net"] > 0.0,
        "top10_removed_net_gt_0": row["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": row["top3_days_removed_net"] > 0.0,
        "best_month_share_lte_30pct": share is not None and share <= 30.0,
    }


def render(payload: dict[str, Any]) -> str:
    row = payload["standalone"]
    episode = payload["episode_audit"]
    lines = [
        "# A1 XAU R2 Prior-D1-Low First-Retest Short V1 Exact-MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "Research-only exact-MT5 evidence for one preregistered structural cell. No portfolio recomposition or runtime change.",
        "",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        f"Frozen tester-input SHA256: `{payload['tester_input_sha256']}`",
        "",
        "## Standalone",
        "",
        "| Trades | WR% | W/L | PF | Net | Stress PF | Stress net | Closed DD | Top10 rem | Top3 days rem | Best month% | Core pass |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        (
            f"| {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | {row['pf'] or 0.0:.4f} | "
            f"{row['net']:.2f} | {row['stress_030_pf'] or 0.0:.4f} | {row['stress_030_net']:.2f} | "
            f"{row['max_closed_dd']:.2f} | {row['top10_removed_net']:.2f} | {row['top3_days_removed_net']:.2f} | "
            f"{row['best_month_share_pct'] or 0.0:.2f} | {all(payload['standalone_checks'].values())} |"
        ),
        "",
        "## Failed Core Checks",
        "",
    ]
    failed = [key for key, value in payload["standalone_checks"].items() if not value]
    lines.append("- " + (", ".join(failed) if failed else "none"))
    lines.extend(["", "## Episode / Overlap / Equity-DD Audit", ""])
    lines.append(f"- passed: `{episode['passed']}`")
    episode_failed = [key for key, value in episode["checks"].items() if not value]
    lines.append("- failed checks: " + (", ".join(episode_failed) if episode_failed else "none"))
    lines.extend(["", "## Guard Counts", ""])
    for reason, count in sorted(payload["guard_counts"].get("guard_reasons", {}).items()):
        lines.append(f"- `{reason}`: {count}")
    lines.extend(["", "## Artifacts", ""])
    for key, path in payload["outputs"].items():
        lines.append(f"- {key}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the one-cell exact-MT5 R2 prior-D1-low first-retest short test.")
    parser.add_argument("--variant-timeout-seconds", type=int, default=1200)
    parser.add_argument("--static-only", action="store_true")
    args = parser.parse_args()

    variants = build_variants()
    checks = static_checks(variants)
    static_payload = {
        "preregistration": rel(PREREG),
        "variant": VARIANT_NAME,
        "source_id": SOURCE_ID,
        "tester_input_sha256": r2_common.stable_hash(FROZEN_INPUTS),
        "static_checks": checks,
        "historical_run_authorized": HISTORICAL_RUN_AUTHORIZED,
    }
    if args.static_only:
        print(json.dumps(static_payload, indent=2))
        return 0 if all(checks.values()) and PREREG.exists() else 1

    r2_common.require_file(PREREG)
    if not HISTORICAL_RUN_AUTHORIZED:
        raise RuntimeError("Historical run has not been authorized")
    if not all(checks.values()):
        raise RuntimeError(f"Invalid frozen runner configuration: {checks}")

    a1.VARIANTS = variants
    mt5_md = REPORTS_DIR / f"{OUTPUT_STEM}_MT5_COMPONENTS.md"
    mt5_json = REPORTS_DIR / f"{OUTPUT_STEM}_MT5_COMPONENTS.json"
    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    normalized_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{VARIANT_NAME}_NORMALIZED_TRADES.csv"
    episode_report_md = REPORTS_DIR / f"{OUTPUT_STEM}_EPISODE_AUDIT.md"
    episode_report_json = REPORTS_DIR / f"{OUTPUT_STEM}_EPISODE_AUDIT.json"

    mt5_payload = a1.run_variants(
        from_date=FROM_DATE,
        to_date=TO_DATE,
        tag=a1.safe_name(TAG),
        report_md=mt5_md,
        report_json=mt5_json,
        variant_timeout_seconds=args.variant_timeout_seconds,
        deposit="10000",
        currency="USD",
    )
    result = mt5_payload["variants"][0]
    rows = normalized_rows(result)
    write_signal_csv(normalized_csv, rows)
    standalone = r2_common.evaluate_book(VARIANT_NAME, rows)
    core_checks = standalone_checks(standalone)
    guards = guard_counts(result)
    episode_payload = episode_audit.build_audit(
        normalized_csv,
        Path(result["signal_csv"]),
        mt5_json,
    )
    episode_report_json.write_text(json.dumps(episode_payload, indent=2, default=str), encoding="utf-8")
    episode_report_md.write_text(episode_audit.render(episode_payload), encoding="utf-8")

    outputs = {
        "report_md": rel(report_md),
        "report_json": rel(report_json),
        "mt5_components_md": rel(mt5_md),
        "mt5_components_json": rel(mt5_json),
        "normalized_trades_csv": rel(normalized_csv),
        "episode_audit_md": rel(episode_report_md),
        "episode_audit_json": rel(episode_report_json),
    }
    core_pass = all(core_checks.values())
    episode_pass = episode_payload["passed"]
    payload = {
        "status": (
            "R2_PDL_FIRST_RETEST_CORE_AND_EPISODE_PASS"
            if core_pass and episode_pass
            else "R2_PDL_FIRST_RETEST_CORE_PASS_EPISODE_FAIL"
            if core_pass
            else "R2_PDL_FIRST_RETEST_NO_CORE_PASS"
        ),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration": rel(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "tester_input_sha256": r2_common.stable_hash(FROZEN_INPUTS),
        "static_checks": checks,
        "standalone": r2_common.strip_heavy(standalone),
        "standalone_checks": core_checks,
        "episode_audit": episode_payload,
        "guard_counts": guards,
        "mt5_scope": mt5_payload["scope"],
        "compile_log": mt5_payload["compile_log"],
        "outputs": outputs,
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(json.dumps(payload, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
