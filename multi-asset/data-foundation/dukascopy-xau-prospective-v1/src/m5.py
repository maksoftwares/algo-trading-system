from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable

import numpy as np
import pandas as pd

from src.snapshot import parse_utc, sha256_file


BAR_MS = 5 * 60 * 1000
BASE_COLUMNS = [
    "timestamp_ms",
    "xau_tick_count",
    "xau_mid_tick_open",
    "xau_mid_tick_close",
    "tick_signed_move",
    "tick_move_count",
    "tick_realized_variance",
    "tick_spread_mean",
    "tick_spread_last",
    "tick_spread_max",
    "tick_book_imbalance_mean",
    "tick_book_imbalance_last",
    "tick_microprice_edge_mean",
    "tick_microprice_edge_last",
    "price_efficiency_5m",
    "bid_open",
    "bid_high",
    "bid_low",
    "bid_close",
    "ask_open",
    "ask_high",
    "ask_low",
    "ask_close",
    "mid_open",
    "mid_high",
    "mid_low",
    "mid_close",
]


def aggregate_ticks(ticks: Iterable[Any]) -> pd.DataFrame:
    values = list(ticks)
    if not values:
        return pd.DataFrame(columns=BASE_COLUMNS)
    times = np.fromiter((tick.timestamp_ms for tick in values), dtype=np.int64)
    bids = np.fromiter((tick.bid for tick in values), dtype=float)
    asks = np.fromiter((tick.ask for tick in values), dtype=float)
    bid_volume = np.fromiter((tick.bid_volume for tick in values), dtype=float)
    ask_volume = np.fromiter((tick.ask_volume for tick in values), dtype=float)
    order = np.argsort(times, kind="stable")
    times = times[order]
    bids = bids[order]
    asks = asks[order]
    bid_volume = bid_volume[order]
    ask_volume = ask_volume[order]
    buckets = times - times % BAR_MS
    starts = np.r_[0, np.flatnonzero(np.diff(buckets)) + 1]
    counts = np.diff(np.r_[starts, len(buckets)])
    ends = starts + counts - 1
    mid = (bids + asks) / 2.0
    spread = asks - bids
    total_volume = bid_volume + ask_volume
    book_imbalance = np.divide(
        bid_volume - ask_volume,
        total_volume,
        out=np.zeros_like(total_volume),
        where=total_volume > 0.0,
    )
    # Legacy cache convention: this named edge is a dimensionless half-scale
    # imbalance, not the price displacement implied by a standard microprice.
    microprice_edge = 0.5 * book_imbalance
    delta = np.diff(mid, prepend=mid[0])
    delta[starts] = 0.0
    signed = np.sign(delta)
    absolute_move = np.add.reduceat(np.abs(delta), starts)
    net_move = mid[ends] - mid[starts]
    result: dict[str, Any] = {
        "timestamp_ms": buckets[starts],
        "xau_tick_count": counts.astype(np.int64),
        "xau_mid_tick_open": mid[starts],
        "xau_mid_tick_close": mid[ends],
        "tick_signed_move": np.add.reduceat(signed, starts),
        "tick_move_count": np.add.reduceat((signed != 0).astype(np.int64), starts),
        "tick_realized_variance": np.add.reduceat(np.square(delta), starts),
        "tick_spread_mean": np.add.reduceat(spread, starts) / counts,
        "tick_spread_last": spread[ends],
        "tick_spread_max": np.maximum.reduceat(spread, starts),
        "tick_book_imbalance_mean": np.add.reduceat(book_imbalance, starts) / counts,
        "tick_book_imbalance_last": book_imbalance[ends],
        "tick_microprice_edge_mean": np.add.reduceat(microprice_edge, starts) / counts,
        "tick_microprice_edge_last": microprice_edge[ends],
        "price_efficiency_5m": np.divide(
            np.abs(net_move),
            absolute_move,
            out=np.zeros_like(net_move),
            where=absolute_move > 0.0,
        ),
    }
    for name, series in (("bid", bids), ("ask", asks), ("mid", mid)):
        result[f"{name}_open"] = series[starts]
        result[f"{name}_high"] = np.maximum.reduceat(series, starts)
        result[f"{name}_low"] = np.minimum.reduceat(series, starts)
        result[f"{name}_close"] = series[ends]
    return pd.DataFrame(result)[BASE_COLUMNS]


