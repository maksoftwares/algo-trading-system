"""Multi-pair FX bar foundation built from the Dukascopy tick archive.

Decoding follows the same source contract as
``multi-asset/data-foundation/dukascopy-ticks-v1``: each hourly JSON payload
carries a base ``timestamp``/``bid``/``ask`` plus delta-encoded ``times``,
``bids`` and ``asks`` arrays that are scaled by ``multiplier``. This module
adds a vectorised decoder and a bid/ask M5 aggregator so a ten-year, three-pair
search is affordable.

M5 buckets never straddle an hour boundary (300000 ms divides 3600000 ms), so
each hourly file aggregates independently and months simply concatenate.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

M5_MS = 300_000

# pip_size / price_scale match dukascopy-ticks-v1 INSTRUMENTS. point_size is the
# MT5 "point" (one unit of the last quoted digit) used for stop/target maths.
INSTRUMENTS: dict[str, dict[str, object]] = {
    "EURUSD": {
        "source_code": "EUR-USD",
        "pip_size": 0.0001,
        "point_size": 0.00001,
        "price_scale": 5,
        "quote_ccy": "USD",
        "contract_size": 100_000.0,
    },
    "GBPUSD": {
        "source_code": "GBP-USD",
        "pip_size": 0.0001,
        "point_size": 0.00001,
        "price_scale": 5,
        "quote_ccy": "USD",
        "contract_size": 100_000.0,
    },
    "USDJPY": {
        "source_code": "USD-JPY",
        "pip_size": 0.01,
        "point_size": 0.001,
        "price_scale": 3,
        "quote_ccy": "JPY",
        "contract_size": 100_000.0,
    },
    # Synthetic crosses built by build_crosses.py from the majors above.
    #
    # quote_ccy is declared "USD" deliberately. Converting their real quote
    # currency (GBP / JPY) to USD needs the *GBPUSD* or *USDJPY* rate, not the
    # cross's own price, so dividing by the cross price would be wrong. A constant
    # point value is used instead: profit factor, win rate and R-multiples — the
    # only metrics these are screened on — are invariant to a constant scaling of
    # point value. Absolute USD amounts for crosses therefore carry a fixed factor
    # (~1/1.27 for EURGBP, ~150/price for the JPY crosses) and are not reported.
    "EURGBP": {
        "source_code": "EUR-GBP",
        "pip_size": 0.0001,
        "point_size": 0.00001,
        "price_scale": 5,
        "quote_ccy": "USD",
        "contract_size": 100_000.0,
        "synthetic": True,
    },
    "EURJPY": {
        "source_code": "EUR-JPY",
        "pip_size": 0.01,
        "point_size": 0.001,
        "price_scale": 3,
        "quote_ccy": "USD",
        "contract_size": 100_000.0,
        "synthetic": True,
    },
    "GBPJPY": {
        "source_code": "GBP-JPY",
        "pip_size": 0.01,
        "point_size": 0.001,
        "price_scale": 3,
        "quote_ccy": "USD",
        "contract_size": 100_000.0,
        "synthetic": True,
    },
    # Index CFD. Selected over BTCUSD by the measured range/cost screen:
    # US500 74.0x vs BTCUSD 16.0x (Capital.com charges a $500 BTC spread).
    # contract_size 1 means one lot is one unit of the index, so a 1.0-point
    # index move is $1 per lot and a 0.1 "point" is $0.10.
    "US500": {
        "source_code": "USA500.IDX-USD",
        "pip_size": 1.0,
        "point_size": 0.1,
        "price_scale": 1,
        "quote_ccy": "USD",
        "contract_size": 1.0,
    },
}

MAJORS = ("EURUSD", "GBPUSD", "USDJPY")
SYNTHETIC_CROSSES = ("EURGBP", "EURJPY", "GBPJPY")
INDICES = ("US500",)

BAR_COLUMNS = (
    "timestamp_ms",
    "bid_open",
    "bid_high",
    "bid_low",
    "bid_close",
    "ask_open",
    "ask_high",
    "ask_low",
    "ask_close",
    "tick_count",
)


class FxDataError(RuntimeError):
    pass


@dataclass(frozen=True)
class DecodedHour:
    timestamp_ms: np.ndarray
    bid: np.ndarray
    ask: np.ndarray

    def __len__(self) -> int:
        return int(self.timestamp_ms.size)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decode_hour(raw: bytes, price_scale: int) -> DecodedHour:
    """Vectorised equivalent of the reference per-tick decoder."""
    payload = json.loads(raw)
    times = payload["times"]
    if not times:
        empty_i = np.empty(0, dtype=np.int64)
        empty_f = np.empty(0, dtype=np.float64)
        return DecodedHour(empty_i, empty_f, empty_f)

    base_ts = int(payload["timestamp"])
    multiplier = float(payload["multiplier"])
    if multiplier <= 0:
        raise FxDataError("multiplier must be positive")
    base_bid = float(payload["bid"])
    base_ask = float(payload["ask"])

    ts = base_ts + np.cumsum(np.asarray(times, dtype=np.int64))
    bid = base_bid + np.cumsum(np.asarray(payload["bids"], dtype=np.float64)) * multiplier
    ask = base_ask + np.cumsum(np.asarray(payload["asks"], dtype=np.float64)) * multiplier

    if ts.size != bid.size or ts.size != ask.size:
        raise FxDataError("delta arrays have inconsistent lengths")
    if np.any(np.diff(ts) < 0):
        raise FxDataError("timestamps are not monotonic")

    bid = np.round(bid, price_scale)
    ask = np.round(ask, price_scale)
    return DecodedHour(ts, bid, ask)


def _ohlc(values: np.ndarray, starts: np.ndarray, ends: np.ndarray) -> tuple[np.ndarray, ...]:
    return (
        values[starts],
        np.maximum.reduceat(values, starts),
        np.minimum.reduceat(values, starts),
        values[ends],
    )


def aggregate_m5(hour: DecodedHour) -> dict[str, np.ndarray] | None:
    """Aggregate one decoded hour into M5 bid/ask OHLC bars."""
    if len(hour) == 0:
        return None
    slots = hour.timestamp_ms - (hour.timestamp_ms % M5_MS)
    starts = np.flatnonzero(np.r_[True, slots[1:] != slots[:-1]])
    ends = np.r_[starts[1:] - 1, slots.size - 1]

    bid_o, bid_h, bid_l, bid_c = _ohlc(hour.bid, starts, ends)
    ask_o, ask_h, ask_l, ask_c = _ohlc(hour.ask, starts, ends)
    return {
        "timestamp_ms": slots[starts].astype(np.int64),
        "bid_open": bid_o,
        "bid_high": bid_h,
        "bid_low": bid_l,
        "bid_close": bid_c,
        "ask_open": ask_o,
        "ask_high": ask_h,
        "ask_low": ask_l,
        "ask_close": ask_c,
        "tick_count": (ends - starts + 1).astype(np.int32),
    }


def raw_month_dir(storage_root: Path, symbol: str, year: int, month: int) -> Path:
    return storage_root / "raw" / symbol / f"year={year:04d}" / f"month={month:02d}"


def build_month_m5(storage_root: Path, symbol: str, year: int, month: int) -> pd.DataFrame:
    """Decode one symbol-month of hourly tick files into M5 bid/ask bars."""
    if symbol not in INSTRUMENTS:
        raise FxDataError(f"unknown symbol: {symbol}")
    price_scale = int(INSTRUMENTS[symbol]["price_scale"])
    directory = raw_month_dir(storage_root, symbol, year, month)
    if not directory.is_dir():
        raise FxDataError(f"missing raw month directory: {directory}")

    chunks: list[dict[str, np.ndarray]] = []
    hour_files = 0
    for path in sorted(directory.glob("*.json")):
        if path.name.startswith("_"):
            continue
        hour_files += 1
        bars = aggregate_m5(decode_hour(path.read_bytes(), price_scale))
        if bars is not None:
            chunks.append(bars)

    if not chunks:
        frame = pd.DataFrame({name: np.empty(0, dtype=np.float64) for name in BAR_COLUMNS})
        frame["timestamp_ms"] = frame["timestamp_ms"].astype(np.int64)
        frame["tick_count"] = frame["tick_count"].astype(np.int32)
    else:
        frame = pd.DataFrame(
            {name: np.concatenate([chunk[name] for chunk in chunks]) for name in BAR_COLUMNS}
        )
    frame.attrs["hour_files"] = hour_files
    return frame.sort_values("timestamp_ms", kind="stable", ignore_index=True)


def cache_path(cache_root: Path, symbol: str) -> Path:
    return cache_root / "bars" / f"{symbol}_M5_BIDASK.parquet"


def load_m5(cache_root: Path, symbol: str) -> pd.DataFrame:
    path = cache_path(cache_root, symbol)
    if not path.is_file():
        raise FxDataError(f"missing M5 cache for {symbol}: {path} (run build_bars.py)")
    return pd.read_parquet(path)


def add_time_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Attach UTC calendar columns used by session logic and reporting."""
    out = frame.copy()
    stamps = pd.to_datetime(out["timestamp_ms"], unit="ms", utc=True)
    out["timestamp_utc"] = stamps
    out["year"] = stamps.dt.year.astype(np.int16)
    out["hour"] = stamps.dt.hour.astype(np.int8)
    out["minute"] = stamps.dt.minute.astype(np.int8)
    out["weekday"] = stamps.dt.weekday.astype(np.int8)
    out["date"] = stamps.dt.strftime("%Y-%m-%d")
    return out


