from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import analyze_a1_r2_prior_d1_low_first_retest_episode_audit as audit_common
import run_a1_r1_box_clean_requalification_exact as clean
import run_a1_r1_pullback_long_v1_exact as r1_metrics
import run_a1_r2_pullback_rejection_short_v1_exact as r2_common
import run_a1_xau_m5_momentum_backtest_variants as mt5
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR, rel
from analyze_a1_xau_source_monthly_firewall import read_ledger
from run_a1_h4_d1_geometry_v2_weekly_shape import sha256_file, write_signal_csv
from run_a1_regime_router_v1_exact import ROUTER_INPUTS


PHASE1_ROOT = Path(__file__).resolve().parents[1]
EA_SOURCE = PHASE1_ROOT / "mt5" / "Experts" / "A1XauM5MomentumContinuationExecutor.mq5"
PREREG = PHASE1_ROOT / "docs" / "A1_XAU_R1_PRIOR_D1_HIGH_FIRST_RETEST_LONG_V1_PREREG_2026_07_10.md"
OUTPUT_STEM = "A1_XAU_R1_PRIOR_D1_HIGH_FIRST_RETEST_LONG_V1_EXACT_20260710"
SOURCE_ID = "r1_prior_d1_high_first_retest_long_v1"
VARIANT_NAME = "r1_pdh_first_retest_structural_v1"
HISTORICAL_RUN_AUTHORIZED = True
SIGNAL_MATCH_WINDOW_SECONDS = 5 * 60

WINDOWS = clean.WINDOWS

CONTROL_PATHS = {
    "primary_202207_202606": {
        "rejected_r1_box": REPORTS_DIR
        / "A1_XAU_R1_BOX_CLEAN_REQUALIFICATION_EXACT_20260710_primary_202207_202606_NORMALIZED_TRADES.csv",
        "rejected_r1_long_expansion": REPORTS_DIR
        / "A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_EXACT_20260709_r1_long_expansion_r3_reclass_strict_r1_NORMALIZED_TRADES.csv",
        "r3_compression_long_control": REPORTS_DIR
        / "A1_XAU_R3_COMPRESSION_LONG_V1_EXACT_20260709_r3_compression_long_v1_broad_box3_atr60_range125_body035_NORMALIZED_TRADES.csv",
    },
    "prehistory_201601_202112": {
        "rejected_r1_box": REPORTS_DIR
        / "A1_XAU_R1_BOX_CLEAN_REQUALIFICATION_EXACT_20260710_prehistory_201601_202112_NORMALIZED_TRADES.csv",
        "rejected_r1_long_expansion": REPORTS_DIR
        / "A1_XAU_R1_LONG_EXPANSION_REPLACEMENT_PREHISTORY_EXACT_20260710_NORMALIZED_TRADES.csv",
    },
}

FROZEN_INPUTS = {
    **ROUTER_INPUTS,
    "InpSignalMode": "23",
    "InpRegimeRouterMode": "1",
    "InpDirectionMode": "1",
    "InpRiskReward": "2.00",
    "InpMaxSpreadPoints": "75",
    "InpMaxEstimatedCostR": "0.10",
    "InpR1PdhAtrPeriod": "14",
    "InpR1PdhH1AtrPercentileLookback": "480",
    "InpR1PdhH1AtrPercentileMin": "40.00",
    "InpR1PdhH1AtrPercentileMax": "90.00",
    "InpR1PdhBreakMarginH1Atr": "0.10",
    "InpR1PdhBreakMinRangeH1Atr": "1.00",
    "InpR1PdhBreakMinBodyFraction": "0.50",
    "InpR1PdhBreakCloseLocationMin": "0.75",
    "InpR1PdhRetestWindowM15Bars": "8",
    "InpR1PdhRetestTouchM15Atr": "0.25",
    "InpR1PdhInvalidBreakdownH1Atr": "0.10",
    "InpR1PdhReclaimDistanceM15Atr": "0.10",
    "InpR1PdhReclaimMinBodyFraction": "0.50",
    "InpR1PdhReclaimCloseLocationMin": "0.75",
    "InpR1PdhStopBufferM15Atr": "0.20",
    "InpR1PdhMaxStopH1Atr": "1.00",
    "InpMinAtrAbsoluteForEntry": "0.00",
    "InpStopFloorPoints": "0",
    "InpStopCeilingPoints": "0",
    "InpStopCapPoints": "0",
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
    "InpLongSessionStartHour": "0",
    "InpLongSessionEndHour": "24",
    "InpShortSessionStartHour": "0",
    "InpShortSessionEndHour": "24",
    "InpUseH1TrendFilter": "false",
    "InpUseH4TrendFilter": "false",
    "InpH4D1SupportiveStateGuardEnabled": "false",
    "InpH4D1WeeklyLossGovernorEnabled": "false",
    "InpH4D1PrevMonthHealthGateEnabled": "false",
    "InpH4D1NegativeStackGuardEnabled": "false",
    "InpH4D1ThirdEntryQualityGateEnabled": "false",
    "InpFeatureLossFilterEnabled": "false",
    "InpD1SupportStateGateMode": "0",
    "InpD1StructuralDownGateEnabled": "false",
    "InpProfitProtectionEnabled": "false",
    "InpPartialCloseEnabled": "false",
    "InpSplitEntryEnabled": "false",
    "InpEarlyAdverseExitEnabled": "false",
    "InpRegimeSnapshotLogEnabled": "false",
}

