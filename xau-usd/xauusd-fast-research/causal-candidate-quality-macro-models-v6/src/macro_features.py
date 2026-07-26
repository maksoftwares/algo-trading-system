from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


MACRO_FEATURE_COLUMNS = (
    "dir_dxy_gold_pressure_15m",
    "dir_dxy_gold_pressure_1h",
    "dir_dxy_gold_pressure_4h",
    "dir_bond_gold_pressure_15m",
    "dir_bond_gold_pressure_1h",
    "dir_bond_gold_pressure_4h",
    "dir_macro_consensus_1h",
    "macro_disagreement_1h",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _aggregate_symbol(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    prefix = symbol.lower()
    required = {
        "timestamp_utc",
        f"{prefix}_available",
        f"{prefix}_mid_open",
        f"{prefix}_mid_high",
        f"{prefix}_mid_low",
        f"{prefix}_mid_close",
        f"{prefix}_mid_tick_count",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Macro source missing {symbol} columns: {missing}")
    source = frame.loc[frame[f"{prefix}_available"], list(required)].copy()
    price_columns = [
        f"{prefix}_mid_open",
        f"{prefix}_mid_high",
        f"{prefix}_mid_low",
        f"{prefix}_mid_close",
    ]
    valid = np.isfinite(source[price_columns]).all(axis=1)
    valid &= source[price_columns].gt(0.0).all(axis=1)
    source = source.loc[valid]
    source["_bucket"] = source["timestamp_utc"].dt.floor("15min")
    source["_offset"] = (
        (source["timestamp_utc"] - source["_bucket"]).dt.total_seconds() / 300
    ).astype(int)
    grouped = source.groupby("_bucket", sort=True, observed=True)["_offset"]
    complete = (
        grouped.size().eq(3)
        & grouped.nunique().eq(3)
        & grouped.min().eq(0)
        & grouped.max().eq(2)
        & grouped.sum().eq(3)
    )
    source = source.loc[source["_bucket"].isin(complete.index[complete])]
    result = (
        source.groupby("_bucket", sort=True, observed=True)
        .agg(
            **{
                f"{prefix}_open": (f"{prefix}_mid_open", "first"),
                f"{prefix}_high": (f"{prefix}_mid_high", "max"),
                f"{prefix}_low": (f"{prefix}_mid_low", "min"),
                f"{prefix}_close": (f"{prefix}_mid_close", "last"),
                f"{prefix}_tick_count": (f"{prefix}_mid_tick_count", "sum"),
            }
        )
        .reset_index()
    )
    result["macro_time"] = result.pop("_bucket") + pd.Timedelta(minutes=15)
    result.attrs["incomplete_buckets_dropped"] = int((~complete).sum())
    return result


def build_macro_state(
    macro_m15: pd.DataFrame, geometry: dict[str, Any]
) -> pd.DataFrame:
    frame = macro_m15.sort_values("macro_time", kind="mergesort").copy()
    labels = {1: "15m", 4: "1h", 16: "4h"}
    scale_bars = int(geometry["scale_bars"])
    minimum = int(geometry["scale_minimum_bars"])
    for prefix, pressure_sign in (
        ("dollaridxusd", -1.0),
        ("ustbondtrusd", 1.0),
    ):
        close = frame[f"{prefix}_close"]
        for bars in geometry["return_bars"]:
            bars = int(bars)
            raw_return = np.log(close / close.shift(bars))
            prior_scale = raw_return.shift(1).rolling(
                scale_bars, min_periods=minimum
            ).std(ddof=0)
            feature_prefix = "dxy" if prefix == "dollaridxusd" else "bond"
            frame[f"{feature_prefix}_gold_pressure_{labels[bars]}"] = (
                pressure_sign * raw_return / prior_scale.replace(0.0, np.nan)
            )
    columns = [
        "macro_time",
        *[
            f"{prefix}_gold_pressure_{label}"
            for prefix in ("dxy", "bond")
            for label in ("15m", "1h", "4h")
        ],
    ]
    return frame[columns]


def load_macro_state(config: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    source = config["macro_source"]
    root = Path(
        os.environ.get(
            str(source["storage_environment_variable"]),
            str(source["default_storage_root"]),
        )
    )
    cache = root / str(source["feature_cache"])
    manifest_path = root / str(source["feature_manifest"])
    if not cache.is_file() or not manifest_path.is_file():
        raise FileNotFoundError(f"Verified macro source is unavailable below {root}")
    cache_hash = sha256_file(cache)
    manifest_hash = sha256_file(manifest_path)
    if cache_hash != source["feature_sha256"]:
        raise ValueError(f"Macro feature SHA-256 mismatch: {cache_hash}")
    if manifest_hash != source["manifest_sha256"]:
        raise ValueError(f"Macro manifest SHA-256 mismatch: {manifest_hash}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frame = pd.read_parquet(cache)
    if len(frame) != int(source["expected_rows"]):
        raise ValueError(
            f"Expected {source['expected_rows']} macro rows, found {len(frame)}"
        )
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True)
    frame = frame.sort_values("timestamp_utc", kind="mergesort").reset_index(drop=True)
    if frame["timestamp_utc"].duplicated().any():
        raise ValueError("Duplicate macro M5 timestamps")
    start = pd.Timestamp(source["start_utc"])
    end = pd.Timestamp(source["end_exclusive_utc"])
    frame = frame.loc[frame["timestamp_utc"].ge(start) & frame["timestamp_utc"].lt(end)]
    dollar = _aggregate_symbol(frame, "DOLLARIDXUSD")
    bond = _aggregate_symbol(frame, "USTBONDTRUSD")
    macro_m15 = dollar.merge(bond, on="macro_time", how="inner", validate="one_to_one")
    macro_state = build_macro_state(macro_m15, config["macro_geometry"])
    evidence = {
        "feature_cache": str(cache),
        "feature_manifest": str(manifest_path),
        "feature_sha256": cache_hash,
        "manifest_sha256": manifest_hash,
        "manifest": manifest,
        "source_rows": int(len(frame)),
        "joint_m15_rows": int(len(macro_m15)),
        "joint_start_utc": macro_m15["macro_time"].min().isoformat(),
        "joint_end_utc": macro_m15["macro_time"].max().isoformat(),
        "dollar_incomplete_buckets_dropped": int(
            dollar.attrs.get("incomplete_buckets_dropped", 0)
        ),
        "bond_incomplete_buckets_dropped": int(
            bond.attrs.get("incomplete_buckets_dropped", 0)
        ),
    }
    return macro_state, evidence


def enrich_actions(
    actions: pd.DataFrame,
    macro_state: pd.DataFrame,
    *,
    tolerance_minutes: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if actions["candidate_id"].duplicated().any():
        raise ValueError("Action candidate IDs are duplicated before macro enrichment")
    source = actions.sort_values("signal_time", kind="mergesort").copy()
    macro = macro_state.sort_values("macro_time", kind="mergesort").copy()
    result = pd.merge_asof(
        source,
        macro,
        left_on="signal_time",
        right_on="macro_time",
        direction="backward",
        tolerance=pd.Timedelta(minutes=tolerance_minutes),
    )
    if result["candidate_id"].duplicated().any() or len(result) != len(actions):
        raise ValueError("Macro enrichment changed action identity or row count")
    age = (result["signal_time"] - result["macro_time"]).dt.total_seconds() / 60.0
    if age.dropna().lt(0.0).any() or age.dropna().gt(tolerance_minutes).any():
        raise ValueError("Macro join violated its causal staleness bound")
    sign = result["direction_sign"].astype(float)
    for prefix in ("dxy", "bond"):
        for horizon in ("15m", "1h", "4h"):
            result[f"dir_{prefix}_gold_pressure_{horizon}"] = (
                sign * result[f"{prefix}_gold_pressure_{horizon}"]
            )
    result["dir_macro_consensus_1h"] = 0.5 * (
        result["dir_dxy_gold_pressure_1h"]
        + result["dir_bond_gold_pressure_1h"]
    )
    result["macro_disagreement_1h"] = (
        result["dxy_gold_pressure_1h"] - result["bond_gold_pressure_1h"]
    ).abs()
    finite = np.isfinite(result[list(MACRO_FEATURE_COLUMNS)].to_numpy(dtype=float))
    complete_rows = finite.all(axis=1)
    complete_events = result.loc[complete_rows, "event_id"].nunique()
    evidence = {
        "action_rows": int(len(result)),
        "event_rows": int(result["event_id"].nunique()),
        "complete_action_rows": int(complete_rows.sum()),
        "complete_event_rows": int(complete_events),
        "complete_action_share": float(complete_rows.mean()),
        "macro_age_minutes_counts": {
            str(float(key)): int(value)
            for key, value in age.loc[complete_rows].value_counts().sort_index().items()
        },
        "missing_values_are_fit_only_median_imputed": True,
        "missingness_indicators_added": False,
    }
    return result.sort_values(["signal_time", "candidate_id"], kind="mergesort").reset_index(drop=True), evidence
