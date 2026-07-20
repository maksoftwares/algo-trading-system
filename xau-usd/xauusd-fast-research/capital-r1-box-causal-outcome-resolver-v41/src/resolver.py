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
CONFIG_PATH = ROOT / "config" / "capital_r1_box_causal_outcome_resolver_v41.json"
FINAL_STATUSES = frozenset(("EXECUTED", "REJECTED"))
CANDIDATE_FIELDS = frozenset(
    (
        "schema_version",
        "record_type",
        "candidate_id",
        "state_id",
        "specialist_id",
        "signal_time_utc",
        "direction",
        "stop_distance",
        "target_r",
        "contract_hash",
        "maximum_entry_gap_minutes",
        "maximum_spread_price",
        "maximum_spread_r",
        "ticket_cost_usd",
        "holding_cost_per_24h_usd",
        "stress_slippage_r",
        "trade_permission",
        "broker_action_allowed",
        "python_execution_authorized",
    )
)
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


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_V40 = load_module(
    "capital_r1_box_v41_v40_utils",
    REPO_ROOT
    / "xau-usd/xauusd-fast-research/capital-core-causal-outcome-resolver-v40/src/resolver.py",
)
Quote = _V40.Quote
FrameTickStore = _V40.FrameTickStore
atomic_write_json = _V40.atomic_write_json
canonical_sha256 = _V40.canonical_sha256
latest_observed_timestamp_ms = _V40.latest_observed_timestamp_ms
load_tick_snapshots = _V40.load_tick_snapshots
quote_slice_evidence = _V40.quote_slice_evidence
sha256_bytes = _V40.sha256_bytes
sha256_file = _V40.sha256_file
stable_line_prefix = _V40.stable_line_prefix
utc_text = _V40.utc_text
utc_timestamp = _V40.utc_timestamp


@dataclass(frozen=True)
class Probe:
    outcome: dict[str, Any] | None
    rejection: str | None
    waiting: str | None
    evidence_end_ms: int
    entry_time: pd.Timestamp | None


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _repo_path(repo_root: Path, relative: str) -> Path:
    root = repo_root.resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"V41 dependency escaped repository: {relative}") from exc
    return path


def verify_contract(
    config: Mapping[str, Any],
    repo_root: Path = REPO_ROOT,
    package_root: Path = ROOT,
) -> dict[str, Any]:
    path = (
        package_root
        / str(config["outputs"]["directory"])
        / str(config["outputs"]["contract_lock"])
    )
    if not path.is_file():
        raise FileNotFoundError("V41 contract lock is absent")
    lock = read_json(path)
    signed = dict(lock)
    observed = str(signed.pop("contract_sha256", ""))
    if observed != canonical_sha256(signed):
        raise ValueError("V41 contract payload hash is invalid")
    for relative, expected in lock["package_files"].items():
        source = (package_root / relative).resolve()
        if not source.is_file() or int(source.stat().st_size) != int(expected["bytes"]):
            raise ValueError(f"V41 package file identity changed: {relative}")
        if sha256_file(source) != str(expected["sha256"]):
            raise ValueError(f"V41 package file hash changed: {relative}")
    for relative, expected in lock["dependencies"].items():
        source = _repo_path(repo_root, str(relative))
        if not source.is_file() or int(source.stat().st_size) != int(expected["bytes"]):
            raise ValueError(f"V41 dependency identity changed: {relative}")
        if sha256_file(source) != str(expected["sha256"]):
            raise ValueError(f"V41 dependency hash changed: {relative}")
    return lock


def source_contract_sha256(
    config: Mapping[str, Any], repo_root: Path = REPO_ROOT
) -> str:
    historical = config["historical"]
    digest = hashlib.sha256()
    for field in ("base_module", "source_module", "source_config"):
        digest.update(_repo_path(repo_root, str(historical[field])).read_bytes())
    return digest.hexdigest()


