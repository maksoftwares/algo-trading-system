from __future__ import annotations

import gzip
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

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
    "xau",
}


@dataclass(frozen=True)
class SourceTick:
    timestamp_ms: int
    bid: float
    ask: float
    bid_volume: float
    ask_volume: float


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


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


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(value))


def deterministic_gzip(raw: bytes) -> bytes:
    return gzip.compress(raw, compresslevel=6, mtime=0)


def expand_gzip(value: bytes) -> bytes:
    try:
        return gzip.decompress(value)
    except (EOFError, OSError) as exc:
        raise ValueError("invalid gzip source payload") from exc


def _round_source_price(value: float, scale: int) -> float:
    factor = 10**scale
    return math.floor(value * factor + 0.5 + 1e-9) / factor


def decode_source_payload(raw: bytes, price_scale: int) -> list[SourceTick]:
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid source JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("source payload is not an object")
    arrays = ("times", "bids", "asks", "bidVolumes", "askVolumes")
    required = ("timestamp", "multiplier", "bid", "ask", *arrays)
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"missing source fields: {missing}")
    lengths = {
        key: len(payload[key]) if isinstance(payload[key], list) else -1
        for key in arrays
    }
    if len(set(lengths.values())) != 1 or next(iter(lengths.values())) < 0:
        raise ValueError(f"inconsistent tick arrays: {lengths}")
    count = lengths["times"]
    if count == 0:
        return []

    try:
        timestamp = int(payload["timestamp"])
        multiplier = float(payload["multiplier"])
        bid = float(payload["bid"])
        ask = float(payload["ask"])
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid base timestamp or price") from exc
    if not math.isfinite(multiplier) or multiplier <= 0:
        raise ValueError("source multiplier must be positive")

    result: list[SourceTick] = []
    previous_timestamp = -1
    for index in range(count):
        timestamp += int(payload["times"][index])
        bid = _round_source_price(
            bid + float(payload["bids"][index]) * multiplier, price_scale
        )
        ask = _round_source_price(
            ask + float(payload["asks"][index]) * multiplier, price_scale
        )
        bid_volume = float(payload["bidVolumes"][index])
        ask_volume = float(payload["askVolumes"][index])
        if timestamp < previous_timestamp:
            raise ValueError("source timestamps are not monotonic")
        if not (
            math.isfinite(bid)
            and math.isfinite(ask)
            and bid > 0
            and ask >= bid
        ):
            raise ValueError("source contains a nonpositive or crossed quote")
        if not (
            math.isfinite(bid_volume)
            and math.isfinite(ask_volume)
            and bid_volume >= 0
            and ask_volume >= 0
        ):
            raise ValueError("source contains invalid best-side volume")
        result.append(SourceTick(timestamp, bid, ask, bid_volume, ask_volume))
        previous_timestamp = timestamp
    return result


def validate_hour_payload(
    raw: bytes, hour: datetime, price_scale: int
) -> list[SourceTick]:
    ticks = decode_source_payload(raw, price_scale)
    start_ms = int(hour.astimezone(UTC).timestamp() * 1000)
    end_ms = start_ms + 3_600_000
    if any(
        tick.timestamp_ms < start_ms or tick.timestamp_ms >= end_ms for tick in ticks
    ):
        raise ValueError("source tick falls outside requested UTC hour")
    return ticks


def raw_hour_path(root: Path, symbol: str, hour: datetime) -> Path:
    return (
        root
        / "raw"
        / symbol
        / f"year={hour.year:04d}"
        / f"month={hour.month:02d}"
        / f"{hour:%Y%m%d%H}.json.gz"
    )


def read_stored_hour(
    path: Path,
    hour: datetime,
    price_scale: int,
    expected_source_sha256: str | None = None,
) -> tuple[bytes, list[SourceTick]]:
    raw = expand_gzip(path.read_bytes())
    if expected_source_sha256 and sha256_bytes(raw) != expected_source_sha256:
        raise ValueError("expanded source checksum mismatch")
    return raw, validate_hour_payload(raw, hour, price_scale)