def load_hours(
    foundation: ModuleType,
    storage_root: Path,
    symbol: str,
    rows: list[dict[str, Any]],
) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for row in rows:
        hour = parse_utc(row["hour_utc"])
        path = (storage_root / row["path"]).resolve()
        ticks = foundation.decode_payload(path.read_bytes(), symbol, row["source_file_id"])
        if ticks:
            first = datetime.fromtimestamp(ticks[0].timestamp_ms / 1000, UTC)
            last = datetime.fromtimestamp(ticks[-1].timestamp_ms / 1000, UTC)
            if first < hour or last >= hour + timedelta(hours=1):
                raise ValueError(f"tick escaped source hour: {hour}")
        part = aggregate_ticks(ticks)
        if not part.empty:
            parts.append(part)
    if not parts:
        return pd.DataFrame(columns=BASE_COLUMNS)
    result = pd.concat(parts, ignore_index=True).sort_values(
        "timestamp_ms", kind="mergesort"
    )
    if result["timestamp_ms"].duplicated().any():
        raise ValueError("duplicate M5 buckets across source hours")
    return result.reset_index(drop=True)


def parity_against_frozen(
    rebuilt: pd.DataFrame, frozen: pd.DataFrame, tolerance: float = 1e-10
) -> dict[str, Any]:
    expected = frozen.loc[
        frozen["timestamp_ms"].isin(rebuilt["timestamp_ms"]), BASE_COLUMNS
    ].sort_values("timestamp_ms", kind="mergesort")
    actual = rebuilt.sort_values("timestamp_ms", kind="mergesort")
    if len(actual) != len(expected) or not np.array_equal(
        actual["timestamp_ms"].to_numpy(), expected["timestamp_ms"].to_numpy()
    ):
        raise ValueError("historical parity timestamp mismatch")
    errors: dict[str, float] = {}
    for column in BASE_COLUMNS:
        if column in {"timestamp_ms", "xau_tick_count", "tick_move_count"}:
            if not np.array_equal(actual[column].to_numpy(), expected[column].to_numpy()):
                raise ValueError(f"historical parity integer mismatch: {column}")
            errors[column] = 0.0
            continue
        error = float(
            np.nanmax(
                np.abs(
                    actual[column].to_numpy(dtype=float)
                    - expected[column].to_numpy(dtype=float)
                )
            )
        )
        errors[column] = error
        if error > tolerance:
            raise ValueError(f"historical parity mismatch {column}: {error}")
    return {"rows": len(actual), "maximum_absolute_error": max(errors.values())}


def _continued_wilder(
    true_range: np.ndarray, previous_atr: float, period: int
) -> np.ndarray:
    alpha = 1.0 / period
    result = np.empty(len(true_range), dtype=float)
    state = float(previous_atr)
    for index, value in enumerate(true_range):
        state = (1.0 - alpha) * state + alpha * float(value)
        result[index] = state
    return result


