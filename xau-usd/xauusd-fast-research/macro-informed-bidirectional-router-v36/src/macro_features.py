from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from contract import sha256_file


def _aggregate_symbol(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    prefix = symbol.lower()
    columns = {
        "timestamp_utc",
        f"{prefix}_available",
        f"{prefix}_mid_open",
        f"{prefix}_mid_high",
        f"{prefix}_mid_low",
        f"{prefix}_mid_close",
        f"{prefix}_mid_tick_count",
    }
    missing = sorted(columns.difference(frame.columns))
    if missing:
        raise ValueError(f"Macro source missing {symbol} columns: {missing}")
    source = frame.loc[frame[f"{prefix}_available"], list(columns)].copy()
    price_columns = [
        f"{prefix}_mid_open",
        f"{prefix}_mid_high",
        f"{prefix}_mid_low",
        f"{prefix}_mid_close",
    ]
    valid = np.isfinite(source[price_columns]).all(axis=1) & (
        source[price_columns] > 0
    ).all(axis=1)
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
    result["timestamp_utc"] = result.pop("_bucket") + pd.Timedelta(minutes=15)
    result.attrs["incomplete_buckets_dropped"] = int((~complete).sum())
    return result


def load_macro_m15(config: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    source = config["macro_source"]
    root = Path(
        os.environ.get(
            source["storage_environment_variable"], source["default_storage_root"]
        )
    )
    cache = root / source["feature_cache"]
    manifest = root / source["feature_manifest"]
    cache_sha = sha256_file(cache)
    manifest_sha = sha256_file(manifest)
    if cache_sha != source["feature_sha256"]:
        raise ValueError(f"Macro feature SHA-256 mismatch: {cache_sha}")
    if manifest_sha != source["manifest_sha256"]:
        raise ValueError(f"Macro manifest SHA-256 mismatch: {manifest_sha}")
    frame = pd.read_parquet(cache)
    if len(frame) != int(source["expected_rows"]):
        raise ValueError(
            f"Expected {source['expected_rows']} macro M5 rows, found {len(frame)}"
        )
    frame = frame.copy()
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True)
    frame = frame.sort_values("timestamp_utc", kind="mergesort").reset_index(drop=True)
    if frame["timestamp_utc"].duplicated().any():
        raise ValueError("Duplicate macro M5 timestamps")
    start = pd.Timestamp(source["start_utc"])
    end = pd.Timestamp(source["end_exclusive_utc"])
    frame = frame.loc[frame["timestamp_utc"].ge(start) & frame["timestamp_utc"].lt(end)]
    dollar = _aggregate_symbol(frame, "DOLLARIDXUSD")
    bond = _aggregate_symbol(frame, "USTBONDTRUSD")
    macro = dollar.merge(bond, on="timestamp_utc", how="inner", validate="one_to_one")
    macro = macro.sort_values("timestamp_utc", kind="mergesort").reset_index(drop=True)
    evidence = {
        "feature_cache": str(cache),
        "feature_manifest": str(manifest),
        "feature_sha256": cache_sha,
        "manifest_sha256": manifest_sha,
        "source_rows": int(len(frame)),
        "dollar_m15_rows": int(len(dollar)),
        "bond_m15_rows": int(len(bond)),
        "joint_m15_rows": int(len(macro)),
        "joint_start_utc": macro["timestamp_utc"].min().isoformat(),
        "joint_end_utc": macro["timestamp_utc"].max().isoformat(),
        "dollar_incomplete_buckets_dropped": int(
            dollar.attrs.get("incomplete_buckets_dropped", 0)
        ),
        "bond_incomplete_buckets_dropped": int(
            bond.attrs.get("incomplete_buckets_dropped", 0)
        ),
    }
    return macro, evidence


def _contiguous_log_return(
    close: pd.Series, timestamp: pd.Series, bars: int
) -> pd.Series:
    elapsed = timestamp - timestamp.shift(bars)
    expected = pd.Timedelta(minutes=15 * bars)
    values = np.log(close / close.shift(bars))
    return values.where(elapsed.eq(expected))


def raw_macro_feature_columns(config: Mapping[str, Any]) -> list[str]:
    columns = []
    for horizon in config["macro_features"]["horizons"]:
        for scale in config["macro_features"]["scales"]:
            columns.extend(
                [f"dxy_pressure_{horizon}_{scale}", f"bond_pressure_{horizon}_{scale}"]
            )
    return columns


def model_macro_feature_columns(config: Mapping[str, Any]) -> list[str]:
    raw = raw_macro_feature_columns(config)
    aligned = [f"route_aligned_{column}" for column in raw]
    return [*raw, *aligned, "macro_feature_age_minutes"]


def build_macro_features(
    macro_m15: pd.DataFrame, config: Mapping[str, Any]
) -> pd.DataFrame:
    frame = macro_m15.copy().sort_values("timestamp_utc", kind="mergesort")
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True)
    if frame["timestamp_utc"].duplicated().any():
        raise ValueError("Duplicate macro decision timestamps")
    settings = config["macro_features"]
    minimum_fraction = float(settings["minimum_scale_fraction"])
    output = frame[["timestamp_utc"]].rename(
        columns={"timestamp_utc": "macro_feature_time"}
    )
    for horizon, raw_bars in settings["horizons"].items():
        bars = int(raw_bars)
        for symbol, pressure_sign in (
            ("dollaridxusd", -1.0),
            ("ustbondtrusd", 1.0),
        ):
            returns = _contiguous_log_return(
                frame[f"{symbol}_close"], frame["timestamp_utc"], bars
            )
            for scale, raw_scale_bars in settings["scales"].items():
                scale_bars = int(raw_scale_bars)
                minimum = max(2, int(scale_bars * minimum_fraction))
                prior_scale = (
                    returns.shift(1)
                    .rolling(scale_bars, min_periods=minimum)
                    .std(ddof=0)
                )
                prefix = "dxy" if symbol == "dollaridxusd" else "bond"
                output[f"{prefix}_pressure_{horizon}_{scale}"] = (
                    pressure_sign * returns / prior_scale.replace(0.0, np.nan)
                )
    return output


