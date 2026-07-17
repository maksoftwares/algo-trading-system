from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SHARED_DATA_PATH = ROOT / "independent-specialists-v1" / "src" / "data.py"


def _load_shared_data() -> Any:
    name = "xau_independent_specialists_shared_data"
    spec = importlib.util.spec_from_file_location(name, SHARED_DATA_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load shared data module from {SHARED_DATA_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SHARED_DATA = _load_shared_data()


@dataclass(frozen=True)
class ResearchInputs:
    gold: Any
    macro_m15: pd.DataFrame
    evidence: dict[str, Any]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    valid_prices = np.isfinite(source[price_columns]).all(axis=1) & (source[price_columns] > 0).all(axis=1)
    source = source.loc[valid_prices]
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
    root = Path(os.environ.get(source["storage_environment_variable"], source["default_storage_root"]))
    cache = root / source["feature_cache"]
    manifest_path = root / source["feature_manifest"]
    if not cache.is_file() or not manifest_path.is_file():
        raise FileNotFoundError(f"Verified intraday macro source is unavailable below {root}")
    cache_sha = sha256_file(cache)
    manifest_sha = sha256_file(manifest_path)
    if cache_sha != source["feature_sha256"]:
        raise ValueError(f"Macro feature SHA-256 mismatch: {cache_sha}")
    if manifest_sha != source["manifest_sha256"]:
        raise ValueError(f"Macro manifest SHA-256 mismatch: {manifest_sha}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frame = pd.read_parquet(cache)
    if len(frame) != int(source["expected_rows"]):
        raise ValueError(f"Expected {source['expected_rows']} macro M5 rows, found {len(frame)}")
    frame = frame.copy()
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True)
    frame = frame.sort_values("timestamp_utc", kind="mergesort").reset_index(drop=True)
    if frame["timestamp_utc"].duplicated().any():
        raise ValueError("Duplicate intraday macro M5 timestamps detected")
    start = pd.Timestamp(source["start_utc"])
    end = pd.Timestamp(source["end_exclusive_utc"])
    frame = frame.loc[(frame["timestamp_utc"] >= start) & (frame["timestamp_utc"] < end)]
    dollar = _aggregate_symbol(frame, "DOLLARIDXUSD")
    bond = _aggregate_symbol(frame, "USTBONDTRUSD")
    macro = dollar.merge(bond, on="timestamp_utc", how="inner", validate="one_to_one")
    macro = macro.sort_values("timestamp_utc", kind="mergesort").reset_index(drop=True)
    evidence = {
        "feature_cache": str(cache),
        "feature_manifest": str(manifest_path),
        "feature_sha256": cache_sha,
        "manifest_sha256": manifest_sha,
        "manifest": manifest,
        "source_rows": int(len(frame)),
        "dollar_m15_rows": int(len(dollar)),
        "bond_m15_rows": int(len(bond)),
        "joint_m15_rows": int(len(macro)),
        "joint_start_utc": macro["timestamp_utc"].min().isoformat(),
        "joint_end_utc": macro["timestamp_utc"].max().isoformat(),
        "dollar_incomplete_buckets_dropped": int(dollar.attrs.get("incomplete_buckets_dropped", 0)),
        "bond_incomplete_buckets_dropped": int(bond.attrs.get("incomplete_buckets_dropped", 0)),
    }
    return macro, evidence


def load_inputs(config: dict[str, Any]) -> ResearchInputs:
    gold = SHARED_DATA.load_bundle(config)
    macro_m15, macro_evidence = load_macro_m15(config)
    return ResearchInputs(
        gold=gold,
        macro_m15=macro_m15,
        evidence={"gold": gold.evidence, "intraday_macro": macro_evidence},
    )
