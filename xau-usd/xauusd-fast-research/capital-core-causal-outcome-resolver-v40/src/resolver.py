from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "capital_core_causal_outcome_resolver_v40.json"
FORWARD_START = pd.Timestamp("2026-07-20T00:00:00Z")
FINAL_STATUSES = frozenset(("EXECUTED", "REJECTED"))
STREAMS = ("v28", "v29", "v34")

V28_FIELDS = frozenset(
    (
        "candidate_id",
        "source_candidate_id",
        "specialist_id",
        "composite_id",
        "origin_attempt",
        "origin_variant_id",
        "regime_owner",
        "mechanic",
        "signal_time_utc",
        "scheduled_entry_time_utc",
        "direction",
        "direction_sign",
        "signal_atr",
        "stop_atr",
        "hold_hours",
        "parameters_json",
        "rule_dependency_sha256",
        "trade_permission",
        "broker_action_allowed",
        "python_execution_authorized",
    )
)
V29_FIELDS = frozenset(
    (
        "candidate_id",
        "specialist_id",
        "decision_time_utc",
        "confirmation_bar_time_utc",
        "direction",
        "signal_reason",
        "regime",
        "stop_points",
        "break_distance_atr",
        "estimated_cost_r",
        "spread_points",
        "rule_dependency_sha256",
        "trade_permission",
        "broker_action_allowed",
        "python_execution_authorized",
    )
)
V34_FIELDS = frozenset(
    (
        "candidate_id",
        "component_priority",
        "origin_attempt",
        "origin_variant_id",
        "regime_owner",
        "mechanic",
        "geometry_id",
        "signal_time_utc",
        "scheduled_entry_time_utc",
        "direction_sign",
        "direction",
        "signal_atr",
        "stop_atr",
        "target_r",
        "hold_hours",
        "source_feed",
        "economic_outcome_opened",
        "rule_dependency_sha256",
    )
)
FIELDS_BY_STREAM = {"v28": V28_FIELDS, "v29": V29_FIELDS, "v34": V34_FIELDS}
FORBIDDEN_OUTCOME_FIELDS = frozenset(
    (
        "entry_price",
        "exit_price",
        "entry_time_utc",
        "exit_time_utc",
        "gross_r",
        "stress_net_r",
        "resolution_status",
        "rejection_reason",
    )
)


@dataclass(frozen=True)
class Probe:
    outcome: dict[str, Any] | None
    rejection: str | None
    waiting: str | None
    evidence_end_ms: int
    entry_time: pd.Timestamp | None


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_V38 = load_module(
    "capital_core_v40_v38_utils",
    REPO_ROOT
    / "xau-usd/xauusd-fast-research/capital-r5-causal-outcome-resolver-v38/src/resolver.py",
)
Quote = _V38.Quote
FrameTickStore = _V38.FrameTickStore
atomic_write_json = _V38.atomic_write_json
canonical_sha256 = _V38.canonical_sha256
latest_observed_timestamp_ms = _V38.latest_observed_timestamp_ms
load_tick_snapshots = _V38.load_tick_snapshots
quote_slice_evidence = _V38.quote_slice_evidence
sha256_bytes = _V38.sha256_bytes
sha256_file = _V38.sha256_file
stable_line_prefix = _V38.stable_line_prefix
utc_text = _V38.utc_text
utc_timestamp = _V38.utc_timestamp


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _repo_path(repo_root: Path, relative: str) -> Path:
    path = Path(relative)
    return path if path.is_absolute() else repo_root / path


def verify_contract(
    config: Mapping[str, Any],
    repo_root: Path = REPO_ROOT,
    package_root: Path = ROOT,
) -> dict[str, Any]:
    path = (
        package_root
        / config["outputs"]["directory"]
        / config["outputs"]["contract_lock"]
    )
    if not path.is_file():
        raise FileNotFoundError("V40 contract lock is absent")
    lock = read_json(path)
    signed = dict(lock)
    observed = str(signed.pop("contract_sha256", ""))
    if observed != canonical_sha256(signed):
        raise ValueError("V40 contract payload hash is invalid")
    for relative, expected in lock["package_files"].items():
        source = package_root / relative
        if not source.is_file() or int(source.stat().st_size) != int(expected["bytes"]):
            raise ValueError(f"V40 package file identity changed: {relative}")
        if sha256_file(source) != str(expected["sha256"]):
            raise ValueError(f"V40 package file hash changed: {relative}")
    for relative, expected in lock["dependencies"].items():
        source = _repo_path(repo_root, relative)
        if not source.is_file() or int(source.stat().st_size) != int(expected["bytes"]):
            raise ValueError(f"V40 dependency identity changed: {relative}")
        if sha256_file(source) != str(expected["sha256"]):
            raise ValueError(f"V40 dependency hash changed: {relative}")
    return lock