def validate_frozen_identity(
    config: Mapping[str, Any], repo_root: Path = REPO_ROOT
) -> None:
    observed = source_contract_sha256(config, repo_root)
    expected = str(config["frozen_identity"]["source_contract_sha256"])
    if observed != expected:
        raise ValueError(f"V41 R1 source contract changed: {observed}")
    source_config = read_json(
        _repo_path(repo_root, str(config["historical"]["source_config"]))
    )
    execution = config["execution"]
    original = source_config["execution"]
    primary = source_config["policies"]["PORTFOLIO_CONSTRAINED_PRIMARY"]
    checks = (
        float(execution["maximum_entry_gap_minutes"])
        == float(original["maximum_entry_gap_minutes"]),
        float(execution["maximum_spread_price"])
        == float(original["maximum_spread_price"]),
        float(execution["maximum_spread_r"]) == float(original["maximum_spread_r"]),
        float(execution["ounces_at_0_01_lot"]) == float(original["ounces_at_0_01_lot"]),
        float(execution["ticket_cost_usd"]) == float(original["ticket_cost_usd"]),
        float(execution["holding_cost_per_24h_usd"])
        == float(original["holding_cost_per_24h_usd"]),
        float(execution["stress_slippage_r"]) == float(original["stress_slippage_r"]),
        float(execution["target_r"]) == 2.0,
        int(execution["maximum_concurrent_positions"])
        == int(primary["maximum_concurrent_positions"]),
        int(execution["maximum_entries_per_utc_day"])
        == int(primary["maximum_entries_per_utc_day"]),
        bool(primary["eligible_for_decision"]),
    )
    if not all(checks):
        raise ValueError("V41 frozen source execution or primary policy changed")


def validate_historical_parity_artifact(
    config: Mapping[str, Any], contract: Mapping[str, Any], package_root: Path = ROOT
) -> dict[str, Any]:
    path = (
        package_root
        / str(config["outputs"]["directory"])
        / str(config["outputs"]["historical_semantic_parity"])
    )
    if not path.is_file():
        raise FileNotFoundError("V41 historical semantic parity artifact is absent")
    parity = read_json(path)
    if str(parity.get("contract_sha256")) != str(contract["contract_sha256"]):
        raise ValueError("V41 parity artifact belongs to another contract")
    if not bool(parity.get("semantic_parity_passed")):
        raise ValueError("V41 historical semantic parity did not pass")
    return parity


def deterministic_id(
    kind: str, specialist_id: str, signal_time: pd.Timestamp, contract_hash: str
) -> str:
    payload = "|".join((kind, specialist_id, utc_text(signal_time), contract_hash))
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def candidate_fact_sha256(record: Mapping[str, Any]) -> str:
    return canonical_sha256({key: record[key] for key in sorted(record)})


