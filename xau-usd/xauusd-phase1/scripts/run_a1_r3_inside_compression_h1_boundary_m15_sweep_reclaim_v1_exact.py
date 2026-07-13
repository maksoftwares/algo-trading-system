from __future__ import annotations

import argparse
import hashlib
import json
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
    / "A1_XAU_R3_INSIDE_COMPRESSION_H1_BOUNDARY_M15_SWEEP_RECLAIM_V1_PREREG_2026_07_10.md"
)
SOURCE_ID = "r3_inside_compression_h1_boundary_m15_sweep_reclaim_v1"
VARIANT_NAME = "r3_chop_h1_boundary_m15_first_sweep_reclaim_v1"
OUTPUT_STEM = "A1_XAU_R3_INSIDE_COMPRESSION_H1_BOUNDARY_M15_SWEEP_RECLAIM_V1_EXACT_20260710"
PROPOSED_SIGNAL_MODE = 28
PROPOSED_ROUTER_MODE = 6
DEPOSIT_USD = 10_000.0
RISK_AMOUNT_USD = 50.0
HISTORICAL_RUN_AUTHORIZED = True
RUNNER_COMPLETE = True

WINDOWS = common.WINDOWS

MODE25_DIAGNOSIS = {
    "prehistory_201601_202112": {
        "registered": 519,
        "accepted": 83,
        "would_signals": 3,
        "executions": 0,
        "established_trend_handoff": 265,
        "expired": 144,
        "shock": 59,
        "first_touch_failed": 38,
    },
    "primary_202207_202606": {
        "registered": 179,
        "accepted": 25,
        "would_signals": 1,
        "executions": 1,
        "net_usd": -49.29,
        "established_trend_handoff": 110,
        "expired": 36,
        "shock": 17,
        "first_touch_failed": 13,
    },
}

CONTROL_PATHS: dict[str, dict[str, Path]] = {
    "prehistory_201601_202112": {
        "r1_box_clean_control": REPORTS_DIR
        / "A1_XAU_R1_BOX_CLEAN_REQUALIFICATION_EXACT_20260710_prehistory_201601_202112_NORMALIZED_TRADES.csv",
        "r3_mode25_killed": REPORTS_DIR
        / "A1_XAU_R3_COMPRESSION_ACCEPTANCE_FIRST_PULLBACK_V1_EXACT_20260710_prehistory_2016_2021_NORMALIZED_TRADES.csv",
    },
    "primary_202207_202606": {
        "r1_box_clean_control": REPORTS_DIR
        / "A1_XAU_R1_BOX_CLEAN_REQUALIFICATION_EXACT_20260710_primary_202207_202606_NORMALIZED_TRADES.csv",
        "r3_mode25_killed": REPORTS_DIR
        / "A1_XAU_R3_COMPRESSION_ACCEPTANCE_FIRST_PULLBACK_V1_EXACT_20260710_current_2022_2026_NORMALIZED_TRADES.csv",
        "r3_h4_release_killed": REPORTS_DIR
        / "A1_XAU_R3_COMPRESSION_RELEASE_TRANSITION_V1_EXACT_20260710_r3_compression_release_transition_v1_strict_symmetric_NORMALIZED_TRADES.csv",
        "r4_m5_failed_break_killed": REPORTS_DIR
        / "A1_XAU_R4_CHOP_FAILED_BREAK_V1_EXACT_20260708_r4_chop_failed_break_v1_sweep_reclaim_NORMALIZED_TRADES.csv",
    },
}

# Availability is not path existence alone. Every control must have causal provenance
# suitable for overlap evidence. Nonconforming mode24 ledgers are deliberately absent.
CONTROL_PROVENANCE = {
    "r1_box_clean_control": {
        "ready": True,
        "basis": "exact_stateless_completed_bar_control",
    },
    "r3_mode25_killed": {
        "ready": True,
        "basis": "corrected_completed_bar_counter_exact",
    },
    "r3_h4_release_killed": {
        "ready": True,
        "basis": "exact_stateless_completed_h4_signal",
    },
    "r4_m5_failed_break_killed": {
        "ready": True,
        "basis": "exact_stateless_completed_m5_signal",
    },
}