def validate_frozen_identity(
    config: Mapping[str, Any], repo_root: Path = REPO_ROOT
) -> None:
    for stream in STREAMS:
        identity = config["frozen_identity"][stream]
        lock = read_json(_repo_path(repo_root, str(identity["contract_lock"])))
        if str(lock.get("contract_sha256")) != str(identity["contract_sha256"]):
            raise ValueError(f"V40 {stream} source contract changed")
        if str(lock.get("rule_dependency_sha256")) != str(
            identity["rule_dependency_sha256"]
        ):
            raise ValueError(f"V40 {stream} rule dependency changed")


def validate_historical_parity_artifact(
    config: Mapping[str, Any], contract: Mapping[str, Any], package_root: Path = ROOT
) -> dict[str, Any]:
    path = (
        package_root
        / config["outputs"]["directory"]
        / config["outputs"]["historical_semantic_parity"]
    )
    if not path.is_file():
        raise FileNotFoundError("V40 historical semantic parity artifact is absent")
    parity = read_json(path)
    if str(parity.get("contract_sha256")) != str(contract["contract_sha256"]):
        raise ValueError("V40 parity artifact belongs to another contract")
    if not bool(parity.get("semantic_parity_passed")):
        raise ValueError("V40 historical semantic parity did not pass")
    return parity


def _source_candidate_id(attempt: int, signal_time: pd.Timestamp) -> str:
    payload = f"{attempt}|{signal_time.isoformat()}".encode("ascii")
    return hashlib.sha256(payload).hexdigest()[:24]


def _v28_candidate_id(source_id: str, dependency_sha: str) -> str:
    payload = f"V28|{source_id}|{dependency_sha}".encode("ascii")
    return hashlib.sha256(payload).hexdigest()[:32]


def _v29_candidate_id(decision_time: pd.Timestamp, dependency_sha: str) -> str:
    payload = (
        f"V29|R1_PULLBACK_LONG|{utc_text(decision_time)}|{dependency_sha}"
    ).encode("ascii")
    return hashlib.sha256(payload).hexdigest()[:32]


def candidate_fact_sha256(record: Mapping[str, Any]) -> str:
    return canonical_sha256({key: record[key] for key in sorted(record)})


def _require_false(
    record: Mapping[str, Any], fields: Sequence[str], stream: str
) -> None:
    for field in fields:
        if bool(record[field]):
            raise ValueError(f"V40 {stream} candidate enables {field}")


