from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import analyze_a1_r2_prior_d1_low_first_retest_episode_audit as audit_common
import run_a1_r1_box_clean_requalification_exact as clean
import run_a1_r1_pullback_long_v1_exact as metrics
import run_a1_xau_m5_momentum_backtest_variants as mt5
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR, rel
from analyze_a1_xau_source_monthly_firewall import read_ledger
from run_a1_h4_d1_geometry_v2_weekly_shape import sha256_file, write_signal_csv
from run_a1_h4_d1_review_repair_exact import guard_counts
from run_a1_regime_router_v1_exact import ROUTER_INPUTS


PHASE1_ROOT = Path(__file__).resolve().parents[1]
EA_SOURCE = PHASE1_ROOT / "mt5" / "Experts" / "A1XauM5MomentumContinuationExecutor.mq5"
PREREG = (
    PHASE1_ROOT
    / "docs"
    / "A1_XAU_R2_SECOND_CONTINUATION_LOWER_HIGH_SHORT_V1_PREREG_2026_07_10.md"
)

SOURCE_ID = "r2_second_continuation_lower_high_short_v1"
VARIANT_NAME = "r2_lhf_second_continuation_structural_v1"
OUTPUT_STEM = "A1_XAU_R2_SECOND_CONTINUATION_LOWER_HIGH_SHORT_V1_EXACT_20260710"
PROPOSED_SIGNAL_MODE = 24
DEPOSIT_USD = 10_000.0
RISK_AMOUNT_USD = 50.0
HISTORICAL_RUN_AUTHORIZED = True
RUNNER_SCAFFOLD_ONLY = False
SIGNAL_MATCH_WINDOW_SECONDS = 5 * 60

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

REQUIRED_OVERLAP_CONTROLS = (
    "r2_pullback_rejection_v1_h1",
    "r2_pullback_rejection_v2_body58",
    "r2_continuation_v1_body45",
    "r2_continuation_v2_break15_30",
    "r2_continuation_v4_atr45",
    "r2_prior_d1_low_first_retest_killed",
)