def resample_from_m5(m5: pd.DataFrame, minutes: int) -> pd.DataFrame:
    """Derive a higher timeframe from M5 bars.

    Higher Dukascopy timeframes are known to be holey in this archive, so every
    decision timeframe is derived from the clean M5 series instead.
    """
    if minutes % 5 != 0:
        raise FxDataError("timeframe must be a multiple of 5 minutes")
    width = minutes * 60_000
    slots = (m5["timestamp_ms"].to_numpy() // width) * width
    grouped = m5.groupby(slots, sort=True)
    out = pd.DataFrame(
        {
            "timestamp_ms": grouped["timestamp_ms"].min().index.to_numpy().astype(np.int64),
            "bid_open": grouped["bid_open"].first().to_numpy(),
            "bid_high": grouped["bid_high"].max().to_numpy(),
            "bid_low": grouped["bid_low"].min().to_numpy(),
            "bid_close": grouped["bid_close"].last().to_numpy(),
            "ask_open": grouped["ask_open"].first().to_numpy(),
            "ask_high": grouped["ask_high"].max().to_numpy(),
            "ask_low": grouped["ask_low"].min().to_numpy(),
            "ask_close": grouped["ask_close"].last().to_numpy(),
            "tick_count": grouped["tick_count"].sum().to_numpy().astype(np.int64),
            "m5_bars": grouped.size().to_numpy().astype(np.int16),
        }
    )
    return out.reset_index(drop=True)


def mid(frame: pd.DataFrame, field: str) -> np.ndarray:
    return (frame[f"bid_{field}"].to_numpy() + frame[f"ask_{field}"].to_numpy()) / 2.0


def iso(timestamp_ms: int) -> str:
    return (
        datetime.fromtimestamp(timestamp_ms / 1000, UTC)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )
