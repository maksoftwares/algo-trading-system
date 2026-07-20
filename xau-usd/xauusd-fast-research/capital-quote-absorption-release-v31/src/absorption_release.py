from __future__ import annotations

from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
CANDIDATE_COLUMNS = (
    "timestamp_utc",
    "tick_time_msc",
    "date_utc",
    "utc_block_start_ms",
    "bid",
    "ask",
    "mid",
    "spread_price",
    "absorption_arm_time_msc",
    "absorption_low",
    "absorption_high",
    "absorption_range_price",
    "absorption_nonzero_updates",
    "signed_update_imbalance",
    "displacement_price",
    "candidate_side",
)


def load_config(root: Path = ROOT) -> dict[str, Any]:
    return json.loads(
        (root / "config" / "absorption_release_v31.json").read_text(encoding="utf-8")
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(payload: Mapping[str, Any], omitted_key: str) -> str:
    work = dict(payload)
    work.pop(omitted_key, None)
    encoded = json.dumps(
        work,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _load_dependency(
    root: Path,
    module_relative: str,
    module_sha: str,
    contract_relative: str,
    contract_file_sha: str,
    contract_sha: str,
    module_name: str,
) -> ModuleType:
    module_path = root / module_relative
    contract_path = root / contract_relative
    if sha256_file(module_path) != module_sha:
        raise ValueError(f"V31 frozen module changed: {module_path}")
    if sha256_file(contract_path) != contract_file_sha:
        raise ValueError(f"V31 frozen contract file changed: {contract_path}")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    actual = contract.get("contract_sha256", contract.get("adapter_contract_sha256"))
    if actual != contract_sha:
        raise ValueError(f"V31 frozen contract identity changed: {contract_path}")
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_locked_v24(config: Mapping[str, Any]) -> ModuleType:
    frozen = config["frozen_v24_1"]
    root = (ROOT / str(frozen["root_relative"])).resolve()
    config_path = root / str(frozen["config_relative"])
    if sha256_file(config_path) != frozen["config_file_sha256"]:
        raise ValueError("V31 frozen V24.1 config changed")
    return _load_dependency(
        root,
        str(frozen["module_relative"]),
        str(frozen["module_file_sha256"]),
        str(frozen["contract_relative"]),
        str(frozen["contract_file_sha256"]),
        str(frozen["contract_sha256"]),
        "v31_locked_v24",
    )


def load_locked_transport(config: Mapping[str, Any]) -> ModuleType:
    frozen = config["frozen_timestamp_adapter"]
    root = (ROOT / str(frozen["root_relative"])).resolve()
    return _load_dependency(
        root,
        str(frozen["module_relative"]),
        str(frozen["module_file_sha256"]),
        str(frozen["contract_relative"]),
        str(frozen["contract_file_sha256"]),
        str(frozen["contract_sha256"]),
        "v31_locked_transport",
    )


def development_source_paths(config: Mapping[str, Any]) -> list[Path]:
    source = config["development_source"]
    directory = (ROOT / str(source["directory"])).resolve()
    return sorted(directory.glob(str(source["filename_glob"])))


def _rolling_min_max(
    values: np.ndarray, starts: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    lows = np.empty(len(values), dtype=float)
    highs = np.empty(len(values), dtype=float)
    minimum: deque[int] = deque()
    maximum: deque[int] = deque()
    for index, value in enumerate(values):
        left = int(starts[index]) + 1
        while minimum and minimum[0] < left:
            minimum.popleft()
        while maximum and maximum[0] < left:
            maximum.popleft()
        while minimum and values[minimum[-1]] >= value:
            minimum.pop()
        while maximum and values[maximum[-1]] <= value:
            maximum.pop()
        minimum.append(index)
        maximum.append(index)
        lows[index] = values[minimum[0]]
        highs[index] = values[maximum[0]]
    return lows, highs


def generate_candidates(
    ticks: pd.DataFrame, config: Mapping[str, Any]
) -> tuple[pd.DataFrame, dict[str, int]]:
    if ticks.empty:
        return pd.DataFrame(columns=CANDIDATE_COLUMNS), {
            "absorption_arm_count": 0,
            "raw_release_count": 0,
        }
    feature = config["feature"]
    times = ticks["tick_time_msc"].to_numpy(dtype=np.int64)
    bid = ticks["bid"].to_numpy(dtype=float)
    ask = ticks["ask"].to_numpy(dtype=float)
    spread = ticks["spread_price"].to_numpy(dtype=float)
    mid = (bid + ask) / 2.0
    target = times - int(feature["absorption_lookback_ms"])
    starts = np.searchsorted(times, target, side="right") - 1
    valid = starts >= 0
    safe_starts = np.maximum(starts, 0)
    signs = np.sign(np.diff(mid, prepend=mid[0]))
    nonzero = signs != 0
    signed_prefix = np.concatenate(([0.0], np.cumsum(signs)))
    count_prefix = np.concatenate(([0], np.cumsum(nonzero.astype(np.int64))))
    index = np.arange(len(times), dtype=np.int64)
    update_sum = signed_prefix[index + 1] - signed_prefix[safe_starts + 1]
    update_count = count_prefix[index + 1] - count_prefix[safe_starts + 1]
    imbalance = np.divide(
        update_sum,
        update_count,
        out=np.zeros(len(times), dtype=float),
        where=update_count > 0,
    )
    lows, highs = _rolling_min_max(mid, starts)
    ranges = highs - lows
    gaps = np.diff(times, prepend=times[0])
    v24 = load_locked_v24(config)
    maximum_gap = v24._rolling_internal_max_gap(gaps, safe_starts)
    state = (
        valid
        & (maximum_gap <= int(feature["maximum_internal_quote_gap_ms"]))
        & (spread <= float(feature["maximum_spread_price"]))
        & (update_count >= int(feature["minimum_nonzero_mid_updates"]))
        & (np.abs(imbalance) <= float(feature["maximum_absolute_update_imbalance"]))
        & (ranges <= float(feature["maximum_absorption_range_price"]))
    )
    rising = state & ~np.r_[False, state[:-1]]
    expiry = int(feature["arm_expiry_ms"])
    release = float(feature["minimum_release_price"])
    refractory = int(feature["post_trigger_refractory_ms"])
    block_ms = int(config["episode"]["utc_block_hours"]) * 60 * 60 * 1000
    armed: dict[str, Any] | None = None
    refractory_until = -1
    arms = 0
    records: list[dict[str, Any]] = []
    for i, now_value in enumerate(times):
        now = int(now_value)
        if armed is not None:
            if now - int(armed["time"]) > expiry:
                armed = None
            else:
                side = ""
                displacement = 0.0
                if mid[i] >= float(armed["high"]) + release:
                    side = "LONG"
                    displacement = float(mid[i] - float(armed["high"]))
                elif mid[i] <= float(armed["low"]) - release:
                    side = "SHORT"
                    displacement = float(mid[i] - float(armed["low"]))
                if side and spread[i] <= float(feature["maximum_spread_price"]):
                    timestamp = pd.Timestamp(now, unit="ms", tz="UTC")
                    records.append(
                        {
                            "timestamp_utc": timestamp.strftime(
                                "%Y-%m-%dT%H:%M:%S.%fZ"
                            ),
                            "tick_time_msc": now,
                            "date_utc": timestamp.strftime("%Y-%m-%d"),
                            "utc_block_start_ms": int((now // block_ms) * block_ms),
                            "bid": float(bid[i]),
                            "ask": float(ask[i]),
                            "mid": float(mid[i]),
                            "spread_price": float(spread[i]),
                            "absorption_arm_time_msc": int(armed["time"]),
                            "absorption_low": float(armed["low"]),
                            "absorption_high": float(armed["high"]),
                            "absorption_range_price": float(armed["range"]),
                            "absorption_nonzero_updates": int(armed["updates"]),
                            "signed_update_imbalance": float(armed["imbalance"]),
                            "displacement_price": displacement,
                            "candidate_side": side,
                        }
                    )
                    armed = None
                    refractory_until = now + refractory
        if armed is None and now >= refractory_until and bool(rising[i]):
            armed = {
                "time": now,
                "low": float(lows[i]),
                "high": float(highs[i]),
                "range": float(ranges[i]),
                "updates": int(update_count[i]),
                "imbalance": float(imbalance[i]),
            }
            arms += 1
    raw_count = len(records)
    candidates = pd.DataFrame(records, columns=CANDIDATE_COLUMNS)
    if not candidates.empty:
        candidates = (
            candidates.sort_values("tick_time_msc", kind="mergesort")
            .drop_duplicates("utc_block_start_ms", keep="first")
            .reset_index(drop=True)
        )
        maximum = int(config["episode"]["maximum_candidates_per_utc_day"])
        if int(candidates.groupby("date_utc").size().max()) > maximum:
            raise ValueError("V31 candidate count exceeded its daily cap")
    return candidates, {
        "absorption_arm_count": int(arms),
        "raw_release_count": int(raw_count),
    }
