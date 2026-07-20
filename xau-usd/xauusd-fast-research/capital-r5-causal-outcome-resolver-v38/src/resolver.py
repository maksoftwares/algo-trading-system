from __future__ import annotations

import csv
from dataclasses import dataclass
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import re
import struct
import sys
from types import SimpleNamespace
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "capital_r5_causal_outcome_resolver_v38.json"
DATE_PATTERN = re.compile(r"_ticks_(\d{8})\.csv$")

CANDIDATE_FIELDS = frozenset(
    {
        "candidate_id",
        "origin_attempt",
        "origin_variant_id",
        "regime_owner",
        "mechanic",
        "geometry_id",
        "direction_sign",
        "direction",
        "signal_atr",
        "stop_atr",
        "target_r",
        "hold_hours",
        "parameters_json",
        "signal_time_utc",
        "scheduled_entry_time_utc",
        "rule_dependency_sha256",
    }
)
FORBIDDEN_CANDIDATE_FIELDS = frozenset(
    {
        "entry_price",
        "exit_price",
        "exit_reason",
        "gross_r",
        "pnl",
        "profit",
        "stress_net_r",
        "target",
        "stop",
    }
)
TICK_FIELDS = (
    "schema_version",
    "timestamp_utc",
    "tick_time_msc",
    "account_login",
    "account_server",
    "symbol",
    "bid",
    "ask",
    "spread_price",
    "dry_run",
    "trade_permission",
    "broker_action_allowed",
    "python_execution_authorized",
)
FINAL_STATUSES = frozenset({"EXECUTED", "REJECTED"})


@dataclass(frozen=True)
class Quote:
    timestamp_ms: int
    bid: float
    ask: float


class FrameTickStore:
    def __init__(self, ticks: pd.DataFrame) -> None:
        if ticks.empty:
            self.times = np.array([], dtype=np.int64)
            self.bids = np.array([], dtype=float)
            self.asks = np.array([], dtype=float)
            return
        self.times = ticks["tick_time_msc"].to_numpy(dtype=np.int64)
        self.bids = ticks["bid"].to_numpy(dtype=float)
        self.asks = ticks["ask"].to_numpy(dtype=float)
        if bool(np.any(np.diff(self.times) <= 0)):
            raise ValueError("V38 tick timestamps are not strictly increasing")

    @property
    def latest_timestamp_ms(self) -> int | None:
        return None if len(self.times) == 0 else int(self.times[-1])

    def first_quote_at_or_after(
        self, timestamp_ms: int, maximum_delay_ms: int
    ) -> Quote | None:
        index = int(np.searchsorted(self.times, int(timestamp_ms), side="left"))
        if index >= len(self.times):
            return None
        found = int(self.times[index])
        if found - int(timestamp_ms) > int(maximum_delay_ms):
            return None
        return Quote(found, float(self.bids[index]), float(self.asks[index]))

    def segments(
        self, start_ms: int, end_ms: int
    ) -> Iterable[tuple[np.ndarray, np.ndarray, np.ndarray]]:
        if end_ms < start_ms or len(self.times) == 0:
            return ()
        start = int(np.searchsorted(self.times, int(start_ms), side="left"))
        end = int(np.searchsorted(self.times, int(end_ms), side="right"))
        if start >= end:
            return ()
        return ((self.times[start:end], self.bids[start:end], self.asks[start:end]),)


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return sha256_bytes(encoded)


def _repo_path(repo_root: Path, relative: str) -> Path:
    root = repo_root.resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"V38 dependency escaped repository: {relative}") from exc
    return path


def verify_contract(
    config: Mapping[str, Any], repo_root: Path = REPO_ROOT, package_root: Path = ROOT
) -> dict[str, Any]:
    output = package_root / str(config["outputs"]["directory"])
    path = output / str(config["outputs"]["contract_lock"])
    if not path.is_file():
        raise FileNotFoundError("V38 contract lock is absent")
    lock = json.loads(path.read_text(encoding="utf-8"))
    work = {key: value for key, value in lock.items() if key != "contract_sha256"}
    if canonical_sha256(work) != str(lock.get("contract_sha256")):
        raise ValueError("V38 contract self-hash mismatch")
    for relative, record in lock["package_files"].items():
        file_path = (package_root / relative).resolve()
        if int(file_path.stat().st_size) != int(record["bytes"]):
            raise ValueError(f"V38 package size changed: {relative}")
        if sha256_file(file_path) != str(record["sha256"]):
            raise ValueError(f"V38 package hash changed: {relative}")
    for relative, record in lock["dependencies"].items():
        file_path = _repo_path(repo_root, relative)
        if int(file_path.stat().st_size) != int(record["bytes"]):
            raise ValueError(f"V38 dependency size changed: {relative}")
        if sha256_file(file_path) != str(record["sha256"]):
            raise ValueError(f"V38 dependency hash changed: {relative}")
    return lock


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_frozen_execution(
    config: Mapping[str, Any], repo_root: Path = REPO_ROOT
) -> Any:
    return load_module(
        "capital_r5_v38_frozen_execution",
        _repo_path(repo_root, str(config["source"]["v9_execution_module"])),
    )


