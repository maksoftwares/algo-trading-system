"""R6-C2 structural validators; no real-evidence generation surface."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from jsonschema import Draft202012Validator

from build_a1_xau_r6_distribution_break_failed_reclaim_census import (
    RULE_SHA256,
    RULE_VERSION,
    TERMINAL_STATUSES,
    FROM_INCLUSIVE,
    TO_EXCLUSIVE,
    Detection,
    RowContext,
    TerminalAnchor,
    broker_time,
    canonical_ids,
    incidence_report,
    minimum_contract_risk,
    normalize_up,
)


FORBIDDEN_FIELDS = {
    "exit_time", "target", "profit", "pnl", "net_r", "win", "loss", "mfe", "mae",
    "drawdown", "equity", "balance", "h4_exposure", "portfolio",
}
FORBIDDEN_FIELD_TOKENS = ("profit", "pnl", "exit", "target", "mfe", "mae", "drawdown", "equity", "balance", "portfolio", "exposure")
ALLOWED_C2_FILES = {
    "scripts/build_a1_xau_r6_distribution_break_failed_reclaim_census.py",
    "scripts/validate_a1_xau_r6_outcome_blind_census.py",
    "tests/test_a1_xau_r6_distribution_break_failed_reclaim_definition.py",
    "tests/test_a1_xau_r6_census_outcome_blind.py",
    "tests/test_a1_xau_r6_census_contract_risk.py",
    "tests/test_a1_xau_r6_census_manifest.py",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_closed_schema(schema: dict[str, Any]) -> None:
    if schema.get("additionalProperties") is not False:
        raise ValueError("row schema must be closed")
    properties = set(schema.get("properties", {}))
    required = set(schema.get("required", []))
    if required != properties:
        raise ValueError("every closed row property must be required")
    lowered = {field.lower() for field in properties}
    token_violation = any(
        token in field and field not in {"risk_exit_price"}
        for field in lowered
        for token in FORBIDDEN_FIELD_TOKENS
    )
    if lowered & FORBIDDEN_FIELDS or token_violation:
        raise ValueError("forbidden outcome field")
    if schema["properties"]["availability_status"].get("const") != "RAW_OPPORTUNITY_AVAILABLE":
        raise ValueError("partial exclusion rows are forbidden")


def _close(actual: object, expected: float, name: str) -> None:
    if not math.isclose(float(actual), expected, rel_tol=1e-10, abs_tol=1e-10):
        raise ValueError(f"{name} formula mismatch")


def validate_row(row: dict[str, Any], schema: dict[str, Any], context: RowContext) -> None:
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(row)
    properties = schema["properties"]
    if set(row) != set(properties):
        raise ValueError("row keys do not equal closed schema")
    if row["availability_status"] != "RAW_OPPORTUNITY_AVAILABLE" or row["exclusion_reason"] != "":
        raise ValueError("row is not a raw available opportunity")
    if row["entry_ask"] < row["entry_bid"] or row["structural_stop"] <= row["entry_ask"]:
        raise ValueError("invalid price relation")
    if row["risk_exit_price"] <= row["structural_stop"]:
        raise ValueError("conservative tick missing")
    if row["reference_risk_feasible"] != (row["minimum_contract_risk_usd"] <= 25.0):
        raise ValueError("reference risk flag mismatch")
    if row["deployment_risk_feasible"] != (row["minimum_contract_risk_usd"] <= 2.5):
        raise ValueError("deployment risk flag mismatch")

    impulse, distribution = context.impulse, context.distribution
    breakdown, reclaim, entry, contract = context.breakdown, context.reclaim, context.entry_tick, context.contract
    if len(impulse) != 6 or len(distribution) != 6:
        raise ValueError("identity context must contain six impulse and distribution bars")
    if row["rule_version"] != RULE_VERSION or row["rule_sha256"] != RULE_SHA256:
        raise ValueError("rule identity mismatch")
    expected_ids = canonical_ids(
        symbol=str(row["symbol"]), distribution=distribution,
        box_low=normalize_up(min(bar.low for bar in distribution), contract),
        box_high=normalize_up(max(bar.high for bar in distribution), contract),
        breakdown_time=breakdown.time, reclaim_time=reclaim.time, entry_tick=entry, contract=contract,
    )
    if (row["box_id"], row["episode_id"], row["candidate_id"]) != expected_ids:
        raise ValueError("canonical identity mismatch")
    expected_times = {
        "impulse_start_h4_time": impulse[0].time,
        "impulse_end_h4_time": impulse[-1].time,
        "box_start_h4_time": distribution[0].time,
        "box_end_h4_time": distribution[-1].time,
        "breakdown_h4_time": breakdown.time,
        "reclaim_h1_time": reclaim.time,
        "entry_tick_time": entry.time,
    }
    if any(row[key] != broker_time(value) for key, value in expected_times.items()):
        raise ValueError("timestamp context mismatch")
    decision = datetime.fromisoformat(str(row["decision_time"]))
    if decision != context.decision_time or not (reclaim.time < decision <= entry.time):
        raise ValueError("timestamp relationship mismatch")
    if (entry.time - decision).total_seconds() > 15 * 60 or row["entry_tick_sequence"] != entry.sequence:
        raise ValueError("entry tick relationship mismatch")
    if entry.time == decision and entry.source_h1_bar_time != decision:
        raise ValueError("same-second tick ownership unavailable")
    if entry.sequence <= context.last_reclaim_tick_sequence:
        raise ValueError("entry tick does not follow reclaim-bar ticks")
    if not (FROM_INCLUSIVE <= entry.time < TO_EXCLUSIVE):
        raise ValueError("entry tick outside locked interval")

    a_impulse, a_box, a_reclaim = (float(row[key]) for key in ("A_impulse", "A_box", "A_reclaim"))
    for name, actual, expected in (
        ("A_impulse", a_impulse, context.a_impulse),
        ("A_box", a_box, context.a_box),
        ("A_reclaim", a_reclaim, context.a_reclaim),
    ):
        _close(actual, expected, name)
    impulse_low, impulse_high = min(bar.low for bar in impulse), max(bar.high for bar in impulse)
    impulse_range = impulse_high - impulse_low
    impulse_net = impulse[-1].close - impulse[0].open
    box_low, box_high = min(bar.low for bar in distribution), max(bar.high for bar in distribution)
    box_width = box_high - box_low
    box_drift = abs(distribution[-1].close - distribution[0].open)
    formulas = {
        "impulse_range_atr": impulse_range / a_impulse,
        "impulse_net_advance_atr": impulse_net / a_impulse,
        "impulse_final_location": (impulse[-1].close - impulse_low) / impulse_range,
        "box_width_atr": box_width / a_box,
        "box_net_drift_atr": box_drift / a_box,
        "breakdown_distance_atr": (box_low - breakdown.close) / a_box,
        "breakdown_body_fraction": abs(breakdown.close - breakdown.open) / (breakdown.high - breakdown.low),
        "breakdown_close_location": (breakdown.close - breakdown.low) / (breakdown.high - breakdown.low),
        "reclaim_touch_distance_atr": (reclaim.high - box_low) / a_reclaim,
        "reclaim_body_fraction": abs(reclaim.close - reclaim.open) / (reclaim.high - reclaim.low),
        "reclaim_close_location": (reclaim.close - reclaim.low) / (reclaim.high - reclaim.low),
        "spread_points": (entry.ask - entry.bid) / contract.point,
    }
    for key, expected in formulas.items():
        _close(row[key], expected, key)
    observed_prices = {
        "impulse_low": impulse_low, "impulse_high": impulse_high,
        "box_low": box_low, "box_high": box_high,
        "entry_bid": entry.bid, "entry_ask": entry.ask,
    }
    for key, expected in observed_prices.items():
        _close(row[key], expected, key)
    if row["impulse_bullish_bars"] != sum(bar.close > bar.open for bar in impulse):
        raise ValueError("impulse bullish count mismatch")
    expected_inner = sum(box_low + 0.2 * box_width <= bar.close <= box_high - 0.2 * box_width for bar in distribution)
    expected_overlap = sum(
        max(0.0, min(first.high, second.high) - max(first.low, second.low))
        / min(first.high - first.low, second.high - second.low) >= 0.25
        for first, second in zip(distribution, distribution[1:])
    )
    if row["box_inner_close_count"] != expected_inner or row["box_overlap_pair_count"] != expected_overlap:
        raise ValueError("box count mismatch")
    raw_stop = max(reclaim.high, box_low) + 0.25 * a_reclaim
    structural_stop = normalize_up(raw_stop, contract)
    risk_exit_price = normalize_up(structural_stop + contract.tick_size, contract)
    _close(row["raw_structural_stop"], raw_stop, "raw_structural_stop")
    _close(row["structural_stop"], structural_stop, "structural_stop")
    _close(row["risk_exit_price"], risk_exit_price, "risk_exit_price")
    _close(row["stop_points"], (risk_exit_price - entry.bid) / contract.point, "stop_points")
    if structural_stop <= entry.ask or risk_exit_price - entry.ask < max(contract.stops_level, contract.freeze_level) * contract.point:
        raise ValueError("initial stop validity mismatch")
    _close(row["minimum_contract_risk_usd"], minimum_contract_risk(entry.bid, risk_exit_price, contract), "minimum_contract_risk_usd")
    contract_fields = {
        "volume_min": contract.volume_min, "volume_step": contract.volume_step,
        "contract_size": contract.contract_size, "tick_size": contract.tick_size,
        "tick_value_loss": contract.tick_value_loss, "point": contract.point, "digits": contract.digits,
    }
    if any(row[key] != expected for key, expected in contract_fields.items()):
        raise ValueError("contract snapshot mismatch")


def validate_funnel(
    funnel: dict[str, int], rows: Sequence[dict[str, Any]], anchors: Sequence[TerminalAnchor],
    incidence: Mapping[str, object],
) -> None:
    if set(funnel) != set(TERMINAL_STATUSES) or any(value < 0 for value in funnel.values()):
        raise ValueError("invalid terminal funnel")
    if funnel["RAW_OPPORTUNITY_AVAILABLE"] != len(rows):
        raise ValueError("raw funnel count mismatch")
    if sum(funnel.values()) != len(anchors):
        raise ValueError("eligible anchor reconciliation mismatch")
    for status in TERMINAL_STATUSES:
        if funnel[status] != sum(anchor.status == status for anchor in anchors):
            raise ValueError("terminal anchor status mismatch")
    if dict(incidence) != incidence_report(rows):
        raise ValueError("reference/deployment incidence mismatch")


def validate_prefix_invariance(
    prefix_rows: Sequence[dict[str, Any]], extended_rows: Sequence[dict[str, Any]], *, prefix_end: datetime | None = None,
) -> None:
    """All previously emitted identities and fields must survive an appended market suffix."""
    by_id = {row["candidate_id"]: row for row in extended_rows}
    for row in prefix_rows:
        if by_id.get(row["candidate_id"]) != row:
            raise ValueError("prefix invariance failure")
    if prefix_end is not None:
        prefix_ids = {row["candidate_id"] for row in prefix_rows}
        if any(
            datetime.fromisoformat(str(row["entry_tick_time"])) <= prefix_end and row["candidate_id"] not in prefix_ids
            for row in extended_rows
        ):
            raise ValueError("extension created an opportunity inside the prefix horizon")


def validate_detector_prefix_invariance(
    detector: Callable[..., Detection], prefix_inputs: Mapping[str, object], extended_inputs: Mapping[str, object],
    *, prefix_end: datetime,
) -> None:
    """Rerun the detector and compare every terminal decision fully owned by the prefix."""
    prefix = detector(**prefix_inputs)
    extended = detector(**extended_inputs)
    stable_prefix = {
        anchor.anchor_time: anchor for anchor in prefix.anchors
        if anchor.horizon_end is not None and anchor.horizon_end <= prefix_end
    }
    extended_by_anchor = {anchor.anchor_time: anchor for anchor in extended.anchors}
    for anchor_time, anchor in stable_prefix.items():
        if extended_by_anchor.get(anchor_time) != anchor:
            raise ValueError("detector terminal prefix invariance failure")
    stable_rows = [row for row in prefix.rows if datetime.fromisoformat(str(row["entry_tick_time"])) <= prefix_end]
    validate_prefix_invariance(stable_rows, extended.rows, prefix_end=prefix_end)


def validate_lock_manifest(root: Path, manifest: Path) -> None:
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    for relative, expected in payload["artifacts"].items():
        path = root / relative
        if sha256(path) != expected["sha256"] or path.stat().st_size != expected["size_bytes"]:
            raise ValueError(f"lock manifest mismatch: {relative}")
    if any(payload["boundary"].get(key) for key in (
        "broker_action_authorized", "census_output_authorized_in_this_commit",
        "detector_code_authorized_in_this_commit", "h4_or_portfolio_join_authorized",
        "mt5_execution_authorized", "pnl_authorized",
    )):
        raise ValueError("lock boundary is not fail closed")


def validate_changed_files(paths: Sequence[str]) -> None:
    normalized = {path.replace("\\", "/") for path in paths}
    trimmed = {path.split("xau-usd/xauusd-phase1/", 1)[-1] for path in normalized}
    if not trimmed <= ALLOWED_C2_FILES:
        raise ValueError("R6-C2 touched a file outside the six-file boundary")