def aggregate_hour_m5(ticks: Iterable[SourceTick], prefix: str) -> pd.DataFrame:
    rows: list[dict[str, float | int]] = []
    previous_mid: float | None = None
    for tick in ticks:
        mid = (tick.bid + tick.ask) / 2.0
        signed_move = 0
        if previous_mid is not None:
            signed_move = int(mid > previous_mid) - int(mid < previous_mid)
        rows.append(
            {
                "timestamp_ms": tick.timestamp_ms,
                "bar_open_timestamp_ms": tick.timestamp_ms
                - tick.timestamp_ms % BAR_WIDTH_MS,
                "bid": tick.bid,
                "ask": tick.ask,
                "mid": mid,
                "spread": tick.ask - tick.bid,
                "bid_volume": tick.bid_volume,
                "ask_volume": tick.ask_volume,
                "signed_move": signed_move,
            }
        )
        previous_mid = mid
    if not rows:
        return pd.DataFrame(columns=bar_columns(prefix))

    frame = pd.DataFrame(rows).sort_values("timestamp_ms", kind="stable")
    grouped = frame.groupby("bar_open_timestamp_ms", sort=True, observed=True)
    result = grouped.agg(
        bid_open=("bid", "first"),
        bid_high=("bid", "max"),
        bid_low=("bid", "min"),
        bid_close=("bid", "last"),
        ask_open=("ask", "first"),
        ask_high=("ask", "max"),
        ask_low=("ask", "min"),
        ask_close=("ask", "last"),
        mid_open=("mid", "first"),
        mid_high=("mid", "max"),
        mid_low=("mid", "min"),
        mid_close=("mid", "last"),
        tick_count=("mid", "size"),
        bid_volume_sum=("bid_volume", "sum"),
        ask_volume_sum=("ask_volume", "sum"),
        signed_move=("signed_move", "sum"),
        spread_mean=("spread", "mean"),
        spread_last=("spread", "last"),
        spread_max=("spread", "max"),
        source_last_timestamp_ms=("timestamp_ms", "last"),
    ).reset_index()
    result["available_timestamp_ms"] = (
        result["bar_open_timestamp_ms"] + BAR_WIDTH_MS
    )
    if not (
        result["source_last_timestamp_ms"] < result["available_timestamp_ms"]
    ).all():
        raise ValueError("source tick crosses its M5 availability boundary")
    rename = {
        column: f"{prefix}_{column}"
        for column in result.columns
        if column != "bar_open_timestamp_ms"
    }
    return result.rename(columns=rename).loc[:, bar_columns(prefix)]


def bar_columns(prefix: str) -> list[str]:
    return [
        "bar_open_timestamp_ms",
        f"{prefix}_available_timestamp_ms",
        f"{prefix}_source_last_timestamp_ms",
        f"{prefix}_bid_open",
        f"{prefix}_bid_high",
        f"{prefix}_bid_low",
        f"{prefix}_bid_close",
        f"{prefix}_ask_open",
        f"{prefix}_ask_high",
        f"{prefix}_ask_low",
        f"{prefix}_ask_close",
        f"{prefix}_mid_open",
        f"{prefix}_mid_high",
        f"{prefix}_mid_low",
        f"{prefix}_mid_close",
        f"{prefix}_tick_count",
        f"{prefix}_bid_volume_sum",
        f"{prefix}_ask_volume_sum",
        f"{prefix}_signed_move",
        f"{prefix}_spread_mean",
        f"{prefix}_spread_last",
        f"{prefix}_spread_max",
    ]


def add_causal_features(frame: pd.DataFrame, prefix: str) -> pd.DataFrame:
    result = frame.sort_values("bar_open_timestamp_ms").reset_index(drop=True).copy()
    log_close = np.log(result[f"{prefix}_mid_close"].where(lambda value: value > 0))
    for bars, name in ((1, "5m"), (3, "15m"), (6, "30m"), (12, "60m")):
        contiguous = result["bar_open_timestamp_ms"].diff(bars).eq(
            bars * BAR_WIDTH_MS
        )
        result[f"{prefix}_return_{name}"] = log_close.diff(bars).where(contiguous)
    prior_ticks = (
        result[f"{prefix}_tick_count"].shift(1).rolling(288, min_periods=48).median()
    )
    result[f"{prefix}_quote_intensity_ratio"] = result[f"{prefix}_tick_count"].div(
        prior_ticks.replace(0.0, np.nan)
    )
    prior_spread = (
        result[f"{prefix}_spread_mean"].shift(1).rolling(288, min_periods=48).median()
    )
    result[f"{prefix}_spread_shock_ratio"] = result[f"{prefix}_spread_mean"].div(
        prior_spread.replace(0.0, np.nan)
    )
    return result


def validate_curated(frame: pd.DataFrame, prefixes: Iterable[str]) -> None:
    lowered = {column.lower() for column in frame.columns}
    forbidden = {
        column
        for column in lowered
        if any(token == column or token in column.split("_") for token in FORBIDDEN_COLUMNS)
    }
    if forbidden:
        raise ValueError(f"outcome-bearing columns are forbidden: {sorted(forbidden)}")
    if frame["bar_open_timestamp_ms"].duplicated().any():
        raise ValueError("duplicate M5 timestamp")
    if not frame["bar_open_timestamp_ms"].is_monotonic_increasing:
        raise ValueError("M5 timestamps are not ordered")
    if not frame["bar_open_timestamp_ms"].mod(BAR_WIDTH_MS).eq(0).all():
        raise ValueError("M5 timestamp is off-grid")
    for prefix in prefixes:
        available = f"{prefix}_available_timestamp_ms"
        present = frame[available].notna()
        expected = frame.loc[present, "bar_open_timestamp_ms"] + BAR_WIDTH_MS
        if not frame.loc[present, available].eq(expected).all():
            raise ValueError(f"{prefix} availability timestamp is noncausal")
