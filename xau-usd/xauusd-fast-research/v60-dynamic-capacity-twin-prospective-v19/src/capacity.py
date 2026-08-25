from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


TICK_COLUMNS = (
    "schema_version",
    "account_login",
    "symbol",
    "tick_time_msc",
    "bid",
    "ask",
)
FINAL_RESOLUTION_STATUSES = frozenset(("EXECUTED", "REJECTED"))


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return sha256_bytes(encoded)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def utc_timestamp(value: Any) -> pd.Timestamp:
    parsed = pd.Timestamp(value)
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp is timezone-naive: {value}")
    return parsed.tz_convert("UTC")


def timestamp_ms(value: Any) -> int:
    return int(utc_timestamp(value).value // 1_000_000)


def utc_text_ms(value: int) -> str:
    return pd.Timestamp(int(value), unit="ms", tz="UTC").isoformat().replace(
        "+00:00", "Z"
    )


def stable_line_prefix(path: Path) -> bytes:
    if not path.is_file():
        return b""
    size = int(path.stat().st_size)
    with path.open("rb") as handle:
        payload = handle.read(size)
    if len(payload) != size:
        raise ValueError(f"Short candidate-ledger read: {path}")
    newline = payload.rfind(b"\n")
    return b"" if newline < 0 else payload[: newline + 1]


@dataclass(frozen=True)
class CandidateFact:
    candidate: Any
    source: Mapping[str, Any]
    fact_sha256: str


@dataclass(frozen=True)
class TickDay:
    path: Path
    day: date
    times: np.ndarray
    bids: np.ndarray
    asks: np.ndarray
    sha256: str
    duplicate_rows_collapsed: int


def _json_rows(snapshot: bytes, path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(snapshot.splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"Candidate row is not an object: {path}:{line_number}")
        rows.append(value)
    return rows


def load_candidate_facts(
    portfolio: Mapping[str, Any],
    executor: Any,
    *,
    boundary: pd.Timestamp,
    point_size: float,
    previous_prefixes: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[list[CandidateFact], dict[str, dict[str, Any]]]:
    previous_prefixes = previous_prefixes or {}
    snapshots: dict[str, bytes] = {}
    prefixes: dict[str, dict[str, Any]] = {}
    facts: list[CandidateFact] = []
    for source in portfolio["sources"]:
        path = Path(str(source["path"])).resolve()
        key = str(path)
        if key not in snapshots:
            snapshot = stable_line_prefix(path)
            prior = previous_prefixes.get(key)
            if prior is not None:
                prior_bytes = int(prior["bytes"])
                if len(snapshot) < prior_bytes:
                    raise ValueError(f"Candidate ledger was truncated: {path}")
                if sha256_bytes(snapshot[:prior_bytes]) != str(prior["sha256"]):
                    raise ValueError(f"Candidate ledger consumed prefix changed: {path}")
            snapshots[key] = snapshot
            prefixes[key] = {
                "bytes": len(snapshot),
                "sha256": sha256_bytes(snapshot),
            }
        source_specialist = str(source["specialist_id"])
        shared = sum(Path(str(item["path"])).resolve() == path for item in portfolio["sources"]) > 1
        for raw in _json_rows(snapshots[key], path):
            row_specialist = raw.get("specialist_id")
            if shared and row_specialist is None:
                raise ValueError(f"Shared ledger candidate lacks specialist_id: {path}")
            if row_specialist is not None and str(row_specialist) != source_specialist:
                continue
            candidate = executor.normalize_candidate(raw, source, float(point_size))
            if candidate is None:
                continue
            if pd.Timestamp(candidate.scheduled_at) < boundary:
                continue
            facts.append(
                CandidateFact(
                    candidate=candidate,
                    source=dict(source),
                    fact_sha256=canonical_sha256(raw),
                )
            )
    facts.sort(
        key=lambda item: (
            item.candidate.scheduled_at,
            item.candidate.source_id,
            item.candidate.candidate_id,
        )
    )
    ids = [str(item.candidate.candidate_id) for item in facts]
    if len(ids) != len(set(ids)):
        raise ValueError("Candidate ledgers contain duplicate candidate IDs")
    return facts, prefixes


_TICK_DATE = re.compile(r"_ticks_(\d{8})\.csv$")


def tick_file_date(path: Path) -> date:
    match = _TICK_DATE.search(path.name)
    if match is None:
        raise ValueError(f"Tick filename has no UTC date: {path}")
    return datetime.strptime(match.group(1), "%Y%m%d").date()


def completed_tick_paths(
    directory: Path, pattern: str, *, now: datetime
) -> list[Path]:
    current_day = now.astimezone(UTC).date()
    result = [
        path
        for path in directory.glob(pattern)
        if tick_file_date(path) < current_day
    ]
    ordered = sorted(result, key=lambda path: (tick_file_date(path), path.name))
    days = [tick_file_date(path) for path in ordered]
    if len(days) != len(set(days)):
        raise ValueError("Multiple completed tick files claim the same UTC day")
    return ordered


def load_tick_day(path: Path, expected_schema: str) -> TickDay:
    frame = pd.read_csv(
        path,
        usecols=list(TICK_COLUMNS),
        dtype={
            "schema_version": "string",
            "account_login": "string",
            "symbol": "string",
            "tick_time_msc": "int64",
            "bid": "float64",
            "ask": "float64",
        },
    )
    if frame.empty:
        empty_times = np.asarray([], dtype=np.int64)
        empty_prices = np.asarray([], dtype=float)
        return TickDay(
            path=path,
            day=tick_file_date(path),
            times=empty_times,
            bids=empty_prices,
            asks=empty_prices.copy(),
            sha256=sha256_file(path),
            duplicate_rows_collapsed=0,
        )
    if not frame["schema_version"].eq(expected_schema).all():
        raise ValueError(f"Unexpected tick schema: {path}")
    if not frame["account_login"].eq("1033030").all():
        raise ValueError(f"Tick file belongs to another account: {path}")
    if not frame["symbol"].eq("XAUUSD").all():
        raise ValueError(f"Tick file belongs to another symbol: {path}")
    duplicate_rows = int(frame["tick_time_msc"].duplicated(keep="first").sum())
    if duplicate_rows:
        duplicate_groups = frame.loc[
            frame["tick_time_msc"].duplicated(keep=False),
            ["tick_time_msc", "bid", "ask"],
        ].groupby("tick_time_msc", sort=False)
        if (duplicate_groups[["bid", "ask"]].nunique() > 1).any().any():
            raise ValueError(f"Conflicting quotes share a tick timestamp: {path}")
        frame = frame.drop_duplicates("tick_time_msc", keep="first")
    times = frame["tick_time_msc"].to_numpy(np.int64)
    bids = frame["bid"].to_numpy(float)
    asks = frame["ask"].to_numpy(float)
    if np.any(np.diff(times) <= 0):
        raise ValueError(f"Tick timestamps are not strictly increasing: {path}")
    expected_day = tick_file_date(path)
    observed_days = pd.to_datetime(times, unit="ms", utc=True).date
    if any(day != expected_day for day in observed_days):
        raise ValueError(f"Tick row is in the wrong UTC file day: {path}")
    if np.any(~np.isfinite(bids)) or np.any(~np.isfinite(asks)) or np.any(asks <= bids):
        raise ValueError(f"Tick prices are invalid: {path}")
    return TickDay(
        path=path,
        day=tick_file_date(path),
        times=times,
        bids=bids,
        asks=asks,
        sha256=sha256_file(path),
        duplicate_rows_collapsed=duplicate_rows,
    )


def initial_resolution(fact: CandidateFact) -> dict[str, Any]:
    candidate = fact.candidate
    return {
        "candidate_id": str(candidate.candidate_id),
        "source_id": str(candidate.source_id),
        "specialist_id": str(candidate.specialist_id),
        "sleeve_type": str(candidate.sleeve_type),
        "direction": str(candidate.direction),
        "event_id": candidate.event_id,
        "scheduled_entry_time_utc": candidate.scheduled_at.isoformat().replace(
            "+00:00", "Z"
        ),
        "fact_sha256": fact.fact_sha256,
        "status": "WAITING_ENTRY",
        "last_tick_time_msc": None,
    }


def _first_index(times: np.ndarray, at_or_after: int) -> int:
    return int(np.searchsorted(times, int(at_or_after), side="left"))


def _finalize_rejection(state: dict[str, Any], reason: str, evidence_ms: int) -> None:
    state.update(
        status="REJECTED",
        rejection_reason=reason,
        evidence_end_time_utc=utc_text_ms(evidence_ms),
    )


def _finalize_exit(
    state: dict[str, Any],
    *,
    exit_ms: int,
    exit_price: float,
    reason: str,
    economics: Mapping[str, Any],
) -> None:
    sign = 1.0 if state["direction"] == "LONG" else -1.0
    holding_days = max(0.0, (exit_ms - int(state["entry_time_msc"])) / 86_400_000.0)
    holding_cost = holding_days * float(economics["holding_cost_per_24h_usd"])
    ticket_cost = float(economics["ticket_cost_usd"])
    market_pnl = sign * (float(exit_price) - float(state["entry_price"]))
    pnl = market_pnl - ticket_cost - holding_cost
    risk = float(state["risk_usd"])
    state.update(
        status="EXECUTED",
        exit_time_msc=int(exit_ms),
        exit_time_utc=utc_text_ms(exit_ms),
        exit_price=float(exit_price),
        exit_reason=reason,
        holding_cost_usd=holding_cost,
        ticket_cost_usd=ticket_cost,
        pnl_usd=pnl,
        stress_pnl_usd=pnl - float(economics["stress_slippage_r"]) * risk,
        evidence_end_time_utc=utc_text_ms(exit_ms),
    )


def advance_resolution(
    state: dict[str, Any],
    fact: CandidateFact,
    ticks: TickDay,
    *,
    economics: Mapping[str, Any],
    maximum_horizon_gap_minutes: int,
) -> dict[str, Any]:
    if str(state["fact_sha256"]) != fact.fact_sha256:
        raise ValueError(f"Candidate fact changed: {state['candidate_id']}")
    if state["status"] in FINAL_RESOLUTION_STATUSES:
        return state
    candidate = fact.candidate
    times, bids, asks = ticks.times, ticks.bids, ticks.asks
    if state["status"] == "WAITING_ENTRY":
        scheduled_ms = int(round(candidate.scheduled_at.timestamp() * 1000.0))
        deadline = scheduled_ms + int(candidate.maximum_entry_gap_minutes) * 60_000
        if int(times[-1]) < scheduled_ms:
            return state
        index = _first_index(times, scheduled_ms)
        if index >= len(times) or int(times[index]) > deadline:
            if int(times[-1]) >= deadline:
                _finalize_rejection(state, "NO_TIMELY_ENTRY_QUOTE", deadline)
            return state
        spread = float(asks[index] - bids[index])
        if spread / float(candidate.stop_distance) > float(candidate.maximum_spread_r):
            _finalize_rejection(state, "SPREAD_R_EXCEEDED", int(times[index]))
            return state
        entry = float(asks[index] if candidate.direction == "LONG" else bids[index])
        sign = 1.0 if candidate.direction == "LONG" else -1.0
        state.update(
            status="OPEN",
            entry_time_msc=int(times[index]),
            entry_time_utc=utc_text_ms(int(times[index])),
            entry_price=entry,
            risk_usd=float(candidate.initial_risk_usd),
            stop_price=entry - sign * float(candidate.stop_distance),
            target_price=(
                None
                if candidate.target_r is None
                else entry + sign * float(candidate.target_r) * float(candidate.stop_distance)
            ),
            horizon_time_msc=(
                None
                if candidate.hold_hours is None
                else int(times[index]) + int(round(float(candidate.hold_hours) * 3_600_000.0))
            ),
            last_tick_time_msc=int(times[index]) - 1,
        )
        if state["target_price"] is None and state["horizon_time_msc"] is None:
            raise ValueError(
                f"Candidate has neither target nor horizon: {state['candidate_id']}"
            )
    if state["status"] != "OPEN":
        return state

    start = _first_index(times, int(state["last_tick_time_msc"]) + 1)
    if start >= len(times):
        return state
    horizon = state.get("horizon_time_msc")
    end_ms = int(times[-1]) if horizon is None else min(int(times[-1]), int(horizon))
    end = int(np.searchsorted(times, end_ms, side="right"))
    if start < end:
        executable = bids[start:end] if state["direction"] == "LONG" else asks[start:end]
        if state["direction"] == "LONG":
            stop_hit = executable <= float(state["stop_price"])
            target_hit = (
                np.zeros(len(executable), dtype=bool)
                if state["target_price"] is None
                else executable >= float(state["target_price"])
            )
        else:
            stop_hit = executable >= float(state["stop_price"])
            target_hit = (
                np.zeros(len(executable), dtype=bool)
                if state["target_price"] is None
                else executable <= float(state["target_price"])
            )
        hits = np.flatnonzero(stop_hit | target_hit)
        if len(hits):
            offset = int(hits[0])
            index = start + offset
            if bool(stop_hit[offset]):
                exit_price = float(executable[offset])
                reason = (
                    "STOP"
                    if math.isclose(exit_price, float(state["stop_price"]), abs_tol=1e-12)
                    else "STOP_SLIPPAGE"
                )
            else:
                exit_price = float(state["target_price"])
                reason = "TARGET"
            _finalize_exit(
                state,
                exit_ms=int(times[index]),
                exit_price=exit_price,
                reason=reason,
                economics=economics,
            )
            return state
    state["last_tick_time_msc"] = int(times[-1])
    if horizon is None or int(times[-1]) < int(horizon):
        return state
    horizon_index = _first_index(times, int(horizon))
    if horizon_index < len(times):
        if int(times[horizon_index]) - int(horizon) > int(maximum_horizon_gap_minutes) * 60_000:
            raise ValueError(f"No horizon quote within locked gap: {state['candidate_id']}")
        exit_price = float(
            bids[horizon_index] if state["direction"] == "LONG" else asks[horizon_index]
        )
        _finalize_exit(
            state,
            exit_ms=int(times[horizon_index]),
            exit_price=exit_price,
            reason="FIXED_HORIZON",
            economics=economics,
        )
    return state


def five_second_cycles(ticks: TickDay, poll_seconds: int) -> dict[str, np.ndarray]:
    if not len(ticks.times):
        return {
            "cycle_ms": np.asarray([], dtype=np.int64),
            "tick_ms": np.asarray([], dtype=np.int64),
            "bid": np.asarray([], dtype=float),
            "ask": np.asarray([], dtype=float),
        }
    poll_ms = int(poll_seconds) * 1000
    first = ((int(ticks.times[0]) + poll_ms - 1) // poll_ms) * poll_ms
    cycles = np.arange(first, int(ticks.times[-1]) + 1, poll_ms, dtype=np.int64)
    indexes = np.searchsorted(ticks.times, cycles, side="right") - 1
    valid = indexes >= 0
    return {
        "cycle_ms": cycles[valid],
        "tick_ms": ticks.times[indexes[valid]],
        "bid": ticks.bids[indexes[valid]],
        "ask": ticks.asks[indexes[valid]],
    }


def resolution_to_replay_candidate(
    replay: Any,
    state: Mapping[str, Any],
    source: Mapping[str, Any],
    *,
    additional_cost_usd: float = 0.0,
    additional_cost_r: float = 0.0,
):
    if state["status"] != "EXECUTED":
        raise ValueError("Only executed resolutions become replay candidates")
    risk = float(state["risk_usd"])
    stress_cost = float(additional_cost_usd) + float(additional_cost_r) * risk
    return replay.Candidate(
        trade_id=str(state["candidate_id"]),
        source_id=str(state["source_id"]),
        specialist_id=str(state["specialist_id"]),
        sleeve_type=str(state["sleeve_type"]),
        entry_ms=int(state["entry_time_msc"]),
        exit_ms=int(state["exit_time_msc"]),
        direction=str(state["direction"]),
        risk_usd=risk,
        pnl_usd=float(state["pnl_usd"]) - stress_cost,
        entry_price=float(state["entry_price"]),
        exit_price=float(state["exit_price"]),
        open_cost_usd=float(state["ticket_cost_usd"]) + stress_cost,
        maximum_risk_usd=float(source["maximum_risk_usd"]),
        maximum_spread_r=float(source["maximum_spread_r"]),
        maximum_open_positions=int(source["maximum_open_positions"]),
        maximum_entries_per_utc_day=int(source["maximum_entries_per_utc_day"]),
        maximum_entry_gap_minutes=int(source["maximum_entry_gap_minutes"]),
        cooldown_minutes=int(source.get("same_direction_post_loss_cooldown_minutes", 0)),
        event_id=(None if state.get("event_id") in (None, "") else str(state["event_id"])),
    )


def warm_started_challenger_class(base: type, warm_start: Mapping[str, Any]) -> type:
    class WarmStarted(base):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            rows: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
            for row in warm_start["rows"]:
                rows[str(row["source_id"])].append(row)
            for source_id, count in warm_start[
                "retained_history_counts_by_source"
            ].items():
                ordered = sorted(
                    rows.get(str(source_id), []),
                    key=lambda item: (
                        utc_timestamp(item["closed_at_utc"]),
                        str(item["candidate_id"]),
                    ),
                )
                self.source_closed[str(source_id)].extend(
                    float(item["pnl_usd"])
                    for item in ordered[-int(self.veto_policy["lookback_closed_trades"]) :]
                )
                self.source_closed_count[str(source_id)] = int(count)
                consecutive = 0
                for item in reversed(ordered):
                    if float(item["pnl_usd"]) >= 0.0:
                        break
                    consecutive += 1
                self.source_consecutive_losses[str(source_id)] = consecutive

    WarmStarted.__name__ = "WarmStartedDynamicV6CapacityTwin"
    return WarmStarted


def load_causal_scores(
    records: Sequence[Mapping[str, Any]],
    *,
    expected_contract_sha256: str,
    maximum_delay_seconds: int,
    maximum_feature_age_minutes: int,
) -> tuple[
    dict[str, float],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, Any],
]:
    ranks: dict[str, float] = {}
    features: dict[str, dict[str, Any]] = {}
    timing: dict[str, dict[str, Any]] = {}
    seen: set[str] = set()
    late = 0
    incomplete_features = 0
    for record in records:
        if str(record.get("event_type")) != "SCORE_DECISION":
            continue
        payload = record["payload"]
        if str(payload.get("prospective_contract_sha256")) != expected_contract_sha256:
            raise ValueError("Score evidence belongs to another prospective contract")
        candidate_id = str(payload["candidate_id"])
        if candidate_id in seen:
            raise ValueError(f"Duplicate score evidence: {candidate_id}")
        seen.add(candidate_id)
        observed = utc_timestamp(record["observed_at_utc"])
        entry = utc_timestamp(payload["entry_time_utc"])
        if observed > entry + pd.Timedelta(seconds=int(maximum_delay_seconds)):
            late += 1
            continue
        rank = float(payload["causal_rank"])
        if not math.isfinite(rank):
            raise ValueError(f"Non-finite causal rank: {candidate_id}")
        feature_bar_text = payload.get("feature_bar_time_utc")
        feature_bar = None if feature_bar_text in (None, "") else utc_timestamp(feature_bar_text)
        feature_complete = bool(payload.get("causal_policy_features_complete"))
        if feature_complete and feature_bar is None:
            raise ValueError(f"Complete feature evidence lacks bar time: {candidate_id}")
        if feature_bar is not None:
            if feature_bar > entry:
                raise ValueError(f"Post-entry feature bar: {candidate_id}")
            if entry - feature_bar > pd.Timedelta(minutes=int(maximum_feature_age_minutes)):
                raise ValueError(f"Stale causal feature bar: {candidate_id}")
        feature_values = {
            name: payload.get(name)
            for name in ("atr_ratio", "dist_hi_24h", "ret_4h", "ret_24h")
        }
        if feature_complete:
            numeric = np.asarray(list(feature_values.values()), dtype=float)
            if not np.isfinite(numeric).all():
                raise ValueError(f"Complete feature evidence is non-finite: {candidate_id}")
        else:
            incomplete_features += 1
        ranks[candidate_id] = rank
        features[candidate_id] = {
            "execution_source_id": str(payload["source_id"]),
            "direction": str(payload.get("candidate_direction")),
            "rank": rank,
            **feature_values,
        }
        timing[candidate_id] = {
            "observed_at_utc": observed.isoformat().replace("+00:00", "Z"),
            "entry_time_utc": entry.isoformat().replace("+00:00", "Z"),
            "feature_bar_time_utc": (
                None if feature_bar is None else feature_bar.isoformat().replace("+00:00", "Z")
            ),
            "causal_policy_features_complete": feature_complete,
        }
    return ranks, features, timing, {
        "timely_score_rows": len(ranks),
        "late_score_rows": late,
        "incomplete_feature_rows": incomplete_features,
    }