def validate_candidate(
    stream: str, record: Mapping[str, Any], config: Mapping[str, Any]
) -> dict[str, Any]:
    if stream not in STREAMS:
        raise ValueError(f"V40 unknown stream: {stream}")
    expected_fields = FIELDS_BY_STREAM[stream]
    if frozenset(record) != expected_fields:
        missing = sorted(expected_fields.difference(record))
        extra = sorted(set(record).difference(expected_fields))
        raise ValueError(
            f"V40 {stream} candidate schema changed; missing={missing}, extra={extra}"
        )
    if set(record).intersection(FORBIDDEN_OUTCOME_FIELDS):
        raise ValueError(f"V40 {stream} candidate contains an economic outcome")
    identity = config["frozen_identity"][stream]
    dependency = str(identity["rule_dependency_sha256"])
    if str(record["rule_dependency_sha256"]) != dependency:
        raise ValueError(f"V40 {stream} candidate rule dependency changed")

    normalized = dict(record)
    if stream == "v29":
        signal = utc_timestamp(record["decision_time_utc"])
        scheduled = signal
        confirmation = utc_timestamp(record["confirmation_bar_time_utc"])
        if confirmation != signal - pd.Timedelta(minutes=15):
            raise ValueError("V40 v29 confirmation clock changed")
        if str(record["direction"]) != "LONG":
            raise ValueError("V40 v29 direction changed")
        if str(record["regime"]) != "UPTREND":
            raise ValueError("V40 v29 accepted candidate is outside R1")
        expected_id = _v29_candidate_id(signal, dependency)
        risk = float(record["stop_points"]) * float(
            config["execution"]["v29"]["point_size"]
        )
        target_r: float | None = float(config["execution"]["v29"]["target_r"])
        hold_hours: float | None = None
        attempt = 0
        priority = 0
        specialist = str(record["specialist_id"])
        _require_false(
            record,
            (
                "trade_permission",
                "broker_action_allowed",
                "python_execution_authorized",
            ),
            stream,
        )
    else:
        signal = utc_timestamp(record["signal_time_utc"])
        scheduled = utc_timestamp(record["scheduled_entry_time_utc"])
        if signal != scheduled:
            raise ValueError(f"V40 {stream} signal/entry timing changed")
        attempt = int(record["origin_attempt"])
        allowed = {int(value) for value in identity["component_attempts"]}
        if attempt not in allowed:
            raise ValueError(f"V40 {stream} component attempt changed")
        direction = int(record["direction_sign"])
        expected_direction = (
            "LONG" if direction == 1 else "SHORT" if direction == -1 else None
        )
        if expected_direction is None or str(record["direction"]) != expected_direction:
            raise ValueError(f"V40 {stream} candidate direction is invalid")
        risk = float(record["stop_atr"]) * float(record["signal_atr"])
        target_r = None if stream == "v28" else float(record["target_r"])
        hold_hours = float(record["hold_hours"])
        priority = 0 if stream == "v28" else int(record["component_priority"])
        specialist = str(record.get("specialist_id", "R4_CHOP"))
        source_id = _source_candidate_id(attempt, signal)
        if stream == "v28":
            if str(record["source_candidate_id"]) != source_id:
                raise ValueError("V40 v28 source candidate identity changed")
            expected_id = _v28_candidate_id(source_id, dependency)
            _require_false(
                record,
                (
                    "trade_permission",
                    "broker_action_allowed",
                    "python_execution_authorized",
                ),
                stream,
            )
            parameters = json.loads(str(record["parameters_json"]))
            if not isinstance(parameters, dict):
                raise ValueError("V40 v28 parameters are not an object")
        else:
            expected_id = source_id
            if bool(record["economic_outcome_opened"]):
                raise ValueError("V40 v34 candidate opens an economic outcome")
            if str(record["source_feed"]) != "CAPITAL_QUOTE_M5_V34":
                raise ValueError("V40 v34 source feed changed")
    if signal < utc_timestamp(config["frozen_identity"]["forward_start_inclusive_utc"]):
        raise ValueError(f"V40 {stream} candidate predates the forward boundary")
    if str(record["candidate_id"]) != expected_id:
        raise ValueError(f"V40 {stream} candidate ID changed")
    if not math.isfinite(risk) or risk <= 0.0:
        raise ValueError(f"V40 {stream} candidate risk is invalid")
    if target_r is not None and (not math.isfinite(target_r) or target_r <= 0.0):
        raise ValueError(f"V40 {stream} candidate target is invalid")
    if hold_hours is not None and (not math.isfinite(hold_hours) or hold_hours <= 0.0):
        raise ValueError(f"V40 {stream} candidate horizon is invalid")

    normalized.update(
        stream=stream,
        signal_time=signal,
        scheduled_entry_time=scheduled,
        origin_attempt=attempt,
        component_priority=priority,
        direction_sign=1 if str(record["direction"]) == "LONG" else -1,
        risk_price=risk,
        target_r=target_r,
        hold_hours=hold_hours,
        specialist_id=specialist,
        candidate_fact_sha256=candidate_fact_sha256(record),
    )
    return normalized


