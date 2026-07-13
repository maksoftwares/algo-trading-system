from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = "a1_xau_router_entry_hold_path_audit_v1"
CLASSIFIER_SCHEMA_VERSION = "a1_xau_router_path_classifier_v1"
AUDIT_ID = "A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_V1"

ROUTER_STATES = frozenset({"SHOCK", "UPTREND", "DOWNTREND", "COMPRESSION", "CHOP"})
STRUCTURAL_DIRECTIONS = frozenset({"UP", "DOWN", "NONE"})
M15_BREAK_DIRECTIONS = frozenset({"BULLISH", "BEARISH", "NONE"})

SOURCE_CONTRACT: dict[str, tuple[str, str, str, int, Decimal]] = {
    "h4_d1_long_best_box2_atr80": ("R1", "LONG", "UPTREND", 145, Decimal("7050.42")),
    "r1_h1_pullback_long_v1": ("R1", "LONG", "UPTREND", 413, Decimal("1665.94")),
    "r2_continuation_short_v1": ("R2", "SHORT", "DOWNTREND", 57, Decimal("589.46")),
    "r2_pullback_rejection_short_v1": ("R2", "SHORT", "DOWNTREND", 63, Decimal("334.23")),
}
EXPECTED_TRADE_COUNT = 678
EXPECTED_NET_USD = Decimal("9640.05")
FROZEN_DD_START = datetime.fromisoformat("2025-12-26 16:05:13")
FROZEN_DD_END = datetime.fromisoformat("2026-01-09 13:30:42")

RECONCILIATION_REQUIRED_CHECKS = frozenset(
    {
        "baseline_sha256_matches",
        "baseline_rows_equal_678",
        "unique_entry_deals_map_to_unique_native_positions",
        "legacy_exit_deal_mismatches_equal_388",
        "legacy_individual_pnl_mismatches_equal_387",
        "one_entry_and_one_exit_per_native_position",
        "full_volume_exit_without_partial_close_or_add_on",
        "namespaced_trade_ids_nonempty_and_unique",
        "native_and_legacy_exit_pnl_multisets_match",
        "source_counts_match",
        "source_pnl_cents_match",
        "aggregate_pnl_cents_match",
        "identity_and_timestamps_complete",
        "router_snapshots_complete",
        "eligible_h1_holding_snapshots_complete",
        "tick_and_event_order_evidence_complete",
        "no_future_bar_reads",
        "no_bar_zero_decisions",
        "all_snapshot_joins_are_backward_asof",
        "later_changes_observed_before_exit",
        "mt5_order_deal_trade_identities_match",
        "original_sl_and_deal_reason_claims_match",
        "initial_risk_calculations_match_to_cent",
        "entry_exit_commission_swap_fee_are_zero",
        "source_direction_and_regime_mappings_match",
        "all_artifact_and_source_hashes_match",
    }
)

PROHIBITED_CLASSIFIER_FIELDS = frozenset(
    {
        "final_r",
        "final_pnl",
        "final_pnl_usd",
        "profit",
        "is_winner",
        "is_loser",
        "mfe_r",
        "mae_r",
        "mfe_r_before_change",
        "mae_r_before_change",
        "unrealized_r_at_change",
        "post_change_r",
        "commission",
        "swap",
        "fee",
        "exit_month",
        "entry_month",
        "entry_year",
        "first_change_year",
        "drawdown_window_member",
    }
)


class PrimaryClass(str, Enum):
    DATA_OR_TIMESTAMP_ERROR = "DATA_OR_TIMESTAMP_ERROR"
    WRONG_ROUTER_ENTRY = "WRONG_ROUTER_ENTRY"
    TRANSITION_ENTRY = "TRANSITION_ENTRY"
    STALE_TREND_ENTRY = "STALE_TREND_ENTRY"
    CORRECT_ENTRY_LATER_REGIME_CHANGE = "CORRECT_ENTRY_LATER_REGIME_CHANGE"
    VALID_LOSS_IN_EXPECTED_REGIME = "VALID_LOSS_IN_EXPECTED_REGIME"
    CORRECT_ENTRY_STABLE_REGIME = "CORRECT_ENTRY_STABLE_REGIME"


