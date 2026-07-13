from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import run_a1_r1_pullback_long_v1_exact as book_metrics
import run_a1_xau_m5_momentum_backtest_variants as mt5
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR, rel
from run_a1_h4_d1_geometry_v2_weekly_shape import sha256_file
from run_a1_h4_d1_review_repair_exact import guard_counts
from run_a1_regime_router_v1_exact import ROUTER_INPUTS


PHASE1_ROOT = Path(__file__).resolve().parents[1]
EA_SOURCE = PHASE1_ROOT / "mt5" / "Experts" / "A1XauM5MomentumContinuationExecutor.mq5"
PREREG = (
    PHASE1_ROOT
    / "docs"
    / "A1_XAU_R1_SECOND_CONTINUATION_HIGHER_LOW_LONG_V1_PREREG_2026_07_10.md"
)

SOURCE_ID = "r1_second_continuation_higher_low_long_v1"
VARIANT_NAME = "r1_hlf_second_continuation_structural_v1"
OUTPUT_STEM = "A1_XAU_R1_SECOND_CONTINUATION_HIGHER_LOW_LONG_V1_EXACT_20260710"
PROPOSED_SIGNAL_MODE = 26
DEPOSIT_USD = 10_000.0
RISK_AMOUNT_USD = 50.0
HISTORICAL_RUN_AUTHORIZED = True
RUNNER_SCAFFOLD_ONLY = False
RUNNER_EVALUATOR_COMPLETE = True

ADMINISTRATIVE_RENUMBERING = {
    "from_proposed_mode": 25,
    "to_proposed_mode": 26,
    "reason": "mode25_refrozen_for_r3_compression_h1_accept_m15_first_pullback",
    "before_implementation_compile_or_history": True,
}

WINDOWS = (
    {
        "name": "prehistory_201601_202112",
        "from_date": "2016.01.01",
        "to_date": "2021.12.31",
        "pre_recent_end": "2021.06.30",
    },
    {
        "name": "primary_202207_202606",
        "from_date": "2022.07.01",
        "to_date": "2026.06.30",
        "pre_recent_end": "2025.12.31",
    },
)

MODE23_ATTRITION = {
    "prehistory_201601_202112": {
        "decision_rows": 141_048,
        "generic_no_candidate": 140_940,
        "observable_terminal_outcomes": 108,
        "expired": 69,
        "first_retest_rejected": 35,
        "invalidated": 2,
        "would_signal": 2,
        "executed": 0,
    },
    "primary_202207_202606": {
        "decision_rows": 94_223,
        "generic_no_candidate": 94_096,
        "observable_terminal_outcomes": 127,
        "expired": 97,
        "first_retest_rejected": 24,
        "invalidated": 4,
        "would_signal": 2,
        "executed": 1,
    },
}

REQUIRED_OVERLAP_CONTROLS = (
    "r1_box_clean_strict_uptrend",
    "r1_long_expansion_r3_reclass_strict_r1",
    "r1_h1_pullback_long_v1_m5_confirm",
    "r1_pullback_long_v2_m15_session_09_15",
    "r1_prior_d1_high_first_retest_killed",
    "r3_compression_long_v1_broad_box3",
)

OVERLAP_CONTROL_FILES_BY_WINDOW = {
    "prehistory_201601_202112": {
        "r1_box_clean_strict_uptrend": REPORTS_DIR
        / "A1_XAU_R1_BOX_CLEAN_REQUALIFICATION_EXACT_20260710_prehistory_201601_202112_NORMALIZED_TRADES.csv",
        "r1_long_expansion_r3_reclass_strict_r1": REPORTS_DIR
        / "A1_XAU_R1_LONG_EXPANSION_REPLACEMENT_PREHISTORY_EXACT_20260710_NORMALIZED_TRADES.csv",
        "r1_prior_d1_high_first_retest_killed": REPORTS_DIR
        / "A1_XAU_R1_PRIOR_D1_HIGH_FIRST_RETEST_LONG_V1_EXACT_20260710_prehistory_201601_202112_NORMALIZED_TRADES.csv",
    },
    "primary_202207_202606": {
        "r1_box_clean_strict_uptrend": REPORTS_DIR
        / "A1_XAU_R1_BOX_CLEAN_REQUALIFICATION_EXACT_20260710_primary_202207_202606_NORMALIZED_TRADES.csv",
        "r1_long_expansion_r3_reclass_strict_r1": REPORTS_DIR
        / "A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_EXACT_20260709_r1_long_expansion_r3_reclass_strict_r1_NORMALIZED_TRADES.csv",
        "r1_h1_pullback_long_v1_m5_confirm": REPORTS_DIR
        / "A1_XAU_R1_PULLBACK_LONG_V1_EXACT_20260708_r1_pullback_long_v1_m5_confirm_NORMALIZED_TRADES.csv",
        "r1_pullback_long_v2_m15_session_09_15": REPORTS_DIR
        / "A1_XAU_R1_PULLBACK_LONG_V2_SESSION_EXACT_20260708_r1_pullback_long_v2_m15_session_09_15_NORMALIZED_TRADES.csv",
        "r1_prior_d1_high_first_retest_killed": REPORTS_DIR
        / "A1_XAU_R1_PRIOR_D1_HIGH_FIRST_RETEST_LONG_V1_EXACT_20260710_primary_202207_202606_NORMALIZED_TRADES.csv",
        "r3_compression_long_v1_broad_box3": REPORTS_DIR
        / "A1_XAU_R3_COMPRESSION_LONG_V1_EXACT_20260709_r3_compression_long_v1_broad_box3_atr60_range125_body035_NORMALIZED_TRADES.csv",
    },
}

LIFECYCLE_STAGES = {
    "registered": "R1_HLF_SETUP_REGISTERED",
    "pivot": "R1_HLF_FIRST_PIVOT_CONSUMED",
    "second_break": "R1_HLF_SECOND_BREAK_CONSUMED",
    "consumed": "R1_HLF_SETUP_CONSUMED",
}

SIGNAL_PREFIX = "R1_SECOND_CONTINUATION_HIGHER_LOW_LONG_STATE_uptrend"

ALLOWED_CONSUMPTION_OUTCOMES = {
    "continuation_without_reset",
    "origin_low_broken",
    "regime_exit_before_pivot",
    "pivot_window_expired",
    "first_pivot_rejected",
    "second_break_before_arm",
    "regime_exit_after_pivot",
    "invalidated_after_pivot",
    "second_break_window_expired",
    "first_second_break_rejected",
    "entry_attempt",
}

ALLOWED_PIVOT_OUTCOMES = {"confirmed", "first_pivot_rejected"}
ALLOWED_SECOND_BREAK_OUTCOMES = {"entry_attempt", "first_second_break_rejected"}

FORBIDDEN_GUARD_REASONS = {
    "blocked_entry_hour",
    "blocked_entry_day_hour",
    "direction_blocked_entry_hour",
    "directional_session_filter_block",
    "portfolio_daily_profit_target",
    "portfolio_daily_loss_stop",
    "h4_d1_previous_month_health_gate",
    "h4_d1_weekly_loss_governor",
    "h4_d1_negative_stack_guard",
    "h4_d1_third_entry_quality_gate",
}

GLOBAL_GATE_THRESHOLDS = {
    "trades_min": 100,
    "owned_episodes_min": 3,
    "exposure_years_min": 3,
    "profitable_years_min": 3,
    "win_rate_pct_min": 50.0,
    "avg_win_loss_min": 2.0,
    "profit_factor_min": 2.0,
    "stress_profit_factor_min": 1.75,
    "best_month_share_pct_max": 30.0,
    "max_episode_positive_net_share_pct": 50.0,
    "native_purity_pct": 100.0,
    "same_event_overlap_pct_strict_max": 20.0,
    "balance_dd_relative_pct_max": 20.0,
    "equity_dd_relative_pct_max": 20.0,
    "net_to_equity_dd_min": 2.0,
    "equity_to_closed_dd_max": 2.0,
    "max_initial_risk_usd": RISK_AMOUNT_USD,
    "ticket_stress_usd": 0.30,
}