REQUIRED_EA_TOKENS = (
    "SIGNAL_R1_PRIOR_D1_HIGH_FIRST_RETEST_LONG = 23",
    "InpR1PdhH1AtrPercentileLookback",
    "g_r1_pdh_last_counted_m15_bar",
    "g_r1_pdh_retest_m15_bars_observed",
    "R1PdhTakeDistinctCompletedM15Bar",
    "TryR1PriorD1HighFirstRetestLongSignal",
    "R1_PRIOR_D1_HIGH_FIRST_RETEST_LONG_STATE_",
    "r1_pdh_first_retest_rejected",
    "r1_pdh_expired",
    "r1_pdh_stop_h1_atr_exceeded",
)


def build_variants() -> list[mt5.Variant]:
    return [
        mt5.Variant(
            name=VARIANT_NAME,
            label=(
                "Strict-R1 prior-D1-high completed-H1 acceptance and first-M15 "
                "failed-breakdown/reclaim long, fixed 2R"
            ),
            run_id="BT_A1_XAU_R1_PDH_FIRST_RETEST_STRUCTURAL_V1",
            tester_inputs=dict(FROZEN_INPUTS),
        )
    ]


def implementation_readiness() -> dict[str, bool]:
    if not EA_SOURCE.exists():
        return {token: False for token in REQUIRED_EA_TOKENS}
    source = EA_SOURCE.read_text(encoding="utf-8")
    return {token: token in source for token in REQUIRED_EA_TOKENS}


def static_checks(variants: list[mt5.Variant] | None = None) -> dict[str, bool]:
    variants = variants or build_variants()
    variant = variants[0] if len(variants) == 1 else None
    inputs = variant.tester_inputs if variant is not None else {}
    calendar_fields = (
        "InpBlockedEntryHoursCsv",
        "InpBlockedEntryDayHoursCsv",
        "InpBlockedLongEntryHoursCsv",
        "InpBlockedShortEntryHoursCsv",
    )
    return {
        "exactly_one_variant": len(variants) == 1,
        "variant_name_frozen": variant is not None and variant.name == VARIANT_NAME,
        "tester_inputs_exactly_frozen": inputs == FROZEN_INPUTS,
        "new_signal_mode_23": inputs.get("InpSignalMode") == "23",
        "strict_native_r1_router": inputs.get("InpRegimeRouterMode") == "1",
        "long_only": inputs.get("InpDirectionMode") == "1",
        "fixed_rr2": inputs.get("InpRiskReward") == "2.00",
        "normalized_h1_volatility_40_90": (
            inputs.get("InpR1PdhH1AtrPercentileLookback") == "480"
            and inputs.get("InpR1PdhH1AtrPercentileMin") == "40.00"
            and inputs.get("InpR1PdhH1AtrPercentileMax") == "90.00"
        ),
        "first_retest_window_8": inputs.get("InpR1PdhRetestWindowM15Bars") == "8",
        "absolute_atr_disabled": inputs.get("InpMinAtrAbsoluteForEntry") == "0.00",
        "absolute_stop_filters_disabled": all(
            inputs.get(field) == "0"
            for field in ("InpStopFloorPoints", "InpStopCeilingPoints", "InpStopCapPoints")
        ),
        "calendar_masks_empty": all(inputs.get(field, "") == "" for field in calendar_fields),
        "session_filter_disabled_full_day": (
            inputs.get("InpUseDirectionalSessionFilter") == "false"
            and inputs.get("InpLongSessionStartHour") == "0"
            and inputs.get("InpLongSessionEndHour") == "24"
        ),
        "risk_normalized_50usd": (
            inputs.get("InpUseRiskNormalizedLots") == "true"
            and inputs.get("InpRiskAmountUsd") == "50.00"
            and inputs.get("InpMaxRiskLots") == "0.10"
        ),
        "risk_overshoot_guard_10pct": (
            inputs.get("InpRejectRiskOvershootEnabled") == "true"
            and inputs.get("InpMaxRiskOvershootPct") == "10.00"
        ),
        "one_position_no_stacking": (
            inputs.get("InpOnePositionPerMagic") == "true"
            and inputs.get("InpMaxOpenPositionsPerMagic") == "1"
        ),
        "no_daily_cooldown_or_previous_pnl_governor": (
            inputs.get("InpMaxTradesPerDay") == "0"
            and inputs.get("InpCooldownMinutes") == "0"
            and inputs.get("InpPortfolioDailyGuardEnabled") == "false"
            and inputs.get("InpH4D1WeeklyLossGovernorEnabled") == "false"
            and inputs.get("InpH4D1PrevMonthHealthGateEnabled") == "false"
        ),
        "no_trade_management_overlay": all(
            inputs.get(field) == "false"
            for field in (
                "InpProfitProtectionEnabled",
                "InpPartialCloseEnabled",
                "InpSplitEntryEnabled",
                "InpEarlyAdverseExitEnabled",
            )
        ),
        "independent_from_box_and_r3_signal_mode": inputs.get("InpSignalMode") != "7",
    }