class AuditStatus(str, Enum):
    INVALID_EVIDENCE = "ROUTER_PATH_INVALID_EVIDENCE"
    WRONG_ENTRY_DEFECT = "ROUTER_PATH_WRONG_ENTRY_DEFECT"
    STALE_ENTRY_V2_JUSTIFIED = "ROUTER_PATH_STALE_ENTRY_V2_JUSTIFIED"
    HOLDING_CHANGE_STUDY_JUSTIFIED = "ROUTER_PATH_HOLDING_CHANGE_STUDY_JUSTIFIED"
    VALID_NO_CHANGE = "ROUTER_PATH_VALID_NO_CHANGE"


class AuditEvidenceError(ValueError):
    """Raised when evidence cannot satisfy the preregistered fail-closed contract."""


@dataclass(frozen=True, order=True)
class EventKey:
    tester_time_msc: int
    callback_sequence: int
    event_sequence: int

    def __post_init__(self) -> None:
        if self.tester_time_msc < 0 or self.callback_sequence < 0 or self.event_sequence < 0:
            raise AuditEvidenceError("event-key values must be nonnegative")

    @classmethod
    def from_value(cls, value: Mapping[str, Any] | Sequence[int] | "EventKey") -> "EventKey":
        if isinstance(value, cls):
            return value
        if isinstance(value, Mapping):
            required = {"tester_time_msc", "callback_sequence", "event_sequence"}
            if set(value) != required:
                raise AuditEvidenceError(f"event key must contain exactly {sorted(required)}")
            return cls(
                int(value["tester_time_msc"]),
                int(value["callback_sequence"]),
                int(value["event_sequence"]),
            )
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and len(value) == 3:
            return cls(*(int(item) for item in value))
        raise AuditEvidenceError("invalid event key")