def utc_timestamp(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError(f"V38 timestamp is timezone-naive: {value}")
    return timestamp.tz_convert("UTC")


def utc_text(value: Any) -> str:
    return utc_timestamp(value).isoformat().replace("+00:00", "Z")


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
        )
    os.replace(temporary, path)


def stable_line_prefix(path: Path) -> bytes:
    if not path.is_file():
        return b""
    size = int(path.stat().st_size)
    with path.open("rb") as handle:
        payload = handle.read(size)
    if len(payload) != size:
        raise ValueError(f"V38 short read: {path}")
    newline = payload.rfind(b"\n")
    return b"" if newline < 0 else payload[: newline + 1]


def verify_source_prefix(snapshot: bytes, state: Mapping[str, Any] | None) -> None:
    if not state:
        return
    previous_bytes = int(state["source_prefix_bytes"])
    if len(snapshot) < previous_bytes:
        raise ValueError("V38 candidate source was truncated")
    if sha256_bytes(snapshot[:previous_bytes]) != str(state["source_prefix_sha256"]):
        raise ValueError("V38 candidate source consumed prefix was mutated")


def verify_resolution_prefix(snapshot: bytes, state: Mapping[str, Any] | None) -> None:
    if not state:
        return
    previous_bytes = int(state.get("resolution_prefix_bytes", 0))
    previous_sha = str(state.get("resolution_prefix_sha256", sha256_bytes(b"")))
    if len(snapshot) < previous_bytes:
        raise ValueError("V38 resolution ledger was truncated")
    if sha256_bytes(snapshot[:previous_bytes]) != previous_sha:
        raise ValueError("V38 resolution ledger consumed prefix was mutated")


def _candidate_identifier(origin_attempt: int, signal_time: pd.Timestamp) -> str:
    payload = f"{origin_attempt}|{signal_time.isoformat()}".encode("ascii")
    return hashlib.sha256(payload).hexdigest()[:24]


def candidate_fact_sha256(record: Mapping[str, Any]) -> str:
    return canonical_sha256({key: record[key] for key in sorted(CANDIDATE_FIELDS)})


