from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


BAR_WIDTH_MS = 300_000
FORBIDDEN_COLUMNS = {
    "signal",
    "direction",
    "entry",
    "exit",
    "pnl",
    "profit",
    "loss",
    "target",
    "stop",
    "label",
}


@dataclass(frozen=True)
class VolTick:
    timestamp_ms: int
    bid: float
    ask: float
    bid_volume: float
    ask_volume: float


def decode_vol_payload(
    raw: bytes, maximum_invalid_fraction: float
) -> tuple[list[VolTick], dict[str, int | float]]:
    payload = json.loads(raw)
    arrays = ("times", "bids", "asks", "bidVolumes", "askVolumes")
    missing = [
        key
        for key in ("timestamp", "multiplier", "bid", "ask", *arrays)
        if key not in payload
    ]
    if missing:
        raise ValueError(f"Missing VOLIDX payload fields: {missing}")
    lengths = {
        key: len(payload[key]) if isinstance(payload[key], list) else -1
        for key in arrays
    }
    if len(set(lengths.values())) != 1 or next(iter(lengths.values())) < 0:
        raise ValueError(f"Inconsistent VOLIDX tick arrays: {lengths}")
    source_count = lengths["times"]
    if source_count == 0:
        return [], {
            "source_tick_count": 0,
            "valid_tick_count": 0,
            "invalid_tick_count": 0,
            "invalid_quote_fraction": 0.0,
        }

    timestamp = int(payload["timestamp"])
    multiplier = float(payload["multiplier"])
    bid = float(payload["bid"])
    ask = float(payload["ask"])
    previous_timestamp = -1
    valid: list[VolTick] = []
    invalid_count = 0
    for index in range(source_count):
        timestamp += int(payload["times"][index])
        bid = round(bid + float(payload["bids"][index]) * multiplier, 6)
        ask = round(ask + float(payload["asks"][index]) * multiplier, 6)
        bid_volume = float(payload["bidVolumes"][index])
        ask_volume = float(payload["askVolumes"][index])
        if timestamp < previous_timestamp:
            raise ValueError("VOLIDX source timestamps are not monotonic")
        previous_timestamp = timestamp
        quote_valid = (
            math.isfinite(bid)
            and math.isfinite(ask)
            and bid > 0
            and ask >= bid
            and math.isfinite(bid_volume)
            and math.isfinite(ask_volume)
            and bid_volume >= 0
            and ask_volume >= 0
        )
        if not quote_valid:
            invalid_count += 1
            continue
        valid.append(VolTick(timestamp, bid, ask, bid_volume, ask_volume))

    invalid_fraction = invalid_count / source_count
    if invalid_fraction > maximum_invalid_fraction:
        raise ValueError(
            f"VOLIDX invalid quote fraction {invalid_fraction:.6f} exceeds "
            f"{maximum_invalid_fraction:.6f}"
        )
    return valid, {
        "source_tick_count": source_count,
        "valid_tick_count": len(valid),
        "invalid_tick_count": invalid_count,
        "invalid_quote_fraction": invalid_fraction,
    }


def validate_hour_payload(
    raw: bytes,
    hour: datetime,
    maximum_invalid_fraction: float,
) -> tuple[list[VolTick], dict[str, int | float]]:
    ticks, quality = decode_vol_payload(raw, maximum_invalid_fraction)
    start_ms = int(hour.timestamp() * 1000)
    end_ms = start_ms + 3_600_000
    if any(
        tick.timestamp_ms < start_ms or tick.timestamp_ms >= end_ms for tick in ticks
    ):
        raise ValueError("VOLIDX tick falls outside requested UTC hour")
    return ticks, quality


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("ascii")


