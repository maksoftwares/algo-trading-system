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
import run_a1_r2_second_continuation_lower_high_short_v1_exact as common
import run_a1_xau_m5_momentum_backtest_variants as mt5
from analyze_a1_owner_goal_step3_portfolio_composition import REPORTS_DIR, rel
from analyze_a1_xau_source_monthly_firewall import read_ledger
from run_a1_h4_d1_geometry_v2_weekly_shape import sha256_file, write_signal_csv
from run_a1_regime_router_v1_exact import ROUTER_INPUTS


PHASE1_ROOT = Path(__file__).resolve().parents[1]
EA_SOURCE = PHASE1_ROOT / "mt5" / "Experts" / "A1XauM5MomentumContinuationExecutor.mq5"
PREREG = (
    PHASE1_ROOT
    / "docs"
    / "A1_XAU_R2_M15_IMPULSE_M5_CONTINUATION_SHORT_V1_PREREG_2026_07_10.md"
)
SOURCE_ID = "r2_m15_impulse_m5_continuation_short_v1"
VARIANT_NAME = "r2_icr_m15_impulse_m5_first_continuation_v1"
OUTPUT_STEM = "A1_XAU_R2_M15_IMPULSE_M5_CONTINUATION_SHORT_V1_EXACT_20260710"
PROPOSED_SIGNAL_MODE = 27
DEPOSIT_USD = 10_000.0
RISK_AMOUNT_USD = 50.0
HISTORICAL_RUN_AUTHORIZED = False
RUNNER_COMPLETE = True

WINDOWS = common.WINDOWS

MODE24_DIAGNOSIS = {
    "prehistory_201601_202112": {
        "registered": 120,
        "pivots": 40,
        "first_break_attempts": 25,
        "would_signals": 3,
        "executions": 0,
        "continuation_without_reset": 66,
        "stop_blocks": 2,
        "cost_blocks": 1,
    },
    "primary_202207_202606": {
        "registered": 82,
        "pivots": 28,
        "first_break_attempts": 15,
        "would_signals": 5,
        "executions": 2,
        "continuation_without_reset": 50,
        "stop_blocks": 3,
        "cost_blocks": 0,
    },
}
MODE24_CAUSAL_STATUS = "NONCONFORMING_WALL_CLOCK_LIFETIME_DIAGNOSTIC_ONLY"

INVALID_COUNTER_OVERLAP_CONTROLS = {
    "r2_prior_d1_low_first_retest_killed",
    "r2_mode24_lhf_killed",
}
REQUIRED_OVERLAP_CONTROLS = tuple(
    control
    for control in common.REQUIRED_OVERLAP_CONTROLS
    if control not in INVALID_COUNTER_OVERLAP_CONTROLS
)
CONTROL_PATHS = {
    window["name"]: {
        control: common.CONTROL_PATHS[window["name"]][control]
        for control in REQUIRED_OVERLAP_CONTROLS
    }
    for window in WINDOWS
}
CONTROL_PROVENANCE = {
    "r2_pullback_rejection_v1_h1": {
        "ready": True,
        "basis": "exact_completed_h1_signal_no_elapsed_event_lifetime",
    },
    "r2_pullback_rejection_v2_body58": {
        "ready": True,
        "basis": "exact_completed_h1_signal_no_elapsed_event_lifetime",
    },
    "r2_continuation_v1_body45": {
        "ready": True,
        "basis": "exact_completed_bar_signal_no_elapsed_event_lifetime",
    },
    "r2_continuation_v2_break15_30": {
        "ready": True,
        "basis": "exact_completed_bar_signal_no_elapsed_event_lifetime",
    },
    "r2_continuation_v4_atr45": {
        "ready": True,
        "basis": "exact_completed_bar_signal_no_elapsed_event_lifetime",
    },
}

