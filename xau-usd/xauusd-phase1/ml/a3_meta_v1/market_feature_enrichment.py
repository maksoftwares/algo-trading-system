from __future__ import annotations

from pathlib import Path
from typing import Any


MARKET_NUMERIC_FEATURES = (
    "h1_return_3",
    "h1_return_12",
    "h1_range_atr",
    "h1_ema20_distance_atr",
    "h1_ema20_slope_atr",
    "h1_atr_ratio_60",
    "h4_return_3",
    "h4_return_12",
    "h4_range_atr",
    "h4_ema20_distance_atr",
    "h4_ema20_slope_atr",
    "h4_atr_ratio_60",
    "d1_return_5",
    "d1_return_20",
    "d1_range_atr",
    "d1_ema20_distance_atr",
    "d1_ema50_distance_atr",
    "d1_ema20_slope_atr",
    "d1_atr_ratio_60",
    "d1_volatility_20",
)


def enrich_rows_with_completed_market_features(
    root: Path, rows: list[dict[str, Any]], config: dict[str, Any]
) -> list[dict[str, Any]]:
    import pandas as pd

    entry_frame = pd.DataFrame(
        {"_row_index": range(len(rows)), "_entry_time": pd.to_datetime([row["entry_time"] for row in rows], utc=True)}
    ).sort_values("_entry_time")
    merged = entry_frame
    for timeframe in ("H1", "H4", "D1"):
        bars = _load_timeframe(root, config, timeframe, pd)
        features = _compute_features(bars, timeframe.lower(), pd)
        merged = pd.merge_asof(
            merged.sort_values("_entry_time"),
            features.sort_values("_bar_end"),
            left_on="_entry_time",
            right_on="_bar_end",
            direction="backward",
            allow_exact_matches=True,
        ).drop(columns=["_bar_end"])
    merged = merged.sort_values("_row_index")
    for feature in MARKET_NUMERIC_FEATURES:
        if feature not in merged or merged[feature].isna().any():
            missing = int(merged[feature].isna().sum()) if feature in merged else len(rows)
            raise ValueError(f"market feature {feature} has {missing} missing rows")
    for index, row in enumerate(rows):
        for feature in MARKET_NUMERIC_FEATURES:
            row[feature] = float(merged.iloc[index][feature])
    return rows


def _load_timeframe(root: Path, config: dict[str, Any], timeframe: str, pd: Any) -> Any:
    delta = {"H1": pd.Timedelta(hours=1), "H4": pd.Timedelta(hours=4), "D1": pd.Timedelta(days=1)}[timeframe]
    frames = []
    for source in config.get(timeframe, []):
        path = _resolve(root, source["path"])
        frame = pd.read_csv(path)
        style = source["style"]
        if style == "bar_end_timestamp":
            frame["_bar_end"] = pd.to_datetime(frame[source.get("time_column", "timestamp_utc")], utc=True)
        elif style == "bar_start_timestamp":
            frame["_bar_end"] = pd.to_datetime(frame[source.get("time_column", "time_utc")], utc=True) + delta
        else:
            raise ValueError(f"unsupported market-data timestamp style: {style}")
        frames.append(frame[["_bar_end", "open", "high", "low", "close"]].copy())
    if not frames:
        raise ValueError(f"no market data configured for {timeframe}")
    combined = pd.concat(frames, ignore_index=True)
    for column in ("open", "high", "low", "close"):
        combined[column] = pd.to_numeric(combined[column], errors="raise")
    return combined.sort_values("_bar_end").drop_duplicates("_bar_end", keep="last").reset_index(drop=True)


def _compute_features(frame: Any, prefix: str, pd: Any) -> Any:
    close = frame["close"]
    previous_close = close.shift(1)
    true_range = pd.concat(
        [frame["high"] - frame["low"], (frame["high"] - previous_close).abs(), (frame["low"] - previous_close).abs()],
        axis=1,
    ).max(axis=1)
    atr = true_range.ewm(alpha=1.0 / 14.0, adjust=False, min_periods=14).mean()
    ema20 = close.ewm(span=20, adjust=False, min_periods=20).mean()
    ema50 = close.ewm(span=50, adjust=False, min_periods=50).mean()
    output = frame[["_bar_end"]].copy()
    if prefix == "d1":
        output[f"{prefix}_return_5"] = close.pct_change(5)
        output[f"{prefix}_return_20"] = close.pct_change(20)
        output[f"{prefix}_ema50_distance_atr"] = (close - ema50) / atr
        output[f"{prefix}_volatility_20"] = close.pct_change().rolling(20, min_periods=20).std()
    else:
        output[f"{prefix}_return_3"] = close.pct_change(3)
        output[f"{prefix}_return_12"] = close.pct_change(12)
    output[f"{prefix}_range_atr"] = true_range / atr
    output[f"{prefix}_ema20_distance_atr"] = (close - ema20) / atr
    output[f"{prefix}_ema20_slope_atr"] = (ema20 - ema20.shift(5)) / atr
    output[f"{prefix}_atr_ratio_60"] = atr / atr.rolling(60, min_periods=60).median()
    return output


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()