def validate_candidate(
    record: Mapping[str, Any], config: Mapping[str, Any]
) -> dict[str, Any]:
    fields = frozenset(record)
    if fields != CANDIDATE_FIELDS:
        missing = sorted(CANDIDATE_FIELDS.difference(fields))
        extra = sorted(fields.difference(CANDIDATE_FIELDS))
        raise ValueError(
            f"V38 candidate schema changed; missing={missing}, extra={extra}"
        )
    if fields.intersection(FORBIDDEN_CANDIDATE_FIELDS):
        raise ValueError("V38 candidate source contains an economic outcome")
    frozen = config["frozen_identity"]
    attempt = int(record["origin_attempt"])
    if attempt not in {int(value) for value in frozen["component_attempts"]}:
        raise ValueError(f"V38 unexpected component attempt: {attempt}")
    signal = utc_timestamp(record["signal_time_utc"])
    scheduled = utc_timestamp(record["scheduled_entry_time_utc"])
    if signal != scheduled:
        raise ValueError("V38 candidate violates frozen signal/entry time parity")
    if signal < utc_timestamp(frozen["forward_start_inclusive_utc"]):
        raise ValueError("V38 candidate predates the frozen forward boundary")
    expected_id = _candidate_identifier(attempt, signal)
    if str(record["candidate_id"]) != expected_id:
        raise ValueError("V38 candidate ID does not match its frozen identity")
    direction = int(record["direction_sign"])
    expected_direction = (
        "LONG" if direction == 1 else "SHORT" if direction == -1 else None
    )
    if expected_direction is None or str(record["direction"]) != expected_direction:
        raise ValueError("V38 candidate direction is invalid")
    for field in ("signal_atr", "stop_atr", "target_r", "hold_hours"):
        value = float(record[field])
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(f"V38 candidate has invalid {field}")
    parameters = json.loads(str(record["parameters_json"]))
    if not isinstance(parameters, dict):
        raise ValueError("V38 candidate parameters are not a JSON object")
    if str(record["rule_dependency_sha256"]) != str(
        frozen["v35_rule_dependency_sha256"]
    ):
        raise ValueError("V38 candidate rule dependency changed")
    normalized = dict(record)
    normalized["origin_attempt"] = attempt
    normalized["direction_sign"] = direction
    normalized["signal_atr"] = float(record["signal_atr"])
    normalized["stop_atr"] = float(record["stop_atr"])
    normalized["target_r"] = float(record["target_r"])
    normalized["hold_hours"] = float(record["hold_hours"])
    normalized["signal_time"] = signal
    normalized["scheduled_entry_time"] = scheduled
    normalized["candidate_fact_sha256"] = candidate_fact_sha256(record)
    return normalized


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
            raise ValueError(f"V38 invalid candidate JSONL line {line_number}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"V38 candidate line {line_number} is not an object")
        rows.append(validate_candidate(value, config))
    ids = [str(row["candidate_id"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("V38 candidate source contains duplicate IDs")
    return sorted(
        rows,
        key=lambda row: (
            row["scheduled_entry_time"],
            int(row["origin_attempt"]),
            str(row["candidate_id"]),
        ),
    )


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_resolution_ledger(path: Path) -> list[dict[str, Any]]:
    snapshot = stable_line_prefix(path)
    if path.is_file() and int(path.stat().st_size) != len(snapshot):
        raise ValueError("V38 resolution ledger has a partial trailing record")
    rows: list[dict[str, Any]] = []
    for line_number, raw in enumerate(snapshot.splitlines(), start=1):
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError(f"V38 resolution line {line_number} is not an object")
        if str(value.get("resolution_status")) not in FINAL_STATUSES:
            raise ValueError(f"V38 resolution line {line_number} has invalid status")
        rows.append(value)
    ids = [str(row.get("candidate_id")) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("V38 resolution ledger contains duplicate candidate IDs")
    return rows


def append_resolution_records(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    block = "".join(
        json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"
        for row in rows
    )
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(block)
        handle.flush()
        os.fsync(handle.fileno())


def _boolean_series(values: pd.Series, field: str) -> pd.Series:
    normalized = values.astype(str).str.strip().str.lower()
    if not normalized.isin(("true", "false")).all():
        raise ValueError(f"V38 tick source contains invalid {field}")
    return normalized.eq("true")


def _parse_tick_frame(
    snapshot: bytes,
    path: Path,
    source_file_order: int,
    config: Mapping[str, Any],
) -> pd.DataFrame:
    if not snapshot:
        return pd.DataFrame(columns=(*TICK_FIELDS, "source_file_order", "source_row"))
    frame = pd.read_csv(io.BytesIO(snapshot), usecols=list(TICK_FIELDS))
    if frame.empty:
        return frame
    source = config["source"]
    quality = config["data_quality"]
    if not frame["schema_version"].eq(source["tick_schema_version"]).all():
        raise ValueError(f"V38 tick schema mismatch: {path}")
    login = pd.to_numeric(frame["account_login"], errors="coerce")
    if login.isna().any() or not login.eq(int(source["account_login"])).all():
        raise ValueError(f"V38 tick account mismatch: {path}")
    if not frame["account_server"].eq(source["account_server"]).all():
        raise ValueError(f"V38 tick server mismatch: {path}")
    if not frame["symbol"].eq(source["symbol"]).all():
        raise ValueError(f"V38 tick symbol mismatch: {path}")
    for field in ("tick_time_msc", "bid", "ask", "spread_price"):
        frame[field] = pd.to_numeric(frame[field], errors="coerce")
    if frame[["tick_time_msc", "bid", "ask", "spread_price"]].isna().any().any():
        raise ValueError(f"V38 tick source has invalid numeric values: {path}")
    frame["tick_time_msc"] = frame["tick_time_msc"].astype(np.int64)
    parsed = pd.to_datetime(
        frame["timestamp_utc"],
        format="%Y.%m.%d %H:%M:%S.%fZ",
        utc=True,
        errors="coerce",
    )
    if parsed.isna().any():
        raise ValueError(f"V38 tick source has invalid UTC timestamps: {path}")
    parsed_ms = parsed.array.as_unit("ms").asi8.astype(np.int64, copy=False)
    disagreement = np.abs(parsed_ms - frame["tick_time_msc"].to_numpy(dtype=np.int64))
    if bool(np.any(disagreement > int(quality["maximum_timestamp_disagreement_ms"]))):
        raise ValueError(f"V38 tick timestamp disagreement: {path}")
    bid = frame["bid"].to_numpy(dtype=float)
    ask = frame["ask"].to_numpy(dtype=float)
    spread = frame["spread_price"].to_numpy(dtype=float)
    if bool(np.any((bid <= 0.0) | (ask < bid) | (spread < 0.0))):
        raise ValueError(f"V38 tick source contains invalid quotes: {path}")
    if bool(
        np.any(
            np.abs((ask - bid) - spread) > float(quality["maximum_spread_field_error"])
        )
    ):
        raise ValueError(f"V38 tick spread field mismatch: {path}")
    dry_run = _boolean_series(frame["dry_run"], "dry_run")
    if bool(quality["require_dry_run_true"]) and not dry_run.all():
        raise ValueError(f"V38 source is not entirely dry-run: {path}")
    if bool(quality["require_all_authority_flags_false"]):
        for field in (
            "trade_permission",
            "broker_action_allowed",
            "python_execution_authorized",
        ):
            if _boolean_series(frame[field], field).any():
                raise ValueError(f"V38 source has authority enabled: {field}")
    frame["source_file_order"] = int(source_file_order)
    frame["source_row"] = np.arange(len(frame), dtype=np.int64)
    return frame


def load_tick_snapshots(
    paths: Sequence[Path], config: Mapping[str, Any]
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    frames: list[pd.DataFrame] = []
    records: list[dict[str, Any]] = []
    for order, path in enumerate(sorted(Path(value) for value in paths)):
        snapshot = stable_line_prefix(path)
        frames.append(_parse_tick_frame(snapshot, path, order, config))
        records.append(
            {
                "path": str(path.resolve()).replace("\\", "/"),
                "prefix_bytes": len(snapshot),
                "prefix_sha256": sha256_bytes(snapshot),
            }
        )
    if not frames:
        return pd.DataFrame(columns=TICK_FIELDS), records
    raw = pd.concat(frames, ignore_index=True)
    if raw.empty:
        return raw, records
    ordered = raw.sort_values(
        ["tick_time_msc", "source_file_order", "source_row"], kind="mergesort"
    )
    ticks = (
        ordered.drop_duplicates("tick_time_msc", keep="last")
        .sort_values("tick_time_msc", kind="mergesort")
        .reset_index(drop=True)
    )
    if bool(np.any(np.diff(ticks["tick_time_msc"].to_numpy(dtype=np.int64)) <= 0)):
        raise ValueError("V38 deduplicated ticks are not strictly increasing")
    return ticks, records


def tick_date(path: Path) -> pd.Timestamp:
    match = DATE_PATTERN.search(path.name)
    if not match:
        raise ValueError(f"V38 tick filename has no UTC date: {path.name}")
    return pd.Timestamp(match.group(1), tz="UTC")


def select_tick_paths(
    paths: Sequence[Path],
    candidates: Sequence[Mapping[str, Any]],
    execution: Mapping[str, Any],
) -> list[Path]:
    if not candidates:
        return []
    start = min(utc_timestamp(row["scheduled_entry_time"]) for row in candidates).floor(
        "D"
    )
    maximum_gap = pd.Timedelta(hours=float(execution["maximum_horizon_gap_hours"]))
    end = max(
        utc_timestamp(row["scheduled_entry_time"])
        + pd.Timedelta(hours=float(row["hold_hours"]))
        + maximum_gap
        for row in candidates
    ).floor("D")
    return [path for path in sorted(paths) if start <= tick_date(path) <= end]


def _last_complete_row(snapshot: bytes) -> dict[str, str] | None:
    lines = snapshot.splitlines()
    if len(lines) < 2:
        return None
    header = next(csv.reader([lines[0].decode("utf-8")]))
    values = next(csv.reader([lines[-1].decode("utf-8")]))
    if len(values) != len(header):
        raise ValueError("V38 latest tick row is malformed")
    return dict(zip(header, values))


def latest_observed_timestamp_ms(
    paths: Sequence[Path], config: Mapping[str, Any]
) -> int | None:
    for path in sorted(paths, reverse=True):
        row = _last_complete_row(stable_line_prefix(path))
        if row is None:
            continue
        source = config["source"]
        if row.get("schema_version") != str(source["tick_schema_version"]):
            raise ValueError("V38 latest tick schema changed")
        if int(row.get("account_login", -1)) != int(source["account_login"]):
            raise ValueError("V38 latest tick account changed")
        if row.get("account_server") != str(source["account_server"]):
            raise ValueError("V38 latest tick server changed")
        if row.get("symbol") != str(source["symbol"]):
            raise ValueError("V38 latest tick symbol changed")
        if str(row.get("dry_run", "")).lower() != "true":
            raise ValueError("V38 latest tick is not dry-run")
        for field in (
            "trade_permission",
            "broker_action_allowed",
            "python_execution_authorized",
        ):
            if str(row.get(field, "")).lower() != "false":
                raise ValueError(f"V38 latest tick has authority enabled: {field}")
        return int(row["tick_time_msc"])
    return None


def quote_slice_evidence(
    ticks: pd.DataFrame, start_ms: int, end_ms: int
) -> dict[str, Any]:
    if ticks.empty:
        selected = ticks
    else:
        selected = ticks.loc[
            ticks["tick_time_msc"].between(int(start_ms), int(end_ms), inclusive="both")
        ]
    digest = hashlib.sha256()
    for row in selected[["tick_time_msc", "bid", "ask"]].itertuples(index=False):
        digest.update(
            struct.pack(">qdd", int(row.tick_time_msc), float(row.bid), float(row.ask))
        )
    return {
        "quote_slice_rows": int(len(selected)),
        "quote_slice_first_timestamp_ms": (
            None if selected.empty else int(selected["tick_time_msc"].iat[0])
        ),
        "quote_slice_last_timestamp_ms": (
            None if selected.empty else int(selected["tick_time_msc"].iat[-1])
        ),
        "quote_slice_sha256": digest.hexdigest(),
    }


def _outcome(
    candidate: Any,
    entry_quote: Quote,
    exit_quote: Quote,
    exit_price: float,
    exit_reason: str,
    execution: Mapping[str, Any],
    risk: float,
    stop: float,
    target: float,
    horizon_quote: Quote | None,
) -> dict[str, Any]:
    direction = int(candidate.direction_sign)
    entry = float(entry_quote.ask if direction > 0 else entry_quote.bid)
    risk_usd = risk * float(execution["ounces_at_lot_size"])
    entry_time = pd.Timestamp(entry_quote.timestamp_ms, unit="ms", tz="UTC")
    exit_time = pd.Timestamp(exit_quote.timestamp_ms, unit="ms", tz="UTC")
    gross_r = direction * (float(exit_price) - entry) / risk
    holding_days = max(0.0, (exit_time - entry_time).total_seconds() / 86_400.0)
    extra_cost_r = (
        float(execution["ticket_cost_usd"])
        + holding_days * float(execution["holding_cost_per_24h_usd"])
    ) / risk_usd
    scheduled = utc_timestamp(candidate.scheduled_entry_time)
    deadline = scheduled + pd.Timedelta(hours=float(candidate.hold_hours))
    return {
        "candidate_id": str(candidate.candidate_id),
        "origin_attempt": int(candidate.origin_attempt),
        "origin_variant_id": str(candidate.origin_variant_id),
        "regime_owner": str(candidate.regime_owner),
        "mechanic": str(candidate.mechanic),
        "geometry_id": str(candidate.geometry_id),
        "signal_time": utc_timestamp(candidate.signal_time),
        "scheduled_entry_time": scheduled,
        "entry_time": entry_time,
        "exit_time": exit_time,
        "entry_tick_timestamp_ms": int(entry_quote.timestamp_ms),
        "exit_tick_timestamp_ms": int(exit_quote.timestamp_ms),
        "direction": "LONG" if direction > 0 else "SHORT",
        "direction_sign": direction,
        "entry_price": entry,
        "exit_price": float(exit_price),
        "stop": stop,
        "target": target,
        "risk_price": risk,
        "risk_usd": risk_usd,
        "entry_spread_r": float(entry_quote.ask - entry_quote.bid) / risk,
        "gross_r": gross_r,
        "stress_net_r": gross_r - extra_cost_r - float(execution["stress_slippage_r"]),
        "holding_minutes": (exit_time - entry_time).total_seconds() / 60.0,
        "horizon_delay_minutes": (
            0.0
            if horizon_quote is None
            else max(
                0.0,
                (
                    pd.Timestamp(horizon_quote.timestamp_ms, unit="ms", tz="UTC")
                    - deadline
                ).total_seconds()
                / 60.0,
            )
        ),
        "exit_reason": exit_reason,
        "raw_tick_execution": True,
    }


def resolve_candidate_causally(
    candidate: Any,
    tick_store: FrameTickStore,
    execution_module: Any,
    execution: Mapping[str, Any],
    observed_through_ms: int | None,
) -> tuple[dict[str, Any] | None, str | None, str | None, int]:
    scheduled = utc_timestamp(candidate.scheduled_entry_time)
    scheduled_ms = int(scheduled.value // 1_000_000)
    entry_gap_ms = int(float(execution["maximum_entry_gap_minutes"]) * 60_000)
    observed_through = -1 if observed_through_ms is None else int(observed_through_ms)
    entry_quote = tick_store.first_quote_at_or_after(scheduled_ms, entry_gap_ms)
    if entry_quote is None:
        cutoff = scheduled_ms + entry_gap_ms
        if observed_through < cutoff:
            return None, None, "AWAITING_ENTRY_WINDOW", cutoff
        return None, "NO_TIMELY_ENTRY_QUOTE", None, cutoff

    direction = int(candidate.direction_sign)
    entry = float(entry_quote.ask if direction > 0 else entry_quote.bid)
    risk = float(candidate.stop_atr) * float(candidate.signal_atr)
    if not np.isfinite(risk) or risk <= 0.0:
        return None, "INVALID_RISK", None, int(entry_quote.timestamp_ms)
    spread = float(entry_quote.ask - entry_quote.bid)
    if spread < 0.0 or spread / risk > float(execution["maximum_entry_spread_r"]):
        return None, "ENTRY_SPREAD_R", None, int(entry_quote.timestamp_ms)
    risk_usd = risk * float(execution["ounces_at_lot_size"])
    if risk_usd > float(execution["maximum_research_risk_usd"]):
        return None, "RISK_CEILING", None, int(entry_quote.timestamp_ms)

    stop = entry - direction * risk
    target = entry + direction * float(candidate.target_r) * risk
    deadline = scheduled + pd.Timedelta(hours=float(candidate.hold_hours))
    deadline_ms = int(deadline.value // 1_000_000)
    horizon_gap_ms = int(float(execution["maximum_horizon_gap_hours"]) * 3_600_000)
    horizon_quote = tick_store.first_quote_at_or_after(deadline_ms, horizon_gap_ms)
    horizon_cutoff_ms = deadline_ms + horizon_gap_ms
    search_end = (
        int(horizon_quote.timestamp_ms) - 1
        if horizon_quote is not None
        else (
            None
            if tick_store.latest_timestamp_ms is None
            else min(int(tick_store.latest_timestamp_ms), horizon_cutoff_ms - 1)
        )
    )
    observed = None
    if search_end is not None and search_end >= int(entry_quote.timestamp_ms):
        observed = execution_module.first_exit_hit(
            tick_store,
            int(entry_quote.timestamp_ms),
            int(search_end),
            direction,
            stop,
            target,
            Quote,
        )
    if observed is not None:
        exit_quote, exit_price, exit_reason = observed
        return (
            _outcome(
                candidate,
                entry_quote,
                exit_quote,
                float(exit_price),
                str(exit_reason),
                execution,
                risk,
                stop,
                target,
                horizon_quote,
            ),
            None,
            None,
            int(exit_quote.timestamp_ms),
        )
    if horizon_quote is not None:
        exit_price = float(horizon_quote.bid if direction > 0 else horizon_quote.ask)
        return (
            _outcome(
                candidate,
                entry_quote,
                horizon_quote,
                exit_price,
                "FIXED_HORIZON",
                execution,
                risk,
                stop,
                target,
                horizon_quote,
            ),
            None,
            None,
            int(horizon_quote.timestamp_ms),
        )
    cutoff = deadline_ms + horizon_gap_ms
    if observed_through < cutoff:
        return None, None, "AWAITING_HORIZON_WINDOW", cutoff
    return None, "NO_HORIZON_QUOTE", None, cutoff


def _candidate_namespace(row: Mapping[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(
        candidate_id=str(row["candidate_id"]),
        origin_attempt=int(row["origin_attempt"]),
        origin_variant_id=str(row["origin_variant_id"]),
        regime_owner=str(row["regime_owner"]),
        mechanic=str(row["mechanic"]),
        geometry_id=str(row["geometry_id"]),
        signal_time=utc_timestamp(row["signal_time"]),
        scheduled_entry_time=utc_timestamp(row["scheduled_entry_time"]),
        direction_sign=int(row["direction_sign"]),
        direction=str(row["direction"]),
        signal_atr=float(row["signal_atr"]),
        stop_atr=float(row["stop_atr"]),
        target_r=float(row["target_r"]),
        hold_hours=float(row["hold_hours"]),
    )


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
                raise ValueError(f"V38 non-finite outcome value: {key}")
            result[key] = number
        elif isinstance(value, (np.bool_, bool)):
            result[key] = bool(value)
        else:
            result[key] = value
    return result


def _base_resolution(
    candidate: Mapping[str, Any], now: pd.Timestamp, knowledge_ms: int
) -> dict[str, Any]:
    return {
        "schema_version": "xauusd_capital_r5_component_resolution_v38",
        "candidate_id": str(candidate["candidate_id"]),
        "candidate_fact_sha256": str(candidate["candidate_fact_sha256"]),
        "origin_attempt": int(candidate["origin_attempt"]),
        "resolved_at_utc": utc_text(now),
        "knowledge_time_utc": utc_text(pd.Timestamp(knowledge_ms, unit="ms", tz="UTC")),
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "broker_action_authorized": False,
    }


def _apply_existing_state(
    resolution: Mapping[str, Any],
    position_until: pd.Timestamp,
    daily_count: dict[Any, int],
    maximum_daily: int,
) -> pd.Timestamp:
    if str(resolution["resolution_status"]) != "EXECUTED":
        return position_until
    entry = utc_timestamp(resolution["entry_time_utc"])
    exit_time = utc_timestamp(resolution["exit_time_utc"])
    if entry < position_until:
        raise ValueError("V38 existing executed outcome violates component overlap")
    day = entry.date()
    if daily_count.get(day, 0) >= maximum_daily:
        raise ValueError("V38 existing executed outcome violates component daily cap")
    daily_count[day] = daily_count.get(day, 0) + 1
    return exit_time


def process_candidates(
    candidates: Sequence[Mapping[str, Any]],
    existing_resolutions: Sequence[Mapping[str, Any]],
    historical_trades: pd.DataFrame,
    ticks: pd.DataFrame,
    tick_source_records: Sequence[Mapping[str, Any]],
    observed_through_ms: int | None,
    execution_module: Any,
    execution: Mapping[str, Any],
    now: pd.Timestamp,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    candidate_by_id = {str(row["candidate_id"]): row for row in candidates}
    existing = {str(row["candidate_id"]): row for row in existing_resolutions}
    unknown = sorted(set(existing).difference(candidate_by_id))
    if unknown:
        raise ValueError(f"V38 ledger contains unknown candidate IDs: {unknown[:3]}")
    for candidate_id, resolution in existing.items():
        if str(resolution.get("candidate_fact_sha256")) != str(
            candidate_by_id[candidate_id]["candidate_fact_sha256"]
        ):
            raise ValueError("V38 resolution candidate fact hash mismatch")

    tick_store = FrameTickStore(ticks)
    maximum_daily = int(execution["maximum_trades_per_component_utc_day"])
    source_snapshot_sha = canonical_sha256(
        {"files": [dict(record) for record in tick_source_records]}
    )
    new_rows: list[dict[str, Any]] = []
    pending: dict[str, int] = {}
    attempts = sorted({int(row["origin_attempt"]) for row in candidates})
    historical = historical_trades.copy()
    if not historical.empty:
        historical["entry_time"] = pd.to_datetime(historical["entry_time"], utc=True)
        historical["exit_time"] = pd.to_datetime(historical["exit_time"], utc=True)

    for attempt in attempts:
        old = (
            historical.loc[historical["attempt_no"].eq(attempt)]
            if not historical.empty
            else historical
        )
        position_until = (
            pd.Timestamp.min.tz_localize("UTC")
            if old.empty
            else utc_timestamp(old["exit_time"].max())
        )
        daily_count: dict[Any, int] = {}
        if not old.empty:
            for entry_time, count in (
                old.groupby(old["entry_time"].dt.date).size().items()
            ):
                daily_count[entry_time] = int(count)
        blocked = False
        component = sorted(
            (row for row in candidates if int(row["origin_attempt"]) == attempt),
            key=lambda row: (row["scheduled_entry_time"], str(row["candidate_id"])),
        )
        for candidate in component:
            candidate_id = str(candidate["candidate_id"])
            if candidate_id in existing:
                if blocked:
                    raise ValueError(
                        "V38 has a later resolution after an unresolved predecessor"
                    )
                position_until = _apply_existing_state(
                    existing[candidate_id], position_until, daily_count, maximum_daily
                )
                continue
            if blocked:
                continue
            outcome, rejection, waiting, evidence_end_ms = resolve_candidate_causally(
                _candidate_namespace(candidate),
                tick_store,
                execution_module,
                execution,
                observed_through_ms,
            )
            if waiting is not None:
                pending[waiting] = pending.get(waiting, 0) + 1
                blocked = True
                continue

            base = _base_resolution(candidate, now, evidence_end_ms)
            base["tick_source_snapshot_sha256"] = source_snapshot_sha
            base.update(
                quote_slice_evidence(
                    ticks,
                    int(
                        utc_timestamp(candidate["scheduled_entry_time"]).value
                        // 1_000_000
                    ),
                    int(evidence_end_ms),
                )
            )
            if outcome is None:
                base["resolution_status"] = "REJECTED"
                base["rejection_reason"] = str(rejection)
                new_rows.append(base)
                continue

            entry = utc_timestamp(outcome["entry_time"])
            if entry < position_until:
                base["resolution_status"] = "REJECTED"
                base["rejection_reason"] = "COMPONENT_POSITION_OVERLAP"
                new_rows.append(base)
                continue
            day = entry.date()
            if daily_count.get(day, 0) >= maximum_daily:
                base["resolution_status"] = "REJECTED"
                base["rejection_reason"] = "COMPONENT_DAILY_CAP"
                new_rows.append(base)
                continue
            base.update(_json_outcome(outcome))
            base["resolution_status"] = "EXECUTED"
            base["rejection_reason"] = None
            new_rows.append(base)
            position_until = utc_timestamp(outcome["exit_time"])
            daily_count[day] = daily_count.get(day, 0) + 1
    return new_rows, dict(sorted(pending.items()))


def verify_candidate_status(path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError("V38 V35 candidate status is absent")
    status = read_json(path)
    if str(status.get("status")) != "ACTIVE_READ_ONLY_CANDIDATE_SHADOW":
        raise ValueError("V38 V35 candidate source is not active")
    source = config["source"]
    if int(status.get("account_login", -1)) != int(source["account_login"]):
        raise ValueError("V38 V35 status account changed")
    if str(status.get("account_server")) != str(source["account_server"]):
        raise ValueError("V38 V35 status server changed")
    if str(status.get("symbol")) != str(source["symbol"]):
        raise ValueError("V38 V35 status symbol changed")
    if str(status.get("rule_dependency_sha256")) != str(
        config["frozen_identity"]["v35_rule_dependency_sha256"]
    ):
        raise ValueError("V38 V35 status dependency changed")
    for field in (
        "trade_permission",
        "broker_action_allowed",
        "python_execution_authorized",
    ):
        if bool(status.get(field)):
            raise ValueError(f"V38 V35 status has authority enabled: {field}")
    return status


def validate_frozen_identity(
    config: Mapping[str, Any], repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    source = config["source"]
    identity = config["frozen_identity"]
    v35_lock = read_json(_repo_path(repo_root, str(source["v35_contract_lock"])))
    if str(v35_lock.get("contract_sha256")) != str(identity["v35_contract_sha256"]):
        raise ValueError("V38 V35 contract identity changed")
    if str(v35_lock.get("rule_dependency_sha256")) != str(
        identity["v35_rule_dependency_sha256"]
    ):
        raise ValueError("V38 V35 rule dependency identity changed")
    if [int(value) for value in v35_lock.get("component_attempts", [])] != [
        int(value) for value in identity["component_attempts"]
    ]:
        raise ValueError("V38 V35 component identity changed")
    v9 = read_json(_repo_path(repo_root, str(source["v9_config"])))
    return dict(v9["execution"])


def validate_historical_parity_artifact(
    config: Mapping[str, Any], contract: Mapping[str, Any], package_root: Path = ROOT
) -> dict[str, Any]:
    path = (
        package_root
        / str(config["outputs"]["directory"])
        / str(config["outputs"]["historical_semantic_parity"])
    )
    if not path.is_file():
        raise FileNotFoundError("V38 historical semantic parity artifact is absent")
    parity = read_json(path)
    if str(parity.get("contract_sha256")) != str(contract["contract_sha256"]):
        raise ValueError("V38 parity artifact belongs to another contract")
    identity = config["frozen_identity"]
    if int(parity.get("candidate_rows", -1)) != int(
        identity["historical_candidate_rows"]
    ):
        raise ValueError("V38 historical candidate row parity changed")
    if int(parity.get("signal_equals_entry_rows", -1)) != int(
        identity["historical_candidate_signal_equals_entry_rows"]
    ):
        raise ValueError("V38 historical candidate timing parity changed")
    if not bool(parity.get("semantic_parity_passed")):
        raise ValueError("V38 historical semantic parity did not pass")
    return parity