def _finite_decimal(value: Any, name: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise AuditEvidenceError(f"{name} is not a decimal") from exc
    if not result.is_finite():
        raise AuditEvidenceError(f"{name} must be finite")
    return result


def type7_quantile(values: Sequence[Any], probability: Decimal | float | str) -> Decimal:
    """Return the deterministic Type-7/linear quantile used by the frozen H1 rule."""

    if not values:
        raise AuditEvidenceError("quantile requires at least one value")
    p = _finite_decimal(probability, "probability")
    if p < 0 or p > 1:
        raise AuditEvidenceError("probability must be in [0, 1]")
    ordered = sorted(_finite_decimal(value, "quantile value") for value in values)
    h = Decimal(len(ordered) - 1) * p
    lower = int(h)
    upper = lower if h == lower else lower + 1
    weight = h - Decimal(lower)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


@dataclass(frozen=True)
class SnapshotFeatures:
    source_event_key: EventKey
    observation_event_key: EventKey
    d1_bar_available_key: EventKey
    h4_bar_available_key: EventKey
    h1_bar_available_key: EventKey
    m15_bar_available_key: EventKey
    m5_bar_available_key: EventKey
    minimum_bar_shift: int
    router_state: str
    d1_structural_direction: str
    h4_structural_direction: str
    h4_expected_stack: bool
    h1_close: Decimal
    h1_ema50: Decimal
    h1_ema20_slope_5_norm: Decimal
    h1_abs_slope_q80: Decimal
    h1_previous_close: Decimal
    h1_previous_ema50: Decimal
    h1_previous_ema20_slope_5_norm: Decimal
    h1_previous_abs_slope_q80: Decimal
    m15_structure_break: str

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "SnapshotFeatures":
        expected = {field.name for field in dataclasses.fields(cls)}
        _require_exact_fields(value, expected, "snapshot")
        key_names = {name for name in expected if name.endswith("_key")}
        decimal_names = {
            "h1_close",
            "h1_ema50",
            "h1_ema20_slope_5_norm",
            "h1_abs_slope_q80",
            "h1_previous_close",
            "h1_previous_ema50",
            "h1_previous_ema20_slope_5_norm",
            "h1_previous_abs_slope_q80",
        }
        converted = dict(value)
        for name in key_names:
            converted[name] = EventKey.from_value(value[name])
        for name in decimal_names:
            converted[name] = _finite_decimal(value[name], name)
        converted["minimum_bar_shift"] = int(value["minimum_bar_shift"])
        if type(value["h4_expected_stack"]) is not bool:
            raise AuditEvidenceError("h4_expected_stack must be a boolean")
        return cls(**converted)

    def errors(self) -> list[str]:
        errors: list[str] = []
        if self.minimum_bar_shift < 1:
            errors.append("bar-0 or future bar was used")
        if self.router_state not in ROUTER_STATES:
            errors.append("unknown router state")
        if self.d1_structural_direction not in STRUCTURAL_DIRECTIONS:
            errors.append("unknown D1 structural direction")
        if self.h4_structural_direction not in STRUCTURAL_DIRECTIONS:
            errors.append("unknown H4 structural direction")
        if self.m15_structure_break not in M15_BREAK_DIRECTIONS:
            errors.append("unknown or ambiguous M15 structure break")
        if self.h1_abs_slope_q80 < 0 or self.h1_previous_abs_slope_q80 < 0:
            errors.append("negative H1 slope threshold")
        if self.observation_event_key > self.source_event_key:
            errors.append("future snapshot observation")
        for name in (
            "d1_bar_available_key",
            "h4_bar_available_key",
            "h1_bar_available_key",
            "m15_bar_available_key",
            "m5_bar_available_key",
        ):
            if getattr(self, name) > self.source_event_key:
                errors.append(f"future {name}")
        return errors


@dataclass(frozen=True)
class PathObservation:
    observation_event_key: EventKey
    h1_bar_available_key: EventKey
    router_state: str
    minimum_bar_shift: int
    position_open: bool

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "PathObservation":
        expected = {field.name for field in dataclasses.fields(cls)}
        _require_exact_fields(value, expected, "path observation")
        if type(value["position_open"]) is not bool:
            raise AuditEvidenceError("position_open must be a boolean")
        return cls(
            observation_event_key=EventKey.from_value(value["observation_event_key"]),
            h1_bar_available_key=EventKey.from_value(value["h1_bar_available_key"]),
            router_state=str(value["router_state"]),
            minimum_bar_shift=int(value["minimum_bar_shift"]),
            position_open=value["position_open"],
        )


@dataclass(frozen=True)
class ClassifierInput:
    source_id: str
    component: str
    trade_id: str
    direction: str
    expected_regime: str
    signal_event_key: EventKey
    entry_deal_event_key: EventKey
    exit_deal_event_key: EventKey
    signal_snapshot: SnapshotFeatures
    entry_snapshot: SnapshotFeatures
    holding_path: tuple[PathObservation, ...]
    exit_snapshot: PathObservation
    path_complete: bool
    original_order_identity_complete: bool
    exit_is_exact_deal_reason_sl: bool
    original_sl_never_modified: bool

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ClassifierInput":
        expected = {field.name for field in dataclasses.fields(cls)}
        _require_exact_fields(value, expected, "classifier input")
        prohibited = {str(name).lower() for name in value}.intersection(PROHIBITED_CLASSIFIER_FIELDS)
        if prohibited:
            raise AuditEvidenceError(f"prohibited classifier fields: {sorted(prohibited)}")
        bool_names = {
            "path_complete",
            "original_order_identity_complete",
            "exit_is_exact_deal_reason_sl",
            "original_sl_never_modified",
        }
        for name in bool_names:
            if type(value[name]) is not bool:
                raise AuditEvidenceError(f"{name} must be a boolean")
        return cls(
            source_id=str(value["source_id"]),
            component=str(value["component"]),
            trade_id=str(value["trade_id"]),
            direction=str(value["direction"]),
            expected_regime=str(value["expected_regime"]),
            signal_event_key=EventKey.from_value(value["signal_event_key"]),
            entry_deal_event_key=EventKey.from_value(value["entry_deal_event_key"]),
            exit_deal_event_key=EventKey.from_value(value["exit_deal_event_key"]),
            signal_snapshot=SnapshotFeatures.from_dict(value["signal_snapshot"]),
            entry_snapshot=SnapshotFeatures.from_dict(value["entry_snapshot"]),
            holding_path=tuple(PathObservation.from_dict(item) for item in value["holding_path"]),
            exit_snapshot=PathObservation.from_dict(value["exit_snapshot"]),
            path_complete=value["path_complete"],
            original_order_identity_complete=value["original_order_identity_complete"],
            exit_is_exact_deal_reason_sl=value["exit_is_exact_deal_reason_sl"],
            original_sl_never_modified=value["original_sl_never_modified"],
        )


CLASSIFIER_INPUT_FIELDS = frozenset(field.name for field in dataclasses.fields(ClassifierInput))
CLASSIFIER_SCHEMA_FIELD_NAMES = frozenset(
    field.name
    for schema_type in (EventKey, SnapshotFeatures, PathObservation, ClassifierInput)
    for field in dataclasses.fields(schema_type)
)
if CLASSIFIER_SCHEMA_FIELD_NAMES.intersection(PROHIBITED_CLASSIFIER_FIELDS):  # pragma: no cover
    raise RuntimeError("classifier schema contains outcome fields")


@dataclass(frozen=True)
class Classification:
    trade_id: str
    primary_class: PrimaryClass
    transition_at_signal: bool
    transition_at_entry: bool
    stale_at_signal: bool
    stale_at_entry: bool
    first_regime_change_key: EventKey | None
    errors: tuple[str, ...]


def _require_exact_fields(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    missing = expected - actual
    extra = actual - expected
    if missing or extra:
        raise AuditEvidenceError(f"{label} schema mismatch; missing={sorted(missing)}, extra={sorted(extra)}")


def _trade_id_is_namespaced(trade_id: str) -> bool:
    parts = trade_id.split("::")
    return len(parts) == 6 and all(part and "::" not in part for part in parts)


def _expected_direction(regime: str) -> str:
    return "UP" if regime == "UPTREND" else "DOWN"


def _h1_strongly_opposed(snapshot: SnapshotFeatures, expected_regime: str, *, previous: bool = False) -> bool:
    prefix = "h1_previous_" if previous else "h1_"
    close = getattr(snapshot, f"{prefix}close")
    ema50 = getattr(snapshot, f"{prefix}ema50")
    slope = getattr(snapshot, f"{prefix}ema20_slope_5_norm")
    q80 = getattr(snapshot, f"{prefix}abs_slope_q80")
    if expected_regime == "UPTREND":
        return close < ema50 and slope <= -q80
    return close > ema50 and slope >= q80


def transition_predicate(snapshot: SnapshotFeatures, expected_regime: str) -> bool:
    expected = _expected_direction(expected_regime)
    directly_opposed = {snapshot.d1_structural_direction, snapshot.h4_structural_direction} == {"UP", "DOWN"}
    h4_lost_expected_stack = snapshot.d1_structural_direction == expected and not snapshot.h4_expected_stack
    aligned_with_expected = (
        snapshot.d1_structural_direction == expected and snapshot.h4_structural_direction == expected
    )
    two_h1_bars_opposed = _h1_strongly_opposed(snapshot, expected_regime) and _h1_strongly_opposed(
        snapshot, expected_regime, previous=True
    )
    return directly_opposed or h4_lost_expected_stack or (aligned_with_expected and two_h1_bars_opposed)


def stale_predicate(snapshot: SnapshotFeatures, expected_regime: str) -> bool:
    if expected_regime == "UPTREND":
        return (
            snapshot.h1_close < snapshot.h1_ema50
            or snapshot.h1_ema20_slope_5_norm <= -snapshot.h1_abs_slope_q80
            or snapshot.m15_structure_break == "BEARISH"
        )
    return (
        snapshot.h1_close > snapshot.h1_ema50
        or snapshot.h1_ema20_slope_5_norm >= snapshot.h1_abs_slope_q80
        or snapshot.m15_structure_break == "BULLISH"
    )


def validate_classifier_input(item: ClassifierInput) -> tuple[str, ...]:
    errors: list[str] = []
    contract = SOURCE_CONTRACT.get(item.source_id)
    if contract is None or (item.component, item.direction, item.expected_regime) != contract[:3]:
        errors.append("source/component/direction/expected-regime contract mismatch")
    if not _trade_id_is_namespaced(item.trade_id):
        errors.append("invalid namespaced trade ID")
    if not (item.signal_event_key <= item.entry_deal_event_key < item.exit_deal_event_key):
        errors.append("noncausal signal/entry/exit event order")
    if not item.path_complete:
        errors.append("holding path is incomplete")
    if not item.original_order_identity_complete:
        errors.append("original order identity is incomplete")
    for label, snapshot, source_key in (
        ("signal", item.signal_snapshot, item.signal_event_key),
        ("entry", item.entry_snapshot, item.entry_deal_event_key),
    ):
        if snapshot.source_event_key != source_key:
            errors.append(f"{label} snapshot source key mismatch")
        errors.extend(f"{label}: {error}" for error in snapshot.errors())

    previous_key = item.entry_deal_event_key
    previous_h1_key: EventKey | None = None
    for observation in item.holding_path:
        if observation.minimum_bar_shift < 1:
            errors.append("holding path used bar 0")
        if observation.router_state not in ROUTER_STATES:
            errors.append("holding path has unknown router state")
        if not observation.position_open:
            errors.append("holding path observation says position was closed")
        if not (item.entry_deal_event_key < observation.observation_event_key < item.exit_deal_event_key):
            errors.append("holding observation is outside open interval")
        if observation.observation_event_key <= previous_key:
            errors.append("holding observation keys are non-monotone")
        if observation.h1_bar_available_key > observation.observation_event_key:
            errors.append("holding observation uses a future H1 bar")
        if previous_h1_key is not None and observation.h1_bar_available_key <= previous_h1_key:
            errors.append("holding path repeats or reverses an H1 bar")
        previous_key = observation.observation_event_key
        previous_h1_key = observation.h1_bar_available_key

    exit_snapshot = item.exit_snapshot
    if exit_snapshot.minimum_bar_shift < 1:
        errors.append("exit snapshot used bar 0")
    if exit_snapshot.router_state not in ROUTER_STATES:
        errors.append("exit snapshot has unknown router state")
    if exit_snapshot.observation_event_key > item.exit_deal_event_key:
        errors.append("exit snapshot is after the exit deal")
    if exit_snapshot.h1_bar_available_key > exit_snapshot.observation_event_key:
        errors.append("exit snapshot uses a future H1 bar")
    return tuple(dict.fromkeys(errors))


def _first_change_key(item: ClassifierInput) -> EventKey | None:
    eligible = list(item.holding_path)
    if item.exit_snapshot.position_open and item.exit_snapshot.observation_event_key < item.exit_deal_event_key:
        eligible.append(item.exit_snapshot)
    for observation in sorted(eligible, key=lambda row: row.observation_event_key):
        if observation.router_state != item.expected_regime:
            return observation.observation_event_key
    return None


def classify_trade(item: ClassifierInput) -> Classification:
    errors = validate_classifier_input(item)
    transition_signal = False
    transition_entry = False
    stale_signal = False
    stale_entry = False
    first_change: EventKey | None = None
    if errors:
        primary = PrimaryClass.DATA_OR_TIMESTAMP_ERROR
    elif item.entry_snapshot.router_state != item.expected_regime:
        primary = PrimaryClass.WRONG_ROUTER_ENTRY
    else:
        transition_signal = transition_predicate(item.signal_snapshot, item.expected_regime)
        transition_entry = transition_predicate(item.entry_snapshot, item.expected_regime)
        stale_signal = stale_predicate(item.signal_snapshot, item.expected_regime)
        stale_entry = stale_predicate(item.entry_snapshot, item.expected_regime)
        if transition_signal or transition_entry:
            primary = PrimaryClass.TRANSITION_ENTRY
        elif stale_signal or stale_entry:
            primary = PrimaryClass.STALE_TREND_ENTRY
        else:
            first_change = _first_change_key(item)
            if first_change is not None:
                primary = PrimaryClass.CORRECT_ENTRY_LATER_REGIME_CHANGE
            elif item.exit_is_exact_deal_reason_sl and item.original_sl_never_modified:
                primary = PrimaryClass.VALID_LOSS_IN_EXPECTED_REGIME
            else:
                primary = PrimaryClass.CORRECT_ENTRY_STABLE_REGIME
    return Classification(
        trade_id=item.trade_id,
        primary_class=primary,
        transition_at_signal=transition_signal,
        transition_at_entry=transition_entry,
        stale_at_signal=stale_signal,
        stale_at_entry=stale_entry,
        first_regime_change_key=first_change,
        errors=errors,
    )


def _canonical(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return {field.name: _canonical(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, tuple):
        return [_canonical(item) for item in value]
    if isinstance(value, list):
        return [_canonical(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _canonical(item) for key, item in sorted(value.items())}
    return value


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def lock_classifications(items: Iterable[ClassifierInput]) -> tuple[list[Classification], str, str]:
    ordered = sorted(items, key=lambda item: item.trade_id)
    if len({item.trade_id for item in ordered}) != len(ordered):
        raise AuditEvidenceError("duplicate trade ID")
    classifications = [classify_trade(item) for item in ordered]
    class_input_sha256 = hashlib.sha256(
        canonical_json_bytes({"schema": CLASSIFIER_SCHEMA_VERSION, "trades": ordered})
    ).hexdigest()
    class_lock_sha256 = hashlib.sha256(
        canonical_json_bytes(
            {
                "schema": CLASSIFIER_SCHEMA_VERSION,
                "class_input_sha256": class_input_sha256,
                "assignments": [
                    {"trade_id": item.trade_id, "primary_class": item.primary_class.value}
                    for item in classifications
                ],
            }
        )
    ).hexdigest()
    return classifications, class_input_sha256, class_lock_sha256


def _parse_broker_datetime(value: Any, name: str) -> datetime:
    try:
        return datetime.fromisoformat(str(value))
    except ValueError as exc:
        raise AuditEvidenceError(f"invalid {name}") from exc


def _sum_decimal(rows: Iterable[Mapping[str, Any]], field: str) -> Decimal:
    return sum((_finite_decimal(row[field], field) for row in rows), Decimal("0"))


def _remove_worst_month(rows: list[Mapping[str, Any]], value_field: str, time_field: str) -> Decimal:
    by_month: dict[str, Decimal] = {}
    for row in rows:
        month = _parse_broker_datetime(row[time_field], time_field).strftime("%Y-%m")
        by_month[month] = by_month.get(month, Decimal("0")) + _finite_decimal(row[value_field], value_field)
    if not by_month:
        return Decimal("0")
    worst_month = min(by_month, key=lambda month: (by_month[month], month))
    return sum((value for month, value in by_month.items() if month != worst_month), Decimal("0"))


def _outside_frozen_dd(rows: list[Mapping[str, Any]], value_field: str, time_field: str) -> Decimal:
    total = Decimal("0")
    for row in rows:
        timestamp = _parse_broker_datetime(row[time_field], time_field)
        if not (FROZEN_DD_START <= timestamp <= FROZEN_DD_END):
            total += _finite_decimal(row[value_field], value_field)
    return total


def stale_entry_gates(
    assignments: Sequence[Classification], outcomes: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    class_by_id = {item.trade_id: item.primary_class for item in assignments}
    specialist_losses = [row for row in outcomes.values() if _finite_decimal(row["final_pnl_usd"], "final_pnl_usd") < 0]
    stale = [outcomes[trade_id] for trade_id, cls in class_by_id.items() if cls is PrimaryClass.STALE_TREND_ENTRY]
    stale_losses = [row for row in stale if _finite_decimal(row["final_pnl_usd"], "final_pnl_usd") < 0]
    net_r = _sum_decimal(stale, "final_r")
    gross_positive = sum((max(_finite_decimal(row["final_r"], "final_r"), Decimal("0")) for row in stale), Decimal("0"))
    gross_negative = abs(
        sum((min(_finite_decimal(row["final_r"], "final_r"), Decimal("0")) for row in stale), Decimal("0"))
    )
    profit_factor = gross_positive / gross_negative if gross_negative > 0 else None
    by_year: dict[int, Decimal] = {}
    for row in stale:
        year = _parse_broker_datetime(row["entry_time_broker"], "entry_time_broker").year
        by_year[year] = by_year.get(year, Decimal("0")) + _finite_decimal(row["final_r"], "final_r")
    loss_ratio = Decimal(len(stale_losses)) / Decimal(len(specialist_losses)) if specialist_losses else Decimal("0")
    checks = {
        "stale_loss_ratio_gte_15pct": loss_ratio >= Decimal("0.15"),
        "stale_net_r_negative": net_r < 0,
        "stale_pf_below_one": profit_factor is not None and profit_factor < 1,
        "stale_count_gte_30": len(stale) >= 30,
        "stale_negative_in_three_entry_years": sum(value < 0 for value in by_year.values()) >= 3,
        "stale_negative_without_worst_entry_month": _remove_worst_month(stale, "final_r", "entry_time_broker") < 0,
        "stale_negative_outside_frozen_dd": _outside_frozen_dd(stale, "final_r", "entry_time_broker") < 0,
    }
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "count": len(stale),
        "losing_count": len(stale_losses),
        "all_specialist_losing_count": len(specialist_losses),
        "loss_ratio": str(loss_ratio),
        "net_r": str(net_r),
        "profit_factor": None if profit_factor is None else str(profit_factor),
        "entry_year_net_r": {str(year): str(value) for year, value in sorted(by_year.items())},
    }


def holding_change_gates(
    assignments: Sequence[Classification], outcomes: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    changed = [
        outcomes[item.trade_id]
        for item in assignments
        if item.primary_class is PrimaryClass.CORRECT_ENTRY_LATER_REGIME_CHANGE
    ]
    net_r = _sum_decimal(changed, "post_change_r")
    by_year: dict[int, Decimal] = {}
    for row in changed:
        year = _parse_broker_datetime(row["first_regime_change_time_broker"], "first_regime_change_time_broker").year
        by_year[year] = by_year.get(year, Decimal("0")) + _finite_decimal(row["post_change_r"], "post_change_r")
    checks = {
        "changed_count_gte_30": len(changed) >= 30,
        "post_change_net_r_negative": net_r < 0,
        "post_change_negative_in_three_years": sum(value < 0 for value in by_year.values()) >= 3,
        "post_change_negative_without_worst_change_month": _remove_worst_month(
            changed, "post_change_r", "first_regime_change_time_broker"
        )
        < 0,
        "post_change_negative_outside_frozen_dd": _outside_frozen_dd(
            changed, "post_change_r", "first_regime_change_time_broker"
        )
        < 0,
    }
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "count": len(changed),
        "net_r": str(net_r),
        "first_change_year_net_r": {str(year): str(value) for year, value in sorted(by_year.items())},
    }


def select_status(
    *, evidence_valid: bool, assignments: Sequence[Classification], stale_pass: bool, holding_pass: bool
) -> AuditStatus:
    if not evidence_valid or any(item.primary_class is PrimaryClass.DATA_OR_TIMESTAMP_ERROR for item in assignments):
        return AuditStatus.INVALID_EVIDENCE
    if any(item.primary_class is PrimaryClass.WRONG_ROUTER_ENTRY for item in assignments):
        return AuditStatus.WRONG_ENTRY_DEFECT
    if stale_pass:
        return AuditStatus.STALE_ENTRY_V2_JUSTIFIED
    if holding_pass:
        return AuditStatus.HOLDING_CHANGE_STUDY_JUSTIFIED
    return AuditStatus.VALID_NO_CHANGE


def frozen_control_reconciliation(
    items: Sequence[ClassifierInput], outcomes: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    counts = {source_id: 0 for source_id in SOURCE_CONTRACT}
    pnl = {source_id: Decimal("0") for source_id in SOURCE_CONTRACT}
    errors: list[str] = []
    for item in items:
        if item.source_id not in counts:
            errors.append(f"unknown source: {item.source_id}")
            continue
        counts[item.source_id] += 1
        try:
            pnl[item.source_id] += _finite_decimal(outcomes[item.trade_id]["final_pnl_usd"], "final_pnl_usd")
        except KeyError:
            errors.append(f"missing final P/L outcome: {item.trade_id}")
    count_match = all(counts[source] == contract[3] for source, contract in SOURCE_CONTRACT.items())
    pnl_match = all(pnl[source] == contract[4] for source, contract in SOURCE_CONTRACT.items())
    aggregate = sum(pnl.values(), Decimal("0"))
    if len(items) != EXPECTED_TRADE_COUNT:
        errors.append(f"expected {EXPECTED_TRADE_COUNT} trades, found {len(items)}")
    if not count_match:
        errors.append("source counts do not match the frozen control")
    if not pnl_match:
        errors.append("source P/L cents do not match the frozen control")
    if aggregate != EXPECTED_NET_USD:
        errors.append("aggregate P/L cents do not match the frozen control")
    return {
        "pass": not errors,
        "trade_count": len(items),
        "source_counts": counts,
        "source_pnl_usd": {source: str(value) for source, value in pnl.items()},
        "aggregate_pnl_usd": str(aggregate),
        "errors": errors,
    }


def analyze_evidence(payload: Mapping[str, Any]) -> dict[str, Any]:
    required = {"schema_version", "audit_id", "provenance_id", "reconciliation", "trades"}
    _require_exact_fields(payload, required, "audit evidence")
    if payload["schema_version"] != SCHEMA_VERSION or payload["audit_id"] != AUDIT_ID:
        raise AuditEvidenceError("audit schema or ID mismatch")
    items: list[ClassifierInput] = []
    outcomes: dict[str, Mapping[str, Any]] = {}
    for record in payload["trades"]:
        _require_exact_fields(record, {"classifier_input", "outcome"}, "trade evidence")
        item = ClassifierInput.from_dict(record["classifier_input"])
        items.append(item)
        if item.trade_id in outcomes:
            raise AuditEvidenceError("duplicate outcome trade ID")
        outcomes[item.trade_id] = record["outcome"]
    assignments, class_input_sha, class_lock_sha = lock_classifications(items)
    reconciliation = payload["reconciliation"]
    if not isinstance(reconciliation, Mapping):
        raise AuditEvidenceError("reconciliation must be a mapping")
    _require_exact_fields(reconciliation, {"all_valid", "checks", "details"}, "reconciliation")
    if type(reconciliation["all_valid"]) is not bool or not isinstance(reconciliation["checks"], Mapping):
        raise AuditEvidenceError("reconciliation all_valid/checks types are invalid")
    checks = reconciliation["checks"]
    _require_exact_fields(checks, set(RECONCILIATION_REQUIRED_CHECKS), "reconciliation checks")
    if any(type(value) is not bool for value in checks.values()):
        raise AuditEvidenceError("every reconciliation check must be a boolean")
    recomputed_all_valid = all(checks.values())
    if reconciliation["all_valid"] is not recomputed_all_valid:
        raise AuditEvidenceError("reconciliation all_valid disagrees with its checks")
    frozen_controls = frozen_control_reconciliation(items, outcomes)
    evidence_valid = recomputed_all_valid and bool(frozen_controls["pass"])
    stale = stale_entry_gates(assignments, outcomes)
    holding = holding_change_gates(assignments, outcomes)
    status = select_status(
        evidence_valid=evidence_valid,
        assignments=assignments,
        stale_pass=bool(stale["pass"]),
        holding_pass=bool(holding["pass"]),
    )
    counts = {primary.value: 0 for primary in PrimaryClass}
    for item in assignments:
        counts[item.primary_class.value] += 1
    return {
        "schema_version": SCHEMA_VERSION,
        "audit_id": AUDIT_ID,
        "provenance_id": str(payload["provenance_id"]),
        "input_sha256": hashlib.sha256(canonical_json_bytes(payload)).hexdigest(),
        "classifier_schema_version": CLASSIFIER_SCHEMA_VERSION,
        "class_input_sha256": class_input_sha,
        "class_lock_sha256": class_lock_sha,
        "outcomes_unsealed_after_class_lock": True,
        "classifier_input_fields": sorted(CLASSIFIER_INPUT_FIELDS),
        "classifier_schema_field_names": sorted(CLASSIFIER_SCHEMA_FIELD_NAMES),
        "prohibited_classifier_fields": sorted(PROHIBITED_CLASSIFIER_FIELDS),
        "trade_count": len(items),
        "reconciliation": _canonical(reconciliation),
        "frozen_control_reconciliation": frozen_controls,
        "class_counts": counts,
        "assignments": [_canonical(item) for item in assignments],
        "stale_entry_gates": stale,
        "holding_change_gates": holding,
        "status": status.value,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offline, outcome-sealed A1 XAU Router V1 path analyzer")
    parser.add_argument("--input-json", type=Path, required=True, help="immutable normalized audit evidence")
    parser.add_argument("--output-json", type=Path, required=True, help="analysis JSON to create")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = json.loads(args.input_json.read_text(encoding="utf-8"))
    result = analyze_evidence(payload)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