FROZEN_INPUTS = {
    **ROUTER_INPUTS,
    "InpAtrPeriod": "14",
    "InpSignalMode": "28",
    "InpRegimeRouterMode": "6",
    "InpDirectionMode": "0",
    "InpRiskReward": "2.00",
    "InpMaxSpreadPoints": "75",
    "InpMaxEstimatedCostR": "0.10",
    "InpR3ChopD1AtrPeriod": "14",
    "InpR3ChopD1AtrPercentileLookback": "252",
    "InpR3ChopD1AtrPercentileMax": "30.00",
    "InpR3ChopD1BoxDays": "5",
    "InpR3ChopD1RangeMedianLookback": "20",
    "InpR3ChopD1RangeMedianMax": "1.00",
    "InpR3ChopH1BoundaryLookback": "4",
    "InpR3ChopEventWindowM15Bars": "4",
    "InpR3ChopSweepM15Atr": "0.05",
    "InpR3ChopReclaimM15Atr": "0.05",
    "InpR3ChopMinBodyFraction": "0.35",
    "InpR3ChopLongCloseLocationMin": "0.65",
    "InpR3ChopShortCloseLocationMax": "0.35",
    "InpR3ChopStopBufferM15Atr": "0.10",
    "InpR3ChopMaxStopH1Atr": "0.75",
    "InpR3ChopConsumeFirstSweep": "true",
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

EXPECTED_FROZEN_INPUT_SHA256 = "bb8f93fc783b0c08f6a08340310f3197fd9402f1556ccbdb2c890adb95ea47b3"

REQUIRED_EA_TOKENS = (
    "SIGNAL_R3_INSIDE_COMPRESSION_H1_BOUNDARY_M15_SWEEP_RECLAIM = 28",
    "REGIME_ROUTER_R3_INSIDE_COMPRESSION_TREND_SHOCK_BLOCK = 6",
    "InpR3ChopH1BoundaryLookback",
    "InpR3ChopEventWindowM15Bars",
    "g_r3_chop_m15_bars_seen",
    "TryR3InsideCompressionH1BoundaryM15SweepReclaimSignal",
    "R3ChopHardRiskAllowed",
    "OrderCalcProfit(order_type",
    "R3_CHOP_CONTEXT_DECISION",
    "R3_CHOP_H1_DECISION",
    "R3_CHOP_EVENT_REGISTERED",
    "R3_CHOP_M15_DECISION",
    "R3_CHOP_EVENT_CONSUMED",
    "R3_COMPRESSION_H1_BOUNDARY_M15_SWEEP_RECLAIM_LONG",
    "R3_COMPRESSION_H1_BOUNDARY_M15_SWEEP_RECLAIM_SHORT",
    "window_end_incomplete",
    '"actual_risk_usd"',
)

LIFECYCLE_STAGES = {
    "context": "R3_CHOP_CONTEXT_DECISION",
    "h1_decision": "R3_CHOP_H1_DECISION",
    "registered": "R3_CHOP_EVENT_REGISTERED",
    "m15_decision": "R3_CHOP_M15_DECISION",
    "consumed": "R3_CHOP_EVENT_CONSUMED",
}
SIGNAL_PREFIXES = {
    "R3_COMPRESSION_H1_BOUNDARY_M15_SWEEP_RECLAIM_LONG",
    "R3_COMPRESSION_H1_BOUNDARY_M15_SWEEP_RECLAIM_SHORT",
}
ALLOWED_CONSUMPTION_OUTCOMES = {
    "entry",
    "first_sweep_failed",
    "ambiguous",
    "expired",
    "shock",
    "trend_handoff",
    "transition_handoff",
    "compression_lost",
    "window_end_incomplete",
}
ALLOWED_H1_DECISION_ACTIONS = {
    "registered",
    "active_event",
    "context_inactive",
    "invalid_boundary_data",
    "handoff",
}


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _float_value(value: Any) -> float | None:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def build_variants() -> list[mt5.Variant]:
    return [
        mt5.Variant(
            name=VARIANT_NAME,
            label=(
                "D1-compressed neutral ownership; repeated completed-H1 rolling-range "
                "event; first completed-M15 symmetric sweep/reclaim; fixed 2R"
            ),
            run_id="BT_A1_XAU_R3_CHOP_H1_BOUNDARY_M15_SWEEP_RECLAIM_V1",
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
    inputs = variant.tester_inputs if variant else {}
    prereg = PREREG.read_text(encoding="utf-8") if PREREG.exists() else ""
    runner = Path(__file__).read_text(encoding="utf-8")
    return {
        "exactly_one_variant": len(variants) == 1,
        "variant_and_inputs_frozen": variant is not None
        and variant.name == VARIANT_NAME
        and inputs == FROZEN_INPUTS,
        "tester_input_hash_frozen": stable_hash(inputs) == EXPECTED_FROZEN_INPUT_SHA256,
        "mode28_and_router6_reserved": inputs.get("InpSignalMode") == "28"
        and inputs.get("InpRegimeRouterMode") == "6"
        and PROPOSED_SIGNAL_MODE == 28
        and PROPOSED_ROUTER_MODE == 6,
        "two_eras_frozen": tuple((row["from_date"], row["to_date"]) for row in WINDOWS)
        == (("2016.01.01", "2021.12.31"), ("2022.07.01", "2026.06.30")),
        "inside_compression_repeated_h1_event": inputs.get("InpR3ChopH1BoundaryLookback") == "4"
        and inputs.get("InpR3ChopEventWindowM15Bars") == "4"
        and inputs.get("InpR3ChopConsumeFirstSweep") == "true",
        "symmetric_m15_geometry": inputs.get("InpR3ChopSweepM15Atr") == "0.05"
        and inputs.get("InpR3ChopReclaimM15Atr") == "0.05"
        and inputs.get("InpR3ChopLongCloseLocationMin") == "0.65"
        and inputs.get("InpR3ChopShortCloseLocationMax") == "0.35",
        "fixed_2r_hard_50usd_zero_overshoot": inputs.get("InpRiskReward") == "2.00"
        and inputs.get("InpUseRiskNormalizedLots") == "true"
        and inputs.get("InpRiskAmountUsd") == "50.00"
        and inputs.get("InpRejectRiskOvershootEnabled") == "true"
        and inputs.get("InpMaxRiskOvershootPct") == "0.00",
        "one_position_no_stacking": inputs.get("InpOnePositionPerMagic") == "true"
        and inputs.get("InpMaxOpenPositionsPerMagic") == "1",
        "no_absolute_atr_or_stop_mask": inputs.get("InpMinAtrAbsoluteForEntry") == "0.00"
        and all(inputs.get(key) == "0" for key in ("InpStopFloorPoints", "InpStopCeilingPoints", "InpStopCapPoints")),
        "no_calendar_or_session_mask": all(
            inputs.get(key) == ""
            for key in (
                "InpBlockedEntryHoursCsv",
                "InpBlockedEntryDayHoursCsv",
                "InpBlockedLongEntryHoursCsv",
                "InpBlockedShortEntryHoursCsv",
            )
        )
        and inputs.get("InpUseDirectionalSessionFilter") == "false",
        "no_pnl_or_management_mask": all(
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
        "completed_bar_counter_contract": "completed-bar counter" in prereg
        and "elapsed seconds" in prereg
        and "process the active event before registering" in prereg,
        "runner_has_no_elapsed_time_window": (".total_seconds()" + " / 900") not in runner
        and ("event_window_" + "seconds") not in runner,
        "overlap_controls_have_valid_provenance": all(
            CONTROL_PROVENANCE.get(control, {}).get("ready") is True
            for paths in CONTROL_PATHS.values()
            for control in paths
        )
        and all("mode24" not in control for paths in CONTROL_PATHS.values() for control in paths),
        "complete_evaluator_available": RUNNER_COMPLETE,
    }


def lifecycle_audit(
    signal_rows: list[dict[str, str]], order_rows: list[dict[str, str]]
) -> dict[str, Any]:
    registered: Counter[str] = Counter()
    consumed: Counter[str] = Counter()
    signals: Counter[str] = Counter()
    registration_fields: dict[str, dict[str, str]] = {}
    consumption_fields: dict[str, dict[str, str]] = {}
    consumed_index: dict[str, int] = {}
    registration_index: dict[str, int] = {}
    decision_rows: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    signal_events: list[dict[str, Any]] = []
    context_rows: list[dict[str, Any]] = []
    h1_decision_rows: list[dict[str, Any]] = []
    artifact_rows: list[dict[str, Any]] = []
    active_event = ""
    active_state = "IDLE"
    overwrite: list[str] = []
    transition_errors: list[str] = []
    future_bar: list[str] = []
    retrospective: list[str] = []
    native_setup: list[str] = []
    native_signal: list[str] = []
    invalid_outcomes: list[str] = []
    context_errors: list[str] = []
    h1_decision_errors: list[str] = []
    suspended_contexts: set[str] = set()
    seen_episode_ids: set[str] = set()

    for index, row in enumerate(signal_rows):
        stage = str(row.get("stage") or "")
        prefix, fields = common.parse_reason(str(row.get("reason") or ""))
        event_id = fields.get("event_id", "")

        if stage == LIFECYCLE_STAGES["context"]:
            previous_context = context_rows[-1] if context_rows else None
            detail = {"row_index": index, "timestamp_broker": row.get("timestamp_broker", ""), **fields}
            context_rows.append(detail)
            artifact_rows.append({"row_index": index, "stage": stage, **fields})
            owned = fields.get("owned") == "1"
            prior_context_suspended = fields.get("prior_context_suspended", "0") == "1"
            if prior_context_suspended and previous_context:
                previous_context_id = str(previous_context.get("context_id") or "")
                if previous_context_id:
                    suspended_contexts.add(previous_context_id)
            if (
                not fields.get("context_id")
                or common._int_value(fields.get("d1_time")) is None
                or fields.get("d1_shift") != "1"
                or fields.get("backfill") != "0"
                or fields.get("owned") not in {"0", "1"}
                or fields.get("prior_context_suspended", "0") not in {"0", "1"}
                or (
                    owned
                    and not (
                        fields.get("episode_id")
                        and fields.get("compressed") == "1"
                        and fields.get("direction_state") == "NEUTRAL"
                        and fields.get("shock") == "0"
                        and fields.get("established") == "0"
                        and fields.get("transition") == "0"
                    )
                )
            ):
                context_errors.append(fields.get("context_id") or f"context:{index}")
            if owned:
                episode_id = fields.get("episode_id", "")
                continuing = bool(
                    previous_context
                    and previous_context.get("owned") == "1"
                    and previous_context.get("context_id") not in suspended_contexts
                    and not prior_context_suspended
                )
                if continuing and episode_id != previous_context.get("episode_id"):
                    context_errors.append(f"{fields.get('context_id')}|episode_continuity")
                if not continuing:
                    if episode_id in seen_episode_ids:
                        context_errors.append(f"{fields.get('context_id')}|episode_reuse")
                    elif episode_id:
                        seen_episode_ids.add(episode_id)
            continue

        if stage == LIFECYCLE_STAGES["h1_decision"]:
            h1_decision_rows.append(
                {"row_index": index, "timestamp_broker": row.get("timestamp_broker", ""), **fields}
            )
            artifact_rows.append({"row_index": index, "stage": stage, **fields})
            h1_time = common._int_value(fields.get("h1_bar_time"))
            setup_time = common._int_value(fields.get("setup_time"))
            if (
                h1_time is None
                or setup_time is None
                or setup_time != h1_time + 3600
                or fields.get("h1_shift") != "1"
                or fields.get("backfill") != "0"
            ):
                future_bar.append(event_id or f"h1:{index}")
            if (
                fields.get("action") not in ALLOWED_H1_DECISION_ACTIONS
                or not fields.get("context_id")
                or (fields.get("action") == "registered" and (not event_id or fields.get("owned") != "1"))
            ):
                h1_decision_errors.append(event_id or f"h1:{index}")
            continue

        if stage == LIFECYCLE_STAGES["m15_decision"]:
            detail = {"row_index": index, "timestamp_broker": row.get("timestamp_broker", ""), **fields}
            decision_rows[event_id].append(detail)
            artifact_rows.append({"row_index": index, "stage": stage, **fields})
            if active_event != event_id or active_state != "WAIT_FIRST_M15_SWEEP":
                transition_errors.append(f"decision:{event_id or index}")
            continue

        if stage in (LIFECYCLE_STAGES["registered"], LIFECYCLE_STAGES["consumed"]):
            artifact_rows.append(
                {"row_index": index, "timestamp_broker": row.get("timestamp_broker", ""), "stage": stage, **fields}
            )

        if stage == LIFECYCLE_STAGES["registered"]:
            registered[event_id] += 1
            registration_fields[event_id] = fields
            registration_index[event_id] = index
            if not event_id or active_event or active_state != "IDLE":
                overwrite.append(event_id or f"missing:{index}")
            if fields.get("from") != "IDLE" or fields.get("to") != "WAIT_FIRST_M15_SWEEP":
                transition_errors.append(f"register:{event_id}")
            setup_time = common._int_value(fields.get("setup_time"))
            h1_bar_time = common._int_value(fields.get("h1_bar_time"))
            if (
                setup_time is None
                or h1_bar_time is None
                or setup_time != h1_bar_time + 3600
                or fields.get("h1_shift") != "1"
                or fields.get("backfill") != "0"
            ):
                future_bar.append(event_id)
            boundary_high = _float_value(fields.get("boundary_high"))
            boundary_low = _float_value(fields.get("boundary_low"))
            h1_atr = _float_value(fields.get("h1_atr"))
            latest_context = context_rows[-1] if context_rows else None
            matching_contexts = bool(
                latest_context
                and int(latest_context["row_index"]) < index
                and latest_context.get("context_id") == fields.get("context_id")
                and latest_context.get("episode_id") == fields.get("episode_id")
                and latest_context.get("owned") == "1"
                and latest_context.get("compressed") == "1"
                and latest_context.get("direction_state") == "NEUTRAL"
                and latest_context.get("shock") == "0"
                and latest_context.get("established") == "0"
                and latest_context.get("transition") == "0"
                and latest_context.get("d1_shift") == "1"
                and latest_context.get("backfill") == "0"
                and common._int_value(latest_context.get("d1_time")) is not None
                and setup_time is not None
                and common._int_value(latest_context.get("d1_time")) < setup_time
                and fields.get("context_id") not in suspended_contexts
            )
            matching_h1 = [
                item
                for item in h1_decision_rows
                if int(item["row_index"]) < index
                and item.get("event_id") == event_id
                and item.get("context_id") == fields.get("context_id")
                and item.get("episode_id") == fields.get("episode_id")
                and item.get("action") == "registered"
                and common._int_value(item.get("setup_time")) == setup_time
                and common._int_value(item.get("h1_bar_time")) == h1_bar_time
                and item.get("owned") == "1"
            ]
            if not (
                fields.get("setup") == "COMPRESSED"
                and fields.get("entry") == "COMPRESSED"
                and fields.get("direction_state") == "NEUTRAL"
                and fields.get("shock") == "0"
                and fields.get("established") == "0"
                and fields.get("transition") == "0"
                and fields.get("boundary_lookback") == FROZEN_INPUTS["InpR3ChopH1BoundaryLookback"]
                and fields.get("episode_id")
                and boundary_high is not None
                and boundary_low is not None
                and boundary_high > boundary_low > 0.0
                and h1_atr is not None
                and h1_atr > 0.0
                and matching_contexts
                and len(matching_h1) == 1
            ):
                native_setup.append(event_id)
            active_event, active_state = event_id, "WAIT_FIRST_M15_SWEEP"
            continue

        if stage == LIFECYCLE_STAGES["consumed"]:
            consumed[event_id] += 1
            consumed_index[event_id] = index
            consumption_fields[event_id] = fields
            if active_event != event_id or active_state != "WAIT_FIRST_M15_SWEEP":
                transition_errors.append(f"consume:{event_id}")
            if fields.get("from") != "WAIT_FIRST_M15_SWEEP" or fields.get("to") != "IDLE":
                transition_errors.append(f"consume_transition:{event_id}")
            if fields.get("outcome") not in ALLOWED_CONSUMPTION_OUTCOMES:
                invalid_outcomes.append(event_id)
            if fields.get("outcome") in {
                "shock",
                "trend_handoff",
                "transition_handoff",
                "compression_lost",
            }:
                context_id = registration_fields.get(event_id, {}).get("context_id", "")
                if context_id:
                    suspended_contexts.add(context_id)
            active_event, active_state = "", "IDLE"
            continue

        if stage == "WOULD_SIGNAL":
            if prefix not in SIGNAL_PREFIXES or not event_id:
                native_signal.append(event_id or f"missing:{index}")
                continue
            signals[event_id] += 1
            signal_direction = str(row.get("direction") or "").upper()
            expected_prefix = (
                f"R3_COMPRESSION_H1_BOUNDARY_M15_SWEEP_RECLAIM_{signal_direction}"
                if signal_direction in {"LONG", "SHORT"}
                else ""
            )
            if not (
                prefix == expected_prefix
                and fields.get("setup") == "COMPRESSED"
                and fields.get("entry") == "COMPRESSED"
                and fields.get("direction_state") == "NEUTRAL"
                and fields.get("shock") == "0"
                and fields.get("established") == "0"
                and fields.get("transition") == "0"
                and fields.get("episode_id") == registration_fields.get(event_id, {}).get("episode_id")
            ):
                native_signal.append(event_id)
            if (
                event_id not in consumed_index
                or consumed_index[event_id] >= index
                or consumption_fields.get(event_id, {}).get("outcome") != "entry"
            ):
                retrospective.append(event_id)
            attempt_time = common._int_value(fields.get("attempt_time"))
            attempt_ordinal = common._int_value(fields.get("attempt_ordinal"))
            matches = [
                item
                for item in decision_rows.get(event_id, [])
                if common._int_value(item.get("decision_bar_time")) == attempt_time
                and common._int_value(item.get("m15_bar_ordinal")) == attempt_ordinal
                and int(item["row_index"]) < index
            ]
            if not attempt_time or not attempt_ordinal or len(matches) != 1:
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
        transition_errors.append(f"active_at_end:{active_event}")

    context_times = [common._int_value(row.get("d1_time")) for row in context_rows]
    if any(
        value is None
        or (position > 0 and context_times[position - 1] is not None and value <= context_times[position - 1])
        for position, value in enumerate(context_times)
    ):
        context_errors.append("context_time_sequence")

    h1_times = [common._int_value(row.get("h1_bar_time")) for row in h1_decision_rows]
    if any(
        value is None
        or (position > 0 and h1_times[position - 1] is not None and value <= h1_times[position - 1])
        for position, value in enumerate(h1_times)
    ):
        h1_decision_errors.append("h1_time_sequence")

    for row in h1_decision_rows:
        if row.get("action") != "registered":
            continue
        event_id = str(row.get("event_id") or "")
        if registered.get(event_id, 0) != 1 or registration_index.get(event_id, -1) <= int(row["row_index"]):
            h1_decision_errors.append(event_id or f"h1:{row['row_index']}")

    counter_errors: list[str] = []
    limit = int(FROZEN_INPUTS["InpR3ChopEventWindowM15Bars"])
    for event_id in sorted(set(registered) | set(consumed) | set(decision_rows)):
        decisions = sorted(decision_rows.get(event_id, []), key=lambda item: int(item["row_index"]))
        ordinals = [common._int_value(item.get("m15_bar_ordinal")) for item in decisions]
        times = [common._int_value(item.get("decision_bar_time")) for item in decisions]
        setup_time = common._int_value(registration_fields.get(event_id, {}).get("setup_time"))
        if (
            ordinals != list(range(1, len(decisions) + 1))
            or len(decisions) > limit
            or any(value is None for value in times)
            or len(set(times)) != len(times)
            or any(
                value is None
                or setup_time is None
                or value <= setup_time
                or (position > 0 and times[position - 1] is not None and value <= times[position - 1])
                for position, value in enumerate(times)
            )
        ):
            counter_errors.append(f"{event_id}|decision_sequence")
        fields = consumption_fields.get(event_id)
        if fields is None:
            continue
        outcome = fields.get("outcome", "")
        bars_seen = common._int_value(fields.get("m15_bars_seen"))
        if bars_seen is None or bars_seen != len(decisions) or not 0 <= bars_seen <= limit:
            counter_errors.append(f"{event_id}|bars_seen")
        if outcome in {"entry", "first_sweep_failed", "ambiguous"}:
            attempt = common._int_value(fields.get("attempt_ordinal"))
            if not ordinals or attempt != ordinals[-1] or attempt != bars_seen:
                counter_errors.append(f"{event_id}|first_sweep_attempt")
        if outcome == "expired" and (bars_seen != limit or ordinals != list(range(1, limit + 1))):
            counter_errors.append(f"{event_id}|expiry")
        if outcome == "window_end_incomplete" and not (
            fields.get("deinit") == "1" and bars_seen is not None and bars_seen < limit
        ):
            counter_errors.append(f"{event_id}|right_censor")

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

    event_episodes = {
        event_id: fields.get("episode_id", "") for event_id, fields in registration_fields.items()
    }
    right_censored = [
        event_id
        for event_id, fields in consumption_fields.items()
        if fields.get("outcome") == "window_end_incomplete"
    ]
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
        "transition_violations": transition_errors,
        "future_bar_violations": sorted(set(future_bar)),
        "retrospective_entry_violations": sorted(set(retrospective)),
        "native_setup_failures": sorted(set(native_setup)),
        "native_signal_failures": sorted(set(native_signal)),
        "invalid_consumption_outcomes": sorted(set(invalid_outcomes)),
        "context_decision_violations": sorted(set(context_errors)),
        "h1_decision_violations": sorted(set(h1_decision_errors)),
        "completed_bar_counter_violations": sorted(set(counter_errors)),
        "missing_executed_signal_matches": missing_execution_matches,
        "impure_executed_signal_matches": impure_execution_matches,
        "executed_event_ids": executed_event_ids,
        "window_end_incomplete_events": len(right_censored),
        "window_end_incomplete_event_ids": sorted(right_censored),
        "owned_episode_count": len({value for value in event_episodes.values() if value}),
        "registered_episode_ids": event_episodes,
        "signal_events_detail": signal_events,
        "decision_rows": [row for rows in decision_rows.values() for row in rows],
        "h1_decision_rows": h1_decision_rows,
        "artifact_rows": artifact_rows,
        "context_rows": context_rows,
    }


def normalize_rows(
    window_name: str, result: dict[str, Any], lifecycle: dict[str, Any]
) -> list[dict[str, Any]]:
    rows = metrics.mt5_rows(result, source_priority=99)
    for row in rows:
        event_id = common.event_for_entry(
            row["entry_time"], str(row.get("direction") or ""), lifecycle
        )
        episode_id = lifecycle["registered_episode_ids"].get(event_id, "")
        row.update(
            {
                "component": SOURCE_ID,
                "source_id": SOURCE_ID,
                "upstream_source_id": SOURCE_ID,
                "upstream_component": VARIANT_NAME,
                "family_group": "xau_r3_inside_compression_mean_reversion",
                "cell_id": SOURCE_ID,
                "event_id": event_id,
                "owned_episode_id": f"{window_name}:{episode_id}" if episode_id else "",
                "window": window_name,
            }
        )
    return rows


def episode_concentration(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pnl: defaultdict[str, float] = defaultdict(float)
    for row in rows:
        pnl[str(row.get("owned_episode_id") or "")] += float(row.get("pnl_usd") or 0.0)
    positive = {key: value for key, value in pnl.items() if key and value > 0.0}
    denominator = sum(positive.values())
    share = 100.0 * max(positive.values(), default=0.0) / denominator if denominator > 0 else None
    return {
        "episode_pnl": {key: round(value, 2) for key, value in sorted(pnl.items())},
        "traded_owned_episodes": len({key for key in pnl if key}),
        "missing_episode_trades": sum(1 for row in rows if not row.get("owned_episode_id")),
        "max_positive_net_share_pct": round(share, 2) if share is not None else None,
    }


def overlap_audit(window_name: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for control, path in CONTROL_PATHS[window_name].items():
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


def window_gate_checks(values: dict[str, Any], required_controls: int) -> dict[str, dict[str, bool]]:
    proxy = dict(values)
    all_controls = values.get("available_overlap_controls") == required_controls
    proxy["required_overlap_controls"] = len(common.REQUIRED_OVERLAP_CONTROLS)
    proxy["available_overlap_controls"] = (
        len(common.REQUIRED_OVERLAP_CONTROLS) if all_controls else -1
    )
    checks = common.window_gate_checks(proxy)
    checks["alpha_checks"].update(
        {
            "long_trades_ge_25": values["long_trades"] >= 25,
            "short_trades_ge_25": values["short_trades"] >= 25,
            "long_stress_net_gt_0": values["long_stress_net_usd"] > 0.0,
            "short_stress_net_gt_0": values["short_stress_net_usd"] > 0.0,
        }
    )
    checks["regime_independence_checks"]["all_required_overlap_controls_available"] = all_controls
    return checks


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
    long_book = metrics.strip_heavy(
        metrics.flat_shape(window["name"] + "_long", [row for row in rows if row.get("direction") == "LONG"])
    )
    short_book = metrics.strip_heavy(
        metrics.flat_shape(window["name"] + "_short", [row for row in rows if row.get("direction") == "SHORT"])
    )
    years = clean.year_rows(rows)
    episodes = episode_concentration(rows)
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
    equity_usd = drawdown["equity_dd_maximal_usd"]
    closed_usd = compact["max_closed_dd"]
    values = {
        "trades": compact["signals"],
        "owned_regime_episodes": episodes["traded_owned_episodes"],
        "exposure_years": len(years),
        "profitable_years": sum(row["net"] > 0.0 for row in years),
        "win_rate_pct": compact["wr"],
        "avg_win_loss": compact["wl"],
        "profit_factor": compact["pf"],
        "stress_profit_factor": compact["stress_030_pf"],
        "stress_net_usd": compact["stress_030_net"],
        "pre_recent_net_usd": sum(
            float(row["pnl_usd"]) for row in rows if row["entry_date"] <= pre_recent_end
        ),
        "top10_removed_net_usd": compact["top10_removed_net"],
        "top3_days_removed_net_usd": compact["top3_days_removed_net"],
        "best_month_share_pct": compact["best_month_share_pct"],
        "max_episode_positive_net_share_pct": episodes["max_positive_net_share_pct"],
        "native_setup_purity_pct": round(setup_purity, 4),
        "native_entry_purity_pct": round(entry_purity, 4),
        "owned_state_net_usd": compact["net"] if episodes["missing_episode_trades"] == 0 else None,
        "required_overlap_controls": len(CONTROL_PATHS[window["name"]]),
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
        "equity_dd_maximal_usd": equity_usd,
        "closed_ledger_dd_usd": closed_usd,
        "net_to_equity_dd": compact["net"] / equity_usd if equity_usd and equity_usd > 0 else None,
        "equity_to_closed_dd": equity_usd / closed_usd if equity_usd and closed_usd > 0 else None,
        "long_trades": long_book["signals"],
        "short_trades": short_book["signals"],
        "long_stress_net_usd": long_book["stress_030_net"],
        "short_stress_net_usd": short_book["stress_030_net"],
    }
    checks = window_gate_checks(values, len(CONTROL_PATHS[window["name"]]))
    checks["regime_independence_checks"].update(
        {
            "registrations_unique": not lifecycle["duplicate_registrations"],
            "consumptions_exact": not lifecycle["duplicate_consumptions"]
            and not lifecycle["missing_consumptions"]
            and not lifecycle["consumed_without_registration"],
            "signals_unique_and_registered": not lifecycle["duplicate_signals"]
            and not lifecycle["signals_without_registration"],
            "state_transitions_valid": not lifecycle["transition_violations"],
            "completed_m15_counters_valid": not lifecycle["completed_bar_counter_violations"],
            "context_decisions_valid": not lifecycle["context_decision_violations"],
            "h1_decisions_valid": not lifecycle["h1_decision_violations"],
            "consumption_outcomes_valid": not lifecycle["invalid_consumption_outcomes"],
            "right_censoring_lte_one": lifecycle["window_end_incomplete_events"] <= 1,
            "executions_match_native_signals": not lifecycle["missing_executed_signal_matches"]
            and not lifecycle["impure_executed_signal_matches"],
        }
    )
    return {
        **compact,
        "window": window["name"],
        "gate_metrics": values,
        "checks": checks,
        "direction": {"LONG": long_book, "SHORT": short_book},
        "year_rows": years,
        "episode_audit": episodes,
        "lifecycle_audit": {
            key: value
            for key, value in lifecycle.items()
            if key
            not in {
                "artifact_rows",
                "context_rows",
                "h1_decision_rows",
                "signal_events_detail",
                "decision_rows",
            }
        },
        "risk_execution_audit": risk,
        "overlap_audit": overlaps,
        "drawdown_audit": drawdown,
    }


def global_evaluation(rows: list[dict[str, Any]], windows: list[dict[str, Any]]) -> dict[str, Any]:
    book = metrics.strip_heavy(metrics.flat_shape(SOURCE_ID + "_global", rows))
    long_book = metrics.strip_heavy(
        metrics.flat_shape(SOURCE_ID + "_global_long", [row for row in rows if row.get("direction") == "LONG"])
    )
    short_book = metrics.strip_heavy(
        metrics.flat_shape(SOURCE_ID + "_global_short", [row for row in rows if row.get("direction") == "SHORT"])
    )
    years = clean.year_rows(rows)
    episodes = episode_concentration(rows)
    non_drawdown_groups = ("alpha_checks", "robustness_checks", "regime_independence_checks", "execution_risk_checks")
    each_window_non_drawdown = all(
        all(result["checks"][group].values()) for result in windows for group in non_drawdown_groups
    )
    each_window_drawdown = all(all(result["checks"]["drawdown_checks"].values()) for result in windows)
    worst_balance = max(
        (result["gate_metrics"]["balance_dd_relative_pct"] for result in windows if result["gate_metrics"]["balance_dd_relative_pct"] is not None),
        default=None,
    )
    worst_equity = max(
        (result["gate_metrics"]["equity_dd_relative_pct"] for result in windows if result["gate_metrics"]["equity_dd_relative_pct"] is not None),
        default=None,
    )
    checks = {
        "both_windows_non_drawdown_pass": each_window_non_drawdown,
        "global_trades_ge_200": book["signals"] >= 200,
        "global_wr_ge_50": book["wr"] >= 50.0,
        "global_wl_ge_2": (book["wl"] or 0.0) >= 2.0,
        "global_pf_ge_2": (book["pf"] or 0.0) >= 2.0,
        "global_stress_pf_ge_1p75": (book["stress_030_pf"] or 0.0) >= 1.75,
        "global_stress_net_gt_0": book["stress_030_net"] > 0.0,
        "exposure_years_ge_3": len(years) >= 3,
        "profitable_years_ge_3": sum(row["net"] > 0.0 for row in years) >= 3,
        "long_trades_ge_50": long_book["signals"] >= 50,
        "short_trades_ge_50": short_book["signals"] >= 50,
        "long_stress_net_gt_0": long_book["stress_030_net"] > 0.0,
        "short_stress_net_gt_0": short_book["stress_030_net"] > 0.0,
        "top10_removed_net_gt_0": book["top10_removed_net"] > 0.0,
        "top3_days_removed_net_gt_0": book["top3_days_removed_net"] > 0.0,
        "best_month_share_lte_30": book["best_month_share_pct"] is not None
        and book["best_month_share_pct"] <= 30.0,
        "episode_share_lte_50": episodes["max_positive_net_share_pct"] is not None
        and episodes["max_positive_net_share_pct"] <= 50.0,
        "all_trades_have_owned_episode": episodes["missing_episode_trades"] == 0,
        "both_windows_drawdown_pass": each_window_drawdown,
        "worst_balance_dd_lte_20": worst_balance is not None and worst_balance <= 20.0,
        "worst_equity_dd_lte_20": worst_equity is not None and worst_equity <= 20.0,
        "each_window_net_to_equity_dd_ge_2": all(
            (result["gate_metrics"]["net_to_equity_dd"] or 0.0) >= 2.0 for result in windows
        ),
        "each_window_equity_to_closed_dd_lte_2": all(
            result["gate_metrics"]["equity_to_closed_dd"] is not None
            and result["gate_metrics"]["equity_to_closed_dd"] <= 2.0
            for result in windows
        ),
    }
    return {
        **book,
        "checks": checks,
        "direction": {"LONG": long_book, "SHORT": short_book},
        "year_rows": years,
        "episode_audit": episodes,
        "worst_balance_dd_relative_pct": worst_balance,
        "worst_equity_dd_relative_pct": worst_equity,
    }


def decide(static: dict[str, bool], windows: list[dict[str, Any]], global_result: dict[str, Any]) -> str:
    if not all(static.values()) or len(windows) != 2:
        return "R3_CHOP_H1_BOUNDARY_M15_SWEEP_RECLAIM_REJECT"
    drawdown_keys = {
        "both_windows_drawdown_pass",
        "worst_balance_dd_lte_20",
        "worst_equity_dd_lte_20",
        "each_window_net_to_equity_dd_ge_2",
        "each_window_equity_to_closed_dd_lte_2",
    }
    non_drawdown = {
        key: value
        for key, value in global_result["checks"].items()
        if key not in drawdown_keys
    }
    if not all(non_drawdown.values()):
        return "R3_CHOP_H1_BOUNDARY_M15_SWEEP_RECLAIM_REJECT"
    if not all(global_result["checks"].values()):
        return "R3_CHOP_H1_BOUNDARY_M15_SWEEP_RECLAIM_ALPHA_ONLY_RISK_REPAIR_REQUIRED"
    return "R3_CHOP_H1_BOUNDARY_M15_SWEEP_RECLAIM_FULLY_QUALIFIED"


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# A1 XAU R3 Inside-Compression H1-Boundary / M15 Sweep-Reclaim V1 Exact-MT5",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Status: `{payload['status']}`",
        f"Frozen tester-input SHA256: `{payload['tester_input_sha256']}`",
        "",
        "| Window | Trades | Long | Short | WR% | W/L | PF | Stress PF | Net | Events | Signals | Equity DD% | Max risk | Max overlap% |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["window_results"]:
        gates = row["gate_metrics"]
        lifecycle = row["lifecycle_audit"]
        lines.append(
            f"| `{row['window']}` | {row['signals']} | {gates['long_trades']} | {gates['short_trades']} | "
            f"{row['wr']:.2f} | {row['wl'] or 0.0:.4f} | {row['pf'] or 0.0:.4f} | "
            f"{row['stress_030_pf'] or 0.0:.4f} | {row['net']:.2f} | {lifecycle['registered_events']} | "
            f"{lifecycle['signal_events']} | {gates['equity_dd_relative_pct'] or 0.0:.2f} | "
            f"{gates['max_executed_initial_risk_usd'] or 0.0:.4f} | "
            f"{gates['max_same_direction_overlap_pct'] or 0.0:.2f} |"
        )
    lines.extend(["", "## Failed Gates", ""])
    for row in payload["window_results"]:
        lines.append(f"### `{row['window']}`")
        for group, checks in row["checks"].items():
            failed = [name for name, passed in checks.items() if not passed]
            lines.append(f"- `{group}`: {', '.join(failed) if failed else 'none'}")
    failed_global = [name for name, passed in payload["global"]["checks"].items() if not passed]
    lines.extend(["", "### `global`", f"- {', '.join(failed_global) if failed_global else 'none'}", "", "## Artifacts", ""])
    for key, value in payload["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the frozen mode28 two-era exact-MT5 exam.")
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--variant-timeout-seconds", type=int, default=1200)
    args = parser.parse_args()

    variants = build_variants()
    checks = static_checks(variants)
    static_payload = {
        "status": "MODE28_IMPLEMENTED_COMPILED_HISTORICAL_RUN_AUTHORIZED",
        "preregistration": rel(PREREG),
        "source_id": SOURCE_ID,
        "variant": VARIANT_NAME,
        "windows": WINDOWS,
        "mode25_diagnosis": MODE25_DIAGNOSIS,
        "tester_input_sha256": stable_hash(FROZEN_INPUTS),
        "static_checks": checks,
        "implementation_readiness": implementation_readiness(),
        "historical_run_authorized": HISTORICAL_RUN_AUTHORIZED,
    }
    if args.static_only:
        print(json.dumps(static_payload, indent=2))
        return 0 if PREREG.exists() and all(checks.values()) else 1

    if not PREREG.exists():
        raise FileNotFoundError(PREREG)
    if not all(checks.values()):
        raise RuntimeError(f"Invalid frozen mode28 runner: {checks}")
    readiness = implementation_readiness()
    if not all(readiness.values()):
        missing = [token for token, present in readiness.items() if not present]
        raise RuntimeError("Mode28 EA implementation is incomplete: " + ", ".join(missing))
    if not HISTORICAL_RUN_AUTHORIZED:
        raise RuntimeError("Mode28 historical execution is locked pending explicit authorization")

    report_md = REPORTS_DIR / f"{OUTPUT_STEM}.md"
    report_json = REPORTS_DIR / f"{OUTPUT_STEM}.json"
    outputs: dict[str, str] = {"report_md": rel(report_md), "report_json": rel(report_json)}
    window_results: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    for window in WINDOWS:
        name = window["name"]
        mt5.VARIANTS = variants
        mt5_md = REPORTS_DIR / f"{OUTPUT_STEM}_{name}_MT5.md"
        mt5_json = REPORTS_DIR / f"{OUTPUT_STEM}_{name}_MT5.json"
        exact = mt5.run_variants(
            from_date=window["from_date"],
            to_date=window["to_date"],
            tag=mt5.safe_name("OWNER_GOAL_R3_CHOP_H1_M15_" + name),
            report_md=mt5_md,
            report_json=mt5_json,
            variant_timeout_seconds=args.variant_timeout_seconds,
            deposit="10000",
            currency="USD",
        )
        result = exact["variants"][0]
        signal_rows = common.read_tsv(Path(result["signal_csv"]))
        order_rows = common.read_tsv(Path(result["order_csv"]))
        lifecycle = lifecycle_audit(signal_rows, order_rows)
        normalized = normalize_rows(name, result, lifecycle)
        risk = common.risk_execution_audit(result, order_rows, normalized)
        overlaps = overlap_audit(name, normalized)
        evaluated = evaluate_window(window, result, normalized, lifecycle, risk, overlaps)
        window_results.append(evaluated)
        all_rows.extend(normalized)

        paths = {
            "normalized": REPORTS_DIR / f"{OUTPUT_STEM}_{name}_NORMALIZED_TRADES.csv",
            "events_csv": REPORTS_DIR / f"{OUTPUT_STEM}_{name}_EVENTS.csv",
            "events_json": REPORTS_DIR / f"{OUTPUT_STEM}_{name}_EVENTS.json",
            "contexts": REPORTS_DIR / f"{OUTPUT_STEM}_{name}_CONTEXTS.csv",
            "h1_decisions": REPORTS_DIR / f"{OUTPUT_STEM}_{name}_H1_DECISIONS.csv",
            "overlap_csv": REPORTS_DIR / f"{OUTPUT_STEM}_{name}_OVERLAP.csv",
            "overlap_json": REPORTS_DIR / f"{OUTPUT_STEM}_{name}_OVERLAP.json",
            "risk": REPORTS_DIR / f"{OUTPUT_STEM}_{name}_RISK_EXECUTION.json",
            "equity_dd": REPORTS_DIR / f"{OUTPUT_STEM}_{name}_EQUITY_DD.json",
        }
        write_signal_csv(paths["normalized"], normalized)
        common.write_dict_rows(paths["events_csv"], lifecycle["artifact_rows"])
        common.write_dict_rows(paths["contexts"], lifecycle["context_rows"])
        common.write_dict_rows(paths["h1_decisions"], lifecycle["h1_decision_rows"])
        common.write_dict_rows(paths["overlap_csv"], overlaps)
        paths["events_json"].write_text(json.dumps(lifecycle, indent=2, default=str), encoding="utf-8")
        paths["overlap_json"].write_text(json.dumps(overlaps, indent=2, default=str), encoding="utf-8")
        paths["risk"].write_text(json.dumps(risk, indent=2, default=str), encoding="utf-8")
        paths["equity_dd"].write_text(json.dumps(evaluated["drawdown_audit"], indent=2, default=str), encoding="utf-8")
        outputs[f"{name}_mt5_md"] = rel(mt5_md)
        outputs[f"{name}_mt5_json"] = rel(mt5_json)
        for key, path in paths.items():
            outputs[f"{name}_{key}"] = rel(path)

    global_result = global_evaluation(all_rows, window_results)
    global_ledger = REPORTS_DIR / f"{OUTPUT_STEM}_GLOBAL_NORMALIZED_TRADES.csv"
    write_signal_csv(global_ledger, all_rows)
    outputs["global_normalized"] = rel(global_ledger)
    status = decide(checks, window_results, global_result)
    payload = {
        **static_payload,
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "preregistration_sha256": sha256_file(PREREG),
        "window_results": window_results,
        "global": global_result,
        "outputs": outputs,
    }
    report_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    report_md.write_text(render(payload), encoding="utf-8")
    print(json.dumps({"status": status, "report": str(report_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
