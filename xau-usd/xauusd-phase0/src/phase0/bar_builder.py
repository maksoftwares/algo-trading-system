from __future__ import annotations

from pathlib import Path

import pandas as pd

from phase0.config import ConfigError, ProjectConfig, resolve_symbol
from phase0.data_loader import latest_normalized_tick_file, processed_bars_dir, read_csv, write_csv
from phase0.data_validator import validate_bars

TIMEFRAME_FREQ = {
    "M1": "1min",
    "M5": "5min",
    "M15": "15min",
    "H1": "1h",
    "H4": "4h",
    "D1": "1D",
}


def build_bars_from_ticks(ticks: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    if timeframe not in TIMEFRAME_FREQ:
        raise ConfigError(f"Unsupported timeframe {timeframe!r}. Supported: {', '.join(TIMEFRAME_FREQ)}.")
    if ticks.empty:
        raise ConfigError("Cannot build bars from an empty tick DataFrame.")

    df = ticks.copy()
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True, errors="coerce")
    if df["timestamp_utc"].isna().any():
        raise ConfigError("Cannot build bars because one or more tick timestamps are invalid.")
    df = df.sort_values("timestamp_utc").set_index("timestamp_utc")

    freq = TIMEFRAME_FREQ[timeframe]
    grouped = df.resample(freq, label="left", closed="left")
    mid_ohlc = grouped["mid"].ohlc()
    bid_ohlc = grouped["bid"].ohlc()
    ask_ohlc = grouped["ask"].ohlc()
    spread_open = grouped["spread_points"].first()
    spread_close = grouped["spread_points"].last()
    spread_median = grouped["spread_points"].median()
    spread_p95 = grouped["spread_points"].quantile(0.95)
    tick_count = grouped["mid"].count()
    volume_sum = grouped["volume"].sum()

    bars = pd.DataFrame(
        {
            "bar_start_utc": mid_ohlc.index,
            "broker": grouped["broker"].first(),
            "symbol": grouped["symbol"].first(),
            "timeframe": timeframe,
            "open": mid_ohlc["open"],
            "high": mid_ohlc["high"],
            "low": mid_ohlc["low"],
            "close": mid_ohlc["close"],
            "mid_open": mid_ohlc["open"],
            "mid_high": mid_ohlc["high"],
            "mid_low": mid_ohlc["low"],
            "mid_close": mid_ohlc["close"],
            "bid_open": bid_ohlc["open"],
            "bid_high": bid_ohlc["high"],
            "bid_low": bid_ohlc["low"],
            "bid_close": bid_ohlc["close"],
            "ask_open": ask_ohlc["open"],
            "ask_high": ask_ohlc["high"],
            "ask_low": ask_ohlc["low"],
            "ask_close": ask_ohlc["close"],
            "spread_open_points": spread_open,
            "spread_close_points": spread_close,
            "spread_median_points": spread_median,
            "spread_p95_points": spread_p95,
            "tick_count": tick_count,
            "volume_sum": volume_sum,
        }
    )
    bars = bars[bars["tick_count"] > 0].reset_index(drop=True)
    offset = pd.tseries.frequencies.to_offset(freq)
    bars["bar_end_utc"] = bars["bar_start_utc"] + offset
    bars["timestamp_utc"] = bars["bar_end_utc"]
    columns = [
        "timestamp_utc",
        "bar_start_utc",
        "bar_end_utc",
        "broker",
        "symbol",
        "timeframe",
        "open",
        "high",
        "low",
        "close",
        "mid_open",
        "mid_high",
        "mid_low",
        "mid_close",
        "bid_open",
        "bid_high",
        "bid_low",
        "bid_close",
        "ask_open",
        "ask_high",
        "ask_low",
        "ask_close",
        "spread_open_points",
        "spread_close_points",
        "spread_median_points",
        "spread_p95_points",
        "tick_count",
        "volume_sum",
    ]
    return _format_datetime_columns(bars.loc[:, columns])


def build_bars_for_latest_ticks(
    config: ProjectConfig,
    broker: str,
    symbol: str,
    timeframes: list[str],
) -> list[Path]:
    canonical_symbol = resolve_symbol(config, symbol)
    tick_file = latest_normalized_tick_file(config, broker, canonical_symbol)
    ticks = read_csv(tick_file)
    written: list[Path] = []
    for timeframe in timeframes:
        bars = build_bars_from_ticks(ticks, timeframe)
        validate_bars(bars, name=f"{tick_file} {timeframe}")
        output_path = bars_output_path(config, broker, canonical_symbol, timeframe, bars)
        written.append(write_csv(bars, output_path))
    return written


def bars_output_path(
    config: ProjectConfig,
    broker: str,
    symbol: str,
    timeframe: str,
    bars: pd.DataFrame,
) -> Path:
    timestamps = pd.to_datetime(bars["timestamp_utc"], utc=True, errors="coerce")
    start = timestamps.min().strftime("%Y%m%d")
    end = timestamps.max().strftime("%Y%m%d")
    return (
        processed_bars_dir(config, broker, symbol, timeframe)
        / f"{symbol}_{broker}_{timeframe}_{start}_{end}.csv"
    )


def parse_timeframes(value: str) -> list[str]:
    timeframes = [item.strip().upper() for item in value.split(",") if item.strip()]
    unsupported = [timeframe for timeframe in timeframes if timeframe not in TIMEFRAME_FREQ]
    if unsupported:
        raise ConfigError(f"Unsupported timeframe(s): {', '.join(unsupported)}.")
    if not timeframes:
        raise ConfigError("At least one timeframe must be supplied.")
    return timeframes


def _format_datetime_columns(bars: pd.DataFrame) -> pd.DataFrame:
    formatted = bars.copy()
    for column in ("timestamp_utc", "bar_start_utc", "bar_end_utc"):
        formatted[column] = pd.to_datetime(formatted[column], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return formatted
