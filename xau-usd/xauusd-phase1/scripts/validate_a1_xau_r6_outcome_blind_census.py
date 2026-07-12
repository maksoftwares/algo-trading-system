"""R6-C2 structural validators; no real-evidence generation surface."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from jsonschema import Draft202012Validator

from build_a1_xau_r6_distribution_break_failed_reclaim_census import (
    RULE_SHA256,
    RULE_VERSION,
    TERMINAL_STATUSES,
    FROM_INCLUSIVE,
    TO_EXCLUSIVE,
    Detection,
    PrefixCutoff,
    RowContext,
    TerminalAnchor,
    TickStreamContract,
    broker_time,
    canonical_ids,
    classify_router,
    detect_structural_windows,
    incidence_report,
    iter_attested_c3_ticks,
    locked_final_status,
    minimum_contract_risk,
    normalize_up,
    parse_c3_market_payload,
    resolve_tick_stream,
    risk_at_or_below,
    select_entry_tick,
    serialize_evidence_package,
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
    "tests/fixtures/A1_XAU_R6_ROUTER_V1_NATIVE_PARITY_V1.json",
    "tests/fixtures/A1_XAU_R6_ORDERCALCPROFIT_PARITY_V1.json",
    "tests/fixtures/A1_XAU_R6_NATIVE_FIXTURE_MANIFEST_V1.json",
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
    if row["reference_risk_feasible"] != risk_at_or_below(float(row["minimum_contract_risk_usd"]), 25.0):
        raise ValueError("reference risk flag mismatch")
    if row["deployment_risk_feasible"] != risk_at_or_below(float(row["minimum_contract_risk_usd"]), 2.5):
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
    if not (
        distribution[-1].close >= box_low
        and breakdown.close <= box_low - 0.1 * a_box
        and breakdown.close < breakdown.open
        and reclaim.high >= box_low - 0.1 * a_reclaim
        and reclaim.close <= box_low - 0.05 * a_reclaim
        and reclaim.close < reclaim.open
        and entry.session_open
    ):
        raise ValueError("locked directional predicate mismatch")
    selected, status, last_reclaim, _, complete = select_entry_tick(
        context.causal_ticks, reclaim_time=reclaim.time, decision_time=decision,
    )
    if not complete or status != "RAW_OPPORTUNITY_AVAILABLE" or selected != entry or last_reclaim != context.last_reclaim_tick_sequence:
        raise ValueError("entry tick was not the first causal eligible tick")
    # The detector's router decision is the next native H4 open, represented by
    # the first router H4 bar strictly after the breakdown bar.
    router_decision = next((bar.time for bar in context.router_h4 if bar.time > breakdown.time), None)
    if router_decision is None:
        raise ValueError("router decision boundary unavailable")
    recomputed_router = classify_router(
        h1=context.router_h1, h4=context.router_h4, d1=context.router_d1, decision=router_decision,
    )
    if row["router_state"] != recomputed_router or recomputed_router not in {"UPTREND", "CHOP"}:
        raise ValueError("router state mismatch")


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
    raw_anchor_ids = [anchor.candidate_id for anchor in anchors if anchor.status == "RAW_OPPORTUNITY_AVAILABLE"]
    row_ids = [str(row["candidate_id"]) for row in rows]
    if raw_anchor_ids != row_ids or any(
        anchor.candidate_id is not None for anchor in anchors if anchor.status != "RAW_OPPORTUNITY_AVAILABLE"
    ):
        raise ValueError("raw row to terminal anchor reconciliation mismatch")
    if dict(incidence) != incidence_report(rows):
        raise ValueError("reference/deployment incidence mismatch")


def validate_prefix_invariance(
    prefix_rows: Sequence[dict[str, Any]], extended_rows: Sequence[dict[str, Any]], *, prefix_cutoff: PrefixCutoff | None = None,
) -> None:
    """All previously emitted identities and fields must survive an appended market suffix."""
    by_id = {row["candidate_id"]: row for row in extended_rows}
    for row in prefix_rows:
        if by_id.get(row["candidate_id"]) != row:
            raise ValueError("prefix invariance failure")
    if prefix_cutoff is not None:
        prefix_ids = {row["candidate_id"] for row in prefix_rows}
        if any(
            (
                datetime.fromisoformat(str(row["entry_tick_time"])), int(row["entry_tick_sequence"])
            ) <= (prefix_cutoff.time, prefix_cutoff.sequence)
            and row["candidate_id"] not in prefix_ids
            for row in extended_rows
        ):
            raise ValueError("extension created an opportunity inside the prefix horizon")


def validate_detector_prefix_invariance(
    detector: Callable[..., Detection], prefix_inputs: Mapping[str, object], extended_inputs: Mapping[str, object],
    *, prefix_cutoff: PrefixCutoff,
) -> None:
    """Rerun the detector and compare every terminal decision fully owned by the prefix."""
    prefix = detector(**prefix_inputs)
    extended = detector(**extended_inputs)
    stable_prefix = tuple(
        anchor for anchor in prefix.anchors if _anchor_owned_by_cutoff(anchor, prefix_cutoff)
    )
    stable_extended = tuple(
        anchor for anchor in extended.anchors if _anchor_owned_by_cutoff(anchor, prefix_cutoff)
    )
    if stable_prefix != stable_extended:
        raise ValueError("detector terminal prefix invariance failure")
    stable_rows = [
        row for row in prefix.rows
        if (datetime.fromisoformat(str(row["entry_tick_time"])), int(row["entry_tick_sequence"]))
        <= (prefix_cutoff.time, prefix_cutoff.sequence)
    ]
    validate_prefix_invariance(stable_rows, extended.rows, prefix_cutoff=prefix_cutoff)


def _anchor_owned_by_cutoff(anchor: TerminalAnchor, cutoff: PrefixCutoff) -> bool:
    if anchor.horizon_end is None:
        return False
    if anchor.horizon_end != cutoff.time:
        return anchor.horizon_end < cutoff.time
    return anchor.horizon_sequence is None or anchor.horizon_sequence <= cutoff.sequence


def validate_detection(detection: Detection, schema: dict[str, Any]) -> None:
    candidate_ids = [str(row["candidate_id"]) for row in detection.rows]
    if len(candidate_ids) != len(set(candidate_ids)) or set(candidate_ids) != set(detection.contexts):
        raise ValueError("detection context reconciliation mismatch")
    for field in ("box_id", "episode_id"):
        values = [str(row[field]) for row in detection.rows]
        if len(values) != len(set(values)):
            raise ValueError(f"duplicate {field} ownership")
    for row in detection.rows:
        validate_row(dict(row), schema, detection.contexts[str(row["candidate_id"])])
    validate_funnel(detection.funnel, detection.rows, detection.anchors, detection.incidence)
    if detection.final_status != locked_final_status(detection.incidence):
        raise ValueError("locked final status mismatch")


def validate_native_fixture_manifest(root: Path, manifest: Path) -> dict[str, Any]:
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    expected = {
        "tests/fixtures/A1_XAU_R6_ROUTER_V1_NATIVE_PARITY_V1.json",
        "tests/fixtures/A1_XAU_R6_ORDERCALCPROFIT_PARITY_V1.json",
    }
    if set(payload.get("fixtures", {})) != expected:
        raise ValueError("native fixture set mismatch")
    for relative, metadata in payload["fixtures"].items():
        path = root / relative
        normalized = path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
        if hashlib.sha256(normalized).hexdigest() != metadata["sha256"] or len(normalized) != metadata["size_bytes"]:
            raise ValueError("native fixture hash mismatch")
    for evidence in payload.get("native_evidence_roots", []):
        path = root / evidence["path"]
        if sha256(path) != evidence["sha256"]:
            raise ValueError("native provenance root mismatch")
    return payload


def validate_c3_input_manifest(manifest: Mapping[str, Any], bars_content: bytes) -> None:
    required_top = {
        "schema_version", "generator", "timestamp_basis", "warmup", "data", "tick_stream",
        "contract_identity", "inputs",
    }
    if set(manifest) != required_top or manifest["schema_version"] != "a1_xau_r6_c3_input_manifest_v1":
        raise ValueError("C3 input manifest schema mismatch")
    if manifest["timestamp_basis"] != "BROKER_SERVER_WALL_CLOCK":
        raise ValueError("C3 timestamp basis mismatch")
    generator = manifest["generator"]
    if set(generator) != {"commit", "tree"} or any(
        len(generator[key]) != 40 or any(char not in "0123456789abcdef" for char in generator[key])
        for key in generator
    ):
        raise ValueError("C3 generator identity mismatch")
    warmup = manifest["warmup"]
    if set(warmup) != {"h1_bars", "h4_bars", "d1_bars", "from_inclusive", "decision_from_inclusive"}:
        raise ValueError("C3 warm-up contract mismatch")
    if any(int(warmup[key]) <= 0 for key in ("h1_bars", "h4_bars", "d1_bars")):
        raise ValueError("C3 warm-up counts invalid")
    if warmup["h1_bars"] < 25 or warmup["h4_bars"] < 61 or warmup["d1_bars"] < 277:
        raise ValueError("C3 Router warm-up is insufficient")
    data = manifest["data"]
    if set(data) != {
        "from_inclusive", "to_exclusive", "h1_bar_count", "h4_bar_count", "d1_bar_count",
        "h1_gap_count", "h4_gap_count", "d1_gap_count",
    }:
        raise ValueError("C3 data contract mismatch")
    if data["from_inclusive"] != "2016-07-01T00:00:00" or data["to_exclusive"] != "2026-07-01T00:00:00":
        raise ValueError("C3 locked interval mismatch")
    if any(int(data[key]) <= 0 for key in ("h1_bar_count", "h4_bar_count", "d1_bar_count")):
        raise ValueError("C3 bar counts invalid")
    if any(int(data[key]) != 0 for key in ("h1_gap_count", "h4_gap_count", "d1_gap_count")):
        raise ValueError("C3 source gap audit failed")
    tick = manifest["tick_stream"]
    if set(tick) != {
        "format", "count", "first_sequence", "last_sequence", "gap_count", "session_open_required",
        "source_h1_bar_time_required", "first_time", "last_time",
    }:
        raise ValueError("C3 tick stream contract mismatch")
    if (
        tick["format"] != "ndjson_utf8"
        or tick["count"] <= 0
        or tick["gap_count"] != 0
        or not tick["session_open_required"]
        or not tick["source_h1_bar_time_required"]
        or tick["last_sequence"] - tick["first_sequence"] + 1 != tick["count"]
        or datetime.fromisoformat(tick["first_time"]) > datetime.fromisoformat(data["from_inclusive"])
        or datetime.fromisoformat(tick["last_time"]) < datetime.fromisoformat(data["to_exclusive"])
    ):
        raise ValueError("C3 tick completeness mismatch")
    contract = manifest["contract_identity"]
    if set(contract) != {"server", "symbol", "account_currency", "snapshot_sha256"} or any(
        not contract[key] for key in ("server", "symbol", "account_currency")
    ) or len(contract["snapshot_sha256"]) != 64 or any(
        char not in "0123456789abcdef" for char in contract["snapshot_sha256"]
    ):
        raise ValueError("C3 contract identity mismatch")
    expected_inputs = {"A1_XAU_R6_C3_BARS_CONTRACT.json", "A1_XAU_R6_C3_TICKS.ndjson"}
    if set(manifest["inputs"]) != expected_inputs:
        raise ValueError("C3 input filenames mismatch")
    for metadata in manifest["inputs"].values():
        if (
            set(metadata) != {"sha256", "size_bytes"}
            or metadata["size_bytes"] <= 0
            or len(metadata["sha256"]) != 64
            or any(char not in "0123456789abcdef" for char in metadata["sha256"])
        ):
            raise ValueError("C3 input artifact metadata mismatch")
    bars_expected = manifest["inputs"]["A1_XAU_R6_C3_BARS_CONTRACT.json"]
    if hashlib.sha256(bars_content).hexdigest() != bars_expected["sha256"] or len(bars_content) != bars_expected["size_bytes"]:
        raise ValueError("C3 bars input manifest hash mismatch")


def validate_c3_parsed_market(market: Mapping[str, object], manifest: Mapping[str, Any]) -> None:
    data, warmup = manifest["data"], manifest["warmup"]
    for timeframe in ("h1", "h4", "d1"):
        bars = market[timeframe]
        if len(bars) != data[f"{timeframe}_bar_count"]:
            raise ValueError("C3 parsed bar count mismatch")
        if sum(bar.time < FROM_INCLUSIVE for bar in bars) < warmup[f"{timeframe}_bars"]:
            raise ValueError("C3 parsed warm-up mismatch")
    contract = market["contract"]
    identity = manifest["contract_identity"]
    snapshot = json.dumps(asdict(contract), sort_keys=True, separators=(",", ":")).encode("utf-8")
    if (
        contract.server != identity["server"]
        or contract.symbol != identity["symbol"]
        or contract.account_currency != identity["account_currency"]
        or hashlib.sha256(snapshot).hexdigest() != identity["snapshot_sha256"]
    ):
        raise ValueError("C3 parsed contract identity mismatch")


def run_c3_in_memory(
    *, manifest: Mapping[str, Any], bars_content: bytes, tick_lines: Iterable[bytes],
    row_schema: dict[str, Any], rule_manifest_sha256: str,
) -> tuple[Detection, dict[str, str]]:
    """Reviewed streaming runner. The caller alone decides whether artifacts are persisted."""
    validate_c3_input_manifest(manifest, bars_content)
    market = parse_c3_market_payload(bars_content.decode("utf-8"))
    validate_c3_parsed_market(market, manifest)
    tick_metadata = manifest["inputs"]["A1_XAU_R6_C3_TICKS.ndjson"]
    ticks = iter_attested_c3_ticks(
        tick_lines, expected_sha256=tick_metadata["sha256"],
        expected_size_bytes=tick_metadata["size_bytes"],
    )
    structural = detect_structural_windows(**market)
    stream = manifest["tick_stream"]
    detection = resolve_tick_stream(
        structural, ticks,
        stream_contract=TickStreamContract(stream["count"], stream["first_sequence"], stream["last_sequence"]),
    )
    validate_detection(detection, row_schema)
    manifest_sha = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    package = serialize_evidence_package(detection, {
        "generator_commit": manifest["generator"]["commit"],
        "generator_tree": manifest["generator"]["tree"],
        "input_manifest_sha256": manifest_sha,
        "rule_manifest_sha256": rule_manifest_sha256,
    }, row_fields=row_schema["required"])
    return detection, package


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
