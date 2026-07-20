from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def load_adapter_config() -> dict[str, Any]:
    return json.loads((ROOT / "config" / "adapter.json").read_text(encoding="utf-8"))


def v30_root(adapter_config: Mapping[str, Any]) -> Path:
    return (ROOT / str(adapter_config["v30_root_relative"])).resolve()


def load_v30_module(adapter_config: Mapping[str, Any]) -> ModuleType:
    path = v30_root(adapter_config) / "src" / "exhaustion_reversal.py"
    spec = importlib.util.spec_from_file_location("v30_locked_exhaustion", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_ticks(
    paths: Iterable[Path],
    config: Mapping[str, Any],
    v30: ModuleType,
) -> tuple[pd.DataFrame, dict[str, Any], pd.DataFrame]:
    columns = (
        "dataset_version",
        "account_scope",
        "account_label",
        "symbol",
        "time_utc",
        "time_msc",
        "bid",
        "ask",
        "spread_price",
    )
    source = config["development_source"]
    frames: list[pd.DataFrame] = []
    records: list[dict[str, Any]] = []
    daily_records: list[dict[str, Any]] = []
    disagreement_min = 999999
    disagreement_max = -1
    for path in sorted(Path(value) for value in paths):
        frame = pd.read_csv(path, usecols=list(columns))
        records.append(
            {
                "path": str(path.resolve()).replace("\\", "/"),
                "bytes": int(path.stat().st_size),
                "sha256": v30.sha256_file(path),
                "raw_rows": int(len(frame)),
            }
        )
        if frame.empty:
            continue
        checks = (
            frame["dataset_version"].eq(source["dataset_version"]).all(),
            frame["account_scope"].eq(int(source["account_scope"])).all(),
            frame["account_label"].eq(source["account_label"]).all(),
            frame["symbol"].eq(source["symbol"]).all(),
        )
        if not all(checks):
            raise ValueError(f"V30 adapter identity mismatch: {path}")
        parsed = pd.to_datetime(frame["time_utc"], utc=True, errors="coerce")
        if parsed.isna().any():
            raise ValueError(f"V30 adapter invalid UTC timestamp: {path}")
        frame = frame.rename(columns={"time_msc": "tick_time_msc"})
        for column in ("tick_time_msc", "bid", "ask", "spread_price"):
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        if frame[["tick_time_msc", "bid", "ask", "spread_price"]].isna().any().any():
            raise ValueError(f"V30 adapter invalid numeric value: {path}")
        frame["tick_time_msc"] = frame["tick_time_msc"].astype(np.int64)
        parsed_ms = parsed.array.as_unit("ms").asi8.astype(np.int64, copy=False)
        time_msc = frame["tick_time_msc"].to_numpy(dtype=np.int64)
        if bool(np.any((time_msc // 1000) != (parsed_ms // 1000))):
            raise ValueError(f"V30 adapter cross-second timestamp mismatch: {path}")
        disagreement = time_msc - parsed_ms
        disagreement_min = min(disagreement_min, int(disagreement.min()))
        disagreement_max = max(disagreement_max, int(disagreement.max()))
        spread_error = np.abs(
            (frame["ask"].to_numpy(float) - frame["bid"].to_numpy(float))
            - frame["spread_price"].to_numpy(float)
        )
        if bool(
            np.any(
                spread_error
                > float(config["data_quality"]["maximum_spread_field_error"])
            )
        ):
            raise ValueError(f"V30 adapter spread mismatch: {path}")
        date_utc = pd.Timestamp(int(time_msc[0]), unit="ms", tz="UTC").strftime(
            "%Y-%m-%d"
        )
        daily_records.append(
            {
                "date_utc": date_utc,
                "raw_rows": int(len(frame)),
                "unique_milliseconds": int(frame["tick_time_msc"].nunique()),
            }
        )
        frames.append(frame.loc[:, ["tick_time_msc", "bid", "ask", "spread_price"]])
    if not frames:
        return pd.DataFrame(), {"source_files": records, "raw_rows": 0}, pd.DataFrame()
    raw = pd.concat(frames, ignore_index=True)
    ticks = (
        raw.drop_duplicates("tick_time_msc", keep="last")
        .sort_values("tick_time_msc", kind="mergesort")
        .reset_index(drop=True)
    )
    timestamp = pd.to_datetime(ticks["tick_time_msc"], unit="ms", utc=True)
    ticks["timestamp_utc"] = timestamp.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    ticks["date_utc"] = timestamp.dt.strftime("%Y-%m-%d")
    raw_daily = pd.DataFrame(daily_records).groupby("date_utc", as_index=False).sum()
    raw_daily["duplicate_millisecond_rows"] = (
        raw_daily["raw_rows"] - raw_daily["unique_milliseconds"]
    )
    raw_daily["duplicate_millisecond_share"] = (
        raw_daily["duplicate_millisecond_rows"] / raw_daily["raw_rows"]
    )
    audit = {
        "source_files": records,
        "raw_rows": int(len(raw)),
        "unique_rows": int(len(ticks)),
        "duplicate_millisecond_rows": int(len(raw) - len(ticks)),
        "minimum_timestamp_representation_difference_ms": disagreement_min,
        "maximum_timestamp_representation_difference_ms": disagreement_max,
        "same_second_agreement_share": 1.0,
        "timestamp_rule": "FLOOR_TIME_MSC_SECOND_EQUALS_TIME_UTC_SECOND",
        "daily_source_quality": raw_daily.to_dict(orient="records"),
    }
    return ticks, audit, raw_daily