FROZEN_INPUTS = {
    **ROUTER_INPUTS,
    "InpAtrPeriod": "14",
    "InpSignalMode": "27",
    "InpRegimeRouterMode": "2",
    "InpDirectionMode": "2",
    "InpRiskReward": "2.00",
    "InpMaxSpreadPoints": "75",
    "InpMaxEstimatedCostR": "0.10",
    "InpR2IcrAtrPeriod": "14",
    "InpR2IcrMaturityD1Bars": "3",
    "InpR2IcrImpulseLookbackM15Bars": "8",
    "InpR2IcrImpulseMinRangeM15Atr": "0.75",
    "InpR2IcrImpulseMinBodyFraction": "0.50",
    "InpR2IcrImpulseCloseLocationMax": "0.30",
    "InpR2IcrEntryWindowM5Bars": "3",
    "InpR2IcrFirstBreakTouchM5Atr": "0.05",
    "InpR2IcrFirstBreakCloseM5Atr": "0.05",
    "InpR2IcrResumeMinBodyFraction": "0.45",
    "InpR2IcrResumeCloseLocationMax": "0.30",
    "InpR2IcrStopBufferM15Atr": "0.10",
    "InpR2IcrMaxStopM15Atr": "1.50",
    "InpR2IcrMaxHoldM5Bars": "12",
    "InpR2IcrExitOnOwnershipLoss": "true",
    "InpR2IcrConsumeFirstBreak": "true",
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

EXPECTED_FROZEN_INPUT_SHA256 = "58621fea70c35ecda9eabbb18877158aff660482b93041bf50e2eb03ff18d3c4"

REQUIRED_EA_TOKENS = (
    "SIGNAL_R2_M15_IMPULSE_M5_CONTINUATION_SHORT = 27",
    "InpR2IcrImpulseLookbackM15Bars",
    "InpR2IcrMaxHoldM5Bars",
    "g_r2_icr_consumed_event_time",
    "g_r2_icr_entry_m5_bars_seen",
    "g_r2_icr_hold_m5_bars_seen",
    "TryR2M15ImpulseM5ContinuationShortSignal",
    "R2IcrHardRiskAllowed",
    "OrderCalcProfit(ORDER_TYPE_SELL",
    "R2_ICR_D1_OWNERSHIP",
    "d1_shift1_time",
    "d1_shift2_time",
    "d1_shift3_time",
    "h4_time",
    "impulse_bar_time",
    "m15_shift",
    "R2_ICR_IMPULSE_REGISTERED",
    "R2_ICR_ENTRY_DECISION",
    "entry_bar_ordinal",
    "touch",
    "R2_ICR_EVENT_CONSUMED",
    "R2_ICR_HOLD_DECISION",
    "hold_bar_ordinal",
    "position_open",
    "R2_ICR_POSITION_EXIT",
    "close_succeeded",
    "R2_M15_IMPULSE_M5_CONTINUATION_SHORT_STATE_",
    "r2_icr_structural_time_exit",
    "r2_icr_ownership_exit",
    "r2_icr_normalized_entry_to_stop_risk_overshoot",
    '"actual_risk_usd"',
)

LIFECYCLE_STAGES = {
    "ownership": "R2_ICR_D1_OWNERSHIP",
    "registered": "R2_ICR_IMPULSE_REGISTERED",
    "entry_decision": "R2_ICR_ENTRY_DECISION",
    "consumed": "R2_ICR_EVENT_CONSUMED",
    "hold_decision": "R2_ICR_HOLD_DECISION",
    "position_exit": "R2_ICR_POSITION_EXIT",
}
ALLOWED_CONSUMPTION_OUTCOMES = {
    "first_break_attempt",
    "entry_window_expired",
    "ownership_lost",
    "tester_deinit",
}


def stable_hash(value: Any) -> str:
    blob = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def build_variants() -> list[mt5.Variant]:
    return [
        mt5.Variant(
            name=VARIANT_NAME,
            label=(
                "Mature-R2 completed-M15 structural impulse and first M5 direct "
                "continuation, 60-minute structural horizon, fixed 2R"
            ),
            run_id="BT_A1_XAU_R2_ICR_M15_IMPULSE_M5_CONTINUATION_V1",
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
    prereg_text = PREREG.read_text(encoding="utf-8") if PREREG.exists() else ""
    runner_text = Path(__file__).read_text(encoding="utf-8")
    return {
        "exactly_one_variant": len(variants) == 1,
        "variant_and_inputs_frozen": variant is not None
        and variant.name == VARIANT_NAME
        and inputs == FROZEN_INPUTS,
        "tester_input_hash_frozen": stable_hash(inputs) == EXPECTED_FROZEN_INPUT_SHA256,
        "two_windows_frozen": tuple(
            (row["from_date"], row["to_date"]) for row in WINDOWS
        ) == (("2016.01.01", "2021.12.31"), ("2022.07.01", "2026.06.30")),
        "mode27_strict_r2_short_rr2": inputs.get("InpSignalMode") == "27"
        and inputs.get("InpRegimeRouterMode") == "2"
        and inputs.get("InpDirectionMode") == "2"
        and inputs.get("InpRiskReward") == "2.00",
        "mature_three_d1": inputs.get("InpR2IcrMaturityD1Bars") == "3",
        "m15_impulse_m5_first_break": inputs.get("InpR2IcrImpulseLookbackM15Bars") == "8"
        and inputs.get("InpR2IcrEntryWindowM5Bars") == "3"
        and inputs.get("InpR2IcrConsumeFirstBreak") == "true",
        "short_structural_horizon": inputs.get("InpR2IcrMaxHoldM5Bars") == "12"
        and inputs.get("InpR2IcrExitOnOwnershipLoss") == "true",
        "no_absolute_atr_or_stop_mask": inputs.get("InpMinAtrAbsoluteForEntry") == "0.00"
        and all(inputs.get(key) == "0" for key in ("InpStopFloorPoints", "InpStopCeilingPoints", "InpStopCapPoints")),
        "no_calendar_or_session_mask": all(
            inputs.get(key, "") == ""
            for key in (
                "InpBlockedEntryHoursCsv",
                "InpBlockedEntryDayHoursCsv",
                "InpBlockedLongEntryHoursCsv",
                "InpBlockedShortEntryHoursCsv",
            )
        )
        and inputs.get("InpUseDirectionalSessionFilter") == "false",
        "no_previous_pnl_or_management_overlay": all(
            inputs.get(key) == "false"
            for key in (
                "InpPortfolioDailyGuardEnabled",
                "InpH4D1WeeklyLossGovernorEnabled",
                "InpH4D1PrevMonthHealthGateEnabled",
                "InpH4D1NegativeStackGuardEnabled",
                "InpH4D1ThirdEntryQualityGateEnabled",
                "InpFeatureLossFilterEnabled",
                "InpProfitProtectionEnabled",
                "InpPartialCloseEnabled",
                "InpSplitEntryEnabled",
                "InpEarlyAdverseExitEnabled",
            )
        ),
        "hard_50usd_zero_overshoot": DEPOSIT_USD == 10_000.0
        and RISK_AMOUNT_USD == 50.0
        and inputs.get("InpUseRiskNormalizedLots") == "true"
        and inputs.get("InpRiskAmountUsd") == "50.00"
        and inputs.get("InpRejectRiskOvershootEnabled") == "true"
        and inputs.get("InpMaxRiskOvershootPct") == "0.00",
        "one_position_no_stacking": inputs.get("InpOnePositionPerMagic") == "true"
        and inputs.get("InpMaxOpenPositionsPerMagic") == "1",
        "five_valid_overlap_controls_frozen": len(REQUIRED_OVERLAP_CONTROLS) == 5
        and not (set(REQUIRED_OVERLAP_CONTROLS) & INVALID_COUNTER_OVERLAP_CONTROLS),
        "overlap_controls_have_valid_provenance": all(
            CONTROL_PROVENANCE.get(control, {}).get("ready") is True
            for control in REQUIRED_OVERLAP_CONTROLS
        ),
        "lifecycle_telemetry_enabled": inputs.get("InpRegimeSnapshotLogEnabled") == "true",
        "completed_bar_counter_contract": "entry_m5_bars_seen=0" in prereg_text
        and "hold_m5_bars_seen=0" in prereg_text
        and "elapsed seconds" in prereg_text,
        "counter_based_evaluator": ("entry_window_" + "seconds") not in runner_text
        and (".total_seconds()" + " / 300.0") not in runner_text,
        "complete_runner_available": RUNNER_COMPLETE,
    }


def lifecycle_audit(
    signal_rows: list[dict[str, str]], order_rows: list[dict[str, str]]
) -> dict[str, Any]:
    registered: Counter[str] = Counter()
    consumed: Counter[str] = Counter()
    signals: Counter[str] = Counter()
    registration_fields: dict[str, dict[str, str]] = {}
    consumed_index: dict[str, int] = {}
    signal_events: list[dict[str, Any]] = []
    artifact_rows: list[dict[str, Any]] = []
    ownership_rows: list[dict[str, Any]] = []
    entry_decision_rows: list[dict[str, Any]] = []
    hold_decision_rows: list[dict[str, Any]] = []
    position_exit_rows: list[dict[str, Any]] = []
    consumption_fields: dict[str, dict[str, str]] = {}
    registration_order: list[dict[str, Any]] = []
    active_event = ""
    active_state = "IDLE"
    overwrite: list[str] = []
    transitions: list[str] = []
    future_bar: list[str] = []
    retrospective: list[str] = []
    native_setup: list[str] = []
    native_signal: list[str] = []
    invalid_outcomes: list[str] = []
    ownership_observation_errors: list[str] = []
    impulse_registration_errors: list[str] = []

    for index, row in enumerate(signal_rows):
        stage = str(row.get("stage") or "")
        prefix, fields = common.parse_reason(str(row.get("reason") or ""))
        event_id = fields.get("event_id", "")
        if stage == LIFECYCLE_STAGES["ownership"]:
            detail = {
                **fields,
                "row_index": index,
                "timestamp_broker": row.get("timestamp_broker", ""),
                "d1_time": common._int_value(fields.get("d1_time")),
                "mature": fields.get("mature") == "1",
            }
            ownership_rows.append(detail)
            d1_shift1_time = common._int_value(fields.get("d1_shift1_time"))
            d1_shift2_time = common._int_value(fields.get("d1_shift2_time"))
            d1_shift3_time = common._int_value(fields.get("d1_shift3_time"))
            h4_time = common._int_value(fields.get("h4_time"))
            if (
                prefix != "R2_ICR_D1_OWNERSHIP"
                or detail["d1_time"] is None
                or fields.get("d1_shift") != "1"
                or fields.get("backfill") != "0"
                or fields.get("mature") not in {"0", "1"}
                or d1_shift1_time is None
                or d1_shift2_time is None
                or d1_shift3_time is None
                or h4_time is None
                or detail["d1_time"] != d1_shift1_time
                or not d1_shift1_time > d1_shift2_time > d1_shift3_time > 0
                or (
                    detail["mature"]
                    and not (
                        fields.get("state") == "downtrend"
                        and fields.get("direction_state") == "DOWN"
                        and fields.get("setup") == "DOWN"
                        and fields.get("phase") == "ESTABLISHED"
                        and fields.get("shock") == "0"
                        and fields.get("maturity") == "3"
                        and fields.get("h4_down") == "1"
                    )
                )
            ):
                ownership_observation_errors.append(str(fields.get("d1_time") or index))
            continue
        if stage == LIFECYCLE_STAGES["entry_decision"]:
            detail = {
                "row_index": index,
                "timestamp_broker": row.get("timestamp_broker", ""),
                **fields,
            }
            entry_decision_rows.append(detail)
            artifact_rows.append({"row_index": index, "stage": stage, **fields})
            if active_event != event_id or active_state != "WAIT_FIRST_M5_BREAK":
                transitions.append(f"entry_decision:{event_id or index}")
            continue
        if stage == LIFECYCLE_STAGES["hold_decision"]:
            detail = {
                "row_index": index,
                "timestamp_broker": row.get("timestamp_broker", ""),
                **fields,
            }
            hold_decision_rows.append(detail)
            artifact_rows.append({"row_index": index, "stage": stage, **fields})
            continue
        if stage == LIFECYCLE_STAGES["position_exit"]:
            position_exit_rows.append({"row_index": index, "timestamp_broker": row.get("timestamp_broker", ""), **fields})
            artifact_rows.append({"row_index": index, "stage": stage, **fields})
            continue
        if stage in (LIFECYCLE_STAGES["registered"], LIFECYCLE_STAGES["consumed"]):
            artifact_rows.append({"row_index": index, "timestamp_broker": row.get("timestamp_broker", ""), "stage": stage, **fields})

        if stage == LIFECYCLE_STAGES["registered"]:
            registered[event_id] += 1
            registration_fields[event_id] = fields
            if not event_id or active_event or active_state != "IDLE":
                overwrite.append(event_id or f"missing:{index}")
            if fields.get("from") != "IDLE" or fields.get("to") != "WAIT_FIRST_M5_BREAK":
                transitions.append(f"register:{event_id}")
            setup_time = common._int_value(fields.get("setup_time"))
            impulse_time = common._int_value(fields.get("impulse_time"))
            impulse_bar_time = common._int_value(fields.get("impulse_bar_time"))
            registration_order.append(
                {
                    "event_id": event_id,
                    "row_index": index,
                    "impulse_time": impulse_time,
                }
            )
            if (
                setup_time is None
                or impulse_time is None
                or impulse_bar_time is None
                or setup_time != impulse_time
                or impulse_time != impulse_bar_time + 900
                or fields.get("m15_shift") != "1"
                or fields.get("backfill") != "0"
                or event_id != f"R2ICR_{impulse_time}"
            ):
                future_bar.append(event_id)
            eligible_ownership = [
                item
                for item in ownership_rows
                if item.get("d1_time") is not None
                and setup_time is not None
                and int(item["d1_time"]) <= setup_time
            ]
            latest_ownership = max(
                eligible_ownership,
                key=lambda item: int(item["d1_time"]),
                default=None,
            )
            if not (
                fields.get("setup") == "DOWN"
                and fields.get("phase") == "ESTABLISHED"
                and fields.get("shock") == "0"
                and fields.get("maturity") == "3"
                and latest_ownership is not None
                and latest_ownership.get("mature") is True
                and latest_ownership.get("state") == "downtrend"
                and latest_ownership.get("direction_state") == "DOWN"
                and latest_ownership.get("h4_down") == "1"
                and common._int_value(latest_ownership.get("h4_time")) is not None
                and setup_time is not None
                and common._int_value(latest_ownership.get("h4_time")) < setup_time
            ):
                native_setup.append(event_id)
            active_event, active_state = event_id, "WAIT_FIRST_M5_BREAK"
            continue

        if stage == LIFECYCLE_STAGES["consumed"]:
            consumed[event_id] += 1
            consumed_index[event_id] = index
            consumption_fields[event_id] = fields
            if active_event != event_id or active_state != "WAIT_FIRST_M5_BREAK":
                transitions.append(f"consume:{event_id}")
            if fields.get("from") != "WAIT_FIRST_M5_BREAK" or fields.get("to") != "IDLE":
                transitions.append(f"consume_transition:{event_id}")
            if fields.get("outcome") not in ALLOWED_CONSUMPTION_OUTCOMES:
                invalid_outcomes.append(event_id)
            active_event, active_state = "", "IDLE"
            continue

        if stage == "WOULD_SIGNAL":
            if not prefix.startswith("R2_M15_IMPULSE_M5_CONTINUATION_SHORT_STATE_") or not event_id:
                native_signal.append(event_id or f"missing:{index}")
                continue
            signals[event_id] += 1
            if not (
                prefix == "R2_M15_IMPULSE_M5_CONTINUATION_SHORT_STATE_downtrend"
                and str(row.get("direction") or "").upper() == "SHORT"
                and fields.get("setup") == "DOWN"
                and fields.get("phase") == "ESTABLISHED"
                and fields.get("shock") == "0"
                and fields.get("maturity") == "3"
            ):
                native_signal.append(event_id)
            if event_id not in consumed_index or consumed_index[event_id] >= index:
                retrospective.append(event_id)
            impulse_time = common._int_value(fields.get("impulse_time"))
            attempt_time = common._int_value(fields.get("attempt_time"))
            attempt_ordinal = common._int_value(fields.get("attempt_ordinal"))
            matching_decisions = [
                item
                for item in entry_decision_rows
                if item.get("event_id") == event_id
                and common._int_value(item.get("decision_bar_time")) == attempt_time
                and common._int_value(item.get("entry_bar_ordinal")) == attempt_ordinal
                and int(item["row_index"]) < index
            ]
            if (
                impulse_time is None
                or attempt_time is None
                or attempt_time <= impulse_time
                or attempt_ordinal is None
                or attempt_ordinal < 1
                or attempt_ordinal > int(FROZEN_INPUTS["InpR2IcrEntryWindowM5Bars"])
                or len(matching_decisions) != 1
            ):
                retrospective.append(event_id)
            try:
                timestamp = audit_common.parse_signal_time(str(row.get("timestamp_broker") or ""))
            except ValueError:
                timestamp = None
                retrospective.append(event_id)
            signal_events.append(
                {
                    "event_id": event_id,
                    "timestamp": timestamp,
                    "timestamp_text": row.get("timestamp_broker", ""),
                    "direction": str(row.get("direction") or "").upper(),
                    "native": event_id not in native_signal,
                }
            )

    if active_event:
        transitions.append(f"active_at_end:{active_event}")

    ownership_times = [row.get("d1_time") for row in ownership_rows]
    if any(
        value is None
        or (
            position > 0
            and ownership_times[position - 1] is not None
            and int(value) <= int(ownership_times[position - 1])
        )
        for position, value in enumerate(ownership_times)
    ):
        ownership_observation_errors.append("d1_time_sequence")

    impulse_times = [row.get("impulse_time") for row in registration_order]
    if any(
        value is None
        or (
            position > 0
            and impulse_times[position - 1] is not None
            and int(value) <= int(impulse_times[position - 1])
        )
        for position, value in enumerate(impulse_times)
    ):
        impulse_registration_errors.append("impulse_time_sequence")

    entry_rows_by_event: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in entry_decision_rows:
        entry_rows_by_event[str(row.get("event_id") or "")].append(row)
    entry_counter_violations: list[str] = []
    entry_limit = int(FROZEN_INPUTS["InpR2IcrEntryWindowM5Bars"])
    for event_id in sorted(set(registered) | set(entry_rows_by_event) | set(consumed)):
        decisions = sorted(entry_rows_by_event.get(event_id, []), key=lambda row: int(row["row_index"]))
        ordinals = [common._int_value(row.get("entry_bar_ordinal")) for row in decisions]
        decision_times = [common._int_value(row.get("decision_bar_time")) for row in decisions]
        touches = [row.get("touch") for row in decisions]
        ownership = [row.get("owned") for row in decisions]
        impulse_time = common._int_value(registration_fields.get(event_id, {}).get("impulse_time"))
        expected_ordinals = list(range(1, len(decisions) + 1))
        if (
            ordinals != expected_ordinals
            or len(decisions) > entry_limit
            or any(value is None for value in decision_times)
            or len(set(decision_times)) != len(decision_times)
            or any(value not in {"0", "1"} for value in touches)
            or any(value not in {"0", "1"} for value in ownership)
            or any(
                decision_times[index] is None
                or (index == 0 and (impulse_time is None or decision_times[index] <= impulse_time))
                or (index > 0 and decision_times[index] <= decision_times[index - 1])
                for index in range(len(decision_times))
            )
        ):
            entry_counter_violations.append(f"{event_id}|decision_sequence")
        fields = consumption_fields.get(event_id)
        if fields is None:
            continue
        outcome = str(fields.get("outcome") or "")
        bars_seen = common._int_value(fields.get("entry_bars_seen"))
        if bars_seen is None or bars_seen != len(decisions) or bars_seen < 0 or bars_seen > entry_limit:
            entry_counter_violations.append(f"{event_id}|bars_seen")
        if outcome == "first_break_attempt":
            attempt_ordinal = common._int_value(fields.get("attempt_ordinal"))
            attempt_time = common._int_value(fields.get("attempt_time"))
            if (
                attempt_ordinal is None
                or attempt_ordinal < 1
                or attempt_ordinal > entry_limit
                or not ordinals
                or attempt_ordinal != ordinals[-1]
                or attempt_ordinal != bars_seen
                or not decision_times
                or attempt_time != decision_times[-1]
                or touches[:-1] != ["0"] * max(0, len(touches) - 1)
                or not touches
                or touches[-1] != "1"
                or ownership != ["1"] * len(ownership)
            ):
                entry_counter_violations.append(f"{event_id}|attempt_ordinal")
        elif outcome == "entry_window_expired" and (
            bars_seen != entry_limit
            or ordinals != list(range(1, entry_limit + 1))
            or touches != ["0"] * entry_limit
            or ownership != ["1"] * entry_limit
        ):
            entry_counter_violations.append(f"{event_id}|expiry_ordinal")
        elif outcome == "ownership_lost" and (
            not ownership
            or ownership[-1] != "0"
            or any(value != "1" for value in ownership[:-1])
            or any(value != "0" for value in touches)
        ):
            entry_counter_violations.append(f"{event_id}|ownership_loss")
        elif outcome == "tester_deinit" and (
            fields.get("deinit") != "1"
            or bars_seen is None
            or bars_seen >= entry_limit
            or any(value != "0" for value in touches)
            or any(value != "1" for value in ownership)
        ):
            entry_counter_violations.append(f"{event_id}|tester_deinit")

    hold_rows_by_event: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in hold_decision_rows:
        hold_rows_by_event[str(row.get("event_id") or "")].append(row)
    hold_counter_violations: list[str] = []
    hold_limit = int(FROZEN_INPUTS["InpR2IcrMaxHoldM5Bars"])
    for event_id, raw_decisions in sorted(hold_rows_by_event.items()):
        decisions = sorted(raw_decisions, key=lambda row: int(row["row_index"]))
        ordinals = [common._int_value(row.get("hold_bar_ordinal")) for row in decisions]
        decision_times = [common._int_value(row.get("decision_bar_time")) for row in decisions]
        entry_times = [common._int_value(row.get("entry_time")) for row in decisions]
        position_ids = [str(row.get("position_id") or "") for row in decisions]
        tickets = [str(row.get("ticket") or "") for row in decisions]
        position_open = [str(row.get("position_open") or "") for row in decisions]
        ownership = [str(row.get("owned") or "") for row in decisions]
        attempt_time = common._int_value(consumption_fields.get(event_id, {}).get("attempt_time"))
        if (
            ordinals != list(range(1, len(decisions) + 1))
            or len(decisions) > hold_limit
            or any(value is None for value in decision_times)
            or len(set(decision_times)) != len(decision_times)
            or any(value is None for value in entry_times)
            or len(set(entry_times)) != 1
            or attempt_time is None
            or not entry_times
            or entry_times[0] < attempt_time
            or not position_ids
            or not position_ids[0]
            or len(set(position_ids)) != 1
            or not tickets
            or not tickets[0]
            or len(set(tickets)) != 1
            or any(value != "1" for value in position_open)
            or any(value not in {"0", "1"} for value in ownership)
            or any(
                decision_times[index] is None
                or entry_times[index] is None
                or decision_times[index] <= entry_times[index]
                or (index > 0 and decision_times[index] <= decision_times[index - 1])
                for index in range(len(decision_times))
            )
        ):
            hold_counter_violations.append(f"{event_id}|decision_sequence")

    episode = 0
    in_episode = False
    ordered_ownership = sorted(
        [row for row in ownership_rows if row.get("d1_time") is not None],
        key=lambda row: int(row["d1_time"]),
    )
    for row in ordered_ownership:
        if row["mature"] and not in_episode:
            episode += 1
        row["episode_id"] = episode if row["mature"] else 0
        in_episode = bool(row["mature"])
    event_episodes: dict[str, int] = {}
    for event_id, fields in registration_fields.items():
        setup_time = common._int_value(fields.get("setup_time"))
        eligible = [row for row in ordered_ownership if setup_time is not None and int(row["d1_time"]) <= setup_time]
        latest = max(eligible, key=lambda row: int(row["d1_time"]), default=None)
        event_episodes[event_id] = int(latest["episode_id"]) if latest and latest["mature"] else 0

    executed = [row for row in order_rows if row.get("action") == "ORDER_SEND_OK"]
    executed_event_ids: list[str] = []
    missing_execution_matches: list[str] = []
    impure_execution_matches: list[str] = []
    for row in executed:
        matches = [
            signal
            for signal in signal_events
            if signal["timestamp_text"] == row.get("timestamp_broker", "")
            and signal["direction"] == str(row.get("direction") or "").upper()
        ]
        if len(matches) != 1:
            missing_execution_matches.append(str(row.get("timestamp_broker") or ""))
        else:
            executed_event_ids.append(matches[0]["event_id"])
            if not matches[0]["native"]:
                impure_execution_matches.append(matches[0]["event_id"])

    for event_id in sorted(hold_rows_by_event):
        if not event_id or event_id not in executed_event_ids:
            hold_counter_violations.append(f"{event_id or 'missing'}|without_execution")

    orphan_position_exits = [
        str(row.get("event_id") or "")
        for row in position_exit_rows
        if not row.get("event_id") or str(row.get("event_id")) not in executed_event_ids
    ]
    invalid_position_exits = [
        str(row.get("event_id") or "")
        for row in position_exit_rows
        if str(row.get("event_id") or "") in executed_event_ids
        and (
            str(row.get("outcome") or "") not in {"structural_time_exit", "ownership_exit"}
            or str(row.get("close_attempted") or "") != "1"
            or str(row.get("close_succeeded") or "") != "1"
            or common._int_value(row.get("decision_bar_time")) is None
            or common._int_value(row.get("entry_time")) is None
            or not str(row.get("position_id") or "")
            or not str(row.get("ticket") or "")
            or common._int_value(row.get("hold_bar_ordinal")) is None
            or common._int_value(row.get("hold_bar_ordinal")) < 1
            or common._int_value(row.get("hold_bar_ordinal")) > hold_limit
            or (
                str(row.get("outcome") or "") == "structural_time_exit"
                and common._int_value(row.get("hold_bar_ordinal")) != hold_limit
            )
        )
    ]
    exits_by_event: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in position_exit_rows:
        exits_by_event[str(row.get("event_id") or "")].append(row)
    for event_id, exits in exits_by_event.items():
        if event_id not in executed_event_ids:
            continue
        if len(exits) != 1:
            hold_counter_violations.append(f"{event_id}|duplicate_position_exit")
        decisions = hold_rows_by_event.get(event_id, [])
        last_ordinal = max(
            (common._int_value(row.get("hold_bar_ordinal")) or 0 for row in decisions),
            default=0,
        )
        if any(
            common._int_value(row.get("hold_bar_ordinal")) != last_ordinal for row in exits
        ):
            hold_counter_violations.append(f"{event_id}|exit_ordinal_mismatch")
        for exit_row in exits:
            matching = [
                decision
                for decision in decisions
                if int(decision["row_index"]) < int(exit_row["row_index"])
                and common._int_value(decision.get("hold_bar_ordinal"))
                == common._int_value(exit_row.get("hold_bar_ordinal"))
                and common._int_value(decision.get("decision_bar_time"))
                == common._int_value(exit_row.get("decision_bar_time"))
                and common._int_value(decision.get("entry_time"))
                == common._int_value(exit_row.get("entry_time"))
                and str(decision.get("position_id") or "")
                == str(exit_row.get("position_id") or "")
                and str(decision.get("ticket") or "") == str(exit_row.get("ticket") or "")
            ]
            if len(matching) != 1 or (
                str(exit_row.get("outcome") or "") == "ownership_exit"
                and (not matching or str(matching[0].get("owned") or "") != "0")
            ):
                invalid_position_exits.append(event_id)
        if exits and any(
            int(decision["row_index"]) > min(int(row["row_index"]) for row in exits)
            for decision in decisions
        ):
            hold_counter_violations.append(f"{event_id}|decision_after_exit")
    for event_id, decisions in hold_rows_by_event.items():
        last_ordinal = max(
            (common._int_value(row.get("hold_bar_ordinal")) or 0 for row in decisions),
            default=0,
        )
        exits = exits_by_event.get(event_id, [])
        for decision in decisions:
            if str(decision.get("owned") or "") != "0":
                continue
            matching_ownership_exits = [
                row
                for row in exits
                if str(row.get("outcome") or "") == "ownership_exit"
                and common._int_value(row.get("hold_bar_ordinal"))
                == common._int_value(decision.get("hold_bar_ordinal"))
                and common._int_value(row.get("decision_bar_time"))
                == common._int_value(decision.get("decision_bar_time"))
            ]
            if len(matching_ownership_exits) != 1:
                hold_counter_violations.append(f"{event_id}|ownership_loss_without_close")
        if last_ordinal == hold_limit and not any(
            str(row.get("close_attempted") or "") == "1" for row in exits
        ):
            hold_counter_violations.append(f"{event_id}|horizon_without_close")

    tester_deinit_event_ids = sorted(
        event_id
        for event_id, fields in consumption_fields.items()
        if fields.get("outcome") == "tester_deinit"
    )

    return {
        "registered_events": len(registered),
        "consumed_events": len(consumed),
        "signal_events": len(signals),
        "duplicate_registrations": sorted(key for key, count in registered.items() if count != 1),
        "duplicate_consumptions": sorted(key for key, count in consumed.items() if count != 1),
        "duplicate_signals": sorted(key for key, count in signals.items() if count > 1),
        "missing_consumptions": sorted(set(registered) - set(consumed)),
        "consumed_without_registration": sorted(set(consumed) - set(registered)),
        "signals_without_registration": sorted(set(signals) - set(registered)),
        "active_state_overwrite_violations": overwrite,
        "transition_violations": transitions,
        "future_bar_violations": future_bar,
        "retrospective_entry_violations": sorted(set(retrospective)),
        "native_setup_failures": sorted(set(native_setup)),
        "native_signal_failures": sorted(set(native_signal)),
        "invalid_consumption_outcomes": sorted(set(invalid_outcomes)),
        "ownership_observation_violations": sorted(set(ownership_observation_errors)),
        "impulse_registration_violations": sorted(set(impulse_registration_errors)),
        "tester_deinit_events": len(tester_deinit_event_ids),
        "tester_deinit_event_ids": tester_deinit_event_ids,
        "missing_executed_signal_matches": missing_execution_matches,
        "impure_executed_signal_matches": impure_execution_matches,
        "entry_counter_violations": sorted(set(entry_counter_violations)),
        "hold_counter_violations": sorted(set(hold_counter_violations)),
        "orphan_position_exits": sorted(set(orphan_position_exits)),
        "invalid_position_exits": sorted(set(invalid_position_exits)),
        "ownership_episode_count": episode,
        "registered_episode_ids": event_episodes,
        "signal_events_detail": signal_events,
        "entry_decision_rows": entry_decision_rows,
        "hold_decision_rows": hold_decision_rows,
        "position_exit_rows": position_exit_rows,
        "artifact_rows": artifact_rows,
        "ownership_rows": ownership_rows,
    }


def normalize_rows(result: dict[str, Any], lifecycle: dict[str, Any]) -> list[dict[str, Any]]:
    rows = metrics.mt5_rows(result, source_priority=98)
    for row in rows:
        event_id = common.event_for_entry(row["entry_time"], str(row.get("direction") or ""), lifecycle)
        row.update(
            {
                "component": SOURCE_ID,
                "source_id": SOURCE_ID,
                "upstream_source_id": SOURCE_ID,
                "upstream_component": VARIANT_NAME,
                "family_group": "xau_r2_m15_impulse_m5_continuation",
                "cell_id": SOURCE_ID,
                "event_id": event_id,
                "owned_episode_id": lifecycle["registered_episode_ids"].get(event_id, 0),
            }
        )
    return rows


def overlap_audit(window_name: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for control in REQUIRED_OVERLAP_CONTROLS:
        path = CONTROL_PATHS[window_name][control]
        provenance = CONTROL_PROVENANCE.get(control, {})
        if not path.exists() or provenance.get("ready") is not True:
            output.append(
                {
                    "control": control,
                    "available": False,
                    "path": str(path),
                    "candidate_trades": len(rows),
                    "overlap_trades": None,
                    "overlap_pct": None,
                    "provenance_ready": provenance.get("ready") is True,
                    "provenance_basis": provenance.get("basis", "missing"),
                }
            )
            continue
        result = audit_common.overlap_with_control(rows, read_ledger(path), control)
        result.update(
            {
                "available": True,
                "path": str(path),
                "provenance_ready": True,
                "provenance_basis": provenance["basis"],
            }
        )
        output.append(result)
    return output


def overlap_control_readiness() -> dict[str, bool]:
    return {
        f"{window_name}:{control}": path.exists()
        and CONTROL_PROVENANCE.get(control, {}).get("ready") is True
        for window_name, paths in CONTROL_PATHS.items()
        for control, path in paths.items()
    }


def window_gate_checks(values: dict[str, Any]) -> dict[str, dict[str, bool]]:
    proxy = dict(values)
    all_controls = (
        values.get("required_overlap_controls") == len(REQUIRED_OVERLAP_CONTROLS)
        and values.get("available_overlap_controls") == len(REQUIRED_OVERLAP_CONTROLS)
    )
    proxy["required_overlap_controls"] = len(common.REQUIRED_OVERLAP_CONTROLS)
    proxy["available_overlap_controls"] = (
        len(common.REQUIRED_OVERLAP_CONTROLS) if all_controls else -1
    )
    checks = common.window_gate_checks(proxy)
    checks["regime_independence_checks"]["all_required_overlap_controls_available"] = all_controls
    return checks


def holding_audit(rows: list[dict[str, Any]], lifecycle: dict[str, Any]) -> dict[str, Any]:
    trade_event_ids = {str(row.get("event_id") or "") for row in rows}
    ordinals = [
        common._int_value(row.get("hold_bar_ordinal"))
        for row in lifecycle["hold_decision_rows"]
    ]
    violations = list(lifecycle["hold_counter_violations"])
    for row in lifecycle["hold_decision_rows"]:
        event_id = str(row.get("event_id") or "")
        if not event_id or event_id not in trade_event_ids:
            violations.append(f"{event_id or 'missing'}|without_normalized_trade")
    trades_by_event: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        trades_by_event[str(row.get("event_id") or "")].append(row)
    for exit_row in lifecycle["position_exit_rows"]:
        event_id = str(exit_row.get("event_id") or "")
        try:
            exit_decision = audit_common.parse_signal_time(
                str(exit_row.get("timestamp_broker") or "")
            )
        except ValueError:
            exit_decision = None
        matches = [
            row
            for row in trades_by_event.get(event_id, [])
            if exit_decision is not None
            and row.get("exit_time") is not None
            and abs((row["exit_time"] - exit_decision).total_seconds())
            <= common.SIGNAL_MATCH_WINDOW_SECONDS
        ]
        if len(matches) != 1:
            violations.append(f"{event_id or 'missing'}|actual_exit_not_reconciled")
    return {
        "trade_count": len(rows),
        "maximum_holding_m5_bars": max(
            (value for value in ordinals if value is not None),
            default=None,
        ),
        "hold_decision_rows": len(lifecycle["hold_decision_rows"]),
        "position_exit_rows": len(lifecycle["position_exit_rows"]),
        "actual_mode_exit_matches": len(lifecycle["position_exit_rows"])
        - sum(value.endswith("|actual_exit_not_reconciled") for value in violations),
        "holding_horizon_violations": sorted(set(violations)),
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
    episodes = common.episode_concentration(rows)
    holding = holding_audit(rows, lifecycle)
    drawdown = clean.mt5_drawdown(result.get("mt5_report_metrics", {}))
    available = [row for row in overlaps if row["available"]]
    max_overlap = max((float(row["overlap_pct"]) for row in available), default=None)
    pre_recent_end = date.fromisoformat(window["pre_recent_end"].replace(".", "-"))
    setup_purity = (
        100.0 * (lifecycle["registered_events"] - len(lifecycle["native_setup_failures"]))
        / lifecycle["registered_events"]
        if lifecycle["registered_events"]
        else 0.0
    )
    entry_purity = (
        100.0 * (risk["successful_orders"] - len(lifecycle["impure_executed_signal_matches"]))
        / risk["successful_orders"]
        if risk["successful_orders"]
        else 0.0
    )
    values = {
        "trades": compact["signals"],
        "owned_regime_episodes": len(set(lifecycle["registered_episode_ids"].values()) - {0}),
        "exposure_years": len(years),
        "profitable_years": sum(row["net"] > 0.0 for row in years),
        "win_rate_pct": compact["wr"],
        "avg_win_loss": compact["wl"],
        "profit_factor": compact["pf"],
        "stress_profit_factor": compact["stress_030_pf"],
        "stress_net_usd": compact["stress_030_net"],
        "pre_recent_net_usd": sum(float(row["pnl_usd"]) for row in rows if row["entry_date"] <= pre_recent_end),
        "top10_removed_net_usd": compact["top10_removed_net"],
        "top3_days_removed_net_usd": compact["top3_days_removed_net"],
        "best_month_share_pct": compact["best_month_share_pct"],
        "max_episode_positive_net_share_pct": episodes["max_positive_net_share_pct"],
        "native_setup_purity_pct": round(setup_purity, 4),
        "native_entry_purity_pct": round(entry_purity, 4),
        "owned_state_net_usd": compact["net"] if episodes["missing_episode_trades"] == 0 else None,
        "required_overlap_controls": len(REQUIRED_OVERLAP_CONTROLS),
        "available_overlap_controls": len(available),
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
    checks = window_gate_checks(values)
    checks["regime_independence_checks"].update(
        {
            "registrations_unique": not lifecycle["duplicate_registrations"],
            "consumptions_exact": not lifecycle["duplicate_consumptions"]
            and not lifecycle["missing_consumptions"]
            and not lifecycle["consumed_without_registration"],
            "signals_unique_and_registered": not lifecycle["duplicate_signals"]
            and not lifecycle["signals_without_registration"],
            "state_transitions_valid": not lifecycle["transition_violations"],
            "ownership_observations_causal": not lifecycle["ownership_observation_violations"],
            "impulse_registration_sequence_valid": not lifecycle["impulse_registration_violations"],
            "entry_completed_bar_counters_valid": not lifecycle["entry_counter_violations"],
            "consumption_outcomes_valid": not lifecycle["invalid_consumption_outcomes"],
            "tester_end_right_censoring_lte_one": lifecycle["tester_deinit_events"] <= 1,
            "executions_match_native_signals": not lifecycle["missing_executed_signal_matches"]
            and not lifecycle["impure_executed_signal_matches"],
            "position_exits_match_executed_events": not lifecycle["orphan_position_exits"],
            "position_exit_fields_valid": not lifecycle["invalid_position_exits"],
            "holding_completed_bar_counters_valid": not lifecycle["hold_counter_violations"],
            "holding_horizon_audited": not holding["holding_horizon_violations"],
        }
    )
    return {
        **compact,
        "window": window["name"],
        "gate_metrics": values,
        "checks": checks,
        "year_rows": years,
        "episode_audit": episodes,
        "holding_audit": holding,
        "lifecycle_audit": {
            key: value
            for key, value in lifecycle.items()
            if key
            not in {
                "artifact_rows",
                "ownership_rows",
                "signal_events_detail",
                "entry_decision_rows",
                "hold_decision_rows",
                "position_exit_rows",
            }
        },
        "risk_execution_audit": risk,
        "overlap_audit": overlaps,
        "drawdown_audit": drawdown,
    }


def decide(static: dict[str, bool], windows: list[dict[str, dict[str, bool]]]) -> str:
    groups = (
        "alpha_checks",
        "robustness_checks",
        "regime_independence_checks",
        "execution_risk_checks",
    )
    if not all(static.values()) or len(windows) != 2:
        return "R2_ICR_M15_M5_CONTINUATION_REJECT"
    if not all(all(window[group].values()) for window in windows for group in groups):
        return "R2_ICR_M15_M5_CONTINUATION_REJECT"
    if not all(all(window["drawdown_checks"].values()) for window in windows):
        return "R2_ICR_M15_M5_CONTINUATION_ALPHA_ONLY_RISK_REPAIR_REQUIRED"
    return "R2_ICR_M15_M5_CONTINUATION_FULLY_QUALIFIED"


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU R2 M15-Impulse / M5-Continuation Short V1 Exact-MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "| Window | Trades | WR% | W/L | PF | Stress PF | Net | Events | Signals | Max hold M5 | Equity DD% | Max risk |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["window_results"]:
        lifecycle = row["lifecycle_audit"]
        gates = row["gate_metrics"]
        lines.append(
            f"| `{row['window']}` | {row['signals']} | {row['wr']:.2f} | {row['wl'] or 0.0:.4f} | "
            f"{row['pf'] or 0.0:.4f} | {row['stress_030_pf'] or 0.0:.4f} | {row['net']:.2f} | "
            f"{lifecycle['registered_events']} | {lifecycle['signal_events']} | "
            f"{row['holding_audit']['maximum_holding_m5_bars'] or 0.0:.2f} | "
            f"{gates['equity_dd_relative_pct'] or 0.0:.2f} | {gates['max_executed_initial_risk_usd'] or 0.0:.4f} |"
        )
    lines.extend(["", "## Failed Gates", ""])
    for row in payload["window_results"]:
        lines.append(f"### `{row['window']}`")
        for group, checks in row["checks"].items():
            failed = [name for name, passed in checks.items() if not passed]
            lines.append(f"- `{group}`: {', '.join(failed) if failed else 'none'}")
    lines.extend(["", "## Artifacts", ""])
    for key, value in payload["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the frozen mode27 two-window exact-MT5 exam.")
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--variant-timeout-seconds", type=int, default=1200)
    args = parser.parse_args()

    variants = build_variants()
    checks = static_checks(variants)
    static_payload = {
        "status": "PREREGISTERED_RUNNER_LOCKED_NOT_IMPLEMENTED_NOT_RUN",
        "preregistration": rel(PREREG),
        "source_id": SOURCE_ID,
        "variant": VARIANT_NAME,
        "windows": WINDOWS,
        "mode24_diagnosis": MODE24_DIAGNOSIS,
        "mode24_causal_status": MODE24_CAUSAL_STATUS,
        "tester_input_sha256": stable_hash(FROZEN_INPUTS),
        "static_checks": checks,
        "implementation_readiness": implementation_readiness(),
        "overlap_control_readiness": overlap_control_readiness(),
        "historical_run_authorized": HISTORICAL_RUN_AUTHORIZED,
    }
    if args.static_only:
        print(json.dumps(static_payload, indent=2))
        return 0 if PREREG.exists() and all(checks.values()) else 1

    if not PREREG.exists():
        raise FileNotFoundError(PREREG)
    if not all(checks.values()):
        raise RuntimeError(f"Invalid frozen mode27 runner: {checks}")
    readiness = implementation_readiness()
    if not all(readiness.values()):
        missing = [token for token, present in readiness.items() if not present]
        raise RuntimeError("Mode27 EA implementation is incomplete: " + ", ".join(missing))
    if not HISTORICAL_RUN_AUTHORIZED:
        raise RuntimeError("Mode27 historical execution is locked pending explicit authorization")
    control_readiness = overlap_control_readiness()
    if not all(control_readiness.values()):
        missing = [name for name, ready in control_readiness.items() if not ready]
        raise RuntimeError(
            "Mode27 overlap controls are missing or nonconforming: " + ", ".join(missing)
        )

    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    outputs: dict[str, str] = {"report_md": rel(report_md), "report_json": rel(report_json)}
    window_results: list[dict[str, Any]] = []
    for window in WINDOWS:
        name = window["name"]
        mt5.VARIANTS = variants
        mt5_md = REPORTS_DIR / f"{OUTPUT_STEM}_{name}_MT5.md"
        mt5_json = REPORTS_DIR / f"{OUTPUT_STEM}_{name}_MT5.json"
        mt5_payload = mt5.run_variants(
            from_date=window["from_date"],
            to_date=window["to_date"],
            tag=mt5.safe_name("OWNER_GOAL_R2_ICR_M15_M5_" + name),
            report_md=mt5_md,
            report_json=mt5_json,
            variant_timeout_seconds=args.variant_timeout_seconds,
            deposit="10000",
            currency="USD",
        )
        result = mt5_payload["variants"][0]
        signal_rows = common.read_tsv(Path(result["signal_csv"]))
        order_rows = common.read_tsv(Path(result["order_csv"]))
        lifecycle = lifecycle_audit(signal_rows, order_rows)
        normalized = normalize_rows(result, lifecycle)
        risk = common.risk_execution_audit(result, order_rows, normalized)
        overlaps = overlap_audit(name, normalized)
        evaluated = evaluate_window(window, result, normalized, lifecycle, risk, overlaps)
        window_results.append(evaluated)

        paths = {
            "normalized": REPORTS_DIR / f"{OUTPUT_STEM}_{name}_NORMALIZED_TRADES.csv",
            "events_csv": REPORTS_DIR / f"{OUTPUT_STEM}_{name}_EVENTS.csv",
            "events_json": REPORTS_DIR / f"{OUTPUT_STEM}_{name}_EVENTS.json",
            "ownership": REPORTS_DIR / f"{OUTPUT_STEM}_{name}_D1_OWNERSHIP.csv",
            "overlap_csv": REPORTS_DIR / f"{OUTPUT_STEM}_{name}_OVERLAP.csv",
            "overlap_json": REPORTS_DIR / f"{OUTPUT_STEM}_{name}_OVERLAP.json",
            "risk": REPORTS_DIR / f"{OUTPUT_STEM}_{name}_RISK_EXECUTION.json",
            "holding": REPORTS_DIR / f"{OUTPUT_STEM}_{name}_HOLDING.json",
            "equity_dd": REPORTS_DIR / f"{OUTPUT_STEM}_{name}_EQUITY_DD.json",
        }
        write_signal_csv(paths["normalized"], normalized)
        common.write_dict_rows(paths["events_csv"], lifecycle["artifact_rows"])
        common.write_dict_rows(paths["ownership"], lifecycle["ownership_rows"])
        common.write_dict_rows(paths["overlap_csv"], overlaps)
        paths["events_json"].write_text(json.dumps(lifecycle, indent=2, default=str), encoding="utf-8")
        paths["overlap_json"].write_text(json.dumps(overlaps, indent=2, default=str), encoding="utf-8")
        paths["risk"].write_text(json.dumps(risk, indent=2, default=str), encoding="utf-8")
        paths["holding"].write_text(json.dumps(evaluated["holding_audit"], indent=2, default=str), encoding="utf-8")
        paths["equity_dd"].write_text(json.dumps(evaluated["drawdown_audit"], indent=2, default=str), encoding="utf-8")
        outputs[f"{name}_mt5_md"] = rel(mt5_md)
        outputs[f"{name}_mt5_json"] = rel(mt5_json)
        for key, path in paths.items():
            outputs[f"{name}_{key}"] = rel(path)

    status = decide(checks, [row["checks"] for row in window_results])
    payload = {
        **static_payload,
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
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