def align_macro_features(
    actions: pd.DataFrame,
    macro_features: pd.DataFrame,
    config: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    left = actions.copy()
    left["signal_time"] = pd.to_datetime(left["signal_time"], utc=True)
    left["entry_time"] = pd.to_datetime(left["entry_time"], utc=True)
    left["exit_time"] = pd.to_datetime(left["exit_time"], utc=True)
    left = left.sort_values(["signal_time", "event_id", "action_id"], kind="mergesort")
    right = macro_features.copy()
    right["macro_feature_time"] = pd.to_datetime(right["macro_feature_time"], utc=True)
    right = right.sort_values("macro_feature_time", kind="mergesort")
    maximum_age = int(config["macro_features"]["maximum_feature_age_minutes"])
    merged = pd.merge_asof(
        left,
        right,
        left_on="signal_time",
        right_on="macro_feature_time",
        direction="backward",
        tolerance=pd.Timedelta(minutes=maximum_age),
        allow_exact_matches=True,
    )
    merged["macro_feature_age_minutes"] = (
        merged["signal_time"] - merged["macro_feature_time"]
    ).dt.total_seconds() / 60.0
    route_sign = np.where(merged["direction"].eq("LONG"), 1.0, -1.0)
    raw = raw_macro_feature_columns(config)
    for column in raw:
        merged[f"route_aligned_{column}"] = merged[column] * route_sign
    features = model_macro_feature_columns(config)
    required = list(config["macro_features"]["required_finite_features"])
    ready = (
        np.isfinite(merged[required]).all(axis=1)
        if required
        else pd.Series(True, index=merged.index)
    )
    aligned = merged.loc[ready].copy()
    if np.isinf(aligned[features]).any(axis=None):
        raise ValueError("Infinite macro feature reached an action")
    available = aligned["macro_feature_time"].notna()
    if (
        aligned.loc[available, "macro_feature_time"]
        > aligned.loc[available, "signal_time"]
    ).any():
        raise ValueError("Future macro timestamp reached an action")
    ages = aligned.loc[available, "macro_feature_age_minutes"]
    if ages.lt(0.0).any() or ages.gt(float(maximum_age)).any():
        raise ValueError("Macro feature age violates the causal boundary")
    if aligned.duplicated(["event_id", "action_id"]).any():
        raise ValueError("Duplicate action after macro alignment")
    evidence = {
        "base_action_rows": int(len(actions)),
        "aligned_action_rows_before_finite_filter": int(len(merged)),
        "dropped_missing_required_macro_rows": int((~ready).sum()),
        "merged_action_rows": int(len(aligned)),
        "macro_timestamp_available_rows": int(available.sum()),
        "macro_timestamp_unavailable_rows": int((~available).sum()),
        "events": int(aligned["event_id"].nunique()),
        "first_signal_time": aligned["signal_time"].min().isoformat(),
        "last_signal_time": aligned["signal_time"].max().isoformat(),
        "minimum_macro_feature_age_minutes": float(ages.min()),
        "maximum_macro_feature_age_minutes": float(ages.max()),
        "required_finite_macro_features": required,
        "finite_macro_feature_rows": {
            column: int(np.isfinite(merged[column]).sum()) for column in features
        },
        "macro_features": features,
    }
    return aligned.reset_index(drop=True), evidence