def aggregate_m5(ticks: Iterable[Any]) -> pd.DataFrame:
    rows = []
    previous_mid: float | None = None
    for tick in ticks:
        mid = (float(tick.bid) + float(tick.ask)) / 2.0
        signed_move = 0
        if previous_mid is not None:
            signed_move = int(mid > previous_mid) - int(mid < previous_mid)
        rows.append(
            {
                "timestamp_ms": int(tick.timestamp_ms),
                "bar_open_timestamp_ms": int(tick.timestamp_ms)
                - int(tick.timestamp_ms) % BAR_WIDTH_MS,
                "bid": float(tick.bid),
                "ask": float(tick.ask),
                "mid": mid,
                "spread": float(tick.ask) - float(tick.bid),
                "signed_move": signed_move,
            }
        )
        previous_mid = mid
    if not rows:
        return empty_feature_frame()

    frame = pd.DataFrame(rows).sort_values("timestamp_ms", kind="stable")
    grouped = frame.groupby("bar_open_timestamp_ms", sort=True, observed=True)
    result = grouped.agg(
        vol_bid_open=("bid", "first"),
        vol_bid_high=("bid", "max"),
        vol_bid_low=("bid", "min"),
        vol_bid_close=("bid", "last"),
        vol_ask_open=("ask", "first"),
        vol_ask_high=("ask", "max"),
        vol_ask_low=("ask", "min"),
        vol_ask_close=("ask", "last"),
        vol_mid_open=("mid", "first"),
        vol_mid_high=("mid", "max"),
        vol_mid_low=("mid", "min"),
        vol_mid_close=("mid", "last"),
        vol_tick_count=("mid", "size"),
        vol_signed_move=("signed_move", "sum"),
        vol_spread_mean=("spread", "mean"),
        vol_spread_last=("spread", "last"),
        vol_spread_max=("spread", "max"),
        source_last_timestamp_ms=("timestamp_ms", "last"),
    ).reset_index()
    result["available_timestamp_ms"] = result["bar_open_timestamp_ms"] + BAR_WIDTH_MS
    if not (
        result["source_last_timestamp_ms"] < result["available_timestamp_ms"]
    ).all():
        raise ValueError("M5 source tick crosses its availability boundary")
    return result.loc[:, feature_columns()]


def empty_feature_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=feature_columns())


def feature_columns() -> list[str]:
    return [
        "bar_open_timestamp_ms",
        "available_timestamp_ms",
        "source_last_timestamp_ms",
        "vol_bid_open",
        "vol_bid_high",
        "vol_bid_low",
        "vol_bid_close",
        "vol_ask_open",
        "vol_ask_high",
        "vol_ask_low",
        "vol_ask_close",
        "vol_mid_open",
        "vol_mid_high",
        "vol_mid_low",
        "vol_mid_close",
        "vol_tick_count",
        "vol_signed_move",
        "vol_spread_mean",
        "vol_spread_last",
        "vol_spread_max",
    ]


def add_causal_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.sort_values("bar_open_timestamp_ms").reset_index(drop=True).copy()
    contiguous = result["bar_open_timestamp_ms"].diff().eq(BAR_WIDTH_MS)
    log_close = np.log(result["vol_mid_close"].where(result["vol_mid_close"].gt(0)))
    result["vol_return_5m"] = log_close.diff().where(contiguous)
    result["vol_return_15m"] = log_close.diff(3).where(
        result["bar_open_timestamp_ms"].diff(3).eq(3 * BAR_WIDTH_MS)
    )
    result["vol_return_60m"] = log_close.diff(12).where(
        result["bar_open_timestamp_ms"].diff(12).eq(12 * BAR_WIDTH_MS)
    )
    baseline_ticks = (
        result["vol_tick_count"].shift(1).rolling(48, min_periods=12).median()
    )
    result["vol_quote_intensity_ratio"] = result["vol_tick_count"].div(
        baseline_ticks.replace(0.0, np.nan)
    )
    prior_spread = (
        result["vol_spread_mean"].shift(1).rolling(48, min_periods=12).median()
    )
    result["vol_spread_shock_ratio"] = result["vol_spread_mean"].div(
        prior_spread.replace(0.0, np.nan)
    )
    return result


def validate_curated(frame: pd.DataFrame) -> None:
    lowered = {column.lower() for column in frame.columns}
    forbidden = lowered & FORBIDDEN_COLUMNS
    if forbidden:
        raise ValueError(f"Outcome-bearing columns are forbidden: {sorted(forbidden)}")
    if frame["bar_open_timestamp_ms"].duplicated().any():
        raise ValueError("Duplicate VOLIDX M5 timestamp")
    if not frame["bar_open_timestamp_ms"].is_monotonic_increasing:
        raise ValueError("VOLIDX M5 timestamps are not ordered")
    if not frame["bar_open_timestamp_ms"].mod(BAR_WIDTH_MS).eq(0).all():
        raise ValueError("VOLIDX M5 timestamps are off-grid")
    if (
        not frame["available_timestamp_ms"]
        .eq(frame["bar_open_timestamp_ms"] + BAR_WIDTH_MS)
        .all()
    ):
        raise ValueError("VOLIDX availability timestamp is noncausal")


def write_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(payload))