def validate_candidate(
    record: Mapping[str, Any], config: Mapping[str, Any]
) -> dict[str, Any]:
    if frozenset(record) != CANDIDATE_FIELDS:
        missing = sorted(CANDIDATE_FIELDS.difference(record))
        extra = sorted(set(record).difference(CANDIDATE_FIELDS))
        raise ValueError(
            f"V41 R1 candidate schema changed; missing={missing}, extra={extra}"
        )
    if FORBIDDEN_OUTCOME_FIELDS.intersection(record):
        raise ValueError("V41 candidate contains an outcome field")
    source = config["source"]
    identity = config["frozen_identity"]
    execution = config["execution"]
    if str(record["schema_version"]) != str(source["candidate_schema_version"]):
        raise ValueError("V41 candidate schema version changed")
    if str(record["record_type"]) != "CANDIDATE":
        raise ValueError("V41 candidate record type changed")
    if str(record["specialist_id"]) != str(source["specialist_id"]):
        raise ValueError("V41 candidate specialist changed")
    if str(record["contract_hash"]) != str(identity["source_contract_sha256"]):
        raise ValueError("V41 candidate source contract changed")
    signal = utc_timestamp(record["signal_time_utc"])
    if signal < utc_timestamp(identity["forward_start_inclusive_utc"]):
        raise ValueError("V41 candidate predates the frozen forward boundary")
    expected_candidate = deterministic_id(
        "candidate", str(source["specialist_id"]), signal, str(record["contract_hash"])
    )
    expected_state = deterministic_id(
        "state", str(source["specialist_id"]), signal, str(record["contract_hash"])
    )
    if str(record["candidate_id"]) != expected_candidate:
        raise ValueError("V41 candidate ID does not match the frozen identity")
    if str(record["state_id"]) != expected_state:
        raise ValueError("V41 state ID does not match the frozen identity")
    if str(record["direction"]) != "LONG":
        raise ValueError("V41 candidate direction changed")
    risk = float(record["stop_distance"])
    if not math.isfinite(risk) or risk <= 0.0:
        raise ValueError("V41 candidate stop distance is invalid")
    exact_values = (
        (record["target_r"], execution["target_r"]),
        (record["maximum_entry_gap_minutes"], execution["maximum_entry_gap_minutes"]),
        (record["maximum_spread_price"], execution["maximum_spread_price"]),
        (record["maximum_spread_r"], execution["maximum_spread_r"]),
        (record["ticket_cost_usd"], execution["ticket_cost_usd"]),
        (record["holding_cost_per_24h_usd"], execution["holding_cost_per_24h_usd"]),
        (record["stress_slippage_r"], execution["stress_slippage_r"]),
    )
    if not all(float(actual) == float(expected) for actual, expected in exact_values):
        raise ValueError("V41 candidate execution settings changed")
    for field in (
        "trade_permission",
        "broker_action_allowed",
        "python_execution_authorized",
    ):
        if bool(record[field]):
            raise ValueError(f"V41 candidate enables {field}")
    return {
        **dict(record),
        "signal_time": signal,
        "scheduled_entry_time": signal,
        "direction_sign": 1,
        "risk_price": risk,
        "candidate_fact_sha256": candidate_fact_sha256(record),
    }