def normalize_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows = r1_metrics.mt5_rows(result, source_priority=96)
    for row in rows:
        row.update(
            {
                "component": SOURCE_ID,
                "source_id": SOURCE_ID,
                "upstream_source_id": SOURCE_ID,
                "upstream_component": VARIANT_NAME,
                "family_group": "xau_r1_prior_d1_high_first_retest_long",
                "cell_id": SOURCE_ID,
            }
        )
    return rows


def episode_positive_net_share(episodes: list[dict[str, Any]]) -> float:
    positive = [max(0.0, float(row["net"])) for row in episodes]
    total = sum(positive)
    return round(100.0 * max(positive, default=0.0) / total, 2) if total > 0.0 else 0.0


def native_r1_purity(rows: list[dict[str, Any]], signal_csv: Path) -> dict[str, Any]:
    signals = audit_common.read_signal_reasons(signal_csv)
    matched = 0
    uptrend = 0
    missing: list[str] = []
    for row in rows:
        entry_time = row["entry_time"]
        candidates = [
            signal
            for signal in signals
            if signal["direction"] == "LONG"
            and abs((entry_time - signal["timestamp"]).total_seconds()) <= SIGNAL_MATCH_WINDOW_SECONDS
        ]
        if not candidates:
            missing.append(entry_time.strftime("%Y-%m-%d %H:%M:%S"))
            continue
        nearest = min(
            candidates,
            key=lambda signal: abs((entry_time - signal["timestamp"]).total_seconds()),
        )
        matched += 1
        if nearest["reason"] == "R1_PRIOR_D1_HIGH_FIRST_RETEST_LONG_STATE_uptrend":
            uptrend += 1
    return {
        "trades": len(rows),
        "matched_signal_reasons": matched,
        "uptrend_reasons": uptrend,
        "purity_pct": round(100.0 * uptrend / len(rows), 2) if rows else 0.0,
        "missing_entry_times": missing,
    }