def parse_candidate_snapshot(
    stream: str, snapshot: bytes, config: Mapping[str, Any]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, raw in enumerate(snapshot.splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"V40 {stream} invalid JSONL line {line_number}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"V40 {stream} candidate line is not an object")
        rows.append(validate_candidate(stream, value, config))
    ids = [str(row["candidate_id"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError(f"V40 {stream} candidate source contains duplicate IDs")
    return sorted(
        rows,
        key=lambda row: (
            row["scheduled_entry_time"],
            int(row["component_priority"]),
            int(row["origin_attempt"]),
            str(row["candidate_id"]),
        ),
    )


def verify_prefix(
    snapshot: bytes,
    state: Mapping[str, Any] | None,
    bytes_field: str,
    sha_field: str,
    label: str,
) -> None:
    if not state:
        return
    previous_bytes = int(state.get(bytes_field, 0))
    previous_sha = str(state.get(sha_field, sha256_bytes(b"")))
    if len(snapshot) < previous_bytes:
        raise ValueError(f"V40 {label} was truncated")
    if sha256_bytes(snapshot[:previous_bytes]) != previous_sha:
        raise ValueError(f"V40 {label} consumed prefix was mutated")


def read_resolution_ledger(path: Path) -> list[dict[str, Any]]:
    snapshot = stable_line_prefix(path)
    if path.is_file() and int(path.stat().st_size) != len(snapshot):
        raise ValueError("V40 resolution ledger has a partial trailing record")
    rows: list[dict[str, Any]] = []
    for line_number, raw in enumerate(snapshot.splitlines(), start=1):
        value = json.loads(raw)
        if (
            not isinstance(value, dict)
            or str(value.get("resolution_status")) not in FINAL_STATUSES
        ):
            raise ValueError(f"V40 invalid resolution line {line_number}")
        rows.append(value)
    ids = [str(row.get("candidate_id")) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("V40 resolution ledger contains duplicate candidate IDs")
    return rows


def append_resolution_records(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(
                json.dumps(
                    dict(row), sort_keys=True, separators=(",", ":"), ensure_ascii=True
                )
                + "\n"
            )
        handle.flush()


def verify_candidate_status(
    stream: str, path: Path, config: Mapping[str, Any]
) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"V40 {stream} candidate status is absent")
    status = read_json(path)
    source = config["source"]
    identity = config["frozen_identity"][stream]
    if int(status.get("account_login", -1)) != int(source["account_login"]):
        raise ValueError(f"V40 {stream} candidate account changed")
    if str(status.get("account_server")) != str(source["account_server"]):
        raise ValueError(f"V40 {stream} candidate server changed")
    if str(status.get("symbol")) != str(source["symbol"]):
        raise ValueError(f"V40 {stream} candidate symbol changed")
    if str(status.get("rule_dependency_sha256")) != str(
        identity["rule_dependency_sha256"]
    ):
        raise ValueError(f"V40 {stream} status rule dependency changed")
    if str(status.get("status")) != "ACTIVE_READ_ONLY_CANDIDATE_SHADOW":
        raise ValueError(f"V40 {stream} candidate collector is not active")
    if bool(status.get("economic_outcomes_opened", True)):
        raise ValueError(f"V40 {stream} candidate collector opened outcomes")
    for field in (
        "trade_permission",
        "broker_action_allowed",
        "python_execution_authorized",
    ):
        if bool(status.get(field, True)):
            raise ValueError(f"V40 {stream} candidate status enables {field}")
    return status


def select_tick_paths(
    paths: Sequence[Path], candidates: Sequence[Mapping[str, Any]]
) -> list[Path]:
    if not candidates:
        return []
    start = min(utc_timestamp(row["scheduled_entry_time"]) for row in candidates).floor(
        "D"
    )
    return [path for path in sorted(paths) if _V38.tick_date(path) >= start]


def _first_exit_hit(
    tick_store: Any,
    start_ms: int,
    end_ms: int,
    direction: int,
    stop: float,
    target: float | None,
) -> tuple[Any, float, str] | None:
    if end_ms < start_ms:
        return None
    for times, bids, asks in tick_store.segments(start_ms, end_ms):
        executable = bids if direction > 0 else asks
        stop_hit = executable <= stop if direction > 0 else executable >= stop
        target_hit = np.zeros(len(executable), dtype=bool)
        if target is not None:
            target_hit = executable >= target if direction > 0 else executable <= target
        indices = np.flatnonzero(stop_hit | target_hit)
        if len(indices) == 0:
            continue
        index = int(indices[0])
        quote = Quote(int(times[index]), float(bids[index]), float(asks[index]))
        price = float(executable[index])
        if bool(stop_hit[index]):
            return quote, price, "STOP" if price == stop else "STOP_SLIPPAGE"
        return quote, float(target), "TARGET"
    return None


def _outcome(
    candidate: Mapping[str, Any],
    entry_quote: Any,
    exit_quote: Any,
    exit_price: float,
    exit_reason: str,
    config: Mapping[str, Any],
    stop: float,
    target: float | None,
    horizon_delay_minutes: float,
) -> dict[str, Any]:
    common = config["execution"]["common"]
    direction = int(candidate["direction_sign"])
    entry = float(entry_quote.ask if direction > 0 else entry_quote.bid)
    risk = float(candidate["risk_price"])
    risk_usd = risk * float(common["ounces_at_lot_size"])
    entry_time = pd.Timestamp(entry_quote.timestamp_ms, unit="ms", tz="UTC")
    exit_time = pd.Timestamp(exit_quote.timestamp_ms, unit="ms", tz="UTC")
    gross_r = direction * (float(exit_price) - entry) / risk
    holding_days = max(0.0, (exit_time - entry_time).total_seconds() / 86_400.0)
    extra_cost_r = (
        float(common["ticket_cost_usd"])
        + holding_days * float(common["holding_cost_per_24h_usd"])
    ) / risk_usd
    return {
        "entry_time": entry_time,
        "exit_time": exit_time,
        "entry_tick_timestamp_ms": int(entry_quote.timestamp_ms),
        "exit_tick_timestamp_ms": int(exit_quote.timestamp_ms),
        "entry_price": entry,
        "exit_price": float(exit_price),
        "stop": float(stop),
        "target": None if target is None else float(target),
        "risk_price": risk,
        "risk_usd": risk_usd,
        "entry_spread_r": float(entry_quote.ask - entry_quote.bid) / risk,
        "gross_r": gross_r,
        "stress_net_r": gross_r - extra_cost_r - float(common["stress_slippage_r"]),
        "holding_minutes": (exit_time - entry_time).total_seconds() / 60.0,
        "horizon_delay_minutes": float(horizon_delay_minutes),
        "exit_reason": exit_reason,
        "raw_tick_execution": True,
    }


def resolve_candidate_causally(
    candidate: Mapping[str, Any],
    tick_store: Any,
    config: Mapping[str, Any],
    observed_through_ms: int | None,
) -> Probe:
    stream = str(candidate["stream"])
    execution = config["execution"][stream]
    common = config["execution"]["common"]
    scheduled = utc_timestamp(candidate["scheduled_entry_time"])
    scheduled_ms = int(scheduled.value // 1_000_000)
    entry_gap_ms = int(float(execution["maximum_entry_gap_minutes"]) * 60_000)
    observed_through = -1 if observed_through_ms is None else int(observed_through_ms)
    entry_quote = tick_store.first_quote_at_or_after(scheduled_ms, entry_gap_ms)
    if entry_quote is None:
        cutoff = scheduled_ms + entry_gap_ms
        if observed_through < cutoff:
            return Probe(None, None, "AWAITING_ENTRY_WINDOW", cutoff, None)
        return Probe(None, "NO_TIMELY_ENTRY_QUOTE", None, cutoff, None)

    direction = int(candidate["direction_sign"])
    entry = float(entry_quote.ask if direction > 0 else entry_quote.bid)
    risk = float(candidate["risk_price"])
    spread = float(entry_quote.ask - entry_quote.bid)
    if spread < 0.0 or spread / risk > float(common["maximum_entry_spread_r"]):
        return Probe(None, "ENTRY_SPREAD_R", None, int(entry_quote.timestamp_ms), None)
    if risk * float(common["ounces_at_lot_size"]) > float(
        common["maximum_research_risk_usd"]
    ):
        return Probe(None, "RISK_CEILING", None, int(entry_quote.timestamp_ms), None)

    entry_time = pd.Timestamp(entry_quote.timestamp_ms, unit="ms", tz="UTC")
    stop = entry - direction * risk
    target = (
        None
        if candidate["target_r"] is None
        else entry + direction * float(candidate["target_r"]) * risk
    )
    if stream == "v29":
        search_end = (
            None
            if tick_store.latest_timestamp_ms is None
            else int(tick_store.latest_timestamp_ms)
        )
        observed = (
            None
            if search_end is None
            else _first_exit_hit(
                tick_store,
                int(entry_quote.timestamp_ms),
                search_end,
                direction,
                stop,
                target,
            )
        )
        if observed is None:
            evidence_end = max(int(entry_quote.timestamp_ms), observed_through)
            return Probe(None, None, "OPEN_POSITION", evidence_end, entry_time)
        exit_quote, exit_price, reason = observed
        outcome = _outcome(
            candidate,
            entry_quote,
            exit_quote,
            exit_price,
            reason,
            config,
            stop,
            target,
            0.0,
        )
        return Probe(outcome, None, None, int(exit_quote.timestamp_ms), entry_time)

    deadline = scheduled + pd.Timedelta(hours=float(candidate["hold_hours"]))
    deadline_ms = int(deadline.value // 1_000_000)
    horizon_gap_ms = int(float(execution["maximum_horizon_gap_minutes"]) * 60_000)
    horizon_quote = tick_store.first_quote_at_or_after(deadline_ms, horizon_gap_ms)
    cutoff = deadline_ms + horizon_gap_ms
    if stream == "v28":
        search_end = (
            int(horizon_quote.timestamp_ms)
            if horizon_quote is not None
            else None
            if tick_store.latest_timestamp_ms is None
            else min(int(tick_store.latest_timestamp_ms), cutoff - 1)
        )
    else:
        search_end = (
            int(horizon_quote.timestamp_ms) - 1
            if horizon_quote is not None
            else None
            if tick_store.latest_timestamp_ms is None
            else min(int(tick_store.latest_timestamp_ms), cutoff - 1)
        )
    observed = (
        None
        if search_end is None
        else _first_exit_hit(
            tick_store,
            int(entry_quote.timestamp_ms),
            search_end,
            direction,
            stop,
            target,
        )
    )
    if observed is not None:
        exit_quote, exit_price, reason = observed
        outcome = _outcome(
            candidate,
            entry_quote,
            exit_quote,
            exit_price,
            reason,
            config,
            stop,
            target,
            0.0,
        )
        return Probe(outcome, None, None, int(exit_quote.timestamp_ms), entry_time)
    if horizon_quote is not None:
        exit_price = float(horizon_quote.bid if direction > 0 else horizon_quote.ask)
        delay = max(
            0.0,
            (
                pd.Timestamp(horizon_quote.timestamp_ms, unit="ms", tz="UTC") - deadline
            ).total_seconds()
            / 60.0,
        )
        outcome = _outcome(
            candidate,
            entry_quote,
            horizon_quote,
            exit_price,
            "FIXED_HORIZON",
            config,
            stop,
            target,
            delay,
        )
        return Probe(outcome, None, None, int(horizon_quote.timestamp_ms), entry_time)
    if observed_through < cutoff:
        return Probe(None, None, "AWAITING_HORIZON_WINDOW", cutoff, entry_time)
    return Probe(None, "NO_HORIZON_QUOTE", None, cutoff, entry_time)


def _json_outcome(outcome: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in outcome.items():
        if isinstance(value, pd.Timestamp):
            result[f"{key}_utc"] = utc_text(value)
        elif isinstance(value, (np.integer, int)):
            result[key] = int(value)
        elif isinstance(value, (np.floating, float)):
            number = float(value)
            if not math.isfinite(number):
                raise ValueError(f"V40 non-finite outcome value: {key}")
            result[key] = number
        elif isinstance(value, (np.bool_, bool)):
            result[key] = bool(value)
        else:
            result[key] = value
    return result


def _base_resolution(
    candidate: Mapping[str, Any], now: pd.Timestamp, evidence_end_ms: int
) -> dict[str, Any]:
    return {
        "schema_version": "xauusd_capital_core_candidate_resolution_v40",
        "stream": str(candidate["stream"]),
        "candidate_id": str(candidate["candidate_id"]),
        "candidate_fact_sha256": str(candidate["candidate_fact_sha256"]),
        "specialist_id": str(candidate["specialist_id"]),
        "origin_attempt": int(candidate["origin_attempt"]),
        "resolved_at_utc": utc_text(now),
        "knowledge_time_utc": utc_text(
            pd.Timestamp(evidence_end_ms, unit="ms", tz="UTC")
        ),
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "broker_action_authorized": False,
    }


def _finalize(
    candidate: Mapping[str, Any],
    probe: Probe,
    now: pd.Timestamp,
    ticks: pd.DataFrame,
    tick_source_sha: str,
    rejection_override: str | None = None,
) -> dict[str, Any]:
    base = _base_resolution(candidate, now, probe.evidence_end_ms)
    base["tick_source_snapshot_sha256"] = tick_source_sha
    base.update(
        quote_slice_evidence(
            ticks,
            int(utc_timestamp(candidate["scheduled_entry_time"]).value // 1_000_000),
            int(probe.evidence_end_ms),
        )
    )
    rejection = rejection_override or probe.rejection
    if rejection is not None:
        base["resolution_status"] = "REJECTED"
        base["rejection_reason"] = str(rejection)
        return base
    if probe.outcome is None:
        raise ValueError("V40 attempted to finalize a pending candidate")
    base.update(_json_outcome(probe.outcome))
    base["resolution_status"] = "EXECUTED"
    base["rejection_reason"] = None
    return base


def _check_existing(
    candidates: Sequence[Mapping[str, Any]], existing: Sequence[Mapping[str, Any]]
) -> dict[str, Mapping[str, Any]]:
    candidate_by_id = {str(row["candidate_id"]): row for row in candidates}
    result = {str(row["candidate_id"]): row for row in existing}
    unknown = sorted(set(result).difference(candidate_by_id))
    if unknown:
        raise ValueError(f"V40 ledger contains unknown candidate IDs: {unknown[:3]}")
    for candidate_id, resolution in result.items():
        if str(resolution.get("candidate_fact_sha256")) != str(
            candidate_by_id[candidate_id]["candidate_fact_sha256"]
        ):
            raise ValueError("V40 resolution candidate fact hash mismatch")
    return result


def _source_snapshot_sha(records: Sequence[Mapping[str, Any]]) -> str:
    return canonical_sha256({"files": [dict(record) for record in records]})


def process_v28(
    candidates: Sequence[Mapping[str, Any]],
    existing_resolutions: Sequence[Mapping[str, Any]],
    ticks: pd.DataFrame,
    tick_records: Sequence[Mapping[str, Any]],
    observed_through_ms: int | None,
    config: Mapping[str, Any],
    now: pd.Timestamp,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    existing = _check_existing(candidates, existing_resolutions)
    store = FrameTickStore(ticks)
    maximum_daily = int(
        config["execution"]["v28"]["maximum_trades_per_component_utc_day"]
    )
    source_sha = _source_snapshot_sha(tick_records)
    rows: list[dict[str, Any]] = []
    pending: dict[str, int] = {}
    attempts = sorted({int(row["origin_attempt"]) for row in candidates})
    for attempt in attempts:
        position_until = pd.Timestamp.min.tz_localize("UTC")
        daily_count: dict[Any, int] = {}
        blocked = False
        component = [row for row in candidates if int(row["origin_attempt"]) == attempt]
        for candidate in component:
            candidate_id = str(candidate["candidate_id"])
            if candidate_id in existing:
                if blocked:
                    raise ValueError(
                        "V40 v28 has a resolution after an unresolved predecessor"
                    )
                resolution = existing[candidate_id]
                if str(resolution["resolution_status"]) == "EXECUTED":
                    entry = utc_timestamp(resolution["entry_time_utc"])
                    if entry < position_until:
                        raise ValueError("V40 v28 existing component overlap")
                    day = entry.date()
                    if daily_count.get(day, 0) >= maximum_daily:
                        raise ValueError(
                            "V40 v28 existing component daily cap violation"
                        )
                    daily_count[day] = daily_count.get(day, 0) + 1
                    position_until = utc_timestamp(resolution["exit_time_utc"])
                continue
            if blocked:
                continue
            probe = resolve_candidate_causally(
                candidate, store, config, observed_through_ms
            )
            if probe.waiting is not None:
                pending[probe.waiting] = pending.get(probe.waiting, 0) + 1
                blocked = True
                continue
            if probe.rejection is not None:
                rows.append(_finalize(candidate, probe, now, ticks, source_sha))
                continue
            assert probe.outcome is not None and probe.entry_time is not None
            if probe.entry_time < position_until:
                rows.append(
                    _finalize(
                        candidate,
                        probe,
                        now,
                        ticks,
                        source_sha,
                        "COMPONENT_POSITION_OVERLAP",
                    )
                )
                continue
            day = probe.entry_time.date()
            if daily_count.get(day, 0) >= maximum_daily:
                rows.append(
                    _finalize(
                        candidate, probe, now, ticks, source_sha, "COMPONENT_DAILY_CAP"
                    )
                )
                continue
            rows.append(_finalize(candidate, probe, now, ticks, source_sha))
            position_until = utc_timestamp(probe.outcome["exit_time"])
            daily_count[day] = daily_count.get(day, 0) + 1
    return rows, dict(sorted(pending.items()))


def process_v34(
    candidates: Sequence[Mapping[str, Any]],
    existing_resolutions: Sequence[Mapping[str, Any]],
    ticks: pd.DataFrame,
    tick_records: Sequence[Mapping[str, Any]],
    observed_through_ms: int | None,
    config: Mapping[str, Any],
    now: pd.Timestamp,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    existing = _check_existing(candidates, existing_resolutions)
    store = FrameTickStore(ticks)
    execution = config["execution"]["v34"]
    maximum_daily = int(execution["maximum_trades_per_utc_day"])
    cooldown = pd.Timedelta(minutes=float(execution["cooldown_minutes"]))
    source_sha = _source_snapshot_sha(tick_records)
    position_until = pd.Timestamp.min.tz_localize("UTC")
    cooldown_until = position_until
    daily_count: dict[Any, int] = {}
    rows: list[dict[str, Any]] = []
    pending: dict[str, int] = {}
    blocked = False
    for candidate in candidates:
        candidate_id = str(candidate["candidate_id"])
        if candidate_id in existing:
            if blocked:
                raise ValueError(
                    "V40 v34 has a resolution after an unresolved predecessor"
                )
            resolution = existing[candidate_id]
            if str(resolution["resolution_status"]) == "EXECUTED":
                entry = utc_timestamp(resolution["entry_time_utc"])
                if entry < position_until or entry < cooldown_until:
                    raise ValueError("V40 v34 existing policy overlap")
                day = entry.date()
                if daily_count.get(day, 0) >= maximum_daily:
                    raise ValueError("V40 v34 existing daily cap violation")
                daily_count[day] = daily_count.get(day, 0) + 1
                position_until = utc_timestamp(resolution["exit_time_utc"])
                cooldown_until = position_until + cooldown
            continue
        if blocked:
            continue
        probe = resolve_candidate_causally(
            candidate, store, config, observed_through_ms
        )
        if probe.waiting is not None:
            pending[probe.waiting] = pending.get(probe.waiting, 0) + 1
            blocked = True
            continue
        if probe.rejection is not None:
            rows.append(_finalize(candidate, probe, now, ticks, source_sha))
            continue
        assert probe.outcome is not None and probe.entry_time is not None
        rejection = None
        if probe.entry_time < position_until:
            rejection = "POSITION_OVERLAP"
        elif probe.entry_time < cooldown_until:
            rejection = "COOLDOWN"
        elif daily_count.get(probe.entry_time.date(), 0) >= maximum_daily:
            rejection = "DAILY_CAP"
        rows.append(_finalize(candidate, probe, now, ticks, source_sha, rejection))
        if rejection is None:
            daily_count[probe.entry_time.date()] = (
                daily_count.get(probe.entry_time.date(), 0) + 1
            )
            position_until = utc_timestamp(probe.outcome["exit_time"])
            cooldown_until = position_until + cooldown
    return rows, dict(sorted(pending.items()))


def process_v29(
    candidates: Sequence[Mapping[str, Any]],
    existing_resolutions: Sequence[Mapping[str, Any]],
    ticks: pd.DataFrame,
    tick_records: Sequence[Mapping[str, Any]],
    observed_through_ms: int | None,
    config: Mapping[str, Any],
    now: pd.Timestamp,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    existing = _check_existing(candidates, existing_resolutions)
    store = FrameTickStore(ticks)
    execution = config["execution"]["v29"]
    maximum_open = int(execution["maximum_open_positions"])
    maximum_daily = int(execution["maximum_trades_per_utc_day"])
    source_sha = _source_snapshot_sha(tick_records)
    intervals: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    daily_count: dict[Any, int] = {}
    rows: list[dict[str, Any]] = []
    pending: dict[str, int] = {}
    far_future = pd.Timestamp.max.tz_localize("UTC")
    for candidate in candidates:
        candidate_id = str(candidate["candidate_id"])
        if candidate_id in existing:
            resolution = existing[candidate_id]
            if str(resolution["resolution_status"]) == "EXECUTED":
                entry = utc_timestamp(resolution["entry_time_utc"])
                exit_time = utc_timestamp(resolution["exit_time_utc"])
                concurrent = sum(start <= entry < end for start, end in intervals)
                if concurrent >= maximum_open:
                    raise ValueError("V40 v29 existing concurrency cap violation")
                day = entry.date()
                if daily_count.get(day, 0) >= maximum_daily:
                    raise ValueError("V40 v29 existing daily cap violation")
                intervals.append((entry, exit_time))
                daily_count[day] = daily_count.get(day, 0) + 1
            continue

        probe = resolve_candidate_causally(
            candidate, store, config, observed_through_ms
        )
        if probe.waiting == "AWAITING_ENTRY_WINDOW":
            pending[probe.waiting] = pending.get(probe.waiting, 0) + 1
            continue
        if probe.rejection is not None:
            rows.append(_finalize(candidate, probe, now, ticks, source_sha))
            continue
        if probe.entry_time is None:
            raise ValueError("V40 v29 pending candidate has no entry")
        entry = probe.entry_time
        concurrent = sum(start <= entry < end for start, end in intervals)
        rejection = None
        if concurrent >= maximum_open:
            rejection = "MAX_OPEN_POSITIONS"
        elif daily_count.get(entry.date(), 0) >= maximum_daily:
            rejection = "DAILY_CAP"
        if rejection is not None:
            rows.append(_finalize(candidate, probe, now, ticks, source_sha, rejection))
            continue
        exit_time = (
            far_future
            if probe.outcome is None
            else utc_timestamp(probe.outcome["exit_time"])
        )
        intervals.append((entry, exit_time))
        daily_count[entry.date()] = daily_count.get(entry.date(), 0) + 1
        if probe.waiting is not None:
            pending[probe.waiting] = pending.get(probe.waiting, 0) + 1
            continue
        rows.append(_finalize(candidate, probe, now, ticks, source_sha))
    return rows, dict(sorted(pending.items()))


PROCESSORS = {"v28": process_v28, "v29": process_v29, "v34": process_v34}