def add_rolling_features(base: pd.DataFrame, frozen: pd.DataFrame) -> pd.DataFrame:
    result = base.copy()
    prior = frozen.sort_values("timestamp_ms", kind="mergesort").tail(288).copy()
    previous_close = float(prior.iloc[-1]["mid_close"])
    previous_atr = float(prior.iloc[-1]["atr"])
    high = result["mid_high"].to_numpy(dtype=float)
    low = result["mid_low"].to_numpy(dtype=float)
    close = result["mid_close"].to_numpy(dtype=float)
    previous = np.r_[previous_close, close[:-1]]
    true_range = np.maximum.reduce([high - low, np.abs(high - previous), np.abs(low - previous)])
    result["atr"] = _continued_wilder(true_range, previous_atr, 14)
    prior_atr = prior["atr"].to_numpy(dtype=float)
    all_atr = np.r_[prior_atr, result["atr"].to_numpy(dtype=float)]
    result["atr_ratio"] = [
        all_atr[len(prior_atr) + index]
        / np.median(all_atr[index : len(prior_atr) + index])
        for index in range(len(result))
    ]
    prior_counts = prior["xau_tick_count"].to_numpy(dtype=float)
    all_counts = np.r_[prior_counts, result["xau_tick_count"].to_numpy(dtype=float)]
    result["quote_intensity_ratio"] = [
        all_counts[len(prior_counts) + index]
        / np.median(all_counts[index : len(prior_counts) + index])
        for index in range(len(result))
    ]
    result["tick_imbalance_5m"] = result["tick_signed_move"].div(
        result["tick_move_count"].replace(0, np.nan)
    )
    prior_signed = prior["tick_signed_move"].tail(2).to_numpy(dtype=float)
    prior_moves = prior["tick_move_count"].tail(2).to_numpy(dtype=float)
    signed = pd.Series(np.r_[prior_signed, result["tick_signed_move"]])
    moves = pd.Series(np.r_[prior_moves, result["tick_move_count"]])
    result["tick_imbalance_15m"] = (
        signed.rolling(3).sum().div(moves.rolling(3).sum().replace(0, np.nan)).iloc[2:].to_numpy()
    )
    span = (result["mid_high"] - result["mid_low"]).replace(0.0, np.nan)
    result["body_fraction"] = (
        (result["mid_close"] - result["mid_open"]).abs().div(span).fillna(0.0)
    )
    result["close_location"] = (
        (result["mid_close"] - result["mid_low"]).div(span).fillna(0.5)
    )
    timestamp = pd.to_datetime(result["timestamp_ms"], unit="ms", utc=True)
    result["date_utc"] = timestamp.dt.strftime("%Y-%m-%d")
    result["hour_utc"] = timestamp.dt.hour.astype(np.int64)
    return result[[*BASE_COLUMNS, "atr", "atr_ratio", "quote_intensity_ratio", "tick_imbalance_5m", "tick_imbalance_15m", "body_fraction", "close_location", "date_utc", "hour_utc"]]


def write_features(
    foundation: ModuleType,
    storage_root: Path,
    snapshot_path: Path,
    frozen_path: Path,
    features: pd.DataFrame,
    parity: dict[str, Any],
) -> tuple[Path, Path]:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    start = parse_utc(snapshot["start_utc"])
    end = parse_utc(snapshot["end_exclusive_utc"])
    directory = storage_root / "prospective-v1" / "features"
    directory.mkdir(parents=True, exist_ok=True)
    stem = f"XAUUSD_{start:%Y%m%d%H}_{end:%Y%m%d%H}_M5_FEATURES_V1"
    output = directory / f"{stem}.parquet"
    features.to_parquet(output, index=False, compression="zstd")
    manifest = directory / f"{stem}.manifest.json"
    foundation.write_json(
        manifest,
        {
            "schema_version": "dukascopy_xau_prospective_m5_features_v1",
            "snapshot_manifest": str(snapshot_path),
            "snapshot_manifest_sha256": sha256_file(snapshot_path),
            "frozen_context": str(frozen_path),
            "frozen_context_sha256": sha256_file(frozen_path),
            "historical_parity": parity,
            "rows": len(features),
            "columns": features.columns.tolist(),
            "start_timestamp_ms": int(features["timestamp_ms"].min()),
            "end_timestamp_ms": int(features["timestamp_ms"].max()),
            "feature_sha256": sha256_file(output),
            "feature_path": str(output),
        },
    )
    return output, manifest
