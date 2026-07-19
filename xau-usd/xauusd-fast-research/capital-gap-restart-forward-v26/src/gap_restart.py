from __future__ import annotations

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
RESEARCH_ROOT = ROOT.parent
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
    "restart_time_msc",
    "preceding_gap_ms",
    "elapsed_since_restart_ms",
    "nonzero_mid_updates",
    "signed_update_imbalance",
    "displacement_price",
    "candidate_side",
)


def load_config(root: Path = ROOT) -> dict[str, Any]:
    path = root / "config" / "capital_gap_restart_forward_v26.json"
    return json.loads(path.read_text(encoding="utf-8"))


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


def frozen_v24_root(config: Mapping[str, Any]) -> Path:
    return (ROOT / str(config["frozen_v24_1"]["root_relative"])).resolve()


def load_locked_v24(config: Mapping[str, Any]) -> ModuleType:
    frozen = config["frozen_v24_1"]
    dependency_root = frozen_v24_root(config)
    for relative, expected in (
        (frozen["config_relative"], frozen["config_file_sha256"]),
        (frozen["module_relative"], frozen["module_file_sha256"]),
        (frozen["contract_relative"], frozen["contract_file_sha256"]),
    ):
        path = dependency_root / str(relative)
        if not path.is_file() or sha256_file(path) != str(expected):
            raise ValueError(f"V26 frozen V24.1 dependency changed: {path}")
    contract = json.loads(
        (dependency_root / str(frozen["contract_relative"])).read_text(
            encoding="utf-8"
        )
    )
    if str(contract["contract_sha256"]) != str(frozen["contract_sha256"]):
        raise ValueError("V26 frozen V24.1 contract identity changed")
    module_path = dependency_root / str(frozen["module_relative"])
    spec = importlib.util.spec_from_file_location("v26_locked_v24_microburst", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def assert_v24_execution_parity(
    config: Mapping[str, Any], v24: ModuleType | None = None
) -> None:
    module = v24 or load_locked_v24(config)
    origin = module.load_config(frozen_v24_root(config))
    sections = ("data_quality", "simulation", "gates")
    differences = [key for key in sections if config[key] != origin[key]]
    source_keys = ("directory", "filename_glob", "schema_version", "account_login", "account_server", "symbol", "calibration_file", "calibration_file_sha256")
    if any(config["source"][key] != origin["source"][key] for key in source_keys):
        differences.append("source_identity")
    if differences:
        raise ValueError(f"V26 execution contract differs from V24.1: {differences}")


def generate_candidates(
    ticks: pd.DataFrame, config: Mapping[str, Any]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if ticks.empty:
        return pd.DataFrame(columns=CANDIDATE_COLUMNS), {
            "restart_episode_count": 0,
            "raw_candidate_count": 0,
        }
    feature = config["feature"]
    episode = config["episode"]
    times = ticks["tick_time_msc"].to_numpy(dtype=np.int64)
    bid = ticks["bid"].to_numpy(dtype=float)
    ask = ticks["ask"].to_numpy(dtype=float)
    spread = ticks["spread_price"].to_numpy(dtype=float)
    mid = (bid + ask) / 2.0
    gaps = np.diff(times, prepend=times[0])
    restarts = np.flatnonzero(
        (gaps >= int(feature["minimum_preceding_gap_ms"]))
        & (gaps <= int(feature["maximum_preceding_gap_ms"]))
    )
    records: list[dict[str, Any]] = []
    for restart in restarts:
        stop = int(
            np.searchsorted(
                times,
                times[restart] + int(feature["restart_observation_ms"]),
                side="right",
            )
        )
        segment = mid[restart:stop]
        if len(segment) < 2:
            continue
        signs = np.sign(np.diff(segment, prepend=segment[0]))
        nonzero = signs != 0
        update_sum = np.cumsum(signs)
        update_count = np.cumsum(nonzero.astype(np.int64))
        imbalance = np.divide(
            update_sum,
            update_count,
            out=np.zeros(len(segment), dtype=float),
            where=update_count > 0,
        )
        displacement = segment - segment[0]
        local_spread = spread[restart:stop]
        gate = (
            (update_count >= int(feature["minimum_nonzero_mid_updates"]))
            & (
                np.abs(imbalance)
                >= float(feature["minimum_absolute_update_imbalance"])
            )
            & (
                np.abs(displacement)
                >= float(feature["minimum_absolute_displacement_price"])
            )
            & (np.sign(imbalance) == np.sign(displacement))
            & (np.sign(displacement) != 0)
            & (local_spread <= float(feature["maximum_spread_price"]))
        )
        qualified = np.flatnonzero(gate)
        if not len(qualified):
            continue
        local = int(qualified[0])
        index = restart + local
        block_ms = int(episode["utc_block_hours"]) * 60 * 60 * 1000
        timestamp = pd.Timestamp(times[index], unit="ms", tz="UTC")
        records.append(
            {
                "timestamp_utc": timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "tick_time_msc": int(times[index]),
                "date_utc": timestamp.strftime("%Y-%m-%d"),
                "utc_block_start_ms": int((times[index] // block_ms) * block_ms),
                "bid": float(bid[index]),
                "ask": float(ask[index]),
                "mid": float(mid[index]),
                "spread_price": float(spread[index]),
                "restart_time_msc": int(times[restart]),
                "preceding_gap_ms": int(gaps[restart]),
                "elapsed_since_restart_ms": int(times[index] - times[restart]),
                "nonzero_mid_updates": int(update_count[local]),
                "signed_update_imbalance": float(imbalance[local]),
                "displacement_price": float(displacement[local]),
                "candidate_side": "LONG" if imbalance[local] > 0 else "SHORT",
            }
        )
    raw_count = len(records)
    candidates = pd.DataFrame(records, columns=CANDIDATE_COLUMNS)
    if not candidates.empty:
        candidates = (
            candidates.sort_values("tick_time_msc", kind="mergesort")
            .drop_duplicates("utc_block_start_ms", keep="first")
            .reset_index(drop=True)
        )
        maximum = int(episode["maximum_candidates_per_utc_day"])
        if int(candidates.groupby("date_utc").size().max()) > maximum:
            raise ValueError("V26 candidate count exceeded its daily structural cap")
    return candidates, {
        "restart_episode_count": int(len(restarts)),
        "raw_candidate_count": int(raw_count),
    }


def evaluate_stage(
    trades: pd.DataFrame,
    stage_dates: list[str],
    partition: str,
    config: Mapping[str, Any],
    v24: ModuleType,
) -> tuple[dict[str, Any], pd.DataFrame]:
    audit, daily = v24.evaluate_stage(trades, stage_dates, partition, config)
    multiple = config["multiple_testing"]
    values = (
        daily.sort_values("date_utc", kind="mergesort")["base_pnl_dollars"]
        .to_numpy(dtype=float)
    )
    block_length = int(multiple["block_length_weekdays"])
    if len(values) < block_length:
        raise ValueError("V26 has too few daily observations for its block bootstrap")
    observed_mean = float(values.mean())
    centered = values - observed_mean
    rng = np.random.default_rng(int(multiple["daily_bootstrap_seed"]))
    sample_count = int(multiple["daily_bootstrap_samples"])
    block_count = int(np.ceil(len(values) / block_length))
    starts = rng.integers(0, len(values), size=(sample_count, block_count))
    offsets = np.arange(block_length, dtype=np.int64)
    indexes = (starts[..., None] + offsets) % len(values)
    bootstrap = centered[indexes].reshape(sample_count, -1)[:, : len(values)].mean(axis=1)
    pvalue = float(
        (1 + int(np.count_nonzero(bootstrap >= observed_mean)))
        / (sample_count + 1)
    )
    familywise_pass = pvalue <= float(multiple["maximum_one_sided_pvalue"])
    audit["schema_version"] = "xauusd_v26_forward_stage_audit"
    audit["metrics"]["selection_adjusted_daily_block_bootstrap_pvalue"] = pvalue
    audit["gate_checks"]["selection_adjusted_daily_block_bootstrap_pvalue"] = (
        familywise_pass
    )
    audit["gate_passed"] = bool(audit["gate_passed"] and familywise_pass)
    audit["registered_capital_forward_hypotheses"] = int(
        multiple["registered_capital_forward_hypotheses"]
    )
    audit["family_alpha"] = float(multiple["family_alpha"])
    audit["bonferroni_stage_alpha"] = float(multiple["maximum_one_sided_pvalue"])
    audit["block_length_weekdays"] = block_length
    audit["v24_1_external_admission_recheck_required"] = bool(
        multiple["v24_1_external_admission_recheck_required"]
    )
    audit["audit_sha256"] = canonical_hash(audit, "audit_sha256")
    return audit, daily