CONTROL_PATHS = {
    "primary_202207_202606": {
        "r2_pullback_rejection_v1_h1": REPORTS_DIR
        / "A1_XAU_R2_PULLBACK_REJECTION_SHORT_V1_EXACT_20260708_r2_pullback_short_h1_confirm_NORMALIZED_TRADES.csv",
        "r2_pullback_rejection_v2_body58": REPORTS_DIR
        / "A1_XAU_R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_EXACT_20260709_r2_h1_m5_body58_NORMALIZED_TRADES.csv",
        "r2_continuation_v1_body45": REPORTS_DIR
        / "A1_XAU_R2_CONTINUATION_SHORT_V1_EXACT_20260709_r2_impulse_retest_body45_NORMALIZED_TRADES.csv",
        "r2_continuation_v2_break15_30": REPORTS_DIR
        / "A1_XAU_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_20260709_r2_impulse_break15_30_cap20_NORMALIZED_TRADES.csv",
        "r2_continuation_v4_atr45": REPORTS_DIR
        / "A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_r2_impulse_body45_atr45_NORMALIZED_TRADES.csv",
        "r2_prior_d1_low_first_retest_killed": REPORTS_DIR
        / "A1_XAU_R2_PRIOR_D1_LOW_FIRST_RETEST_SHORT_V1_EXACT_20260710_r2_pdl_first_retest_structural_v1_NORMALIZED_TRADES.csv",
    },
    "prehistory_201601_202112": {
        name: REPORTS_DIR / f"A1_XAU_R2_CONTROL_PREHISTORY_201601_202112_{name}_NORMALIZED_TRADES.csv"
        for name in REQUIRED_OVERLAP_CONTROLS
    },
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
    "InpRegimeRouterMode": "2",
    "InpDirectionMode": "2",
    "InpRiskReward": "2.00",
    "InpMaxSpreadPoints": "75",
    "InpMaxEstimatedCostR": "0.10",
    "InpR2LhfAtrPeriod": "14",
    "InpR2LhfMaturityD1Bars": "3",
    "InpR2LhfLeg1LookbackH1Bars": "12",
    "InpR2LhfLeg1BreakMarginH1Atr": "0.10",
    "InpR2LhfLeg1MinRangeH1Atr": "1.00",
    "InpR2LhfLeg1MinBodyFraction": "0.50",
    "InpR2LhfLeg1CloseLocationMax": "0.25",
    "InpR2LhfResetWindowM15Bars": "16",
    "InpR2LhfPivotLeftBars": "2",
    "InpR2LhfPivotRightBars": "2",
    "InpR2LhfResetMinDepthH1Atr": "0.35",
    "InpR2LhfLowerHighMarginH1Atr": "0.10",
    "InpR2LhfSecondBreakWindowM15Bars": "16",
    "InpR2LhfSecondTouchM15Atr": "0.10",
    "InpR2LhfSecondCloseM15Atr": "0.10",
    "InpR2LhfSecondMinBodyFraction": "0.50",
    "InpR2LhfSecondCloseLocationMax": "0.25",
    "InpR2LhfInvalidReclaimH1Atr": "0.10",
    "InpR2LhfStopBufferM15Atr": "0.20",
    "InpR2LhfMaxStopH1Atr": "1.00",
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

EXPECTED_FROZEN_INPUT_SHA256 = "d86bbb02074ff4cfdc6464a7c00e3f5792c2ecb6e8181e9a6837f36f85b2f12c"

REQUIRED_EA_TOKENS = (
    "SIGNAL_R2_SECOND_CONTINUATION_LOWER_HIGH_SHORT = 24",
    "InpR2LhfMaturityD1Bars",
    "R2_LHF_STATE_WAIT_FIRST_PIVOT",
    "R2_LHF_STATE_LOWER_HIGH_CONFIRMED",
    "g_r2_lhf_consumed_setup_time",
    "g_r2_lhf_last_counted_m15_bar",
    "g_r2_lhf_reset_m15_bars_observed",
    "g_r2_lhf_second_break_m15_bars_observed",
    "R2LhfTakeDistinctCompletedM15Bar",
    "final_reset_bar",
    "final_second_break_bar",
    "TryR2SecondContinuationLowerHighShortSignal",
    "r2_lhf_first_pivot_rejected",
    "r2_lhf_second_break_before_arm",
    "r2_lhf_first_second_break_rejected",
    "r2_lhf_stop_h1_atr_exceeded",
    "R2_SECOND_CONTINUATION_LOWER_HIGH_SHORT_STATE_",
    "OrderCalcProfit(ORDER_TYPE_SELL",
    "R2_LHF_LEG_ONE_REGISTERED",
    "R2_LHF_FIRST_PIVOT_CONFIRMED",
    "R2_LHF_EVENT_CONSUMED",
    "R2_LHF_D1_OWNERSHIP",
    '"actual_risk_usd"',
)


def stable_hash(value: Any) -> str:
    blob = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def build_variants() -> list[mt5.Variant]:
    return [
        mt5.Variant(
            name=VARIANT_NAME,
            label=(
                "Strict established-R2 H1 leg one, first confirmed M15 lower high, "
                "and first second-break acceptance short, fixed 2R"
            ),
            run_id="BT_A1_XAU_R2_LHF_SECOND_CONTINUATION_STRUCTURAL_V1",
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
    return {
        "exactly_one_variant": len(variants) == 1,
        "variant_name_frozen": variant is not None and variant.name == VARIANT_NAME,
        "tester_inputs_exactly_frozen": inputs == FROZEN_INPUTS,
        "tester_input_hash_frozen": stable_hash(inputs) == EXPECTED_FROZEN_INPUT_SHA256,
        "two_frozen_exact_windows": actual_windows == expected_windows,
        "new_appended_signal_mode_24": inputs.get("InpSignalMode") == "24",
        "strict_native_r2_short_only": (
            inputs.get("InpRegimeRouterMode") == "2" and inputs.get("InpDirectionMode") == "2"
        ),
        "fixed_rr2": inputs.get("InpRiskReward") == "2.00",
        "mature_three_d1_state": inputs.get("InpR2LhfMaturityD1Bars") == "3",
        "first_two_sided_pivot_only": (
            inputs.get("InpR2LhfPivotLeftBars") == "2"
            and inputs.get("InpR2LhfPivotRightBars") == "2"
        ),
        "finite_first_event_windows": (
            inputs.get("InpR2LhfResetWindowM15Bars") == "16"
            and inputs.get("InpR2LhfSecondBreakWindowM15Bars") == "16"
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
            and inputs.get("InpShortSessionStartHour") == "0"
            and inputs.get("InpShortSessionEndHour") == "24"
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
        "complete_runner_available": not RUNNER_SCAFFOLD_ONLY,
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
    """Fail-closed gate contract for each future exact-MT5 window report."""

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
            "top3_days_removed_net_gt_0": _ge(
                metrics, "top3_days_removed_net_usd", 0.0000001
            ),
            "best_month_share_lte_30": _le(
                metrics,
                "best_month_share_pct",
                GLOBAL_GATE_THRESHOLDS["best_month_share_pct_max"],
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
                and required_controls == float(len(REQUIRED_OVERLAP_CONTROLS))
                and available_controls == required_controls
            ),
            "same_event_overlap_strictly_below_20pct": (
                (_number(metrics, "max_same_direction_overlap_pct") is not None)
                and _number(metrics, "max_same_direction_overlap_pct")
                < GLOBAL_GATE_THRESHOLDS["same_event_overlap_pct_strict_max"]
            ),
            "zero_future_bar_violations": _eq(metrics, "future_bar_violations", 0.0),
            "zero_retrospective_pivot_entries": _eq(
                metrics, "retrospective_pivot_entry_violations", 0.0
            ),
            "zero_state_overwrites": _eq(metrics, "active_state_overwrite_violations", 0.0),
            "zero_multiple_consumptions": _eq(
                metrics, "multiple_consumption_violations", 0.0
            ),
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


LIFECYCLE_STAGES = {
    "registered": "R2_LHF_LEG_ONE_REGISTERED",
    "pivot": "R2_LHF_FIRST_PIVOT_CONFIRMED",
    "consumed": "R2_LHF_EVENT_CONSUMED",
    "ownership": "R2_LHF_D1_OWNERSHIP",
}

ALLOWED_CONSUMPTION_OUTCOMES = {
    "r2_lhf_regime_ownership_lost",
    "r2_lhf_reset_expired",
    "r2_lhf_continuation_without_reset",
    "r2_lhf_origin_high_invalidated",
    "r2_lhf_first_pivot_rejected",
    "r2_lhf_second_break_before_arm",
    "r2_lhf_second_break_expired",
    "r2_lhf_lower_high_invalidated",
    "r2_lhf_first_second_break_consumed",
    "tester_deinit",
}

FORBIDDEN_GUARD_MARKERS = (
    "blocked_entry_hour",
    "blocked_entry_day_hour",
    "direction_blocked_entry_hour",
    "directional_session_filter",
    "previous_month",
    "weekly_loss",
    "negative_stack",
    "third_entry",
    "feature_loss",
    "portfolio_daily",
    "portfolio_cooldown",
)


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_dict_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields or ["empty"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def parse_reason(reason: str) -> tuple[str, dict[str, str]]:
    parts = [part.strip() for part in str(reason or "").split("|") if part.strip()]
    prefix = parts[0] if parts and "=" not in parts[0] else ""
    fields: dict[str, str] = {}
    for part in parts[1 if prefix else 0 :]:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        fields[key.strip()] = value.strip()
    return prefix, fields


def _int_value(value: Any) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def lifecycle_audit(
    signal_rows: list[dict[str, str]], order_rows: list[dict[str, str]]
) -> dict[str, Any]:
    registered: Counter[str] = Counter()
    pivots: Counter[str] = Counter()
    consumed: Counter[str] = Counter()
    signals: Counter[str] = Counter()
    registration_fields: dict[str, dict[str, str]] = {}
    pivot_fields: dict[str, dict[str, str]] = {}
    consumed_index: dict[str, int] = {}
    pivot_index: dict[str, int] = {}
    signal_events: list[dict[str, Any]] = []
    artifact_rows: list[dict[str, Any]] = []
    ownership_rows: list[dict[str, Any]] = []
    active_event = ""
    active_state = "IDLE"
    active_state_overwrite_violations: list[str] = []
    transition_violations: list[str] = []
    future_bar_violations: list[str] = []
    retrospective_entry_violations: list[str] = []
    native_setup_failures: list[str] = []
    native_signal_failures: list[str] = []
    invalid_consumption_outcomes: list[str] = []

    for index, row in enumerate(signal_rows):
        stage = str(row.get("stage") or "")
        prefix, fields = parse_reason(str(row.get("reason") or ""))
        event_id = fields.get("event_id", "")
        if stage == LIFECYCLE_STAGES["ownership"] and prefix == "R2_LHF_D1_OWNERSHIP":
            d1_time = _int_value(fields.get("d1_time"))
            ownership_rows.append(
                {
                    "row_index": index,
                    "timestamp_broker": row.get("timestamp_broker", ""),
                    "d1_time": d1_time,
                    "mature": fields.get("mature") == "1",
                    "state": fields.get("state", ""),
                    "setup": fields.get("setup", ""),
                    "phase": fields.get("phase", ""),
                    "shock": fields.get("shock", ""),
                    "maturity": fields.get("maturity", ""),
                }
            )
            continue

        if stage in LIFECYCLE_STAGES.values() and stage != LIFECYCLE_STAGES["ownership"]:
            artifact_rows.append(
                {
                    "row_index": index,
                    "timestamp_broker": row.get("timestamp_broker", ""),
                    "stage": stage,
                    "prefix": prefix,
                    **fields,
                }
            )

        if stage == LIFECYCLE_STAGES["registered"]:
            if not event_id or prefix != "R2_LHF_LIFECYCLE":
                transition_violations.append(f"registration_missing_event:{index}")
                continue
            registered[event_id] += 1
            registration_fields[event_id] = fields
            if active_event or active_state != "IDLE":
                active_state_overwrite_violations.append(event_id)
            if fields.get("from") != "IDLE" or fields.get("to") != "WAIT_FIRST_PIVOT":
                transition_violations.append(f"registration_transition:{event_id}")
            if not (
                fields.get("setup") == "DOWN"
                and fields.get("phase") == "ESTABLISHED"
                and fields.get("shock") == "0"
                and fields.get("maturity") == "3"
            ):
                native_setup_failures.append(event_id)
            active_event = event_id
            active_state = "WAIT_FIRST_PIVOT"
            continue

        if stage == LIFECYCLE_STAGES["pivot"]:
            if not event_id:
                transition_violations.append(f"pivot_missing_event:{index}")
                continue
            pivots[event_id] += 1
            pivot_fields[event_id] = fields
            pivot_index[event_id] = index
            if active_event != event_id or active_state != "WAIT_FIRST_PIVOT":
                transition_violations.append(f"pivot_without_wait:{event_id}")
            if fields.get("from") != "WAIT_FIRST_PIVOT" or fields.get("to") != "LOWER_HIGH_CONFIRMED":
                transition_violations.append(f"pivot_transition:{event_id}")
            pivot_time = _int_value(fields.get("pivot_time"))
            confirm_time = _int_value(fields.get("confirm_time"))
            expected_lag = (int(FROZEN_INPUTS["InpR2LhfPivotRightBars"]) + 1) * 15 * 60
            if pivot_time is None or confirm_time is None or confirm_time - pivot_time != expected_lag:
                future_bar_violations.append(event_id)
            active_state = "LOWER_HIGH_CONFIRMED"
            continue

        if stage == LIFECYCLE_STAGES["consumed"]:
            if not event_id:
                transition_violations.append(f"consumption_missing_event:{index}")
                continue
            consumed[event_id] += 1
            consumed_index[event_id] = index
            if active_event != event_id or active_state not in {"WAIT_FIRST_PIVOT", "LOWER_HIGH_CONFIRMED"}:
                transition_violations.append(f"consumption_without_active:{event_id}")
            if fields.get("from") != active_state or fields.get("to") != "IDLE":
                transition_violations.append(f"consumption_transition:{event_id}")
            if fields.get("outcome") not in ALLOWED_CONSUMPTION_OUTCOMES:
                invalid_consumption_outcomes.append(event_id)
            active_event = ""
            active_state = "IDLE"
            continue

        if stage == "WOULD_SIGNAL":
            if not prefix.startswith("R2_SECOND_CONTINUATION_LOWER_HIGH_SHORT_STATE_") or not event_id:
                native_signal_failures.append(event_id or f"missing_event:{index}")
                continue
            signals[event_id] += 1
            if not (
                prefix == "R2_SECOND_CONTINUATION_LOWER_HIGH_SHORT_STATE_downtrend"
                and fields.get("setup") == "DOWN"
                and fields.get("phase") == "ESTABLISHED"
                and fields.get("shock") == "0"
                and fields.get("maturity") == "3"
            ):
                native_signal_failures.append(event_id)
            if event_id not in pivot_index or pivot_index[event_id] >= index:
                retrospective_entry_violations.append(event_id)
            if event_id not in consumed_index or consumed_index[event_id] >= index:
                retrospective_entry_violations.append(event_id)
            try:
                signal_time = audit_common.parse_signal_time(str(row.get("timestamp_broker") or ""))
            except ValueError:
                signal_time = None
                retrospective_entry_violations.append(event_id)
            signal_events.append(
                {
                    "event_id": event_id,
                    "timestamp": signal_time,
                    "timestamp_text": row.get("timestamp_broker", ""),
                    "direction": str(row.get("direction") or "").upper(),
                    "row_index": index,
                    "native": event_id not in native_signal_failures,
                }
            )

    if active_event:
        transition_violations.append(f"active_at_log_end:{active_event}")

    episode_count = 0
    in_episode = False
    for row in sorted(ownership_rows, key=lambda item: (item["d1_time"] is None, item["d1_time"] or 0)):
        mature = bool(row["mature"])
        if mature and not in_episode:
            episode_count += 1
        row["episode_id"] = episode_count if mature else 0
        in_episode = mature

    registered_episode_ids: dict[str, int] = {}
    ordered_ownership = [row for row in ownership_rows if row["d1_time"] is not None]
    for event_id, fields in registration_fields.items():
        setup_time = _int_value(fields.get("setup_time"))
        eligible = [row for row in ordered_ownership if setup_time is not None and row["d1_time"] <= setup_time]
        latest = max(eligible, key=lambda row: row["d1_time"], default=None)
        registered_episode_ids[event_id] = int(latest["episode_id"]) if latest and latest["mature"] else 0

    executed_rows = [row for row in order_rows if row.get("action") == "ORDER_SEND_OK"]
    missing_executed_signal_matches: list[str] = []
    impure_executed_signal_matches: list[str] = []
    for row in executed_rows:
        timestamp = str(row.get("timestamp_broker") or "")
        direction = str(row.get("direction") or "").upper()
        matches = [
            signal
            for signal in signal_events
            if signal["timestamp_text"] == timestamp and signal["direction"] == direction
        ]
        if len(matches) != 1:
            missing_executed_signal_matches.append(f"{timestamp}|{direction}")
        elif not matches[0]["native"]:
            impure_executed_signal_matches.append(matches[0]["event_id"])

    return {
        "registered_events": len(registered),
        "pivot_events": len(pivots),
        "consumed_events": len(consumed),
        "signal_events": len(signals),
        "duplicate_registrations": sorted(key for key, count in registered.items() if count != 1),
        "duplicate_pivots": sorted(key for key, count in pivots.items() if count > 1),
        "duplicate_consumptions": sorted(key for key, count in consumed.items() if count != 1),
        "duplicate_signals": sorted(key for key, count in signals.items() if count > 1),
        "missing_consumptions": sorted(set(registered) - set(consumed)),
        "consumed_without_registration": sorted(set(consumed) - set(registered)),
        "pivot_without_registration": sorted(set(pivots) - set(registered)),
        "signals_without_registration": sorted(set(signals) - set(registered)),
        "active_state_overwrite_violations": active_state_overwrite_violations,
        "transition_violations": transition_violations,
        "future_bar_violations": future_bar_violations,
        "retrospective_entry_violations": sorted(set(retrospective_entry_violations)),
        "native_setup_failures": sorted(set(native_setup_failures)),
        "native_signal_failures": sorted(set(native_signal_failures)),
        "invalid_consumption_outcomes": sorted(set(invalid_consumption_outcomes)),
        "missing_executed_signal_matches": missing_executed_signal_matches,
        "impure_executed_signal_matches": impure_executed_signal_matches,
        "ownership_episode_count": episode_count,
        "registered_episode_ids": registered_episode_ids,
        "signal_events_detail": signal_events,
        "artifact_rows": artifact_rows,
        "ownership_rows": ownership_rows,
    }


def event_for_entry(entry_time: datetime, direction: str, lifecycle: dict[str, Any]) -> str:
    candidates = [
        row
        for row in lifecycle["signal_events_detail"]
        if row["timestamp"] is not None
        and row["direction"] == direction.upper()
        and abs((entry_time - row["timestamp"]).total_seconds()) <= SIGNAL_MATCH_WINDOW_SECONDS
    ]
    if not candidates:
        return ""
    nearest = min(candidates, key=lambda row: abs((entry_time - row["timestamp"]).total_seconds()))
    return str(nearest["event_id"])


def normalize_rows(result: dict[str, Any], lifecycle: dict[str, Any]) -> list[dict[str, Any]]:
    rows = metrics.mt5_rows(result, source_priority=97)
    for row in rows:
        event_id = event_for_entry(row["entry_time"], str(row.get("direction") or ""), lifecycle)
        row.update(
            {
                "component": SOURCE_ID,
                "source_id": SOURCE_ID,
                "upstream_source_id": SOURCE_ID,
                "upstream_component": VARIANT_NAME,
                "family_group": "xau_r2_second_continuation_lower_high",
                "cell_id": SOURCE_ID,
                "event_id": event_id,
                "owned_episode_id": lifecycle["registered_episode_ids"].get(event_id, 0),
            }
        )
    return rows


def risk_execution_audit(result: dict[str, Any], order_rows: list[dict[str, str]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    actions = Counter(row.get("action", "") for row in order_rows)
    reasons = Counter(row.get("reason", "") for row in order_rows if row.get("action") == "GUARD_BLOCK")
    failures = [row for row in order_rows if row.get("action") == "ORDER_SEND_FAIL"]
    actual_risks: list[float] = []
    missing_risk = 0
    for row in order_rows:
        if row.get("action") != "ORDER_SEND_OK":
            continue
        try:
            risk = float(str(row.get("actual_risk_usd") or "").strip())
        except ValueError:
            missing_risk += 1
            continue
        if risk <= 0.0:
            missing_risk += 1
            continue
        actual_risks.append(risk)
    report_trades = int(
        re.sub(r"\D", "", str(result.get("mt5_report_metrics", {}).get("Total Trades", "0"))) or "0"
    )
    forbidden = {
        reason: count
        for reason, count in reasons.items()
        if any(marker in reason for marker in FORBIDDEN_GUARD_MARKERS)
    }
    return {
        "actions": dict(actions),
        "guard_reasons": dict(reasons),
        "order_send_failures": [
            {
                "timestamp_broker": row.get("timestamp_broker", ""),
                "direction": row.get("direction", ""),
                "retcode": row.get("retcode", ""),
                "retcode_description": row.get("retcode_description", ""),
            }
            for row in failures
        ],
        "unexplained_send_failures": sum(
            1
            for row in failures
            if not row.get("timestamp_broker") or not row.get("retcode") or not row.get("retcode_description")
        ),
        "successful_orders": actions.get("ORDER_SEND_OK", 0),
        "mt5_trades": report_trades,
        "normalized_trades": len(rows),
        "forbidden_guard_blocks": sum(forbidden.values()),
        "forbidden_guard_reasons": forbidden,
        "risk_amount_overshoot_blocks": reasons.get("risk_amount_overshoot", 0),
        "missing_initial_risk_calculations": missing_risk,
        "actual_initial_risk_usd": {
            "count": len(actual_risks),
            "minimum": min(actual_risks) if actual_risks else None,
            "maximum": max(actual_risks) if actual_risks else None,
            "mean": sum(actual_risks) / len(actual_risks) if actual_risks else None,
            "above_50_count": sum(value > 50.0000001 for value in actual_risks),
        },
        "open_positions_at_end": sum(1 for row in rows if not row.get("exit_time")),
    }


def overlap_audit(window_name: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for control_name in REQUIRED_OVERLAP_CONTROLS:
        path = CONTROL_PATHS[window_name][control_name]
        if not path.exists():
            output.append(
                {
                    "control": control_name,
                    "available": False,
                    "path": str(path),
                    "candidate_trades": len(rows),
                    "overlap_trades": None,
                    "overlap_pct": None,
                }
            )
            continue
        result = audit_common.overlap_with_control(rows, read_ledger(path), control_name)
        result.update({"available": True, "path": str(path)})
        output.append(result)
    return output


def episode_concentration(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pnl: dict[int, float] = defaultdict(float)
    for row in rows:
        pnl[int(row.get("owned_episode_id") or 0)] += float(row.get("pnl_usd") or 0.0)
    positive = {key: value for key, value in pnl.items() if key > 0 and value > 0.0}
    total = sum(positive.values())
    share = 100.0 * max(positive.values(), default=0.0) / total if total > 0.0 else None
    return {
        "episode_pnl": {str(key): round(value, 2) for key, value in sorted(pnl.items())},
        "traded_owned_episodes": len({key for key in pnl if key > 0}),
        "missing_episode_trades": sum(1 for row in rows if int(row.get("owned_episode_id") or 0) <= 0),
        "max_positive_net_share_pct": round(share, 2) if share is not None else None,
    }


def evaluate_window(
    window: dict[str, str],
    result: dict[str, Any],
    rows: list[dict[str, Any]],
    lifecycle: dict[str, Any],
    risk: dict[str, Any],
    overlaps: list[dict[str, Any]],
) -> dict[str, Any]:
    book = metrics.flat_shape(window["name"], rows)
    compact = metrics.strip_heavy(book)
    years = clean.year_rows(rows)
    profitable_years = sum(1 for row in years if row["net"] > 0.0)
    pre_recent_end = date.fromisoformat(window["pre_recent_end"].replace(".", "-"))
    pre_recent_net = sum(float(row["pnl_usd"]) for row in rows if row["entry_date"] <= pre_recent_end)
    episodes = episode_concentration(rows)
    drawdown = clean.mt5_drawdown(result.get("mt5_report_metrics", {}))
    available_overlaps = [row for row in overlaps if row["available"]]
    max_overlap = (
        max(float(row["overlap_pct"]) for row in available_overlaps)
        if available_overlaps
        else None
    )
    valid_setups = lifecycle["registered_events"] - len(lifecycle["native_setup_failures"])
    valid_entries = risk["successful_orders"] - len(lifecycle["impure_executed_signal_matches"])
    native_setup_purity = (
        100.0 * valid_setups / lifecycle["registered_events"]
        if lifecycle["registered_events"]
        else 0.0
    )
    native_entry_purity = (
        100.0 * valid_entries / risk["successful_orders"] if risk["successful_orders"] else 0.0
    )
    gate_metrics = {
        "trades": compact["signals"],
        "owned_regime_episodes": len(set(lifecycle["registered_episode_ids"].values()) - {0}),
        "exposure_years": len(years),
        "profitable_years": profitable_years,
        "win_rate_pct": compact["wr"],
        "avg_win_loss": compact["wl"],
        "profit_factor": compact["pf"],
        "stress_profit_factor": compact["stress_030_pf"],
        "stress_net_usd": compact["stress_030_net"],
        "pre_recent_net_usd": round(pre_recent_net, 2),
        "top10_removed_net_usd": compact["top10_removed_net"],
        "top3_days_removed_net_usd": compact["top3_days_removed_net"],
        "best_month_share_pct": compact["best_month_share_pct"],
        "max_episode_positive_net_share_pct": episodes["max_positive_net_share_pct"],
        "native_setup_purity_pct": round(native_setup_purity, 4),
        "native_entry_purity_pct": round(native_entry_purity, 4),
        "owned_state_net_usd": (
            compact["net"] if episodes["missing_episode_trades"] == 0 else None
        ),
        "required_overlap_controls": len(REQUIRED_OVERLAP_CONTROLS),
        "available_overlap_controls": len(available_overlaps),
        "max_same_direction_overlap_pct": max_overlap,
        "future_bar_violations": len(lifecycle["future_bar_violations"]),
        "retrospective_pivot_entry_violations": len(lifecycle["retrospective_entry_violations"]),
        "active_state_overwrite_violations": len(lifecycle["active_state_overwrite_violations"]),
        "multiple_consumption_violations": len(lifecycle["duplicate_consumptions"]),
        "successful_orders": risk["successful_orders"],
        "mt5_trades": risk["mt5_trades"],
        "normalized_trades": risk["normalized_trades"],
        "unexplained_send_failures": risk["unexplained_send_failures"],
        "open_positions_at_end": risk["open_positions_at_end"],
        "forbidden_guard_blocks": risk["forbidden_guard_blocks"],
        "missing_initial_risk_calculations": risk["missing_initial_risk_calculations"],
        "max_executed_initial_risk_usd": risk["actual_initial_risk_usd"]["maximum"],
        "balance_dd_relative_pct": drawdown["balance_dd_relative_pct"],
        "equity_dd_relative_pct": drawdown["equity_dd_relative_pct"],
        "net_usd": compact["net"],
        "equity_dd_maximal_usd": drawdown["equity_dd_maximal_usd"],
        "closed_ledger_dd_usd": compact["max_closed_dd"],
    }
    checks = window_gate_checks(gate_metrics)
    lifecycle_checks = {
        "registrations_unique": not lifecycle["duplicate_registrations"],
        "pivots_unique": not lifecycle["duplicate_pivots"],
        "consumptions_exact": not lifecycle["duplicate_consumptions"]
        and not lifecycle["missing_consumptions"]
        and not lifecycle["consumed_without_registration"],
        "signals_unique_and_registered": not lifecycle["duplicate_signals"]
        and not lifecycle["signals_without_registration"],
        "state_transitions_valid": not lifecycle["transition_violations"],
        "consumption_outcomes_valid": not lifecycle["invalid_consumption_outcomes"],
        "executions_match_native_signals": not lifecycle["missing_executed_signal_matches"]
        and not lifecycle["impure_executed_signal_matches"],
    }
    checks["regime_independence_checks"].update(lifecycle_checks)
    return {
        **compact,
        "window": window["name"],
        "gate_metrics": gate_metrics,
        "checks": checks,
        "year_rows": years,
        "episode_audit": episodes,
        "lifecycle_audit": {
            key: value
            for key, value in lifecycle.items()
            if key not in {"artifact_rows", "ownership_rows", "signal_events_detail"}
        },
        "risk_execution_audit": risk,
        "overlap_audit": overlaps,
        "drawdown_audit": drawdown,
    }


def decide(static: dict[str, bool], windows: list[dict[str, dict[str, bool]]]) -> str:
    non_drawdown_groups = (
        "alpha_checks",
        "robustness_checks",
        "regime_independence_checks",
        "execution_risk_checks",
    )
    if not all(static.values()) or len(windows) != len(WINDOWS):
        return "R2_LHF_SECOND_CONTINUATION_REJECT"
    if not all(
        all(window[group].values())
        for window in windows
        for group in non_drawdown_groups
    ):
        return "R2_LHF_SECOND_CONTINUATION_REJECT"
    if not all(all(window["drawdown_checks"].values()) for window in windows):
        return "R2_LHF_SECOND_CONTINUATION_ALPHA_ONLY_RISK_REPAIR_REQUIRED"
    return "R2_LHF_SECOND_CONTINUATION_FULLY_QUALIFIED"


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU R2 Second-Continuation Lower-High Short V1 Exact-MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        f"Preregistration: `{payload['preregistration']}`",
        f"Preregistration SHA256: `{payload['preregistration_sha256']}`",
        f"Frozen tester-input SHA256: `{payload['tester_input_sha256']}`",
        "",
        "| Window | Trades | WR% | W/L | PF | Stress PF | Net | Setup purity% | Entry purity% | Equity DD% | Max risk | Max overlap% |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["window_results"]:
        gates = row["gate_metrics"]
        lines.append(
            f"| `{row['window']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['pf'] or 0.0:.4f} | {row['stress_030_pf'] or 0.0:.4f} | {row['net']:.2f} | "
            f"{gates['native_setup_purity_pct']:.2f} | {gates['native_entry_purity_pct']:.2f} | "
            f"{gates['equity_dd_relative_pct'] or 0.0:.2f} | "
            f"{gates['max_executed_initial_risk_usd'] or 0.0:.4f} | "
            f"{gates['max_same_direction_overlap_pct'] or 0.0:.2f} |"
        )
    lines.extend(["", "## Failed Gates", ""])
    for row in payload["window_results"]:
        lines.append(f"### `{row['window']}`")
        for group, checks in row["checks"].items():
            failed = [name for name, passed in checks.items() if not passed]
            lines.append(f"- `{group}`: {', '.join(failed) if failed else 'none'}")
        lines.append("")
    lines.extend(["## Artifacts", ""])
    for key, value in payload["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the frozen two-window R2 lower-high second-continuation exact test."
    )
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--variant-timeout-seconds", type=int, default=1200)
    args = parser.parse_args()

    checks = static_checks()
    payload = {
        "status": (
            "IMPLEMENTED_COMPLETE_RUNNER_AUTHORIZED_NOT_RUN"
            if HISTORICAL_RUN_AUTHORIZED
            else "IMPLEMENTED_COMPLETE_RUNNER_NOT_AUTHORIZED_NOT_RUN"
        ),
        "preregistration": rel(PREREG),
        "source_id": SOURCE_ID,
        "variant": VARIANT_NAME,
        "windows": WINDOWS,
        "deposit_usd": DEPOSIT_USD,
        "risk_amount_usd": RISK_AMOUNT_USD,
        "tester_input_sha256": stable_hash(FROZEN_INPUTS),
        "static_checks": checks,
        "implementation_readiness": implementation_readiness(),
        "historical_run_authorized": HISTORICAL_RUN_AUTHORIZED,
        "runner_scaffold_only": RUNNER_SCAFFOLD_ONLY,
    }
    if args.static_only:
        print(json.dumps(payload, indent=2))
        return 0 if PREREG.exists() and all(checks.values()) else 1

    if not PREREG.exists():
        raise FileNotFoundError(PREREG)
    if not all(checks.values()):
        raise RuntimeError(f"Invalid frozen runner configuration: {checks}")
    readiness = implementation_readiness()
    if not all(readiness.values()):
        missing = [token for token, present in readiness.items() if not present]
        raise RuntimeError("Mode24 EA implementation is incomplete: " + ", ".join(missing))
    if not HISTORICAL_RUN_AUTHORIZED:
        raise RuntimeError("Historical execution is locked pending explicit authorization")

    variants = build_variants()
    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    outputs: dict[str, str] = {"report_md": rel(report_md), "report_json": rel(report_json)}
    window_results: list[dict[str, Any]] = []

    for window in WINDOWS:
        window_name = window["name"]
        mt5.VARIANTS = variants
        mt5_md = REPORTS_DIR / f"{OUTPUT_STEM}_{window_name}_MT5.md"
        mt5_json = REPORTS_DIR / f"{OUTPUT_STEM}_{window_name}_MT5.json"
        mt5_payload = mt5.run_variants(
            from_date=window["from_date"],
            to_date=window["to_date"],
            tag=mt5.safe_name("OWNER_GOAL_R2_LHF_SECOND_CONTINUATION_" + window_name),
            report_md=mt5_md,
            report_json=mt5_json,
            variant_timeout_seconds=args.variant_timeout_seconds,
            deposit="10000",
            currency="USD",
        )
        result = mt5_payload["variants"][0]
        signal_rows = read_tsv(Path(result["signal_csv"]))
        order_rows = read_tsv(Path(result["order_csv"]))
        lifecycle = lifecycle_audit(signal_rows, order_rows)
        normalized = normalize_rows(result, lifecycle)
        risk = risk_execution_audit(result, order_rows, normalized)
        overlaps = overlap_audit(window_name, normalized)
        evaluated = evaluate_window(window, result, normalized, lifecycle, risk, overlaps)
        window_results.append(evaluated)

        normalized_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{window_name}_NORMALIZED_TRADES.csv"
        events_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{window_name}_EVENTS.csv"
        events_json = REPORTS_DIR / f"{OUTPUT_STEM}_{window_name}_EVENTS.json"
        ownership_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{window_name}_D1_OWNERSHIP.csv"
        overlap_csv = REPORTS_DIR / f"{OUTPUT_STEM}_{window_name}_OVERLAP.csv"
        overlap_json = REPORTS_DIR / f"{OUTPUT_STEM}_{window_name}_OVERLAP.json"
        risk_json = REPORTS_DIR / f"{OUTPUT_STEM}_{window_name}_RISK_EXECUTION.json"
        equity_dd_json = REPORTS_DIR / f"{OUTPUT_STEM}_{window_name}_EQUITY_DD.json"

        write_signal_csv(normalized_csv, normalized)
        write_dict_rows(events_csv, lifecycle["artifact_rows"])
        write_dict_rows(ownership_csv, lifecycle["ownership_rows"])
        write_dict_rows(overlap_csv, overlaps)
        events_json.write_text(json.dumps(lifecycle, indent=2, default=str), encoding="utf-8")
        overlap_json.write_text(json.dumps(overlaps, indent=2, default=str), encoding="utf-8")
        risk_json.write_text(json.dumps(risk, indent=2, default=str), encoding="utf-8")
        equity_dd_json.write_text(
            json.dumps(evaluated["drawdown_audit"], indent=2, default=str), encoding="utf-8"
        )

        prefix = window_name
        outputs[f"{prefix}_mt5_md"] = rel(mt5_md)
        outputs[f"{prefix}_mt5_json"] = rel(mt5_json)
        outputs[f"{prefix}_normalized_trades"] = rel(normalized_csv)
        outputs[f"{prefix}_events_csv"] = rel(events_csv)
        outputs[f"{prefix}_events_json"] = rel(events_json)
        outputs[f"{prefix}_d1_ownership_csv"] = rel(ownership_csv)
        outputs[f"{prefix}_overlap_csv"] = rel(overlap_csv)
        outputs[f"{prefix}_overlap_json"] = rel(overlap_json)
        outputs[f"{prefix}_risk_execution_json"] = rel(risk_json)
        outputs[f"{prefix}_equity_dd_json"] = rel(equity_dd_json)

    status = decide(checks, [row["checks"] for row in window_results])
    payload = {
        **payload,
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
            "+00:00", "Z"
        ),
        "preregistration_sha256": sha256_file(PREREG),
        "window_results": window_results,
        "outputs": outputs,
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(json.dumps({"status": status, "report": str(report_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