def parse_candidate_snapshot(
    snapshot: bytes, config: Mapping[str, Any]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, raw in enumerate(snapshot.splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"V41 invalid candidate JSONL line {line_number}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"V41 candidate line {line_number} is not an object")
        rows.append(validate_candidate(value, config))
    ids = [str(row["candidate_id"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("V41 candidate source contains duplicate IDs")
    return sorted(rows, key=lambda row: (row["signal_time"], str(row["candidate_id"])))


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
        raise ValueError(f"V41 {label} was truncated")
    if sha256_bytes(snapshot[:previous_bytes]) != previous_sha:
        raise ValueError(f"V41 {label} consumed prefix was mutated")


def read_resolution_ledger(path: Path) -> list[dict[str, Any]]:
    snapshot = stable_line_prefix(path)
    if path.is_file() and int(path.stat().st_size) != len(snapshot):
        raise ValueError("V41 resolution ledger has a partial trailing record")
    rows: list[dict[str, Any]] = []
    for line_number, raw in enumerate(snapshot.splitlines(), start=1):
        value = json.loads(raw)
        if (
            not isinstance(value, dict)
            or str(value.get("schema_version"))
            != "xauusd_capital_r1_box_candidate_resolution_v41"
            or str(value.get("resolution_status")) not in FINAL_STATUSES
        ):
            raise ValueError(f"V41 invalid resolution line {line_number}")
        for field in (
            "model_training_authorized",
            "python_predictions_authorized",
            "ea_consumption_authorized",
            "broker_action_authorized",
        ):
            if bool(value.get(field, True)):
                raise ValueError(f"V41 resolution enables {field}")
        rows.append(value)
    ids = [str(row.get("candidate_id")) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("V41 resolution ledger contains duplicate candidate IDs")
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


def verify_candidate_status(path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError("V41 R1 candidate status is absent")
    status = read_json(path)
    source = config["source"]
    identity = config["frozen_identity"]
    checks = (
        int(status.get("account_login", -1)) == int(source["account_login"]),
        str(status.get("account_server")) == str(source["account_server"]),
        str(status.get("symbol")) == str(source["symbol"]),
        str(status.get("specialist_id")) == str(source["specialist_id"]),
        str(status.get("contract_hash")) == str(identity["source_contract_sha256"]),
        str(status.get("status")) == "ACTIVE_READ_ONLY_SHADOW",
    )
    if not all(checks):
        raise ValueError("V41 R1 candidate status identity or liveness changed")
    for field in (
        "trade_permission",
        "broker_action_allowed",
        "python_execution_authorized",
    ):
        if bool(status.get(field, True)):
            raise ValueError(f"V41 R1 candidate status enables {field}")
    return status


def select_tick_paths(
    paths: Sequence[Path], candidates: Sequence[Mapping[str, Any]]
) -> list[Path]:
    return _V40.select_tick_paths(paths, candidates)


def _first_exit_hit(
    store: Any, start_ms: int, end_ms: int, stop: float, target: float
) -> tuple[Any, float, str] | None:
    if end_ms < start_ms:
        return None
    for times, bids, asks in store.segments(start_ms, end_ms):
        stop_hit = bids <= stop
        target_hit = bids >= target
        indices = np.flatnonzero(stop_hit | target_hit)
        if len(indices) == 0:
            continue
        index = int(indices[0])
        quote = Quote(int(times[index]), float(bids[index]), float(asks[index]))
        if bool(stop_hit[index]):
            price = float(bids[index])
            return quote, price, "STOP" if price == stop else "STOP_SLIPPAGE"
        return quote, float(target), "TARGET"
    return None


def _outcome(
    candidate: Mapping[str, Any],
    entry_quote: Any,
    exit_quote: Any,
    exit_price: float,
    reason: str,
    config: Mapping[str, Any],
    stop: float,
    target: float,
) -> dict[str, Any]:
    execution = config["execution"]
    entry = float(entry_quote.ask)
    risk = float(candidate["risk_price"])
    risk_usd = risk * float(execution["ounces_at_0_01_lot"])
    entry_time = pd.Timestamp(entry_quote.timestamp_ms, unit="ms", tz="UTC")
    exit_time = pd.Timestamp(exit_quote.timestamp_ms, unit="ms", tz="UTC")
    gross_r = (float(exit_price) - entry) / risk
    holding_days = max(0.0, (exit_time - entry_time).total_seconds() / 86_400.0)
    extra_cost_r = (
        float(execution["ticket_cost_usd"])
        + holding_days * float(execution["holding_cost_per_24h_usd"])
    ) / risk_usd
    return {
        "entry_time": entry_time,
        "exit_time": exit_time,
        "entry_tick_timestamp_ms": int(entry_quote.timestamp_ms),
        "exit_tick_timestamp_ms": int(exit_quote.timestamp_ms),
        "entry_price": entry,
        "exit_price": float(exit_price),
        "stop": float(stop),
        "target": float(target),
        "risk_price": risk,
        "risk_usd": risk_usd,
        "entry_spread": float(entry_quote.ask - entry_quote.bid),
        "entry_spread_r": float(entry_quote.ask - entry_quote.bid) / risk,
        "gross_r": gross_r,
        "extra_cost_r": extra_cost_r,
        "stress_net_r": gross_r - extra_cost_r - float(execution["stress_slippage_r"]),
        "holding_minutes": (exit_time - entry_time).total_seconds() / 60.0,
        "exit_reason": reason,
        "raw_tick_execution": True,
    }


def resolve_candidate_causally(
    candidate: Mapping[str, Any],
    store: Any,
    config: Mapping[str, Any],
    observed_through_ms: int | None,
) -> Probe:
    scheduled = utc_timestamp(candidate["scheduled_entry_time"])
    scheduled_ms = int(scheduled.value // 1_000_000)
    entry_gap_ms = int(float(candidate["maximum_entry_gap_minutes"]) * 60_000)
    observed_through = -1 if observed_through_ms is None else int(observed_through_ms)
    entry_quote = store.first_quote_at_or_after(scheduled_ms, entry_gap_ms)
    if entry_quote is None:
        cutoff = scheduled_ms + entry_gap_ms
        if observed_through < cutoff:
            return Probe(None, None, "AWAITING_ENTRY_WINDOW", cutoff, None)
        return Probe(None, "NO_TIMELY_ENTRY_QUOTE", None, cutoff, None)

    risk = float(candidate["risk_price"])
    spread = float(entry_quote.ask - entry_quote.bid)
    if spread < 0.0:
        return Probe(
            None, "INVALID_ENTRY_SPREAD", None, int(entry_quote.timestamp_ms), None
        )
    if spread > float(candidate["maximum_spread_price"]):
        return Probe(
            None, "SPREAD_PRICE_LIMIT", None, int(entry_quote.timestamp_ms), None
        )
    if spread / risk > float(candidate["maximum_spread_r"]):
        return Probe(None, "SPREAD_R_LIMIT", None, int(entry_quote.timestamp_ms), None)

    entry_time = pd.Timestamp(entry_quote.timestamp_ms, unit="ms", tz="UTC")
    entry = float(entry_quote.ask)
    stop = entry - risk
    target = entry + float(candidate["target_r"]) * risk
    search_end = store.latest_timestamp_ms
    hit = (
        None
        if search_end is None
        else _first_exit_hit(
            store, int(entry_quote.timestamp_ms), int(search_end), stop, target
        )
    )
    if hit is None:
        return Probe(
            None, None, "OPEN_POSITION", int(entry_quote.timestamp_ms), entry_time
        )
    exit_quote, exit_price, reason = hit
    outcome = _outcome(
        candidate, entry_quote, exit_quote, exit_price, reason, config, stop, target
    )
    return Probe(outcome, None, None, int(exit_quote.timestamp_ms), entry_time)


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
                raise ValueError(f"V41 non-finite outcome value: {key}")
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
        "schema_version": "xauusd_capital_r1_box_candidate_resolution_v41",
        "candidate_id": str(candidate["candidate_id"]),
        "candidate_fact_sha256": str(candidate["candidate_fact_sha256"]),
        "specialist_id": str(candidate["specialist_id"]),
        "policy_id": "PORTFOLIO_CONSTRAINED_PRIMARY",
        "signal_time_utc": utc_text(candidate["signal_time"]),
        "resolved_at_utc": utc_text(now),
        "knowledge_time_utc": utc_text(
            pd.Timestamp(evidence_end_ms, unit="ms", tz="UTC")
        ),
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "broker_action_authorized": False,
    }


def _source_snapshot_sha(records: Sequence[Mapping[str, Any]]) -> str:
    return canonical_sha256({"files": [dict(record) for record in records]})


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
        if probe.entry_time is not None:
            base["entry_time_utc"] = utc_text(probe.entry_time)
        return base
    if probe.outcome is None:
        raise ValueError("V41 attempted to finalize a pending candidate")
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
        raise ValueError(f"V41 ledger contains unknown candidate IDs: {unknown[:3]}")
    for candidate_id, resolution in result.items():
        if str(resolution.get("candidate_fact_sha256")) != str(
            candidate_by_id[candidate_id]["candidate_fact_sha256"]
        ):
            raise ValueError("V41 resolution candidate fact hash mismatch")
    return result


def process_candidates(
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
    maximum_open = int(config["execution"]["maximum_concurrent_positions"])
    maximum_daily = int(config["execution"]["maximum_entries_per_utc_day"])
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
                    raise ValueError("V41 existing concurrency cap violation")
                if daily_count.get(entry.date(), 0) >= maximum_daily:
                    raise ValueError("V41 existing daily cap violation")
                intervals.append((entry, exit_time))
                daily_count[entry.date()] = daily_count.get(entry.date(), 0) + 1
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
            raise ValueError("V41 pending candidate has no entry")
        entry = probe.entry_time
        concurrent = sum(start <= entry < end for start, end in intervals)
        policy_rejection = None
        if concurrent >= maximum_open:
            policy_rejection = "MAX_CONCURRENT_POSITIONS"
        elif daily_count.get(entry.date(), 0) >= maximum_daily:
            policy_rejection = "DAILY_ENTRY_CAP"
        if policy_rejection is not None:
            entry_evidence = Probe(
                None,
                None,
                None,
                int(entry.value // 1_000_000),
                entry,
            )
            rows.append(
                _finalize(
                    candidate,
                    entry_evidence,
                    now,
                    ticks,
                    source_sha,
                    policy_rejection,
                )
            )
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