FROZEN_INPUTS = {
    **ROUTER_INPUTS,
    "InpSignalMode": str(PROPOSED_SIGNAL_MODE),
    "InpRegimeRouterMode": "1",
    "InpDirectionMode": "1",
    "InpRiskReward": "2.00",
    "InpMaxSpreadPoints": "75",
    "InpMaxEstimatedCostR": "0.10",
    "InpR1HlfAtrPeriod": "14",
    "InpR1HlfMaturityD1Bars": "3",
    "InpR1HlfLeg1LookbackH1Bars": "12",
    "InpR1HlfLeg1BreakMarginH1Atr": "0.10",
    "InpR1HlfLeg1MinRangeH1Atr": "1.00",
    "InpR1HlfLeg1MinBodyFraction": "0.50",
    "InpR1HlfLeg1CloseLocationMin": "0.75",
    "InpR1HlfResetWindowM15Bars": "16",
    "InpR1HlfPivotLeftBars": "2",
    "InpR1HlfPivotRightBars": "2",
    "InpR1HlfResetMinDepthH1Atr": "0.35",
    "InpR1HlfHigherLowMarginH1Atr": "0.10",
    "InpR1HlfSecondBreakWindowM15Bars": "16",
    "InpR1HlfSecondTouchM15Atr": "0.10",
    "InpR1HlfSecondCloseM15Atr": "0.10",
    "InpR1HlfSecondMinBodyFraction": "0.50",
    "InpR1HlfSecondCloseLocationMin": "0.75",
    "InpR1HlfInvalidBreakdownH1Atr": "0.10",
    "InpR1HlfStopBufferM15Atr": "0.20",
    "InpR1HlfMaxStopH1Atr": "1.00",
    "InpMinAtrAbsoluteForEntry": "0.00",
    "InpStopFloorPoints": "0",
    "InpStopCeilingPoints": "0",
    "InpStopCapPoints": "0",
    "InpUseRiskNormalizedLots": "true",
    "InpRiskAmountUsd": "50.00",
    "InpMaxRiskLots": "0.10",
    "InpRejectRiskOvershootEnabled": "true",
    "InpMaxRiskOvershootPct": "0.00",
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
    "InpRegimeSnapshotLogEnabled": "true",
}

EXPECTED_FROZEN_INPUT_SHA256 = "9fb023f1b492f9acec4d68c3880bcacdc757e0460ae33db9b9789f9d6f213418"

REQUIRED_EA_TOKENS = (
    "SIGNAL_R1_SECOND_CONTINUATION_HIGHER_LOW_LONG = 26",
    "InpR1HlfMaturityD1Bars",
    "R1_HLF_STATE_WAIT_FIRST_PIVOT",
    "R1_HLF_STATE_HIGHER_LOW_CONFIRMED",
    "g_r1_hlf_consumed_setup_time",
    "TryR1SecondContinuationHigherLowLongSignal",
    "r1_hlf_first_pivot_rejected",
    "r1_hlf_second_break_before_arm",
    "r1_hlf_first_second_break_rejected",
    "r1_hlf_stop_h1_atr_exceeded",
    "R1_SECOND_CONTINUATION_HIGHER_LOW_LONG_STATE_",
    "OrderCalcProfit(ORDER_TYPE_BUY",
    "actual_risk_usd",
    "intended_risk_usd",
    "risk_calc_method",
    "R1_HLF_SETUP_REGISTERED",
    "R1_HLF_FIRST_PIVOT_CONSUMED",
    "R1_HLF_SECOND_BREAK_CONSUMED",
    "R1_HLF_SETUP_CONSUMED",
)


