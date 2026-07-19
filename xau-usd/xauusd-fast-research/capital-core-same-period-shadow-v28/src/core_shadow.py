from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd


CANDIDATE_COLUMNS = (
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


@dataclass(frozen=True)
class FrozenRegimeComposites:
    package_config: dict[str, Any]
    source_config: dict[str, Any]
    manifest: pd.DataFrame
    modules: dict[str, Any]
    dependency_sha256: str
    repo_root: Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def dependency_sha256(repo_root: Path, paths: list[str]) -> str:
    digest = hashlib.sha256()
    for relative in sorted(paths):
        path = repo_root / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        digest.update(relative.replace("\\", "/").encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_frozen(repo_root: Path, package_root: Path) -> FrozenRegimeComposites:
    repo_root = repo_root.resolve()
    package_config = json.loads(
        (
            package_root / "config" / "capital_core_same_period_shadow_v28.json"
        ).read_text(encoding="utf-8")
    )
    source_path = repo_root / package_config["source"]["regime_composite_config"]
    source_config = json.loads(source_path.read_text(encoding="utf-8"))
    manifest_path = repo_root / package_config["source"]["campaign_manifest"]
    observed_manifest_sha = sha256_file(manifest_path)
    if observed_manifest_sha != package_config["source"]["campaign_manifest_sha256"]:
        raise ValueError("Frozen regime campaign manifest hash changed")
    candidates_path = repo_root / package_config["source"]["historical_candidates"]
    if (
        sha256_file(candidates_path)
        != package_config["source"]["historical_candidates_sha256"]
    ):
        raise ValueError("Frozen historical candidate artifact hash changed")
    research = repo_root / "xau-usd" / "xauusd-fast-research"
    modules = {
        "r2": load_module(
            "capital_core_v28_r2",
            research / "r2-downtrend-portability-v2" / "src" / "downtrend.py",
        ),
        "data": load_module(
            "capital_core_v28_data",
            research / "independent-specialists-v1" / "src" / "data.py",
        ),
        "regimes": load_module(
            "capital_core_v28_regimes",
            research / "independent-specialists-v1" / "src" / "research.py",
        ),
        "adaptive": load_module(
            "capital_core_v28_adaptive",
            research / "adaptive-h4-specialists-v1" / "src" / "adaptive.py",
        ),
        "campaign": load_module(
            "capital_core_v28_campaign",
            research / "regime-mechanism-campaign-v1" / "src" / "campaign.py",
        ),
        "composite": load_module(
            "capital_core_v28_composite",
            research / "regime-composite-rawtick-v1" / "src" / "composite.py",
        ),
    }
    return FrozenRegimeComposites(
        package_config=package_config,
        source_config=source_config,
        manifest=pd.read_csv(manifest_path),
        modules=modules,
        dependency_sha256=dependency_sha256(
            repo_root, package_config["contract_scope"]
        ),
        repo_root=repo_root,
    )


def build_feature_frame(
    m5: pd.DataFrame, frozen: FrozenRegimeComposites
) -> pd.DataFrame:
    data = frozen.modules["data"]
    h1 = data.aggregate_complete_bars(m5, 60, "H1")
    h4 = data.aggregate_complete_bars(m5, 240, "H4")
    return frozen.modules["campaign"].prepare_features(
        h1,
        h4,
        frozen.source_config,
        frozen.modules["adaptive"],
        frozen.modules["regimes"],
    )


def _source_candidate_id(origin_attempt: int, signal_time: pd.Timestamp) -> str:
    payload = f"{origin_attempt}|{signal_time.isoformat()}".encode("ascii")
    return hashlib.sha256(payload).hexdigest()[:24]


def _candidate_id(source_candidate_id: str, dependency_digest: str) -> str:
    payload = f"V28|{source_candidate_id}|{dependency_digest}".encode("ascii")
    return hashlib.sha256(payload).hexdigest()[:32]


def generate_regime_candidates(
    frame: pd.DataFrame,
    frozen: FrozenRegimeComposites,
    *,
    start_inclusive: pd.Timestamp,
    end_exclusive: pd.Timestamp,
    require_next_bar: bool,
) -> pd.DataFrame:
    start = pd.Timestamp(start_inclusive)
    end = pd.Timestamp(end_exclusive)
    requested = {
        int(attempt)
        for composite in frozen.source_config["composites"]
        for attempt in composite["component_attempts"]
    }
    memberships = {
        int(attempt): str(composite["composite_id"])
        for composite in frozen.source_config["composites"]
        for attempt in composite["component_attempts"]
    }
    specialists = {
        str(composite["composite_id"]): (
            "R2_DOWNTREND"
            if str(composite["regime_owner"]) == "DOWNTREND"
            else "R3_COMPRESSION"
        )
        for composite in frozen.source_config["composites"]
    }
    indexed = frozen.manifest.set_index("attempt_no", drop=False)
    rows: list[dict[str, Any]] = []
    for origin_attempt in sorted(requested):
        source = indexed.loc[origin_attempt]
        params = json.loads(str(source["parameters_json"]))
        mask, direction = frozen.modules["campaign"].signal_mask_direction(
            frame, str(source["mechanic"]), params
        )
        for signal_index in np.flatnonzero(mask.to_numpy(dtype=bool)):
            signal_index = int(signal_index)
            signal = frame.iloc[signal_index]
            signal_time = pd.Timestamp(signal["timestamp_utc"])
            if signal_time < start or signal_time >= end:
                continue
            entry_index = signal_index + 1
            if entry_index < len(frame):
                scheduled = pd.Timestamp(frame.iloc[entry_index]["bar_start_utc"])
                if scheduled != signal_time:
                    continue
            elif require_next_bar:
                continue
            else:
                scheduled = signal_time
            if scheduled < start or scheduled >= end:
                continue
            sign = int(direction.iat[signal_index])
            source_id = _source_candidate_id(origin_attempt, signal_time)
            composite_id = memberships[origin_attempt]
            rows.append(
                {
                    "candidate_id": _candidate_id(source_id, frozen.dependency_sha256),
                    "source_candidate_id": source_id,
                    "specialist_id": specialists[composite_id],
                    "composite_id": composite_id,
                    "origin_attempt": origin_attempt,
                    "origin_variant_id": str(source["variant_id"]),
                    "regime_owner": str(source["regime_owner"]),
                    "mechanic": str(source["mechanic"]),
                    "signal_time_utc": signal_time,
                    "scheduled_entry_time_utc": scheduled,
                    "direction": "LONG" if sign > 0 else "SHORT",
                    "direction_sign": sign,
                    "signal_atr": float(signal["atr14"]),
                    "stop_atr": float(params["stop_atr"]),
                    "hold_hours": float(params["hold_hours"]),
                    "parameters_json": str(source["parameters_json"]),
                    "rule_dependency_sha256": frozen.dependency_sha256,
                    "trade_permission": False,
                    "broker_action_allowed": False,
                    "python_execution_authorized": False,
                }
            )
    if not rows:
        return pd.DataFrame(columns=CANDIDATE_COLUMNS)
    result = (
        pd.DataFrame(rows, columns=CANDIDATE_COLUMNS)
        .sort_values(["scheduled_entry_time_utc", "origin_attempt"], kind="mergesort")
        .reset_index(drop=True)
    )
    if result["candidate_id"].duplicated().any():
        raise ValueError("Duplicate V28 candidate IDs")
    return result


def verify_historical_candidate_parity(
    frozen: FrozenRegimeComposites,
) -> dict[str, Any]:
    m5, _ = frozen.modules["r2"].load_continuous_m5(frozen.source_config)
    frame = build_feature_frame(m5, frozen)
    observed = generate_regime_candidates(
        frame,
        frozen,
        start_inclusive=pd.Timestamp(frozen.source_config["source"]["start_utc"]),
        end_exclusive=pd.Timestamp(frozen.source_config["source"]["end_exclusive_utc"]),
        require_next_bar=True,
    )
    expected_path = (
        frozen.repo_root / frozen.package_config["source"]["historical_candidates"]
    )
    expected = pd.read_parquet(expected_path)
    renames = {
        "source_candidate_id": "candidate_id",
        "signal_time_utc": "signal_time",
        "scheduled_entry_time_utc": "scheduled_entry_time",
    }
    comparable = observed.drop(columns=["candidate_id"]).rename(columns=renames)
    keys = [
        "candidate_id",
        "composite_id",
        "origin_attempt",
        "origin_variant_id",
        "regime_owner",
        "mechanic",
        "signal_time",
        "scheduled_entry_time",
        "direction",
        "direction_sign",
        "signal_atr",
        "stop_atr",
        "hold_hours",
        "parameters_json",
    ]
    expected = expected[keys].reset_index(drop=True)
    comparable = comparable[keys].reset_index(drop=True)
    exact_columns = [column for column in keys if column != "signal_atr"]
    timestamp_columns = {"signal_time", "scheduled_entry_time"}
    column_parity = {}
    for column in exact_columns:
        if column in timestamp_columns:
            left = pd.DatetimeIndex(
                pd.to_datetime(comparable[column], utc=True)
            ).as_unit("ns")
            right = pd.DatetimeIndex(
                pd.to_datetime(expected[column], utc=True)
            ).as_unit("ns")
            column_parity[column] = bool(np.array_equal(left.asi8, right.asi8))
        else:
            column_parity[column] = bool(comparable[column].equals(expected[column]))
    exact_equal = all(column_parity.values())
    atr_equal = (
        bool(
            np.allclose(
                comparable["signal_atr"].to_numpy(dtype=float),
                expected["signal_atr"].to_numpy(dtype=float),
                rtol=0.0,
                atol=1e-12,
            )
        )
        if len(comparable) == len(expected)
        else False
    )
    result = {
        "expected_rows": int(len(expected)),
        "observed_rows": int(len(comparable)),
        "exact_columns_equal": bool(exact_equal),
        "column_parity": column_parity,
        "signal_atr_equal": atr_equal,
        "pass": bool(len(comparable) == len(expected) and exact_equal and atr_equal),
    }
    if not result["pass"]:
        raise ValueError(f"V28 historical candidate parity failed: {result}")
    return result
