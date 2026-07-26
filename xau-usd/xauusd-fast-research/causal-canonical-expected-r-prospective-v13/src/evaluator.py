from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import math
import os
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import ModuleType
from typing import Any

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
V10_ROOT = REPO_ROOT / "xau-usd/xauusd-fast-research/causal-canonical-expected-r-v10"
V38_PATH = (
    REPO_ROOT
    / "xau-usd/xauusd-fast-research"
    / "capital-r5-causal-outcome-resolver-v38/src/resolver.py"
)
V47_PATH = (
    REPO_ROOT
    / "xau-usd/xauusd-fast-research"
    / "capital-r2-r4-prospective-confirmation-v47/src/evaluator.py"
)
AUTHORITY_FIELDS = (
    "trade_permission",
    "broker_action_allowed",
    "broker_action_authorized",
    "python_execution_authorized",
    "python_predictions_authorized",
    "ml_shadow_authorized",
    "ea_consumption_authorized",
    "demo_authorized",
    "live_authorized",
)
FINAL_SCORE_ACTIONS = frozenset(("RETAIN", "VETO", "MODEL_ABSTAIN_RETAIN_ALL"))
FINAL_RESOLUTION_STATUSES = frozenset(("EXECUTED", "REJECTED", "CENSORED"))
M5_MS = 300_000
HOUR_MS = 3_600_000


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


v38 = load_module("expected_r_prospective_v13_v38", V38_PATH)
v47 = load_module("expected_r_prospective_v13_v47", V47_PATH)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(payload: Mapping[str, Any], omitted_key: str) -> str:
    value = dict(payload)
    value.pop(omitted_key, None)
    encoded = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return sha256_bytes(encoded)


def utc_timestamp(value: Any) -> pd.Timestamp:
    result = pd.Timestamp(value)
    if result.tzinfo is None:
        raise ValueError(f"Timezone-naive timestamp: {value}")
    return result.tz_convert("UTC")


def utc_text(value: Any) -> str:
    return utc_timestamp(value).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"Expected JSON object: {path}")
    return value


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, allow_nan=False, indent=2, sort_keys=True)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def stable_jsonl_snapshot(path: Path) -> tuple[list[dict[str, Any]], bytes]:
    if not path.is_file():
        return [], b""
    payload = path.read_bytes()
    if payload and not payload.endswith(b"\n"):
        last_newline = payload.rfind(b"\n")
        payload = b"" if last_newline < 0 else payload[: last_newline + 1]
    rows: list[dict[str, Any]] = []
    for line_number, raw in enumerate(payload.splitlines(), start=1):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL {path}:{line_number}") from exc
        if not isinstance(value, dict):
            raise TypeError(f"Non-object JSONL {path}:{line_number}")
        rows.append(value)
    return rows, payload