def stable_hash(value: Any) -> str:
    blob = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def build_variants() -> list[mt5.Variant]:
    return [
        mt5.Variant(
            name=VARIANT_NAME,
            label=(
                "Strict established-R1 H1 leg one, first confirmed M15 higher low, "
                "and first second-break acceptance long, fixed 2R"
            ),
            run_id="BT_A1_XAU_R1_HLF_SECOND_CONTINUATION_STRUCTURAL_V1",
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
    previous_pnl_fields = (
        "InpPortfolioDailyGuardEnabled",
        "InpH4D1WeeklyLossGovernorEnabled",
        "InpH4D1PrevMonthHealthGateEnabled",
        "InpH4D1NegativeStackGuardEnabled",
        "InpH4D1ThirdEntryQualityGateEnabled",
        "InpFeatureLossFilterEnabled",
    )
    management_fields = (
        "InpProfitProtectionEnabled",
        "InpPartialCloseEnabled",
        "InpSplitEntryEnabled",
        "InpEarlyAdverseExitEnabled",
    )
    expected_windows = (
        ("prehistory_201601_202112", "2016.01.01", "2021.12.31", "2021.06.30"),
        ("primary_202207_202606", "2022.07.01", "2026.06.30", "2025.12.31"),
    )
    actual_windows = tuple(
        (row["name"], row["from_date"], row["to_date"], row["pre_recent_end"])
        for row in WINDOWS
    )
    attrition_exact = (
        MODE23_ATTRITION["prehistory_201601_202112"]["would_signal"] == 2
        and MODE23_ATTRITION["prehistory_201601_202112"]["executed"] == 0
        and MODE23_ATTRITION["primary_202207_202606"]["would_signal"] == 2
        and MODE23_ATTRITION["primary_202207_202606"]["executed"] == 1
    )
    return {
        "exactly_one_variant": len(variants) == 1,
        "variant_name_frozen": variant is not None and variant.name == VARIANT_NAME,
        "tester_inputs_exactly_frozen": inputs == FROZEN_INPUTS,
        "tester_input_hash_frozen": stable_hash(inputs) == EXPECTED_FROZEN_INPUT_SHA256,
        "two_frozen_exact_windows": actual_windows == expected_windows,
        "mode23_attrition_evidence_frozen": attrition_exact,
        "preimplementation_admin_renumbering_to_mode26": (
            ADMINISTRATIVE_RENUMBERING["from_proposed_mode"] == 25
            and ADMINISTRATIVE_RENUMBERING["to_proposed_mode"] == 26
            and ADMINISTRATIVE_RENUMBERING["before_implementation_compile_or_history"] is True
        ),
        "new_appended_signal_mode_26": inputs.get("InpSignalMode") == "26",
        "strict_native_r1_long_only": (
            inputs.get("InpRegimeRouterMode") == "1" and inputs.get("InpDirectionMode") == "1"
        ),
        "fixed_rr2": inputs.get("InpRiskReward") == "2.00",
        "mature_three_d1_state": inputs.get("InpR1HlfMaturityD1Bars") == "3",
        "first_two_sided_pivot_only": (
            inputs.get("InpR1HlfPivotLeftBars") == "2"
            and inputs.get("InpR1HlfPivotRightBars") == "2"
        ),
        "finite_first_event_windows": (
            inputs.get("InpR1HlfResetWindowM15Bars") == "16"
            and inputs.get("InpR1HlfSecondBreakWindowM15Bars") == "16"
        ),
        "structurally_not_mode23_box_or_pullback": (
            not any(key.startswith("InpR1Pdh") for key in inputs)
            and not any(key.startswith("InpD1Compression") for key in inputs)
            and not any(key.startswith("InpR1Pullback") for key in inputs)
        ),
        "no_absolute_atr_or_stop_threshold": (
            inputs.get("InpMinAtrAbsoluteForEntry") == "0.00"
            and all(
                inputs.get(field) == "0"
                for field in ("InpStopFloorPoints", "InpStopCeilingPoints", "InpStopCapPoints")
            )
        ),
        "calendar_masks_empty": all(inputs.get(field, "") == "" for field in calendar_fields),
        "session_filter_disabled_full_day": (
            inputs.get("InpUseDirectionalSessionFilter") == "false"
            and inputs.get("InpLongSessionStartHour") == "0"
            and inputs.get("InpLongSessionEndHour") == "24"
        ),
        "no_previous_pnl_or_mined_governor": all(
            inputs.get(field) == "false" for field in previous_pnl_fields
        ),
        "no_management_overlay": all(inputs.get(field) == "false" for field in management_fields),
        "hard_50usd_risk_no_overshoot": (
            DEPOSIT_USD == 10_000.0
            and RISK_AMOUNT_USD == 50.0
            and inputs.get("InpUseRiskNormalizedLots") == "true"
            and inputs.get("InpRiskAmountUsd") == "50.00"
            and inputs.get("InpRejectRiskOvershootEnabled") == "true"
            and inputs.get("InpMaxRiskOvershootPct") == "0.00"
        ),
        "one_position_no_stacking": (
            inputs.get("InpOnePositionPerMagic") == "true"
            and inputs.get("InpMaxOpenPositionsPerMagic") == "1"
        ),
        "required_overlap_controls_frozen": len(REQUIRED_OVERLAP_CONTROLS) == 6,
        "regime_telemetry_enabled": inputs.get("InpRegimeSnapshotLogEnabled") == "true",
        "runner_evaluator_complete": RUNNER_EVALUATOR_COMPLETE and not RUNNER_SCAFFOLD_ONLY,
    }


def _number(metrics: dict[str, Any], key: str) -> float | None:
    value = metrics.get(key)
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed != parsed or parsed in (float("inf"), float("-inf")):
        return None
    return parsed


def _ge(metrics: dict[str, Any], key: str, threshold: float) -> bool:
    value = _number(metrics, key)
    return value is not None and value >= threshold


def _le(metrics: dict[str, Any], key: str, threshold: float) -> bool:
    value = _number(metrics, key)
    return value is not None and value <= threshold


def _eq(metrics: dict[str, Any], key: str, expected: float) -> bool:
    value = _number(metrics, key)
    return value is not None and value == expected


def window_gate_checks(metrics: dict[str, Any]) -> dict[str, dict[str, bool]]:
    """Fail-closed contract for each future exact-MT5 window report."""

    net = _number(metrics, "net_usd")
    equity_dd = _number(metrics, "equity_dd_maximal_usd")
    closed_dd = _number(metrics, "closed_ledger_dd_usd")
    net_to_equity = net / equity_dd if net is not None and equity_dd is not None and equity_dd > 0 else None
    equity_to_closed = (
        equity_dd / closed_dd
        if equity_dd is not None and closed_dd is not None and closed_dd > 0
        else None
    )
    successful_orders = _number(metrics, "successful_orders")
    mt5_trades = _number(metrics, "mt5_trades")
    normalized_trades = _number(metrics, "normalized_trades")
    required_controls = _number(metrics, "required_overlap_controls")
    available_controls = _number(metrics, "available_overlap_controls")
    expected_controls = _number(metrics, "required_overlap_controls_expected")
    if expected_controls is None:
        expected_controls = float(len(REQUIRED_OVERLAP_CONTROLS))

    return {
        "alpha_checks": {
            "trades_ge_100": _ge(metrics, "trades", GLOBAL_GATE_THRESHOLDS["trades_min"]),
            "owned_episodes_ge_3": _ge(
                metrics, "owned_regime_episodes", GLOBAL_GATE_THRESHOLDS["owned_episodes_min"]
            ),
            "exposure_years_ge_3": _ge(
                metrics, "exposure_years", GLOBAL_GATE_THRESHOLDS["exposure_years_min"]
            ),
            "profitable_years_ge_3": _ge(
                metrics, "profitable_years", GLOBAL_GATE_THRESHOLDS["profitable_years_min"]
            ),
            "wr_ge_50": _ge(metrics, "win_rate_pct", GLOBAL_GATE_THRESHOLDS["win_rate_pct_min"]),
            "wl_ge_2": _ge(metrics, "avg_win_loss", GLOBAL_GATE_THRESHOLDS["avg_win_loss_min"]),
            "pf_ge_2": _ge(metrics, "profit_factor", GLOBAL_GATE_THRESHOLDS["profit_factor_min"]),
            "stress_pf_ge_1p75": _ge(
                metrics, "stress_profit_factor", GLOBAL_GATE_THRESHOLDS["stress_profit_factor_min"]
            ),
            "stress_net_gt_0": _ge(metrics, "stress_net_usd", 0.0000001),
            "pre_recent_net_gt_0": _ge(metrics, "pre_recent_net_usd", 0.0000001),
        },
        "robustness_checks": {
            "top10_removed_net_gt_0": _ge(metrics, "top10_removed_net_usd", 0.0000001),
            "top3_days_removed_net_gt_0": _ge(metrics, "top3_days_removed_net_usd", 0.0000001),
            "best_month_share_lte_30": _le(
                metrics, "best_month_share_pct", GLOBAL_GATE_THRESHOLDS["best_month_share_pct_max"]
            ),
            "max_episode_share_lte_50": _le(
                metrics,
                "max_episode_positive_net_share_pct",
                GLOBAL_GATE_THRESHOLDS["max_episode_positive_net_share_pct"],
            ),
        },
        "regime_independence_checks": {
            "setup_purity_100pct": _eq(
                metrics, "native_setup_purity_pct", GLOBAL_GATE_THRESHOLDS["native_purity_pct"]
            ),
            "entry_purity_100pct": _eq(
                metrics, "native_entry_purity_pct", GLOBAL_GATE_THRESHOLDS["native_purity_pct"]
            ),
            "owned_state_net_gt_0": _ge(metrics, "owned_state_net_usd", 0.0000001),
            "all_required_overlap_controls_available": (
                required_controls is not None
                and available_controls is not None
                and required_controls == expected_controls
                and available_controls == required_controls
            ),
            "same_event_overlap_strictly_below_20pct": (
                _number(metrics, "max_same_direction_overlap_pct") is not None
                and _number(metrics, "max_same_direction_overlap_pct")
                < GLOBAL_GATE_THRESHOLDS["same_event_overlap_pct_strict_max"]
            ),
            "zero_future_bar_violations": _eq(metrics, "future_bar_violations", 0.0),
            "zero_retrospective_pivot_entries": _eq(
                metrics, "retrospective_pivot_entry_violations", 0.0
            ),
            "zero_state_overwrites": _eq(metrics, "active_state_overwrite_violations", 0.0),
            "zero_multiple_consumptions": _eq(metrics, "multiple_consumption_violations", 0.0),
            "lifecycle_evidence_complete": _eq(metrics, "lifecycle_evidence_complete", 1.0),
            "all_trades_have_event_and_episode": _eq(metrics, "missing_event_trade_count", 0.0),
        },
        "execution_risk_checks": {
            "successful_orders_match_mt5_and_ledger": (
                successful_orders is not None
                and mt5_trades is not None
                and normalized_trades is not None
                and successful_orders == mt5_trades == normalized_trades
            ),
            "zero_unexplained_send_failures": _eq(metrics, "unexplained_send_failures", 0.0),
            "zero_open_at_end": _eq(metrics, "open_positions_at_end", 0.0),
            "zero_forbidden_guard_blocks": _eq(metrics, "forbidden_guard_blocks", 0.0),
            "zero_missing_initial_risk_calculations": _eq(
                metrics, "missing_initial_risk_calculations", 0.0
            ),
            "max_executed_initial_risk_lte_50usd": _le(
                metrics,
                "max_executed_initial_risk_usd",
                GLOBAL_GATE_THRESHOLDS["max_initial_risk_usd"],
            ),
        },
        "drawdown_checks": {
            "balance_dd_relative_lte_20": _le(
                metrics,
                "balance_dd_relative_pct",
                GLOBAL_GATE_THRESHOLDS["balance_dd_relative_pct_max"],
            ),
            "equity_dd_relative_lte_20": _le(
                metrics,
                "equity_dd_relative_pct",
                GLOBAL_GATE_THRESHOLDS["equity_dd_relative_pct_max"],
            ),
            "net_to_equity_dd_ge_2": (
                net_to_equity is not None
                and net_to_equity >= GLOBAL_GATE_THRESHOLDS["net_to_equity_dd_min"]
            ),
            "equity_to_closed_dd_lte_2": (
                equity_to_closed is not None
                and equity_to_closed <= GLOBAL_GATE_THRESHOLDS["equity_to_closed_dd_max"]
            ),
        },
    }


def require_ready() -> None:
    for path in (EA_SOURCE, PREREG):
        if not path.exists():
            raise FileNotFoundError(path)
    if stable_hash(FROZEN_INPUTS) != EXPECTED_FROZEN_INPUT_SHA256:
        raise RuntimeError("Frozen mode26 tester inputs no longer match their preregistered hash")
    missing = [token for token, present in implementation_readiness().items() if not present]
    if missing:
        raise RuntimeError(
            "R1 HLF mode26 infrastructure is not implemented; missing EA tokens: "
            + ", ".join(missing)
        )


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def parse_timestamp(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    text = str(value or "").strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        return parsed.replace(tzinfo=None)
    except ValueError:
        pass
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def parse_reason(reason: str) -> tuple[str, dict[str, str]]:
    parts = [part.strip() for part in str(reason or "").split("|") if part.strip()]
    prefix = parts[0] if parts and "=" not in parts[0] else ""
    fields: dict[str, str] = {}
    for part in parts[1 if prefix else 0 :]:
        if "=" in part:
            key, value = part.split("=", 1)
            fields[key.strip()] = value.strip()
    return prefix, fields


def native_r1_fields(fields: dict[str, str]) -> bool:
    direction = str(fields.get("canonical_direction") or fields.get("direction") or "").upper()
    phase = str(fields.get("phase") or "").upper()
    shock = str(fields.get("shock") or "").lower()
    compatibility = str(fields.get("compatibility") or fields.get("state") or "").lower()
    return (
        direction == "UP"
        and phase == "ESTABLISHED"
        and shock in {"0", "false"}
        and compatibility == "uptrend"
    )


def _telemetry_time(
    fields: dict[str, str], row: dict[str, str], *field_names: str
) -> datetime | None:
    for name in field_names:
        parsed = parse_timestamp(fields.get(name))
        if parsed is not None:
            return parsed
    return parse_timestamp(row.get("timestamp_broker"))


def lifecycle_audit(
    signal_rows: list[dict[str, str]], order_rows: list[dict[str, str]]
) -> dict[str, Any]:
    events: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: {"registered": [], "pivot": [], "second_break": [], "consumed": [], "signal": []}
    )
    missing_event_id_rows: list[str] = []
    unexpected_signal_reasons: list[str] = []

    stage_to_key = {stage: key for key, stage in LIFECYCLE_STAGES.items()}
    for row in signal_rows:
        stage = str(row.get("stage") or "")
        prefix, fields = parse_reason(str(row.get("reason") or ""))
        event_id = str(fields.get("event_id") or "")
        if stage in stage_to_key:
            if not event_id:
                missing_event_id_rows.append(f"{stage}|{row.get('timestamp_broker', '')}")
                continue
            events[event_id][stage_to_key[stage]].append({"row": dict(row), "fields": fields})
        elif stage == "WOULD_SIGNAL":
            if prefix != SIGNAL_PREFIX or not event_id:
                unexpected_signal_reasons.append(str(row.get("reason") or ""))
                continue
            events[event_id]["signal"].append({"row": dict(row), "fields": fields})

    duplicate_registrations: list[str] = []
    duplicate_pivots: list[str] = []
    duplicate_second_breaks: list[str] = []
    duplicate_consumptions: list[str] = []
    duplicate_signals: list[str] = []
    missing_consumptions: list[str] = []
    unregistered_transitions: list[str] = []
    invalid_consumption_outcomes: list[str] = []
    invalid_transition_outcomes: list[str] = []
    future_bar_violations: list[str] = []
    retrospective_pivot_entry_violations: list[str] = []
    setup_native = 0
    signal_native = 0
    native_event_ids: set[str] = set()
    event_rows: list[dict[str, Any]] = []
    event_by_timestamp: dict[str, list[dict[str, str]]] = defaultdict(list)
    active_intervals: list[tuple[datetime, datetime, str]] = []

    for event_id, event in sorted(events.items()):
        registered = event["registered"]
        pivots = event["pivot"]
        second_breaks = event["second_break"]
        consumed = event["consumed"]
        signals = event["signal"]
        if len(registered) != 1:
            duplicate_registrations.append(event_id)
        if len(pivots) > 1:
            duplicate_pivots.append(event_id)
        if len(second_breaks) > 1:
            duplicate_second_breaks.append(event_id)
        if len(consumed) > 1:
            duplicate_consumptions.append(event_id)
        if len(signals) > 1:
            duplicate_signals.append(event_id)
        if registered and not consumed:
            missing_consumptions.append(event_id)
        if not registered and (pivots or second_breaks or consumed or signals):
            unregistered_transitions.append(event_id)

        registration = registered[0] if len(registered) == 1 else None
        registration_fields = registration["fields"] if registration else {}
        registration_row = registration["row"] if registration else {}
        setup_time = (
            _telemetry_time(registration_fields, registration_row, "setup_time", "leg_one_close_time")
            if registration
            else None
        )
        episode_id = str(registration_fields.get("episode_id") or "")
        is_native_setup = bool(registration and native_r1_fields(registration_fields))
        if is_native_setup:
            setup_native += 1
            native_event_ids.add(event_id)

        pivot_time: datetime | None = None
        confirmation_time: datetime | None = None
        pivot_outcome = ""
        if len(pivots) == 1:
            pivot_fields = pivots[0]["fields"]
            pivot_row = pivots[0]["row"]
            pivot_time = parse_timestamp(pivot_fields.get("pivot_time"))
            confirmation_time = _telemetry_time(
                pivot_fields, pivot_row, "pivot_confirmation_time", "confirmation_time"
            )
            pivot_outcome = str(pivot_fields.get("outcome") or "")
            if pivot_outcome not in ALLOWED_PIVOT_OUTCOMES:
                invalid_transition_outcomes.append(f"{event_id}|pivot|{pivot_outcome}")
            if str(pivot_fields.get("pivot_ordinal") or "") != "1":
                retrospective_pivot_entry_violations.append(f"{event_id}|pivot_ordinal")
            if setup_time is None or pivot_time is None or confirmation_time is None:
                future_bar_violations.append(f"{event_id}|missing_pivot_time")
            else:
                if pivot_time <= setup_time:
                    future_bar_violations.append(f"{event_id}|pivot_not_after_setup")
                if confirmation_time < pivot_time + timedelta(minutes=30):
                    retrospective_pivot_entry_violations.append(
                        f"{event_id}|confirmation_before_two_right_bars"
                    )

        attempt_time: datetime | None = None
        second_outcome = ""
        if len(second_breaks) == 1:
            second_fields = second_breaks[0]["fields"]
            second_row = second_breaks[0]["row"]
            attempt_time = _telemetry_time(
                second_fields, second_row, "attempt_time", "second_break_time"
            )
            second_outcome = str(second_fields.get("outcome") or "")
            if second_outcome not in ALLOWED_SECOND_BREAK_OUTCOMES:
                invalid_transition_outcomes.append(f"{event_id}|second_break|{second_outcome}")
            if str(second_fields.get("attempt_ordinal") or "") != "1":
                duplicate_second_breaks.append(f"{event_id}|attempt_ordinal")
            if confirmation_time is None or attempt_time is None or attempt_time <= confirmation_time:
                retrospective_pivot_entry_violations.append(
                    f"{event_id}|second_break_not_after_confirmation"
                )

        consumption_time: datetime | None = None
        consumption_outcome = ""
        if len(consumed) == 1:
            consumption_fields = consumed[0]["fields"]
            consumption_row = consumed[0]["row"]
            consumption_time = _telemetry_time(
                consumption_fields, consumption_row, "consumed_time", "consumption_time"
            )
            consumption_outcome = str(consumption_fields.get("outcome") or "")
            if consumption_outcome not in ALLOWED_CONSUMPTION_OUTCOMES:
                invalid_consumption_outcomes.append(event_id)
            if setup_time is None or consumption_time is None or consumption_time < setup_time:
                future_bar_violations.append(f"{event_id}|invalid_consumption_time")
            elif setup_time is not None:
                active_intervals.append((setup_time, consumption_time, event_id))

        for signal in signals:
            fields = signal["fields"]
            row = signal["row"]
            if native_r1_fields(fields):
                signal_native += 1
            signal_time = parse_timestamp(row.get("timestamp_broker"))
            if confirmation_time is None or signal_time is None or signal_time <= confirmation_time:
                retrospective_pivot_entry_violations.append(
                    f"{event_id}|signal_not_after_pivot_confirmation"
                )
            if len(second_breaks) != 1:
                future_bar_violations.append(f"{event_id}|signal_without_one_second_break")
            if pivot_outcome != "confirmed" or second_outcome != "entry_attempt":
                future_bar_violations.append(f"{event_id}|signal_from_nonqualifying_transition")
            timestamp = str(row.get("timestamp_broker") or "")
            event_by_timestamp[timestamp].append(
                {
                    "event_id": event_id,
                    "episode_id": episode_id,
                    "direction": str(row.get("direction") or "").upper(),
                    "native": "1" if native_r1_fields(fields) else "0",
                }
            )

        event_rows.append(
            {
                "event_id": event_id,
                "episode_id": episode_id,
                "setup_time": setup_time,
                "pivot_time": pivot_time,
                "pivot_confirmation_time": confirmation_time,
                "second_break_time": attempt_time,
                "consumption_time": consumption_time,
                "pivot_outcome": pivot_outcome,
                "second_break_outcome": second_outcome,
                "consumption_outcome": consumption_outcome,
                "registered_count": len(registered),
                "pivot_count": len(pivots),
                "second_break_count": len(second_breaks),
                "consumption_count": len(consumed),
                "would_signal_count": len(signals),
                "native_setup": is_native_setup,
            }
        )

    active_state_overwrite_violations: list[str] = []
    intervals = sorted(active_intervals)
    for previous, current in zip(intervals, intervals[1:]):
        if current[0] < previous[1]:
            active_state_overwrite_violations.append(f"{previous[2]}->{current[2]}")

    executed = [row for row in order_rows if row.get("action") == "ORDER_SEND_OK"]
    missing_executed_matches: list[str] = []
    impure_executed_matches: list[str] = []
    executed_event_ids: list[str] = []
    for row in executed:
        timestamp = str(row.get("timestamp_broker") or "")
        direction = str(row.get("direction") or "").upper()
        matches = [
            item for item in event_by_timestamp.get(timestamp, []) if item["direction"] == direction
        ]
        if len(matches) != 1:
            missing_executed_matches.append(f"{timestamp}|{direction}")
            continue
        match = matches[0]
        executed_event_ids.append(match["event_id"])
        if match["native"] != "1":
            impure_executed_matches.append(match["event_id"])

    registration_count = sum(len(event["registered"]) for event in events.values())
    signal_count = sum(len(event["signal"]) for event in events.values())
    setup_purity = 100.0 * setup_native / registration_count if registration_count else 0.0
    native_executed = len(executed_event_ids) - len(impure_executed_matches)
    entry_purity = 100.0 * native_executed / len(executed) if executed else 0.0
    missing_lifecycle_fields = [
        row["event_id"]
        for row in event_rows
        if not row["episode_id"] or row["setup_time"] is None or row["consumption_time"] is None
    ]
    multiple_consumption_violations = sorted(
        set(duplicate_pivots + duplicate_second_breaks + duplicate_consumptions + duplicate_signals)
    )
    lifecycle_complete = bool(registration_count) and not any(
        (
            missing_event_id_rows,
            duplicate_registrations,
            duplicate_consumptions,
            missing_consumptions,
            unregistered_transitions,
            invalid_consumption_outcomes,
            invalid_transition_outcomes,
            missing_lifecycle_fields,
            unexpected_signal_reasons,
            missing_executed_matches,
        )
    )

    return {
        "registered_events": registration_count,
        "pivot_events": sum(len(event["pivot"]) for event in events.values()),
        "second_break_events": sum(len(event["second_break"]) for event in events.values()),
        "consumed_events": sum(len(event["consumed"]) for event in events.values()),
        "would_signal_events": signal_count,
        "setup_purity_pct": round(setup_purity, 6),
        "entry_purity_pct": round(entry_purity, 6),
        "native_event_ids": sorted(native_event_ids),
        "executed_event_ids": executed_event_ids,
        "missing_event_id_rows": missing_event_id_rows,
        "duplicate_registrations": duplicate_registrations,
        "duplicate_pivots": duplicate_pivots,
        "duplicate_second_breaks": duplicate_second_breaks,
        "duplicate_consumptions": duplicate_consumptions,
        "duplicate_signals": duplicate_signals,
        "missing_consumptions": missing_consumptions,
        "unregistered_transitions": unregistered_transitions,
        "invalid_consumption_outcomes": invalid_consumption_outcomes,
        "invalid_transition_outcomes": invalid_transition_outcomes,
        "unexpected_signal_reasons": unexpected_signal_reasons,
        "missing_executed_matches": missing_executed_matches,
        "impure_executed_matches": impure_executed_matches,
        "missing_lifecycle_fields": missing_lifecycle_fields,
        "future_bar_violations": sorted(set(future_bar_violations)),
        "retrospective_pivot_entry_violations": sorted(
            set(retrospective_pivot_entry_violations)
        ),
        "active_state_overwrite_violations": active_state_overwrite_violations,
        "multiple_consumption_violations": multiple_consumption_violations,
        "lifecycle_evidence_complete": lifecycle_complete,
        "event_by_timestamp": {
            timestamp: items[0]
            for timestamp, items in event_by_timestamp.items()
            if len(items) == 1
        },
        "event_rows": event_rows,
    }


def normalized_rows(
    result: dict[str, Any], event_by_timestamp: dict[str, dict[str, str]]
) -> list[dict[str, Any]]:
    rows = book_metrics.mt5_rows(result, source_priority=95)
    for row in rows:
        entry_time = row.get("entry_time")
        timestamp = (
            entry_time.strftime("%Y.%m.%d %H:%M:%S")
            if isinstance(entry_time, datetime)
            else str(entry_time or "")
        )
        event = event_by_timestamp.get(timestamp, {})
        row.update(
            {
                "component": SOURCE_ID,
                "source_id": SOURCE_ID,
                "upstream_source_id": SOURCE_ID,
                "upstream_component": result["name"],
                "family_group": "xau_r1_mature_second_continuation",
                "cell_id": "r1_hlf_second_continuation_structural_v1",
                "event_id": event.get("event_id", ""),
                "owned_episode_id": event.get("episode_id", ""),
            }
        )
    return rows


def parse_maximal_dd(value: object) -> dict[str, float | None]:
    text = str(value or "").strip()
    match = re.search(r"([-+]?\d[\d\s,]*\.?\d*)\s*\(([-+]?\d+(?:\.\d+)?)%\)", text)
    if not match:
        return {"usd": None, "pct": None}
    return {
        "usd": float(match.group(1).replace(" ", "").replace(",", "")),
        "pct": float(match.group(2)),
    }


def parse_relative_dd(value: object) -> dict[str, float | None]:
    text = str(value or "").strip()
    match = re.search(r"([-+]?\d+(?:\.\d+)?)%\s*\(([-+]?\d[\d\s,]*\.?\d*)\)", text)
    if not match:
        return {"usd": None, "pct": None}
    return {
        "usd": float(match.group(2).replace(" ", "").replace(",", "")),
        "pct": float(match.group(1)),
    }


def drawdown_audit(result: dict[str, Any]) -> dict[str, Any]:
    report = result.get("mt5_report_metrics", {})
    return {
        "balance_maximal": parse_maximal_dd(report.get("Balance Drawdown Maximal")),
        "balance_relative": parse_relative_dd(report.get("Balance Drawdown Relative")),
        "equity_maximal": parse_maximal_dd(report.get("Equity Drawdown Maximal")),
        "equity_relative": parse_relative_dd(report.get("Equity Drawdown Relative")),
        "raw": {
            "balance_maximal": report.get("Balance Drawdown Maximal"),
            "balance_relative": report.get("Balance Drawdown Relative"),
            "equity_maximal": report.get("Equity Drawdown Maximal"),
            "equity_relative": report.get("Equity Drawdown Relative"),
        },
    }


def _float_or_none(value: object) -> float | None:
    try:
        parsed = float(str(value or "").strip())
    except ValueError:
        return None
    if parsed != parsed or parsed in (float("inf"), float("-inf")):
        return None
    return parsed


def execution_risk_audit(
    result: dict[str, Any], order_rows: list[dict[str, str]]
) -> dict[str, Any]:
    base = guard_counts(result)
    actions = Counter(str(row.get("action") or "") for row in order_rows)
    reasons = Counter(str(row.get("reason") or "") for row in order_rows)
    successful = [row for row in order_rows if row.get("action") == "ORDER_SEND_OK"]
    failures = [row for row in order_rows if row.get("action") == "ORDER_SEND_FAIL"]
    unexplained_failures = [
        row
        for row in failures
        if not str(row.get("timestamp_broker") or "").strip()
        or not str(row.get("retcode") or "").strip()
        or not str(row.get("retcode_description") or "").strip()
        or not str(row.get("reason") or "").strip()
    ]

    risk_rows: list[dict[str, Any]] = []
    executed_risks: list[float] = []
    missing_risk = 0
    for row in order_rows:
        action = str(row.get("action") or "")
        reason = str(row.get("reason") or "")
        if action != "ORDER_SEND_OK" and reason not in {
            "risk_amount_overshoot",
            "r1_hlf_normalized_entry_to_stop_risk_overshoot",
        }:
            continue
        raw_risk = _float_or_none(row.get("actual_risk_usd"))
        actual_risk = abs(raw_risk) if raw_risk is not None else None
        intended_risk = _float_or_none(row.get("intended_risk_usd"))
        method = str(row.get("risk_calc_method") or "")
        if action == "ORDER_SEND_OK":
            if (
                actual_risk is None
                or actual_risk <= 0.0
                or intended_risk is None
                or intended_risk <= 0.0
                or method.lower() != "ordercalcprofit"
            ):
                missing_risk += 1
            else:
                executed_risks.append(actual_risk)
        risk_rows.append(
            {
                "timestamp_broker": row.get("timestamp_broker", ""),
                "action": action,
                "direction": row.get("direction", ""),
                "lots": row.get("lots", ""),
                "entry_reference": row.get("entry_reference", ""),
                "sl": row.get("sl", ""),
                "intended_risk_usd": intended_risk,
                "actual_risk_usd": actual_risk,
                "risk_calc_method": method,
                "reason": reason,
            }
        )

    trade_rows = read_csv(Path(result["trade_csv"]))
    open_at_end = sum(1 for row in trade_rows if not str(row.get("exit_time") or "").strip())
    report_text = str(result.get("mt5_report_metrics", {}).get("Total Trades", "0"))
    report_trades = int(re.sub(r"\D", "", report_text) or 0)
    forbidden_count = sum(reasons.get(reason, 0) for reason in FORBIDDEN_GUARD_REASONS)
    base.update(
        {
            "actions": dict(actions),
            "guard_reasons": dict(reasons),
            "successful_orders": len(successful),
            "mt5_trades": report_trades,
            "unexplained_send_failures": len(unexplained_failures),
            "order_send_failures": failures,
            "open_positions_at_end": open_at_end,
            "forbidden_guard_blocks": forbidden_count,
            "missing_initial_risk_calculations": missing_risk,
            "actual_initial_risk_usd": {
                "count": len(executed_risks),
                "minimum": round(min(executed_risks), 6) if executed_risks else None,
                "mean": (
                    round(sum(executed_risks) / len(executed_risks), 6)
                    if executed_risks
                    else None
                ),
                "maximum": round(max(executed_risks), 6) if executed_risks else None,
                "missing_count": missing_risk,
                "above_50_count": sum(value > RISK_AMOUNT_USD + 1e-7 for value in executed_risks),
            },
            "risk_rows": risk_rows,
        }
    )
    return base


def _ledger_entries(path: Path) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in read_csv(path):
        entry_time = parse_timestamp(row.get("entry_time"))
        direction = str(row.get("direction") or "").upper()
        if entry_time is not None and direction:
            output.append({"entry_time": entry_time, "direction": direction})
    return output


def overlap_audit(
    candidate_rows: list[dict[str, Any]], control_files: dict[str, Path]
) -> dict[str, Any]:
    candidate = [
        {
            "entry_time": parse_timestamp(row.get("entry_time")),
            "direction": str(row.get("direction") or "").upper(),
        }
        for row in candidate_rows
    ]
    candidate = [row for row in candidate if row["entry_time"] is not None and row["direction"]]
    report_rows: list[dict[str, Any]] = []
    for control, path in control_files.items():
        available = path.exists()
        controls = _ledger_entries(path) if available else []
        overlap_count = 0
        if available:
            for trade in candidate:
                if any(
                    item["direction"] == trade["direction"]
                    and abs((item["entry_time"] - trade["entry_time"]).total_seconds()) <= 900
                    for item in controls
                ):
                    overlap_count += 1
        overlap_pct = (
            100.0 * overlap_count / len(candidate) if available and candidate else None
        )
        report_rows.append(
            {
                "control": control,
                "path": rel(path),
                "available": available,
                "sha256": sha256_file(path) if available else None,
                "candidate_trades": len(candidate),
                "control_trades": len(controls),
                "overlap_count": overlap_count if available else None,
                "overlap_pct": round(overlap_pct, 6) if overlap_pct is not None else None,
            }
        )
    available_pcts = [row["overlap_pct"] for row in report_rows if row["overlap_pct"] is not None]
    return {
        "required_controls": len(control_files),
        "available_controls": sum(bool(row["available"]) for row in report_rows),
        "max_same_direction_overlap_pct": max(available_pcts) if available_pcts else None,
        "rows": report_rows,
    }


def calendar_year_audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        entry_date = row.get("entry_date")
        if isinstance(entry_date, date):
            grouped[entry_date.year].append(row)
    year_rows = []
    for year, items in sorted(grouped.items()):
        net = sum(float(row.get("pnl_usd") or 0.0) for row in items)
        year_rows.append({"year": year, "trades": len(items), "net_usd": round(net, 2)})
    return {
        "rows": year_rows,
        "exposure_years": len(year_rows),
        "profitable_years": sum(row["net_usd"] > 0.0 for row in year_rows),
    }


def episode_audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pnl: dict[str, float] = defaultdict(float)
    missing = 0
    for row in rows:
        episode_id = str(row.get("owned_episode_id") or "")
        event_id = str(row.get("event_id") or "")
        if not episode_id or not event_id:
            missing += 1
            continue
        pnl[episode_id] += float(row.get("pnl_usd") or 0.0)
    positive_total = sum(max(value, 0.0) for value in pnl.values())
    best_positive = max((max(value, 0.0) for value in pnl.values()), default=0.0)
    share = 100.0 * best_positive / positive_total if positive_total > 0.0 else None
    return {
        "owned_regime_episodes": len(pnl),
        "missing_event_trade_count": missing,
        "episode_net": {key: round(value, 2) for key, value in sorted(pnl.items())},
        "max_episode_positive_net_share_pct": round(share, 6) if share is not None else None,
    }


def real_evidence_metrics(
    *,
    rows: list[dict[str, Any]],
    book: dict[str, Any],
    lifecycle: dict[str, Any],
    execution: dict[str, Any],
    drawdown: dict[str, Any],
    overlap: dict[str, Any],
    pre_recent_end: str,
) -> dict[str, Any]:
    years = calendar_year_audit(rows)
    episodes = episode_audit(rows)
    pre_recent_date = date.fromisoformat(pre_recent_end.replace(".", "-"))
    pre_recent_net = sum(
        float(row.get("pnl_usd") or 0.0)
        for row in rows
        if isinstance(row.get("entry_date"), date) and row["entry_date"] <= pre_recent_date
    )
    native_ids = set(lifecycle["native_event_ids"])
    owned_state_net = sum(
        float(row.get("pnl_usd") or 0.0)
        for row in rows
        if str(row.get("event_id") or "") in native_ids
    )
    actual_risk = execution["actual_initial_risk_usd"]
    return {
        "trades": book["signals"],
        "owned_regime_episodes": episodes["owned_regime_episodes"],
        "exposure_years": years["exposure_years"],
        "profitable_years": years["profitable_years"],
        "win_rate_pct": book["wr"],
        "avg_win_loss": book["wl"],
        "profit_factor": book["pf"],
        "stress_profit_factor": book["stress_030_pf"],
        "stress_net_usd": book["stress_030_net"],
        "pre_recent_net_usd": round(pre_recent_net, 2),
        "top10_removed_net_usd": book["top10_removed_net"],
        "top3_days_removed_net_usd": book["top3_days_removed_net"],
        "best_month_share_pct": book["best_month_share_pct"],
        "max_episode_positive_net_share_pct": episodes[
            "max_episode_positive_net_share_pct"
        ],
        "native_setup_purity_pct": lifecycle["setup_purity_pct"],
        "native_entry_purity_pct": lifecycle["entry_purity_pct"],
        "owned_state_net_usd": round(owned_state_net, 2),
        "required_overlap_controls_expected": overlap["required_controls"],
        "required_overlap_controls": overlap["required_controls"],
        "available_overlap_controls": overlap["available_controls"],
        "max_same_direction_overlap_pct": overlap["max_same_direction_overlap_pct"],
        "future_bar_violations": len(lifecycle["future_bar_violations"]),
        "retrospective_pivot_entry_violations": len(
            lifecycle["retrospective_pivot_entry_violations"]
        ),
        "active_state_overwrite_violations": len(
            lifecycle["active_state_overwrite_violations"]
        ),
        "multiple_consumption_violations": len(
            lifecycle["multiple_consumption_violations"]
        ),
        "lifecycle_evidence_complete": int(lifecycle["lifecycle_evidence_complete"]),
        "missing_event_trade_count": episodes["missing_event_trade_count"],
        "successful_orders": execution["successful_orders"],
        "mt5_trades": execution["mt5_trades"],
        "normalized_trades": len(rows),
        "unexplained_send_failures": execution["unexplained_send_failures"],
        "open_positions_at_end": execution["open_positions_at_end"],
        "forbidden_guard_blocks": execution["forbidden_guard_blocks"],
        "missing_initial_risk_calculations": execution[
            "missing_initial_risk_calculations"
        ],
        "max_executed_initial_risk_usd": actual_risk["maximum"],
        "balance_dd_relative_pct": drawdown["balance_relative"]["pct"],
        "equity_dd_relative_pct": drawdown["equity_relative"]["pct"],
        "net_usd": book["net"],
        "equity_dd_maximal_usd": drawdown["equity_maximal"]["usd"],
        "closed_ledger_dd_usd": book["max_closed_dd"],
        "calendar_years": years,
        "episodes": episodes,
    }


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            output = dict(row)
            for key, value in output.items():
                if isinstance(value, datetime):
                    output[key] = value.strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(value, date):
                    output[key] = value.isoformat()
            writer.writerow(output)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def decide(static: dict[str, bool], windows: list[dict[str, dict[str, bool]]]) -> str:
    non_drawdown_groups = (
        "alpha_checks",
        "robustness_checks",
        "regime_independence_checks",
        "execution_risk_checks",
    )
    if not all(static.values()) or len(windows) != len(WINDOWS):
        return "R1_HLF_SECOND_CONTINUATION_REJECT"
    if not all(
        all(window[group].values())
        for window in windows
        for group in non_drawdown_groups
    ):
        return "R1_HLF_SECOND_CONTINUATION_REJECT"
    if not all(all(window["drawdown_checks"].values()) for window in windows):
        return "R1_HLF_SECOND_CONTINUATION_ALPHA_ONLY_RISK_REPAIR_REQUIRED"
    return "R1_HLF_SECOND_CONTINUATION_FULLY_QUALIFIED"


def _public_lifecycle(lifecycle: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in lifecycle.items()
        if key not in {"event_by_timestamp", "event_rows", "native_event_ids"}
    }


def _public_execution(execution: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in execution.items() if key != "risk_rows"}


def run_window(window: dict[str, str], timeout: int) -> dict[str, Any]:
    name = window["name"]
    mt5.VARIANTS = build_variants()
    mt5_md = REPORTS_DIR / f"{OUTPUT_STEM}_{name}_MT5.md"
    mt5_json = REPORTS_DIR / f"{OUTPUT_STEM}_{name}_MT5.json"
    exact = mt5.run_variants(
        from_date=window["from_date"],
        to_date=window["to_date"],
        tag=mt5.safe_name(f"OWNER_GOAL_R1_HLF_SECOND_CONTINUATION_{name}"),
        report_md=mt5_md,
        report_json=mt5_json,
        variant_timeout_seconds=timeout,
        deposit="10000",
        currency="USD",
    )
    result = exact["variants"][0]
    signal_rows = read_tsv(Path(result["signal_csv"]))
    order_rows = read_tsv(Path(result["order_csv"]))
    lifecycle = lifecycle_audit(signal_rows, order_rows)
    rows = normalized_rows(result, lifecycle["event_by_timestamp"])
    book = book_metrics.evaluate_book(f"{SOURCE_ID}_{name}", rows)
    execution = execution_risk_audit(result, order_rows)
    drawdown = drawdown_audit(result)
    overlap = overlap_audit(rows, OVERLAP_CONTROL_FILES_BY_WINDOW[name])
    evidence = real_evidence_metrics(
        rows=rows,
        book=book,
        lifecycle=lifecycle,
        execution=execution,
        drawdown=drawdown,
        overlap=overlap,
        pre_recent_end=window["pre_recent_end"],
    )
    checks = window_gate_checks(evidence)

    normalized_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{name}_NORMALIZED_TRADES.csv"
    lifecycle_json = REPORTS_DIR / f"{OUTPUT_STEM}_{name}_LIFECYCLE_AUDIT.json"
    lifecycle_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{name}_LIFECYCLE_EVENTS.csv"
    overlap_json = REPORTS_DIR / f"{OUTPUT_STEM}_{name}_OVERLAP_AUDIT.json"
    overlap_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{name}_OVERLAP_AUDIT.csv"
    risk_json = REPORTS_DIR / f"{OUTPUT_STEM}_{name}_ORDERCALCPROFIT_RISK_AUDIT.json"
    risk_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{name}_ORDERCALCPROFIT_RISK_AUDIT.csv"
    drawdown_json = REPORTS_DIR / f"{OUTPUT_STEM}_{name}_EQUITY_DRAWDOWN_AUDIT.json"
    gates_json = REPORTS_DIR / f"{OUTPUT_STEM}_{name}_REAL_EVIDENCE_GATES.json"

    write_rows(normalized_csv, rows)
    write_rows(lifecycle_csv, lifecycle["event_rows"])
    write_json(lifecycle_json, _public_lifecycle(lifecycle))
    write_rows(overlap_csv, overlap["rows"])
    write_json(overlap_json, overlap)
    write_rows(risk_csv, execution["risk_rows"])
    write_json(risk_json, _public_execution(execution))
    write_json(drawdown_json, drawdown)
    write_json(gates_json, {"metrics": evidence, "checks": checks})

    outputs = {
        "mt5_md": rel(mt5_md),
        "mt5_json": rel(mt5_json),
        "normalized_trades_csv": rel(normalized_csv),
        "lifecycle_audit_json": rel(lifecycle_json),
        "lifecycle_events_csv": rel(lifecycle_csv),
        "overlap_audit_json": rel(overlap_json),
        "overlap_audit_csv": rel(overlap_csv),
        "ordercalcprofit_risk_audit_json": rel(risk_json),
        "ordercalcprofit_risk_audit_csv": rel(risk_csv),
        "equity_drawdown_audit_json": rel(drawdown_json),
        "real_evidence_gates_json": rel(gates_json),
    }
    return {
        "period": {
            "from_date": window["from_date"],
            "to_date": window["to_date"],
            "pre_recent_end": window["pre_recent_end"],
        },
        "book": book_metrics.strip_heavy(book),
        "lifecycle": _public_lifecycle(lifecycle),
        "overlap": overlap,
        "execution_risk": _public_execution(execution),
        "drawdown": drawdown,
        "evidence_metrics": evidence,
        "checks": checks,
        "outputs": outputs,
        "_rows": rows,
    }


def strip_window(window: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in window.items() if key != "_rows"}


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU R1 Second-Continuation Higher-Low Long V1 Exact-MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        f"Frozen tester-input SHA256: `{payload['tester_input_sha256']}`",
        "",
        "## Window Results",
        "",
        "| Window | Trades | WR% | W/L | PF | Stress PF | Net | Equity DD% | Lifecycle complete | Max overlap% | Pass |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |",
    ]
    for name, window in payload["windows"].items():
        book = window["book"]
        evidence = window["evidence_metrics"]
        overlap = evidence["max_same_direction_overlap_pct"]
        lines.append(
            f"| `{name}` | {book['signals']} | {book['wr']:.2f} | {book['wl'] or 0.0:.4f} | "
            f"{book['pf'] or 0.0:.4f} | {book['stress_030_pf'] or 0.0:.4f} | "
            f"{book['net']:.2f} | {evidence['equity_dd_relative_pct'] or 0.0:.2f} | "
            f"{bool(evidence['lifecycle_evidence_complete'])} | "
            f"{overlap if overlap is not None else 0.0:.2f} | "
            f"{all(value for group in window['checks'].values() for value in group.values())} |"
        )

    lines.extend(
        [
            "",
            "## Lifecycle / Ownership",
            "",
            "| Window | Registered | Pivots | Second breaks | Consumed | Would signals | Setup purity% | Entry purity% | Future-bar | Retrospective | Overwrite | Multi-consume |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for name, window in payload["windows"].items():
        life = window["lifecycle"]
        lines.append(
            f"| `{name}` | {life['registered_events']} | {life['pivot_events']} | "
            f"{life['second_break_events']} | {life['consumed_events']} | "
            f"{life['would_signal_events']} | {life['setup_purity_pct']:.2f} | "
            f"{life['entry_purity_pct']:.2f} | {len(life['future_bar_violations'])} | "
            f"{len(life['retrospective_pivot_entry_violations'])} | "
            f"{len(life['active_state_overwrite_violations'])} | "
            f"{len(life['multiple_consumption_violations'])} |"
        )

    lines.extend(
        [
            "",
            "## `OrderCalcProfit` Risk and Equity Drawdown",
            "",
            "| Window | Risk rows | Missing risk | Max risk USD | Balance DD% | Equity DD% | Equity DD USD |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for name, window in payload["windows"].items():
        risk = window["execution_risk"]["actual_initial_risk_usd"]
        dd = window["drawdown"]
        lines.append(
            f"| `{name}` | {risk['count']} | {risk['missing_count']} | "
            f"{risk['maximum'] or 0.0:.6f} | {dd['balance_relative']['pct'] or 0.0:.2f} | "
            f"{dd['equity_relative']['pct'] or 0.0:.2f} | {dd['equity_maximal']['usd'] or 0.0:.2f} |"
        )

    lines.extend(["", "## Failed Gates", ""])
    for name, window in payload["windows"].items():
        failed = [
            f"{group}.{key}"
            for group, values in window["checks"].items()
            for key, passed in values.items()
            if not passed
        ]
        lines.append(f"- `{name}`: {', '.join(failed) if failed else 'none'}")

    lines.extend(["", "## Artifacts", ""])
    for key, value in payload["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail-closed exact runner for the R1 higher-low second-continuation exam."
    )
    parser.add_argument("--variant-timeout-seconds", type=int, default=1200)
    parser.add_argument("--static-only", action="store_true")
    args = parser.parse_args()

    checks = static_checks()
    static_payload = {
        "status": "MODE26_IMPLEMENTED_COMPILED_HISTORICAL_RUN_AUTHORIZED",
        "preregistration": rel(PREREG),
        "source_id": SOURCE_ID,
        "variant": VARIANT_NAME,
        "windows": WINDOWS,
        "deposit_usd": DEPOSIT_USD,
        "risk_amount_usd": RISK_AMOUNT_USD,
        "administrative_renumbering": ADMINISTRATIVE_RENUMBERING,
        "mode23_attrition": MODE23_ATTRITION,
        "tester_input_sha256": stable_hash(FROZEN_INPUTS),
        "static_checks": checks,
        "implementation_readiness": implementation_readiness(),
        "historical_run_authorized": HISTORICAL_RUN_AUTHORIZED,
        "runner_scaffold_only": RUNNER_SCAFFOLD_ONLY,
        "runner_evaluator_complete": RUNNER_EVALUATOR_COMPLETE,
    }
    if args.static_only:
        print(json.dumps(static_payload, indent=2))
        return 0 if PREREG.exists() and all(checks.values()) else 1

    if not all(checks.values()):
        raise RuntimeError(f"Frozen mode26 runner static checks failed: {checks}")
    if not HISTORICAL_RUN_AUTHORIZED:
        raise RuntimeError("Historical run has not been authorized after implementation review")
    require_ready()

    window_results = {
        window["name"]: run_window(window, args.variant_timeout_seconds) for window in WINDOWS
    }
    status = decide(checks, [window["checks"] for window in window_results.values()])
    all_rows = [row for window in window_results.values() for row in window["_rows"]]
    global_csv = REPORTS_DIR / f"{OUTPUT_STEM}_GLOBAL_NORMALIZED_TRADES.csv"
    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    write_rows(global_csv, all_rows)

    outputs = {
        "report_md": rel(report_md),
        "report_json": rel(report_json),
        "global_normalized_trades_csv": rel(global_csv),
    }
    for name, window in window_results.items():
        for key, value in window["outputs"].items():
            outputs[f"{name}_{key}"] = value

    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "preregistration": rel(PREREG),
        "preregistration_sha256": sha256_file(PREREG),
        "source_id": SOURCE_ID,
        "variant": VARIANT_NAME,
        "administrative_renumbering": ADMINISTRATIVE_RENUMBERING,
        "frozen_inputs": FROZEN_INPUTS,
        "tester_input_sha256": EXPECTED_FROZEN_INPUT_SHA256,
        "static_checks": checks,
        "windows": {name: strip_window(window) for name, window in window_results.items()},
        "outputs": outputs,
    }
    write_json(report_json, payload)
    report_md.write_text(render_report(payload), encoding="utf-8")
    print(json.dumps({"status": status, "report": str(report_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