def overlap_rows(window_name: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for name, path in CONTROL_PATHS.get(window_name, {}).items():
        if not path.exists():
            output.append(
                {
                    "control": name,
                    "candidate_trades": len(rows),
                    "overlap_trades": None,
                    "overlap_pct": None,
                    "path": str(path),
                    "available": False,
                }
            )
            continue
        result = audit_common.overlap_with_control(rows, read_ledger(path), name)
        result.update({"path": str(path), "available": True})
        output.append(result)
    return output


def evaluate_window(
    window: dict[str, str],
    result: dict[str, Any],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    shape = r1_metrics.flat_shape(window["name"], rows)
    years = clean.year_rows(rows)
    episodes = clean.episode_rows(rows)
    drawdown = clean.mt5_drawdown(result["mt5_report_metrics"])
    equity_dd = drawdown["equity_dd_maximal_usd"] or 0.0
    execution = clean.execution_reconciliation(result, rows)
    forbidden = clean.forbidden_guard_counts(result)
    regime = native_r1_purity(rows, Path(result["signal_csv"]))
    overlaps = overlap_rows(window["name"], rows)
    compact = r1_metrics.strip_heavy(shape)
    compact.update(
        {
            "window": window["name"],
            "year_rows": years,
            "episodes": episodes,
            "episode_positive_net_share_pct": episode_positive_net_share(episodes),
            "pre_2026_net": round(
                sum(float(row["pnl_usd"]) for row in rows if row["entry_date"] < date(2026, 1, 1)),
                2,
            ),
            "mt5_drawdown": drawdown,
            "net_to_equity_dd": round(shape["net"] / equity_dd, 4) if equity_dd > 0.0 else None,
            "equity_to_closed_dd": (
                round(equity_dd / shape["max_closed_dd"], 4)
                if shape["max_closed_dd"] > 0.0
                else None
            ),
            "execution_reconciliation": execution,
            "forbidden_guard_counts": forbidden,
            "native_r1_purity": regime,
            "overlap": overlaps,
        }
    )
    compact["alpha_checks"] = clean.alpha_checks(
        compact, primary=window["name"].startswith("primary")
    )
    compact["robustness_checks"] = {
        "top10_removed_net_gt_0": compact["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": compact["top3_days_removed_net"] > 0.0,
        "best_month_share_lte_30": (
            compact["best_month_share_pct"] is not None
            and compact["best_month_share_pct"] <= 30.0
        ),
        "episode_positive_net_share_lte_50": compact["episode_positive_net_share_pct"] <= 50.0,
    }
    available_overlaps = [row for row in overlaps if row["available"]]
    compact["regime_independence_checks"] = {
        "native_r1_purity_100pct": regime["purity_pct"] == 100.0
        and not regime["missing_entry_times"],
        "zero_forbidden_guard_blocks": sum(forbidden.values()) == 0,
        "all_available_control_overlap_lte_20pct": bool(available_overlaps)
        and all(float(row["overlap_pct"]) <= 20.0 for row in available_overlaps),
    }
    compact["execution_checks"] = {
        "successful_sends_match_mt5": execution["successful_sends_match_mt5"],
        "mt5_matches_normalized": execution["mt5_matches_normalized"],
        "all_failures_described": execution["all_failures_described"],
    }
    compact["drawdown_checks"] = {
        "balance_dd_relative_lte_20": drawdown["balance_dd_relative_pct"] is not None
        and drawdown["balance_dd_relative_pct"] <= 20.0,
        "equity_dd_relative_lte_20": drawdown["equity_dd_relative_pct"] is not None
        and drawdown["equity_dd_relative_pct"] <= 20.0,
        "net_to_equity_dd_ge_2": compact["net_to_equity_dd"] is not None
        and compact["net_to_equity_dd"] >= 2.0,
        "equity_to_closed_dd_lte_2": compact["equity_to_closed_dd"] is not None
        and compact["equity_to_closed_dd"] <= 2.0,
    }
    return compact


def decide(static: dict[str, bool], windows: list[dict[str, Any]]) -> tuple[str, str]:
    alpha_regime_robust_execution = all(static.values()) and all(
        all(window[group].values())
        for window in windows
        for group in (
            "alpha_checks",
            "robustness_checks",
            "regime_independence_checks",
            "execution_checks",
        )
    )
    if not alpha_regime_robust_execution:
        return (
            "R1_PDH_FIRST_RETEST_REJECT",
            "The one-cell structural R1 family failed alpha, durability, ownership, independence, concentration, or execution integrity. Do not tune it.",
        )
    if not all(all(window["drawdown_checks"].values()) for window in windows):
        return (
            "R1_PDH_FIRST_RETEST_ALPHA_ONLY_RISK_REPAIR_REQUIRED",
            "Alpha and ownership passed both windows, but the frozen capital lane failed a global drawdown gate.",
        )
    return (
        "R1_PDH_FIRST_RETEST_FULLY_QUALIFIED",
        "The new structural R1 owner passed both exact windows and every global drawdown gate.",
    )


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU R1 Prior-D1-High First-Retest Long V1 Exact-MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        payload["interpretation"],
        "",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        f"Frozen tester-input SHA256: `{payload['tester_input_sha256']}`",
        "",
        "| Window | Trades | WR% | W/L | PF | Stress PF | Net | Equity DD% | Net/Equity DD | Equity/Closed DD | Best month% | Episode share% | R1 purity% |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["windows"]:
        dd = row["mt5_drawdown"]
        lines.append(
            f"| `{row['window']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['pf'] or 0.0:.4f} | {row['stress_030_pf'] or 0.0:.4f} | {row['net']:.2f} | "
            f"{dd['equity_dd_relative_pct'] or 0.0:.2f} | {row['net_to_equity_dd'] or 0.0:.2f} | "
            f"{row['equity_to_closed_dd'] or 0.0:.2f} | {row['best_month_share_pct'] or 0.0:.2f} | "
            f"{row['episode_positive_net_share_pct']:.2f} | {row['native_r1_purity']['purity_pct']:.2f} |"
        )
    lines.extend(["", "## Failed Gates", ""])
    for row in payload["windows"]:
        lines.append(f"### `{row['window']}`")
        for group in (
            "alpha_checks",
            "robustness_checks",
            "regime_independence_checks",
            "execution_checks",
            "drawdown_checks",
        ):
            failed = clean.failed_checks(row[group])
            lines.append(f"- `{group}`: {', '.join(failed) if failed else 'none'}")
        lines.append("")
    lines.extend(["## Independence Overlap", ""])
    for row in payload["windows"]:
        for overlap in row["overlap"]:
            value = "missing" if overlap["overlap_pct"] is None else f"{overlap['overlap_pct']:.2f}%"
            lines.append(f"- `{row['window']}` / `{overlap['control']}`: {value}")
    lines.extend(["", "## Artifacts", ""])
    for key, value in payload["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the one-cell R1 prior-D1-high first-retest long exact test."
    )
    parser.add_argument("--variant-timeout-seconds", type=int, default=1200)
    parser.add_argument("--static-only", action="store_true")
    args = parser.parse_args()

    variants = build_variants()
    static = static_checks(variants)
    readiness = implementation_readiness()
    static_payload = {
        "preregistration": rel(PREREG),
        "source_id": SOURCE_ID,
        "variant": VARIANT_NAME,
        "tester_input_sha256": r2_common.stable_hash(FROZEN_INPUTS),
        "static_checks": static,
        "implementation_readiness": readiness,
        "historical_run_authorized": HISTORICAL_RUN_AUTHORIZED,
    }
    if args.static_only:
        print(json.dumps(static_payload, indent=2))
        return 0 if PREREG.exists() and all(static.values()) else 1

    if not PREREG.exists():
        raise FileNotFoundError(PREREG)
    if not all(static.values()):
        raise RuntimeError(f"Invalid frozen runner configuration: {static}")
    if not all(readiness.values()):
        missing = [token for token, present in readiness.items() if not present]
        raise RuntimeError("R1 PDH EA implementation is not ready: " + ", ".join(missing))
    if not HISTORICAL_RUN_AUTHORIZED:
        raise RuntimeError("Historical run has not been authorized after implementation review")

    output_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    output_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    window_rows: list[dict[str, Any]] = []
    outputs: dict[str, str] = {"report_md": rel(output_md), "report_json": rel(output_json)}
    for window in WINDOWS:
        mt5.VARIANTS = variants
        mt5_md = REPORTS_DIR / f"{OUTPUT_STEM}_{window['name']}_MT5.md"
        mt5_json = REPORTS_DIR / f"{OUTPUT_STEM}_{window['name']}_MT5.json"
        mt5_payload = mt5.run_variants(
            from_date=window["from_date"],
            to_date=window["to_date"],
            tag=mt5.safe_name("OWNER_GOAL_R1_PDH_FIRST_RETEST_" + window["name"]),
            report_md=mt5_md,
            report_json=mt5_json,
            variant_timeout_seconds=args.variant_timeout_seconds,
            deposit="10000",
            currency="USD",
        )
        result = mt5_payload["variants"][0]
        rows = normalize_rows(result)
        normalized_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{window['name']}_NORMALIZED_TRADES.csv"
        write_signal_csv(normalized_csv, rows)
        window_rows.append(evaluate_window(window, result, rows))
        outputs[f"{window['name']}_mt5_md"] = rel(mt5_md)
        outputs[f"{window['name']}_mt5_json"] = rel(mt5_json)
        outputs[f"{window['name']}_normalized_trades_csv"] = rel(normalized_csv)

    status, interpretation = decide(static, window_rows)
    payload = {
        **static_payload,
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
            "+00:00", "Z"
        ),
        "preregistration_sha256": sha256_file(PREREG),
        "windows": window_rows,
        "interpretation": interpretation,
        "outputs": outputs,
    }
    output_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    output_md.write_text(render(payload), encoding="utf-8")
    print(json.dumps({"status": status, "report": str(output_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