def append_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as stream:
        for row in rows:
            encoded = json.dumps(
                dict(row),
                allow_nan=False,
                ensure_ascii=True,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("ascii")
            stream.write(encoded + b"\n")
        stream.flush()
        os.fsync(stream.fileno())


def _is_false(value: Any) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return not bool(value)
    return str(value).strip().lower() in ("false", "0")


def validate_no_authority(row: Mapping[str, Any], label: str) -> None:
    for field in AUTHORITY_FIELDS:
        if field in row and not _is_false(row[field]):
            raise ValueError(f"{label} enables {field}")


def verify_config_hashes(config: Mapping[str, Any]) -> None:
    model = config["model"]
    population = config["candidate_population"]
    checks = (
        (
            model["availability_policy_path"],
            model["availability_policy_sha256"],
            "availability policy",
        ),
        (model["model_path"], model["model_sha256"], "Expected-R model"),
        (
            model["expected_r_module_path"],
            model["expected_r_module_sha256"],
            "Expected-R module",
        ),
        (
            population["v60_config_path"],
            population["v60_config_sha256"],
            "V60 source config",
        ),
    )
    for relative, expected, label in checks:
        path = REPO_ROOT / str(relative)
        if not path.is_file() or sha256_file(path) != str(expected):
            raise ValueError(f"{label} identity changed: {path}")


def verify_contract(package_root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    output = package_root / str(config["outputs"]["directory"])
    path = output / str(config["outputs"]["contract_lock"])
    if not path.is_file():
        raise FileNotFoundError("Expected-R V13 contract lock is absent")
    contract = read_json(path)
    if str(contract.get("contract_sha256")) != canonical_hash(
        contract, "contract_sha256"
    ):
        raise ValueError("Expected-R V13 contract self-hash changed")
    if str(contract["forward_start_inclusive_utc"]) != str(
        config["forward_start_inclusive_utc"]
    ):
        raise ValueError("Expected-R V13 forward boundary changed")
    for record in contract["package_files"]:
        source = package_root / str(record["path"])
        if not source.is_file() or source.stat().st_size != int(record["bytes"]):
            raise ValueError(f"Package file identity changed: {record['path']}")
        if sha256_file(source) != str(record["sha256"]):
            raise ValueError(f"Package file hash changed: {record['path']}")
    for record in contract["dependencies"]:
        source = REPO_ROOT / str(record["path"])
        if not source.is_file() or source.stat().st_size != int(record["bytes"]):
            raise ValueError(f"Dependency identity changed: {record['path']}")
        if sha256_file(source) != str(record["sha256"]):
            raise ValueError(f"Dependency hash changed: {record['path']}")
    if contract.get("aggregate_economics_present_at_lock") is not False:
        raise ValueError("Aggregate economics existed at lock")
    verify_config_hashes(config)
    return contract


def load_v60(config: Mapping[str, Any]) -> tuple[dict[str, Any], ModuleType]:
    population = config["candidate_population"]
    v60_config = read_json(REPO_ROOT / str(population["v60_config_path"]))
    executor = load_module(
        "expected_r_prospective_v13_v60_executor",
        REPO_ROOT / str(population["v60_executor_path"]),
    )
    observed = [str(row["source_id"]) for row in v60_config["sources"]]
    expected = [str(value) for value in population["expected_source_ids"]]
    if observed != expected:
        raise ValueError(f"V60 source registry changed: {observed}")
    if bool(v60_config["authorization"]["ml_runtime_authorized"]):
        raise ValueError("V60 unexpectedly enables ML runtime")
    if bool(v60_config["authorization"]["ml_shadow_authorized"]):
        raise ValueError("V60 unexpectedly enables ML shadow")
    return v60_config, executor


def _candidate_fact(row: Mapping[str, Any]) -> str:
    return canonical_hash(row, "__absent__")


def _source_prefix_state(
    path: Path,
    payload: bytes,
    previous: Mapping[str, Any] | None,
) -> dict[str, Any]:
    old = {} if previous is None else dict(previous)
    old_bytes = int(old.get("bytes", 0))
    old_sha = str(old.get("sha256", sha256_bytes(b"")))
    if len(payload) < old_bytes:
        raise ValueError(f"Candidate source was truncated: {path}")
    if sha256_bytes(payload[:old_bytes]) != old_sha:
        raise ValueError(f"Consumed candidate prefix mutated: {path}")
    return {
        "path": str(path.resolve()).replace("\\", "/"),
        "bytes": len(payload),
        "sha256": sha256_bytes(payload),
    }


def load_candidates(
    config: Mapping[str, Any],
    runtime: Path,
    contract_sha256: str,
    now: pd.Timestamp,
) -> list[dict[str, Any]]:
    v60_config, executor = load_v60(config)
    state_path = runtime / str(config["runtime"]["candidate_prefix_state"])
    previous_state = read_json(state_path) if state_path.is_file() else {}
    previous_sources = {
        str(row["path"]): row for row in previous_state.get("sources", [])
    }
    snapshots: dict[str, tuple[list[dict[str, Any]], bytes]] = {}
    prefix_rows: list[dict[str, Any]] = []
    for source in v60_config["sources"]:
        path = Path(str(source["path"]))
        key = str(path.resolve()).replace("\\", "/")
        if key not in snapshots:
            snapshots[key] = stable_jsonl_snapshot(path)
            prefix_rows.append(
                _source_prefix_state(
                    path,
                    snapshots[key][1],
                    previous_sources.get(key),
                )
            )

    boundary = utc_timestamp(config["forward_start_inclusive_utc"])
    family_map = config["candidate_population"]["source_to_family"]
    candidates: dict[str, dict[str, Any]] = {}
    matched_rows: dict[tuple[str, int], int] = {}
    for source in v60_config["sources"]:
        source_id = str(source["source_id"])
        path_key = str(Path(str(source["path"])).resolve()).replace("\\", "/")
        rows = snapshots[path_key][0]
        for row_index, raw in enumerate(rows):
            validate_no_authority(raw, "candidate")
            candidate = executor.normalize_candidate(
                raw,
                source,
                float(config["candidate_population"]["point_size"]),
            )
            if candidate is None:
                continue
            matched_rows[(path_key, row_index)] = (
                matched_rows.get((path_key, row_index), 0) + 1
            )
            if candidate.scheduled_at < boundary.to_pydatetime():
                continue
            family_id = str(family_map[source_id])
            fact = {
                "candidate_id": candidate.candidate_id,
                "source_id": source_id,
                "specialist_id": candidate.specialist_id,
                "family_id": family_id,
                "sleeve_type": candidate.sleeve_type,
                "magic": int(candidate.magic),
                "scheduled_entry_time_utc": utc_text(candidate.scheduled_at),
                "direction": candidate.direction,
                "stop_distance": float(candidate.stop_distance),
                "initial_risk_usd": float(candidate.initial_risk_usd),
                "event_id": candidate.event_id,
                "maximum_open_positions": int(candidate.maximum_open_positions),
                "maximum_entries_per_utc_day": int(
                    candidate.maximum_entries_per_utc_day
                ),
                "target_r": (
                    None if candidate.target_r is None else float(candidate.target_r)
                ),
                "hold_hours": (
                    None
                    if candidate.hold_hours is None
                    else float(candidate.hold_hours)
                ),
                "source_path": path_key,
                "raw_candidate_sha256": _candidate_fact(raw),
            }
            fact["candidate_fact_sha256"] = _candidate_fact(fact)
            existing = candidates.get(candidate.candidate_id)
            if existing is not None and existing != fact:
                raise ValueError(
                    f"Conflicting duplicate candidate: {candidate.candidate_id}"
                )
            candidates[candidate.candidate_id] = fact

    if any(count != 1 for count in matched_rows.values()):
        raise ValueError("A V60 candidate row matched multiple frozen source adapters")
    ordered = sorted(
        candidates.values(),
        key=lambda row: (
            utc_timestamp(row["scheduled_entry_time_utc"]),
            str(row["source_id"]),
            str(row["candidate_id"]),
        ),
    )
    atomic_write_json(
        state_path,
        {
            "schema_version": "xauusd_expected_r_v13_candidate_prefix_state",
            "updated_at_utc": utc_text(now),
            "contract_sha256": contract_sha256,
            "sources": sorted(prefix_rows, key=lambda row: str(row["path"])),
            "post_boundary_candidate_rows": len(ordered),
        },
    )
    return ordered


def _ledger_by_id(
    path: Path,
    candidates: Mapping[str, Mapping[str, Any]],
    *,
    status_field: str,
    allowed: frozenset[str],
) -> dict[str, dict[str, Any]]:
    rows, _ = stable_jsonl_snapshot(path)
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        candidate_id = str(row.get("candidate_id", ""))
        if not candidate_id or candidate_id in result:
            raise ValueError(f"Duplicate ledger candidate: {path}")
        if candidate_id not in candidates:
            raise ValueError(f"Unknown ledger candidate: {path}")
        if str(row.get(status_field)) not in allowed:
            raise ValueError(f"Invalid ledger status: {path}")
        if str(row.get("candidate_fact_sha256")) != str(
            candidates[candidate_id]["candidate_fact_sha256"]
        ):
            raise ValueError(f"Ledger candidate fact changed: {path}")
        validate_no_authority(row, "ledger")
        result[candidate_id] = row
    return result


def load_model(config: Mapping[str, Any]) -> dict[str, Any]:
    model_config = config["model"]
    policy = read_json(REPO_ROOT / str(model_config["availability_policy_path"]))
    if int(policy["actual_final_fit_rows"]) != int(model_config["actual_fit_rows"]):
        raise ValueError("V11 availability fit rows changed")
    if int(policy["minimum_fit_rows"]) != int(model_config["minimum_fit_rows"]):
        raise ValueError("V11 availability minimum changed")
    if not bool(policy["model_available"]):
        raise ValueError("V11 frozen policy unexpectedly has no model")
    if str(policy["v10_model_sha256"]) != str(model_config["model_sha256"]):
        raise ValueError("V11 policy points to a different model")
    if str(V10_ROOT) not in sys.path:
        sys.path.insert(0, str(V10_ROOT))
    payload = joblib.load(REPO_ROOT / str(model_config["model_path"]))
    if str(payload["definition_contract_sha256"]) != str(
        model_config["expected_definition_contract_sha256"]
    ):
        raise ValueError("Expected-R model definition changed")
    expected_families = list(config["candidate_population"]["expected_model_families"])
    if list(payload["families"]) != expected_families:
        raise ValueError("Expected-R model family order changed")
    if int(payload["fit_rows"]) != int(model_config["actual_fit_rows"]):
        raise ValueError("Expected-R model fit population changed")
    return payload


def _tick_paths_between(
    config: Mapping[str, Any], start: pd.Timestamp, end: pd.Timestamp
) -> list[Path]:
    source = config["source"]
    rows: list[tuple[pd.Timestamp, Path]] = []
    for path in Path(str(source["tick_directory"])).glob(
        str(source["tick_filename_glob"])
    ):
        date = v38.tick_date(path)
        if start.floor("D") <= date <= end.floor("D"):
            rows.append((date, path))
    return [path for _, path in sorted(rows)]


def _load_tick_day(
    path: Path, config: Mapping[str, Any]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    ticks, records = v38.load_tick_snapshots([path], config)
    if len(records) != 1:
        raise ValueError(f"Tick source snapshot missing: {path}")
    return ticks, records[0]


def _aggregate_m5(ticks: pd.DataFrame) -> pd.DataFrame:
    if ticks.empty:
        return pd.DataFrame(
            columns=["timestamp_ms", "mid_high", "mid_low", "mid_close"]
        )
    times = ticks["tick_time_msc"].to_numpy(dtype=np.int64)
    mids = (
        ticks["bid"].to_numpy(dtype=float) + ticks["ask"].to_numpy(dtype=float)
    ) / 2.0
    bins = (times // M5_MS) * M5_MS
    unique, starts = np.unique(bins, return_index=True)
    highs = np.maximum.reduceat(mids, starts)
    lows = np.minimum.reduceat(mids, starts)
    ends = np.r_[starts[1:] - 1, len(mids) - 1]
    return pd.DataFrame(
        {
            "timestamp_ms": unique.astype(np.int64),
            "mid_high": highs,
            "mid_low": lows,
            "mid_close": mids[ends],
        }
    )


def market_at_cutoff(
    cutoff: pd.Timestamp, config: Mapping[str, Any]
) -> tuple[pd.DataFrame, float | None, list[dict[str, Any]]]:
    warmup = int(config["data_quality"]["atr_warmup_calendar_days"])
    paths = _tick_paths_between(config, cutoff - pd.Timedelta(days=warmup), cutoff)
    feature_start_ms = int((cutoff - pd.Timedelta(hours=26)).value // 1_000_000)
    cutoff_ms = int(cutoff.value // 1_000_000)
    bars: list[pd.DataFrame] = []
    feature_ticks: list[pd.DataFrame] = []
    evidence: list[dict[str, Any]] = []
    for path in paths:
        ticks, record = _load_tick_day(path, config)
        evidence.append(record)
        local = ticks.loc[ticks["tick_time_msc"].le(cutoff_ms)]
        if not local.empty:
            bars.append(_aggregate_m5(local))
            window = local.loc[local["tick_time_msc"].gt(feature_start_ms)]
            if not window.empty:
                feature_ticks.append(window)
    if bars:
        bar_frame = (
            pd.concat(bars, ignore_index=True)
            .sort_values("timestamp_ms", kind="mergesort")
            .drop_duplicates("timestamp_ms", keep="last")
            .reset_index(drop=True)
        )
        previous_close = bar_frame["mid_close"].shift(1)
        true_range = pd.concat(
            [
                bar_frame["mid_high"] - bar_frame["mid_low"],
                (bar_frame["mid_high"] - previous_close).abs(),
                (bar_frame["mid_low"] - previous_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        bar_frame["atr"] = true_range.ewm(
            alpha=1.0 / 14.0,
            adjust=False,
            min_periods=int(config["data_quality"]["minimum_atr_bars"]),
        ).mean()
        latest_start = cutoff_ms - M5_MS
        eligible = bar_frame.loc[bar_frame["timestamp_ms"].le(latest_start), "atr"]
        atr = (
            float(eligible.iloc[-1])
            if len(eligible)
            and np.isfinite(float(eligible.iloc[-1]))
            and float(eligible.iloc[-1]) > 0.0
            else None
        )
    else:
        atr = None
    if feature_ticks:
        tick_frame = (
            pd.concat(feature_ticks, ignore_index=True)
            .sort_values("tick_time_msc", kind="mergesort")
            .drop_duplicates("tick_time_msc", keep="last")
            .reset_index(drop=True)
        )
    else:
        tick_frame = pd.DataFrame(columns=v38.TICK_FIELDS)
    return tick_frame, atr, evidence


def _window(
    times: np.ndarray,
    bids: np.ndarray,
    asks: np.ndarray,
    cutoff_ms: int,
    width_ms: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    left = int(np.searchsorted(times, cutoff_ms - width_ms, side="right"))
    right = int(np.searchsorted(times, cutoff_ms, side="right"))
    return times[left:right], bids[left:right], asks[left:right]


def _window_stats(
    times: np.ndarray,
    bids: np.ndarray,
    asks: np.ndarray,
    cutoff_ms: int,
    width_ms: int,
) -> dict[str, Any]:
    local_times, local_bids, local_asks = _window(
        times, bids, asks, cutoff_ms, width_ms
    )
    if not len(local_times):
        return {
            "count": 0,
            "change": None,
            "range": None,
            "variance": None,
            "efficiency": None,
            "imbalance": None,
        }
    mids = (local_bids + local_asks) / 2.0
    differences = np.diff(mids)
    nonzero = differences[differences != 0.0]
    path = float(np.abs(differences).sum())
    change = float(mids[-1] - mids[0])
    return {
        "count": len(local_times),
        "change": change,
        "range": float(np.max(mids) - np.min(mids)),
        "variance": float(np.square(differences).sum()),
        "efficiency": abs(change) / path if path > 0.0 else None,
        "imbalance": (
            float((np.sum(nonzero > 0.0) - np.sum(nonzero < 0.0)) / len(nonzero))
            if len(nonzero)
            else None
        ),
    }


def _completed_endpoint_change(
    times: np.ndarray,
    mids: np.ndarray,
    cutoff_ms: int,
    width_ms: int,
) -> float | None:
    current_endpoint = (cutoff_ms // HOUR_MS) * HOUR_MS
    prior_endpoint = current_endpoint - width_ms
    current_index = int(np.searchsorted(times, current_endpoint, side="right") - 1)
    prior_index = int(np.searchsorted(times, prior_endpoint, side="right") - 1)
    if current_index < 0 or prior_index < 0:
        return None
    return float(mids[current_index] - mids[prior_index])


def build_numeric_features(
    candidate: Mapping[str, Any],
    ticks: pd.DataFrame,
    atr: float | None,
    config: Mapping[str, Any],
) -> tuple[dict[str, float | None], str]:
    family = str(candidate["family_id"])
    cutoff = utc_timestamp(candidate["scheduled_entry_time_utc"])
    cutoff_ms = int(cutoff.value // 1_000_000)
    direction = 1.0 if str(candidate["direction"]) == "LONG" else -1.0
    stop = float(candidate["stop_distance"])
    target = candidate["target_r"]
    hold = candidate["hold_hours"]
    barrier_only = family == "R1_UPTREND"
    cap_minutes = (
        float(config["feature_geometry"]["r1_barrier_observation_cap_minutes"])
        if barrier_only
        else None
        if hold is None
        else float(hold) * 60.0
    )
    if cap_minutes is None or cap_minutes <= 0.0:
        raise ValueError(f"Candidate has no frozen observation cap: {family}")
    minute = cutoff.hour * 60 + cutoff.minute + cutoff.second / 60.0
    hour_angle = 2.0 * math.pi * minute / 1440.0
    weekday_angle = 2.0 * math.pi * cutoff.weekday() / 7.0
    values: dict[str, float | None] = {
        "direction_sign": direction,
        "planned_stop_atr": stop / atr if atr is not None and atr > 0.0 else None,
        "planned_stop_price": stop,
        "stop_floor_price": float(
            config["feature_geometry"]["stop_floor_price_by_family"][family]
        ),
        "target_r_filled": 0.0 if target is None else float(target),
        "target_absent_flag": float(target is None),
        "log1p_observation_cap_minutes": math.log1p(cap_minutes),
        "barrier_only_flag": float(barrier_only),
        "utc_hour_sin": math.sin(hour_angle),
        "utc_hour_cos": math.cos(hour_angle),
        "utc_weekday_sin": math.sin(weekday_angle),
        "utc_weekday_cos": math.cos(weekday_angle),
    }
    if ticks.empty or atr is None:
        return values, "ABSTAIN_MISSING_MANDATORY_XAU"
    times = ticks["tick_time_msc"].to_numpy(dtype=np.int64)
    bids = ticks["bid"].to_numpy(dtype=float)
    asks = ticks["ask"].to_numpy(dtype=float)
    last_index = int(np.searchsorted(times, cutoff_ms, side="right") - 1)
    if last_index < 0:
        return values, "ABSTAIN_MISSING_MANDATORY_XAU"
    quote_age = (cutoff_ms - int(times[last_index])) / 1000.0
    spreads = asks - bids
    mids = (bids + asks) / 2.0
    widths = (30_000, 300_000, 900_000, 3_600_000)
    stats = {
        width: _window_stats(times, bids, asks, cutoff_ms, width) for width in widths
    }
    spread_30 = _window(times, bids, asks, cutoff_ms, 30_000)
    spread_5m = _window(times, bids, asks, cutoff_ms, 300_000)
    count_15m = int(stats[900_000]["count"] or 0)
    count_60m = int(stats[3_600_000]["count"] or 0)

    def divided(value: Any, denominator: float) -> float | None:
        return (
            float(value) / denominator
            if value is not None and denominator > 0.0
            else None
        )

    values.update(
        {
            "xau_spread_last_atr": float(spreads[last_index]) / atr,
            "xau_spread_mean_30s_atr": (
                float(np.mean(spread_30[2] - spread_30[1])) / atr
                if len(spread_30[0])
                else None
            ),
            "xau_spread_max_5m_atr": (
                float(np.max(spread_5m[2] - spread_5m[1])) / atr
                if len(spread_5m[0])
                else None
            ),
            "xau_quote_age_seconds": quote_age,
            "xau_tick_count_log1p_30s": math.log1p(int(stats[30_000]["count"] or 0)),
            "xau_tick_count_log1p_5m": math.log1p(int(stats[300_000]["count"] or 0)),
            "xau_quote_intensity_ratio_15m_60m": count_15m / max(count_60m / 4.0, 1.0),
        }
    )
    suffixes = {
        30_000: "30s",
        300_000: "5m",
        900_000: "15m",
        3_600_000: "60m",
    }
    for width, suffix in suffixes.items():
        change = stats[width]["change"]
        values[f"dir_xau_return_{suffix}_atr"] = (
            direction * float(change) / atr if change is not None else None
        )
        if suffix != "30s":
            values[f"xau_range_{suffix}_atr"] = divided(stats[width]["range"], atr)
            values[f"xau_realized_variance_{suffix}_atr2"] = divided(
                stats[width]["variance"], atr * atr
            )
            values[f"xau_efficiency_{suffix}"] = stats[width]["efficiency"]
        if suffix in ("5m", "15m"):
            imbalance = stats[width]["imbalance"]
            values[f"dir_xau_tick_imbalance_{suffix}"] = (
                direction * float(imbalance) if imbalance is not None else None
            )
    for hours, suffix in ((4, "4h"), (24, "24h")):
        change = _completed_endpoint_change(times, mids, cutoff_ms, hours * HOUR_MS)
        values[f"dir_xau_return_{suffix}_atr"] = (
            direction * change / atr if change is not None else None
        )
    missing = [key for key, value in values.items() if value is None or pd.isna(value)]
    if missing:
        return values, "ABSTAIN_MISSING_MANDATORY_XAU"
    if quote_age > float(config["data_quality"]["maximum_feature_quote_age_seconds"]):
        return values, "ABSTAIN_STALE_XAU"
    return values, "PASS"


def score_candidate(
    candidate: Mapping[str, Any],
    payload: Mapping[str, Any],
    config: Mapping[str, Any],
    now: pd.Timestamp,
) -> tuple[dict[str, Any] | None, str | None]:
    cutoff = utc_timestamp(candidate["scheduled_entry_time_utc"])
    ready = cutoff + pd.Timedelta(
        seconds=float(config["data_quality"]["feature_finalization_delay_seconds"])
    )
    if now < ready:
        return None, "AWAITING_FEATURE_FINALIZATION"
    ticks, atr, evidence = market_at_cutoff(cutoff, config)
    values, feature_status = build_numeric_features(candidate, ticks, atr, config)
    missing_model_columns = set(payload["numeric_features"]).difference(values)
    if missing_model_columns:
        raise ValueError(
            f"Prospective feature contract is incomplete: {missing_model_columns}"
        )
    frame = pd.DataFrame(
        [
            {
                "family_id": str(candidate["family_id"]),
                **{name: values[name] for name in payload["numeric_features"]},
            }
        ]
    )
    if feature_status == "PASS":
        model_score = float(payload["model"].predict(frame)[0])
        threshold = float(
            payload["family_thresholds"].get(
                str(candidate["family_id"]), payload["pooled_threshold"]
            )
        )
        selected = model_score >= threshold
        action = "RETAIN" if selected else "VETO"
        reason = "APPLY_FROZEN_EXPECTED_R_V11"
    else:
        model_score = None
        threshold = None
        selected = True
        action = "MODEL_ABSTAIN_RETAIN_ALL"
        reason = feature_status
    row = {
        "schema_version": "xauusd_expected_r_prospective_v13_score",
        "candidate_id": str(candidate["candidate_id"]),
        "candidate_fact_sha256": str(candidate["candidate_fact_sha256"]),
        "source_id": str(candidate["source_id"]),
        "specialist_id": str(candidate["specialist_id"]),
        "family_id": str(candidate["family_id"]),
        "scheduled_entry_time_utc": utc_text(cutoff),
        "feature_status": feature_status,
        "model_score": model_score,
        "threshold": threshold,
        "selected": selected,
        "selection_action": action,
        "selection_reason": reason,
        "numeric_features": {
            name: None if values[name] is None else float(values[name])
            for name in payload["numeric_features"]
        },
        "tick_source_records": evidence,
        "recorded_at_utc": utc_text(now),
        "research_only": True,
        "python_predictions_authorized": False,
        "ml_shadow_authorized": False,
        "ea_consumption_authorized": False,
        "broker_action_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
    }
    return row, None


def _merge_evidence(
    target: dict[str, dict[str, Any]], records: Sequence[Mapping[str, Any]]
) -> None:
    for record in records:
        target[str(record["path"])] = dict(record)


def _first_quote_at_or_after(
    start_ms: int,
    maximum_gap_ms: int,
    config: Mapping[str, Any],
    evidence: dict[str, dict[str, Any]],
) -> tuple[int, float, float] | None:
    start = pd.Timestamp(start_ms, unit="ms", tz="UTC")
    end = pd.Timestamp(start_ms + maximum_gap_ms, unit="ms", tz="UTC")
    for path in _tick_paths_between(config, start, end):
        ticks, record = _load_tick_day(path, config)
        _merge_evidence(evidence, [record])
        times = ticks["tick_time_msc"].to_numpy(dtype=np.int64)
        index = int(np.searchsorted(times, start_ms, side="left"))
        if index < len(times) and int(times[index]) <= start_ms + maximum_gap_ms:
            return (
                int(times[index]),
                float(ticks["bid"].iloc[index]),
                float(ticks["ask"].iloc[index]),
            )
    return None


def _first_barrier_hit(
    start_ms: int,
    end_ms: int,
    direction: int,
    stop: float,
    target: float | None,
    entry_price: float,
    config: Mapping[str, Any],
    evidence: dict[str, dict[str, Any]],
) -> tuple[tuple[int, float, float, float, str] | None, float, float]:
    start = pd.Timestamp(start_ms, unit="ms", tz="UTC")
    end = pd.Timestamp(end_ms, unit="ms", tz="UTC")
    mfe = 0.0
    mae = 0.0
    for path in _tick_paths_between(config, start, end):
        ticks, record = _load_tick_day(path, config)
        _merge_evidence(evidence, [record])
        local = ticks.loc[
            ticks["tick_time_msc"].between(start_ms, end_ms, inclusive="both")
        ]
        if local.empty:
            continue
        times = local["tick_time_msc"].to_numpy(dtype=np.int64)
        bids = local["bid"].to_numpy(dtype=float)
        asks = local["ask"].to_numpy(dtype=float)
        executable = bids if direction > 0 else asks
        stop_hits = executable <= stop if direction > 0 else executable >= stop
        target_hits = np.zeros(len(executable), dtype=bool)
        if target is not None:
            target_hits = (
                executable >= target if direction > 0 else executable <= target
            )
        indices = np.flatnonzero(stop_hits | target_hits)
        if not len(indices):
            favorable = direction * (executable - entry_price)
            mfe = max(mfe, float(np.max(favorable)))
            mae = min(mae, float(np.min(favorable)))
            continue
        index = int(indices[0])
        path_values = direction * (executable[: index + 1] - entry_price)
        mfe = max(mfe, float(np.max(path_values)))
        mae = min(mae, float(np.min(path_values)))
        if bool(stop_hits[index]):
            price = float(executable[index])
            reason = "STOP" if price == stop else "STOP_SLIPPAGE"
        else:
            price = float(target)
            reason = "TARGET"
        return (
            (
                int(times[index]),
                float(bids[index]),
                float(asks[index]),
                price,
                reason,
            ),
            mfe,
            mae,
        )
    return None, mfe, mae


def _resolution_base(
    candidate: Mapping[str, Any],
    now: pd.Timestamp,
    status: str,
    evidence: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    records = [dict(evidence[key]) for key in sorted(evidence)]
    return {
        "schema_version": "xauusd_expected_r_prospective_v13_resolution",
        "candidate_id": str(candidate["candidate_id"]),
        "candidate_fact_sha256": str(candidate["candidate_fact_sha256"]),
        "source_id": str(candidate["source_id"]),
        "specialist_id": str(candidate["specialist_id"]),
        "family_id": str(candidate["family_id"]),
        "scheduled_entry_time_utc": str(candidate["scheduled_entry_time_utc"]),
        "direction": str(candidate["direction"]),
        "resolution_status": status,
        "resolved_at_utc": utc_text(now),
        "tick_source_records": records,
        "tick_source_snapshot_sha256": canonical_hash(
            {"records": records}, "__absent__"
        ),
        "research_only": True,
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ml_shadow_authorized": False,
        "ea_consumption_authorized": False,
        "broker_action_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
    }


def resolve_candidate(
    candidate: Mapping[str, Any],
    config: Mapping[str, Any],
    now: pd.Timestamp,
) -> tuple[dict[str, Any] | None, str | None]:
    family = str(candidate["family_id"])
    scheduled = utc_timestamp(candidate["scheduled_entry_time_utc"])
    scheduled_ms = int(scheduled.value // 1_000_000)
    entry_gap_minutes = int(
        config["feature_geometry"]["entry_maximum_gap_minutes_by_family"][family]
    )
    entry_gap_ms = entry_gap_minutes * 60_000
    evidence: dict[str, dict[str, Any]] = {}
    entry_quote = _first_quote_at_or_after(scheduled_ms, entry_gap_ms, config, evidence)
    if entry_quote is None:
        if now < scheduled + pd.Timedelta(minutes=entry_gap_minutes):
            return None, "AWAITING_ENTRY_WINDOW"
        row = _resolution_base(candidate, now, "REJECTED", evidence)
        row["rejection_reason"] = "NO_TIMELY_ENTRY_QUOTE"
        return row, None

    entry_ms, entry_bid, entry_ask = entry_quote
    direction = 1 if str(candidate["direction"]) == "LONG" else -1
    risk = float(candidate["stop_distance"])
    if not math.isfinite(risk) or risk <= 0.0:
        row = _resolution_base(candidate, now, "REJECTED", evidence)
        row["rejection_reason"] = "INVALID_INITIAL_RISK"
        return row, None
    entry_price = entry_ask if direction > 0 else entry_bid
    stop = entry_price - direction * risk
    target_r = candidate["target_r"]
    target = (
        None if target_r is None else entry_price + direction * float(target_r) * risk
    )
    barrier_only = family == "R1_UPTREND"
    if barrier_only:
        cap_minutes = float(
            config["feature_geometry"]["r1_barrier_observation_cap_minutes"]
        )
    else:
        hold = candidate["hold_hours"]
        if hold is None:
            raise ValueError(
                f"Non-R1 candidate has no horizon: {candidate['candidate_id']}"
            )
        cap_minutes = float(hold) * 60.0
    deadline_ms = entry_ms + round(cap_minutes * 60_000)
    now_ms = int(now.value // 1_000_000)
    search_end_ms = min(deadline_ms, now_ms)
    hit, mfe_price, mae_price = _first_barrier_hit(
        entry_ms,
        search_end_ms,
        direction,
        stop,
        target,
        entry_price,
        config,
        evidence,
    )
    if hit is not None:
        exit_ms, exit_bid, exit_ask, exit_price, exit_reason = hit
    elif barrier_only:
        if now_ms < deadline_ms:
            return None, "OPEN_BARRIER_POSITION"
        row = _resolution_base(candidate, now, "CENSORED", evidence)
        row.update(
            {
                "rejection_reason": "R1_OBSERVATION_CAP",
                "entry_time_utc": utc_text(pd.Timestamp(entry_ms, unit="ms", tz="UTC")),
                "entry_time_msc": entry_ms,
                "entry_price": entry_price,
                "risk_price": risk,
            }
        )
        return row, None
    else:
        horizon_gap_minutes = int(
            config["feature_geometry"]["horizon_maximum_gap_minutes_by_family"][family]
        )
        if now_ms < deadline_ms:
            return None, "AWAITING_HORIZON"
        horizon = _first_quote_at_or_after(
            deadline_ms,
            horizon_gap_minutes * 60_000,
            config,
            evidence,
        )
        if horizon is None:
            if now < pd.Timestamp(deadline_ms, unit="ms", tz="UTC") + pd.Timedelta(
                minutes=horizon_gap_minutes
            ):
                return None, "AWAITING_HORIZON_QUOTE"
            row = _resolution_base(candidate, now, "REJECTED", evidence)
            row["rejection_reason"] = "NO_HORIZON_QUOTE"
            return row, None
        exit_ms, exit_bid, exit_ask = horizon
        exit_price = exit_bid if direction > 0 else exit_ask
        exit_reason = "FIXED_HORIZON"
        final_excursion = direction * (exit_price - entry_price)
        mfe_price = max(mfe_price, final_excursion)
        mae_price = min(mae_price, final_excursion)

    exit_time = pd.Timestamp(exit_ms, unit="ms", tz="UTC")
    entry_time = pd.Timestamp(entry_ms, unit="ms", tz="UTC")
    gross_r = direction * (float(exit_price) - entry_price) / risk
    holding_minutes = max(0.0, (exit_ms - entry_ms) / 60_000.0)
    costs = config["costs"]
    base_cost_r = (
        float(costs["ticket_cost_usd"])
        + holding_minutes / 1440.0 * float(costs["holding_cost_per_24h_usd"])
    ) / (risk * float(costs["ounces_at_0p01_lot"]))
    stress_cost_r = base_cost_r + float(costs["stress_slippage_r"])
    stress_net_r = gross_r - stress_cost_r
    row = _resolution_base(candidate, now, "EXECUTED", evidence)
    row.update(
        {
            "rejection_reason": None,
            "entry_time_utc": utc_text(entry_time),
            "exit_time_utc": utc_text(exit_time),
            "entry_time_msc": entry_ms,
            "exit_time_msc": exit_ms,
            "entry_price": entry_price,
            "exit_price": float(exit_price),
            "stop_price": stop,
            "target_price": target,
            "risk_price": risk,
            "risk_usd_0p01": risk * float(costs["ounces_at_0p01_lot"]),
            "gross_r": gross_r,
            "base_cost_r": base_cost_r,
            "stress_cost_r": stress_cost_r,
            "stress_net_r": stress_net_r,
            "stress_pnl_usd_0p01": stress_net_r
            * risk
            * float(costs["ounces_at_0p01_lot"]),
            "mfe_r": mfe_price / risk,
            "mae_r": mae_price / risk,
            "holding_minutes": holding_minutes,
            "exit_reason": exit_reason,
        }
    )
    return row, None


def process_candidates(
    candidates: Sequence[Mapping[str, Any]],
    scores: Mapping[str, Mapping[str, Any]],
    resolutions: Mapping[str, Mapping[str, Any]],
    payload: Mapping[str, Any],
    config: Mapping[str, Any],
    now: pd.Timestamp,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    new_scores: list[dict[str, Any]] = []
    new_resolutions: list[dict[str, Any]] = []
    waiting: dict[str, int] = {}
    for candidate in candidates:
        candidate_id = str(candidate["candidate_id"])
        if candidate_id not in scores:
            score, reason = score_candidate(candidate, payload, config, now)
            if score is None:
                waiting[str(reason)] = waiting.get(str(reason), 0) + 1
            else:
                new_scores.append(score)
        if candidate_id not in resolutions:
            resolution, reason = resolve_candidate(candidate, config, now)
            if resolution is None:
                waiting[str(reason)] = waiting.get(str(reason), 0) + 1
            else:
                new_resolutions.append(resolution)
    return new_scores, new_resolutions, dict(sorted(waiting.items()))


def _v47_config(config: Mapping[str, Any]) -> dict[str, Any]:
    source = config["source"]
    return {
        "forward_start_inclusive_utc": config["forward_start_inclusive_utc"],
        "sources": {
            "ticks": {
                "directory": source["tick_directory"],
                "filename_glob": source["tick_filename_glob"],
                "schema_version": source["tick_schema_version"],
                "account_login": source["account_login"],
                "account_server": source["account_server"],
                "symbol": source["symbol"],
                "maximum_timestamp_disagreement_ms": config["data_quality"][
                    "maximum_timestamp_disagreement_ms"
                ],
                "maximum_spread_field_error": config["data_quality"][
                    "maximum_spread_field_error"
                ],
            }
        },
        "data_quality": config["data_quality"],
        "day_quality": config["day_quality"],
    }


def update_day_quality(
    runtime: Path, config: Mapping[str, Any], now: pd.Timestamp
) -> list[dict[str, Any]]:
    path = runtime / str(config["runtime"]["day_quality_ledger"])
    return v47.update_day_quality(path, _v47_config(config), now)


def stage_endpoint(
    stage: str,
    eligible_dates: Sequence[str],
    candidates: Sequence[Mapping[str, Any]],
    scores: Mapping[str, Mapping[str, Any]],
    resolutions: Mapping[str, Mapping[str, Any]],
    config: Mapping[str, Any],
    *,
    after_date: str | None = None,
) -> dict[str, Any] | None:
    available = [
        str(value)
        for value in eligible_dates
        if after_date is None or str(value) > str(after_date)
    ]
    spec = config["stages"][stage]
    minimum_days = int(spec["minimum_eligible_weekdays"])
    maximum_days = int(spec["maximum_eligible_weekdays"])
    for count in range(minimum_days, min(len(available), maximum_days) + 1):
        dates = available[:count]
        date_set = set(dates)
        required = {
            str(row["candidate_id"])
            for row in candidates
            if utc_timestamp(row["scheduled_entry_time_utc"]).strftime("%Y-%m-%d")
            in date_set
        }
        if not required.issubset(scores) or not required.issubset(resolutions):
            continue
        executed = {
            candidate_id
            for candidate_id in required
            if str(resolutions[candidate_id]["resolution_status"]) == "EXECUTED"
        }
        model_scored = {
            candidate_id
            for candidate_id in executed
            if scores[candidate_id].get("model_score") is not None
        }
        families = {
            str(scores[candidate_id]["family_id"]) for candidate_id in model_scored
        }
        if len(model_scored) < int(spec["minimum_resolved_scored_candidates"]):
            continue
        if len(families) < int(spec["minimum_scored_families"]):
            continue
        return {
            "stage": stage,
            "eligible_dates": dates,
            "start_date_utc": dates[0],
            "end_date_utc": dates[-1],
            "candidate_ids": sorted(required),
            "executed_candidate_ids": sorted(executed),
            "model_scored_candidate_ids": sorted(model_scored),
        }
    return None


def build_trade_frame(
    endpoint: Mapping[str, Any],
    candidates: Mapping[str, Mapping[str, Any]],
    scores: Mapping[str, Mapping[str, Any]],
    resolutions: Mapping[str, Mapping[str, Any]],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for candidate_id in endpoint["executed_candidate_ids"]:
        candidate = candidates[candidate_id]
        score = scores[candidate_id]
        resolution = resolutions[candidate_id]
        rows.append(
            {
                "candidate_id": candidate_id,
                "source_id": str(candidate["source_id"]),
                "specialist_id": str(candidate["specialist_id"]),
                "family_id": str(candidate["family_id"]),
                "sleeve_type": str(candidate["sleeve_type"]),
                "magic": int(candidate["magic"]),
                "scheduled_entry_time_utc": str(candidate["scheduled_entry_time_utc"]),
                "direction": str(candidate["direction"]),
                "initial_risk_usd": float(candidate["initial_risk_usd"]),
                "event_id": candidate.get("event_id"),
                "maximum_open_positions": int(candidate["maximum_open_positions"]),
                "maximum_entries_per_utc_day": int(
                    candidate["maximum_entries_per_utc_day"]
                ),
                "feature_status": str(score["feature_status"]),
                "model_score": score.get("model_score"),
                "threshold": score.get("threshold"),
                "selected": bool(score["selected"]),
                "selection_action": str(score["selection_action"]),
                "entry_time_utc": str(resolution["entry_time_utc"]),
                "entry_time_msc": int(
                    utc_timestamp(resolution["entry_time_utc"]).value // 1_000_000
                ),
                "exit_time_utc": str(resolution["exit_time_utc"]),
                "exit_time_msc": int(resolution["exit_time_msc"]),
                "risk_usd_0p01": float(resolution["risk_usd_0p01"]),
                "gross_r": float(resolution["gross_r"]),
                "stress_net_r": float(resolution["stress_net_r"]),
                "stress_pnl_usd_0p01": float(resolution["stress_pnl_usd_0p01"]),
                "exit_reason": str(resolution["exit_reason"]),
            }
        )
    if not rows:
        return pd.DataFrame()
    return (
        pd.DataFrame(rows)
        .sort_values(["exit_time_msc", "candidate_id"], kind="mergesort")
        .reset_index(drop=True)
    )


def _effective_policy_limit(policy: Mapping[str, Any], key: str) -> float:
    absolute = float(policy[key])
    fraction = float(policy[key.removesuffix("_usd") + "_fraction"])
    return min(
        absolute,
        float(policy["reference_activation_equity_usd"]) * fraction,
    )


def apply_portfolio_routing(
    trades: pd.DataFrame, config: Mapping[str, Any]
) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()
    policy = config["candidate_population"]["portfolio_policy"]
    result = trades.copy()
    for scenario, selection_required in (
        ("baseline", False),
        ("selected", True),
    ):
        accepted: list[int] = []
        accounted_closed: set[int] = set()
        last_losses: dict[tuple[str, str], int] = {}
        daily_entries: dict[str, int] = {}
        accepted_addon_events: set[str] = set()
        routed = pd.Series(False, index=result.index)
        reasons = pd.Series("", index=result.index, dtype=object)
        ordered = result.sort_values(
            ["entry_time_msc", "source_id", "candidate_id"], kind="mergesort"
        )
        for index, row in ordered.iterrows():
            if selection_required and not bool(row["selected"]):
                reasons.at[index] = "MODEL_VETO_OR_ABSTAIN"
                continue
            entry_msc = int(row["entry_time_msc"])
            for item in accepted:
                if item in accounted_closed:
                    continue
                exit_msc = int(result.at[item, "exit_time_msc"])
                if exit_msc > entry_msc:
                    continue
                completed_source = str(result.at[item, "source_id"])
                completed_direction = str(result.at[item, "direction"])
                if float(result.at[item, "stress_pnl_usd_0p01"]) < 0.0:
                    last_losses[(completed_source, completed_direction)] = max(
                        exit_msc,
                        last_losses.get(
                            (completed_source, completed_direction), exit_msc
                        ),
                    )
                accounted_closed.add(item)
            active = [
                item
                for item in accepted
                if int(result.at[item, "exit_time_msc"]) > entry_msc
            ]
            active_frame = result.loc[active]
            sleeve = str(row["sleeve_type"])
            direction = str(row["direction"])
            source = str(row["source_id"])
            risk = float(row["initial_risk_usd"])
            date = utc_timestamp(row["scheduled_entry_time_utc"]).strftime("%Y-%m-%d")
            source_day = f"{source}:{date}"
            cooldown_minutes = int(
                policy.get(
                    "same_direction_post_loss_cooldown_minutes_by_source", {}
                ).get(source, 0)
            )
            last_loss_msc = last_losses.get((source, direction))
            reason = ""
            if len(active_frame) >= int(policy["maximum_account_xau_positions"]):
                reason = "MAXIMUM_ACCOUNT_XAU_POSITIONS"
            elif (
                sleeve == "CORE"
                and int(active_frame["sleeve_type"].eq("CORE").sum())
                >= int(policy["maximum_core_open_positions"])
            ):
                reason = "MAXIMUM_CORE_OPEN_POSITIONS"
            elif (
                sleeve == "ADDON"
                and int(active_frame["sleeve_type"].eq("ADDON").sum())
                >= int(policy["maximum_addon_open_positions"])
            ):
                reason = "MAXIMUM_ADDON_OPEN_POSITIONS"
            elif (
                int(active_frame["source_id"].eq(source).sum())
                >= int(row["maximum_open_positions"])
            ):
                reason = "MAXIMUM_SOURCE_OPEN_POSITIONS"
            elif (
                cooldown_minutes > 0
                and last_loss_msc is not None
                and entry_msc < last_loss_msc + cooldown_minutes * 60_000
            ):
                reason = "SAME_DIRECTION_POST_LOSS_COOLDOWN"
            elif daily_entries.get(source_day, 0) >= int(
                row["maximum_entries_per_utc_day"]
            ):
                reason = "MAXIMUM_SOURCE_DAILY_ENTRIES"
            elif sum(
                count
                for key, count in daily_entries.items()
                if key.endswith(f":{date}")
            ) >= int(policy["maximum_daily_entries"]):
                reason = "MAXIMUM_DAILY_ENTRIES"
            elif sleeve == "ADDON" and sum(
                count
                for key, count in daily_entries.items()
                if key.split(":", 1)[0] in set(policy["addon_source_ids"])
                and key.endswith(f":{date}")
            ) >= int(policy["maximum_addon_entries_per_utc_day"]):
                reason = "MAXIMUM_ADDON_DAILY_ENTRIES"
            elif sleeve == "ADDON" and row.get("event_id") not in (None, "") and str(
                row["event_id"]
            ) in accepted_addon_events:
                reason = "DUPLICATE_ADDON_EVENT"
            else:
                active_risk = float(active_frame["initial_risk_usd"].sum())
                direction_risk = float(
                    active_frame.loc[
                        active_frame["direction"].eq(direction), "initial_risk_usd"
                    ].sum()
                )
                addon_risk = float(
                    active_frame.loc[
                        active_frame["sleeve_type"].eq("ADDON"), "initial_risk_usd"
                    ].sum()
                )
                if (
                    active_risk + risk
                    > _effective_policy_limit(
                        policy, "maximum_account_concurrent_initial_risk_usd"
                    )
                ):
                    reason = "MAXIMUM_ACCOUNT_CONCURRENT_INITIAL_RISK"
                elif (
                    direction_risk + risk
                    > _effective_policy_limit(
                        policy, "maximum_directional_concurrent_initial_risk_usd"
                    )
                ):
                    reason = "MAXIMUM_DIRECTIONAL_CONCURRENT_INITIAL_RISK"
                elif sleeve == "ADDON" and (
                    addon_risk + risk
                    > float(policy["maximum_addon_concurrent_initial_risk_usd"])
                ):
                    reason = "MAXIMUM_ADDON_CONCURRENT_INITIAL_RISK"
            if reason:
                reasons.at[index] = reason
                continue
            routed.at[index] = True
            reasons.at[index] = "ROUTED"
            accepted.append(index)
            daily_entries[source_day] = daily_entries.get(source_day, 0) + 1
            if sleeve == "ADDON" and row.get("event_id") not in (None, ""):
                accepted_addon_events.add(str(row["event_id"]))
        result[f"{scenario}_routed"] = routed
        result[f"{scenario}_route_reason"] = reasons
    return result


def _profit_factor(values: np.ndarray) -> tuple[float | None, bool]:
    positive = float(np.clip(values, 0.0, None).sum())
    negative = float(np.clip(-values, 0.0, None).sum())
    if negative == 0.0:
        return None, positive > 0.0
    return positive / negative, False


def _metrics(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        return {
            "rows": 0,
            "stress_net_r": 0.0,
            "mean_stress_r": None,
            "profit_factor": None,
            "profit_factor_infinite": False,
            "closed_drawdown_r": 0.0,
            "stress_pnl_usd_0p01": 0.0,
        }
    values = frame["stress_net_r"].to_numpy(dtype=float)
    pf, infinite = _profit_factor(values)
    episode = frame.groupby("exit_time_msc", sort=True)["stress_net_r"].sum().cumsum()
    drawdown = float((episode.cummax() - episode).max()) if len(episode) else 0.0
    return {
        "rows": len(frame),
        "stress_net_r": float(values.sum()),
        "mean_stress_r": float(values.mean()),
        "profit_factor": pf,
        "profit_factor_infinite": infinite,
        "closed_drawdown_r": drawdown,
        "stress_pnl_usd_0p01": float(frame["stress_pnl_usd_0p01"].sum()),
    }


def _pf_for_gate(metrics: Mapping[str, Any]) -> float:
    if bool(metrics["profit_factor_infinite"]):
        return float("inf")
    value = metrics["profit_factor"]
    return 0.0 if value is None else float(value)


def _bootstrap_confidence(
    trades: pd.DataFrame,
    baseline_mask: pd.Series,
    selected_mask: pd.Series,
    config: Mapping[str, Any],
) -> dict[str, float | None]:
    settings = config["confidence"]
    iterations = int(settings["weekly_block_bootstrap_iterations"])
    quantile = float(settings["lower_confidence_quantile"])
    seed = int(settings["random_seed"])
    if "scheduled_entry_time_utc" in trades:
        weeks = (
            pd.to_datetime(trades["scheduled_entry_time_utc"], utc=True)
            .dt.to_period("W-SUN")
            .astype(str)
        )
    else:
        weeks = (
            trades["exit_time_msc"].astype(np.int64) // (7 * 24 * HOUR_MS)
        ).astype(str)
    unique_weeks = sorted(set(weeks))
    empty = {
        "selected_mean_stress_r_lower": None,
        "mean_uplift_r_lower": None,
        "selected_profit_factor_lower": None,
    }
    if not unique_weeks:
        return empty
    blocks = {week: trades.index[weeks.eq(week)].to_numpy() for week in unique_weeks}
    rng = np.random.default_rng(seed)
    selected_means: list[float] = []
    uplifts: list[float] = []
    profit_factors: list[float] = []
    for _ in range(iterations):
        sampled = rng.choice(unique_weeks, size=len(unique_weeks), replace=True)
        indices = np.concatenate([blocks[str(week)] for week in sampled])
        baseline_indices = indices[baseline_mask.loc[indices].to_numpy(dtype=bool)]
        selected_indices = indices[selected_mask.loc[indices].to_numpy(dtype=bool)]
        baseline_values = trades.loc[baseline_indices, "stress_net_r"].to_numpy(
            dtype=float
        )
        selected_values = trades.loc[selected_indices, "stress_net_r"].to_numpy(
            dtype=float
        )
        if not len(baseline_values) or not len(selected_values):
            continue
        selected_means.append(float(selected_values.mean()))
        uplifts.append(float(selected_values.mean() - baseline_values.mean()))
        pf, infinite = _profit_factor(selected_values)
        profit_factors.append(float("inf") if infinite else float(pf or 0.0))
    if not selected_means:
        return empty
    return {
        "selected_mean_stress_r_lower": float(np.quantile(selected_means, quantile)),
        "mean_uplift_r_lower": float(np.quantile(uplifts, quantile)),
        "selected_profit_factor_lower": float(
            np.quantile(profit_factors, quantile)
        ),
    }


def evaluate_stage(
    stage: str,
    endpoint: Mapping[str, Any],
    trades: pd.DataFrame,
    config: Mapping[str, Any],
    contract_sha256: str,
) -> dict[str, Any]:
    baseline_mask = (
        trades["baseline_routed"].astype(bool)
        if "baseline_routed" in trades
        else pd.Series(True, index=trades.index)
    )
    selected_mask = (
        trades["selected_routed"].astype(bool)
        if "selected_routed" in trades
        else trades["selected"].astype(bool)
    )
    baseline_frame = trades.loc[baseline_mask].copy()
    selected_frame = trades.loc[selected_mask].copy()
    rejected_frame = trades.loc[baseline_mask & ~selected_mask].copy()
    baseline = _metrics(baseline_frame)
    selected = _metrics(selected_frame)
    rejected = _metrics(rejected_frame)
    score_coverage = (
        float(baseline_frame["model_score"].notna().mean())
        if len(baseline_frame)
        else 0.0
    )
    selection_coverage = (
        float(len(selected_frame) / len(baseline_frame))
        if len(baseline_frame)
        else 0.0
    )
    mean_uplift = (
        None
        if selected["mean_stress_r"] is None or baseline["mean_stress_r"] is None
        else float(selected["mean_stress_r"] - baseline["mean_stress_r"])
    )
    selected_minus_rejected = (
        None
        if selected["mean_stress_r"] is None or rejected["mean_stress_r"] is None
        else float(selected["mean_stress_r"] - rejected["mean_stress_r"])
    )
    drawdown_ratio = (
        0.0
        if float(baseline["closed_drawdown_r"]) == 0.0
        else float(selected["closed_drawdown_r"]) / float(baseline["closed_drawdown_r"])
    )
    baseline_net = float(baseline["stress_net_r"])
    selected_net = float(selected["stress_net_r"])
    net_retention = selected_net / baseline_net if baseline_net > 0.0 else None
    remove_count = int(config["gates"][stage]["largest_selected_winners_removed"])
    trimmed = selected_frame.sort_values(
        ["stress_net_r", "candidate_id"], ascending=[False, True], kind="mergesort"
    ).iloc[remove_count:]
    trimmed_net = float(trimmed["stress_net_r"].sum()) if len(trimmed) else 0.0
    gates = config["gates"][stage]
    confidence = _bootstrap_confidence(
        trades, baseline_mask, selected_mask, config
    )
    baseline_families = sorted(set(baseline_frame["family_id"]))
    selected_family_counts = (
        selected_frame.groupby("family_id")
        .size()
        .reindex(baseline_families, fill_value=0)
    )
    minimum_family_rows = (
        int(selected_family_counts.min())
        if len(selected_family_counts)
        else 0
    )
    checks = {
        "minimum_selected_routed_candidates": len(selected_frame)
        >= int(gates["minimum_selected_routed_candidates"]),
        "minimum_selected_rows_per_routed_family": minimum_family_rows
        >= int(gates["minimum_selected_rows_per_routed_family"]),
        "minimum_model_score_coverage": score_coverage
        >= float(gates["minimum_model_score_coverage"]),
        "minimum_selection_coverage": selection_coverage
        >= float(gates["minimum_selection_coverage"]),
        "maximum_selection_coverage": selection_coverage
        <= float(gates["maximum_selection_coverage"]),
        "minimum_selected_mean_stress_r": selected["mean_stress_r"] is not None
        and float(selected["mean_stress_r"])
        >= float(gates["minimum_selected_mean_stress_r"]),
        "minimum_selected_profit_factor": _pf_for_gate(selected)
        >= float(gates["minimum_selected_profit_factor"]),
        "minimum_mean_uplift_r": mean_uplift is not None
        and mean_uplift >= float(gates["minimum_mean_uplift_r"]),
        "minimum_selected_minus_rejected_mean_r": selected_minus_rejected is not None
        and selected_minus_rejected
        >= float(gates["minimum_selected_minus_rejected_mean_r"]),
        "maximum_drawdown_ratio_to_baseline": drawdown_ratio
        <= float(gates["maximum_drawdown_ratio_to_baseline"]),
        "minimum_positive_baseline_net_retention": (
            net_retention is not None
            and net_retention >= float(gates["minimum_positive_baseline_net_retention"])
        )
        if baseline_net > 0.0
        else selected_net > 0.0 and selected_net > baseline_net,
        "minimum_trimmed_selected_net_r": trimmed_net
        >= float(gates["minimum_trimmed_selected_net_r"]),
        "minimum_bootstrap_selected_mean_stress_r_lower": confidence[
            "selected_mean_stress_r_lower"
        ]
        is not None
        and float(confidence["selected_mean_stress_r_lower"])
        >= float(gates["minimum_bootstrap_selected_mean_stress_r_lower"]),
        "minimum_bootstrap_mean_uplift_r_lower": confidence[
            "mean_uplift_r_lower"
        ]
        is not None
        and float(confidence["mean_uplift_r_lower"])
        >= float(gates["minimum_bootstrap_mean_uplift_r_lower"]),
        "minimum_bootstrap_selected_profit_factor_lower": confidence[
            "selected_profit_factor_lower"
        ]
        is not None
        and float(confidence["selected_profit_factor_lower"])
        >= float(gates["minimum_bootstrap_selected_profit_factor_lower"]),
    }
    family_rows: list[dict[str, Any]] = []
    for family, group in baseline_frame.groupby("family_id", sort=True):
        family_selected = selected_frame.loc[selected_frame["family_id"].eq(family)]
        family_rows.append(
            {
                "family_id": str(family),
                "baseline": _metrics(group),
                "selected": _metrics(family_selected),
                "selection_coverage": float(len(family_selected) / len(group)),
            }
        )
    passed = all(checks.values())
    return {
        "schema_version": "xauusd_expected_r_prospective_v13_stage_audit",
        "definition_contract_sha256": contract_sha256,
        "stage": stage,
        "endpoint": dict(endpoint),
        "baseline": baseline,
        "selected": selected,
        "rejected": rejected,
        "model_score_coverage": score_coverage,
        "selection_coverage": selection_coverage,
        "selected_mean_uplift_r": mean_uplift,
        "selected_minus_rejected_mean_r": selected_minus_rejected,
        "drawdown_ratio_to_baseline": drawdown_ratio,
        "positive_baseline_net_retention": net_retention,
        "largest_selected_winners_removed": remove_count,
        "trimmed_selected_net_r": trimmed_net,
        "confidence": confidence,
        "minimum_selected_rows_across_routed_families": minimum_family_rows,
        "family_metrics": family_rows,
        "checks": checks,
        "passed_checks": int(sum(checks.values())),
        "required_checks": len(checks),
        "passed": passed,
        "decision": (
            f"EXPECTED_R_V13_{stage.upper()}_PASS_NO_AUTHORITY"
            if passed
            else f"EXPECTED_R_V13_{stage.upper()}_FAIL"
        ),
        "research_only": True,
        "runtime_authorized": False,
        "ml_shadow_authorized": False,
        "ea_consumption_authorized": False,
        "broker_action_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
    }


def _write_stage(
    stage: str,
    endpoint: Mapping[str, Any],
    candidates: Mapping[str, Mapping[str, Any]],
    scores: Mapping[str, Mapping[str, Any]],
    resolutions: Mapping[str, Mapping[str, Any]],
    runtime: Path,
    config: Mapping[str, Any],
    contract_sha256: str,
) -> dict[str, Any]:
    audit_path = runtime / str(config["runtime"][f"{stage}_audit"])
    trades_path = runtime / str(config["runtime"][f"{stage}_trades"])
    trades = apply_portfolio_routing(
        build_trade_frame(endpoint, candidates, scores, resolutions),
        config,
    )
    buffer = io.StringIO()
    trades.to_csv(buffer, index=False, lineterminator="\n")
    trade_bytes = buffer.getvalue().encode("utf-8")
    trade_sha256 = sha256_bytes(trade_bytes)
    expected = evaluate_stage(stage, endpoint, trades, config, contract_sha256)
    expected["trades_sha256"] = trade_sha256
    if audit_path.is_file():
        audit = read_json(audit_path)
        if not trades_path.is_file() or trades_path.read_bytes() != trade_bytes:
            raise ValueError(f"Expected-R V13 {stage} trade artifact changed")
        if canonical_hash(audit, "__absent__") != canonical_hash(
            expected, "__absent__"
        ):
            raise ValueError(f"Expected-R V13 {stage} audit changed")
        return audit
    atomic_write_bytes(trades_path, trade_bytes)
    atomic_write_json(audit_path, expected)
    return expected


def run_cycle(
    package_root: Path,
    config_path: Path,
    *,
    now: pd.Timestamp | None = None,
) -> dict[str, Any]:
    config = read_json(config_path)
    contract = verify_contract(package_root, config)
    current = pd.Timestamp.now(tz="UTC") if now is None else utc_timestamp(now)
    runtime = Path(str(config["runtime"]["directory"]))
    runtime.mkdir(parents=True, exist_ok=True)
    candidates = load_candidates(
        config, runtime, str(contract["contract_sha256"]), current
    )
    candidate_by_id = {str(row["candidate_id"]): row for row in candidates}
    score_path = runtime / str(config["runtime"]["score_ledger"])
    resolution_path = runtime / str(config["runtime"]["resolution_ledger"])
    scores = _ledger_by_id(
        score_path,
        candidate_by_id,
        status_field="selection_action",
        allowed=FINAL_SCORE_ACTIONS,
    )
    resolutions = _ledger_by_id(
        resolution_path,
        candidate_by_id,
        status_field="resolution_status",
        allowed=FINAL_RESOLUTION_STATUSES,
    )
    payload = load_model(config)
    new_scores, new_resolutions, waiting = process_candidates(
        candidates, scores, resolutions, payload, config, current
    )
    append_jsonl(score_path, new_scores)
    append_jsonl(resolution_path, new_resolutions)
    scores = _ledger_by_id(
        score_path,
        candidate_by_id,
        status_field="selection_action",
        allowed=FINAL_SCORE_ACTIONS,
    )
    resolutions = _ledger_by_id(
        resolution_path,
        candidate_by_id,
        status_field="resolution_status",
        allowed=FINAL_RESOLUTION_STATUSES,
    )
    day_rows = update_day_quality(runtime, config, current)
    eligible_dates = [
        str(row["date_utc"]) for row in day_rows if bool(row["eligible_full_weekday"])
    ]
    validation_endpoint = stage_endpoint(
        "validation",
        eligible_dates,
        candidates,
        scores,
        resolutions,
        config,
    )
    validation_audit = None
    if validation_endpoint is not None:
        validation_audit = _write_stage(
            "validation",
            validation_endpoint,
            candidate_by_id,
            scores,
            resolutions,
            runtime,
            config,
            str(contract["contract_sha256"]),
        )
    confirmation_endpoint = None
    confirmation_audit = None
    if validation_audit is not None and bool(validation_audit["passed"]):
        confirmation_endpoint = stage_endpoint(
            "confirmation",
            eligible_dates,
            candidates,
            scores,
            resolutions,
            config,
            after_date=str(validation_audit["endpoint"]["end_date_utc"]),
        )
        if confirmation_endpoint is not None:
            confirmation_audit = _write_stage(
                "confirmation",
                confirmation_endpoint,
                candidate_by_id,
                scores,
                resolutions,
                runtime,
                config,
                str(contract["contract_sha256"]),
            )
    status = {
        "schema_version": "xauusd_expected_r_prospective_v13_status",
        "updated_at_utc": utc_text(current),
        "status": (
            "WAIT_BOUNDARY"
            if current < utc_timestamp(config["forward_start_inclusive_utc"])
            else "ACTIVE_READ_ONLY_PROSPECTIVE_CONFIRMATION"
        ),
        "definition_contract_sha256": str(contract["contract_sha256"]),
        "forward_start_inclusive_utc": config["forward_start_inclusive_utc"],
        "candidate_rows": len(candidates),
        "score_rows": len(scores),
        "resolution_rows": len(resolutions),
        "executed_resolution_rows": sum(
            str(row["resolution_status"]) == "EXECUTED" for row in resolutions.values()
        ),
        "model_veto_rows": sum(
            str(row["selection_action"]) == "VETO" for row in scores.values()
        ),
        "waiting_reasons": waiting,
        "eligible_full_weekdays": len(eligible_dates),
        "validation_endpoint_complete": validation_audit is not None,
        "validation_decision": (
            None if validation_audit is None else validation_audit["decision"]
        ),
        "confirmation_endpoint_complete": confirmation_audit is not None,
        "confirmation_decision": (
            None if confirmation_audit is None else confirmation_audit["decision"]
        ),
        "aggregate_economics_opened": validation_audit is not None,
        "historical_model_refit": False,
        "same_version_tuning_authorized": False,
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ml_shadow_authorized": False,
        "ea_consumption_authorized": False,
        "broker_action_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
    }
    atomic_write_json(runtime / str(config["runtime"]["status"]), status)
    return status


def verify_score_replay(
    scores: Mapping[str, Mapping[str, Any]],
    payload: Mapping[str, Any],
) -> None:
    for row in scores.values():
        if str(row["selection_action"]) == "MODEL_ABSTAIN_RETAIN_ALL":
            if row.get("model_score") is not None or not bool(row["selected"]):
                raise ValueError("Model abstention score changed")
            continue
        frame = pd.DataFrame(
            [
                {
                    "family_id": str(row["family_id"]),
                    **{
                        name: row["numeric_features"][name]
                        for name in payload["numeric_features"]
                    },
                }
            ]
        )
        score = float(payload["model"].predict(frame)[0])
        expected = float(row["model_score"])
        if not math.isclose(score, expected, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError(f"Model score replay changed: {row['candidate_id']}")
        threshold = float(
            payload["family_thresholds"].get(
                str(row["family_id"]), payload["pooled_threshold"]
            )
        )
        if not math.isclose(
            threshold, float(row["threshold"]), rel_tol=0.0, abs_tol=1e-12
        ):
            raise ValueError(f"Threshold replay changed: {row['candidate_id']}")
        if bool(row["selected"]) != (score >= threshold):
            raise ValueError(f"Selection replay changed: {row['candidate_id']}")


def verify_resolution_arithmetic(
    resolutions: Mapping[str, Mapping[str, Any]], config: Mapping[str, Any]
) -> None:
    for row in resolutions.values():
        for record in row.get("tick_source_records", []):
            path = Path(str(record["path"]))
            prefix_bytes = int(record["prefix_bytes"])
            if not path.is_file() or path.stat().st_size < prefix_bytes:
                raise ValueError(f"Resolution tick evidence disappeared: {path}")
            with path.open("rb") as stream:
                prefix = stream.read(prefix_bytes)
            if sha256_bytes(prefix) != str(record["prefix_sha256"]):
                raise ValueError(f"Resolution tick evidence changed: {path}")
        if str(row["resolution_status"]) != "EXECUTED":
            continue
        direction = 1.0 if str(row["direction"]) == "LONG" else -1.0
        risk = float(row["risk_price"])
        gross = (
            direction * (float(row["exit_price"]) - float(row["entry_price"])) / risk
        )
        holding = float(row["holding_minutes"])
        costs = config["costs"]
        base = (
            float(costs["ticket_cost_usd"])
            + holding / 1440.0 * float(costs["holding_cost_per_24h_usd"])
        ) / (risk * float(costs["ounces_at_0p01_lot"]))
        stress = gross - base - float(costs["stress_slippage_r"])
        checks = (
            (gross, float(row["gross_r"]), "gross_r"),
            (base, float(row["base_cost_r"]), "base_cost_r"),
            (stress, float(row["stress_net_r"]), "stress_net_r"),
        )
        for observed, expected, label in checks:
            if not math.isclose(observed, expected, rel_tol=0.0, abs_tol=1e-12):
                raise ValueError(f"Resolution {label} changed: {row['candidate_id']}")


def verify_runtime(package_root: Path, config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    contract = verify_contract(package_root, config)
    runtime = Path(str(config["runtime"]["directory"]))
    candidates = load_candidates(
        config,
        runtime,
        str(contract["contract_sha256"]),
        pd.Timestamp.now(tz="UTC"),
    )
    candidate_by_id = {str(row["candidate_id"]): row for row in candidates}
    scores = _ledger_by_id(
        runtime / str(config["runtime"]["score_ledger"]),
        candidate_by_id,
        status_field="selection_action",
        allowed=FINAL_SCORE_ACTIONS,
    )
    resolutions = _ledger_by_id(
        runtime / str(config["runtime"]["resolution_ledger"]),
        candidate_by_id,
        status_field="resolution_status",
        allowed=FINAL_RESOLUTION_STATUSES,
    )
    payload = load_model(config)
    verify_score_replay(scores, payload)
    verify_resolution_arithmetic(resolutions, config)
    day_path = runtime / str(config["runtime"]["day_quality_ledger"])
    day_rows = v47.read_day_quality(day_path) if day_path.is_file() else []
    eligible_dates = [
        str(row["date_utc"])
        for row in day_rows
        if bool(row["eligible_full_weekday"])
    ]
    validation_path = runtime / str(config["runtime"]["validation_audit"])
    validation_endpoint = stage_endpoint(
        "validation",
        eligible_dates,
        candidates,
        scores,
        resolutions,
        config,
    )
    validation_audit = None
    if validation_path.is_file():
        if validation_endpoint is None:
            raise ValueError("Validation audit exists before its frozen endpoint")
        validation_audit = _write_stage(
            "validation",
            validation_endpoint,
            candidate_by_id,
            scores,
            resolutions,
            runtime,
            config,
            str(contract["contract_sha256"]),
        )
    confirmation_path = runtime / str(config["runtime"]["confirmation_audit"])
    if confirmation_path.is_file():
        if validation_audit is None:
            raise ValueError("Confirmation audit exists without validation")
        confirmation_endpoint = stage_endpoint(
            "confirmation",
            eligible_dates,
            candidates,
            scores,
            resolutions,
            config,
            after_date=str(validation_audit["endpoint"]["end_date_utc"]),
        )
        if confirmation_endpoint is None:
            raise ValueError("Confirmation audit exists before its frozen endpoint")
        _write_stage(
            "confirmation",
            confirmation_endpoint,
            candidate_by_id,
            scores,
            resolutions,
            runtime,
            config,
            str(contract["contract_sha256"]),
        )
    return {
        "schema_version": "xauusd_expected_r_prospective_v13_verification",
        "verified": True,
        "definition_contract_sha256": str(contract["contract_sha256"]),
        "candidate_rows": len(candidates),
        "score_rows_replayed": len(scores),
        "resolution_rows_verified": len(resolutions),
        "stage_artifacts_verified": int(validation_path.is_file())
        + int(confirmation_path.is_file()),
        "broker_action_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
    }
