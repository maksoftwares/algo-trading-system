from __future__ import annotations

import pandas as pd


def candle_components(
    data: pd.DataFrame,
    point_size: float,
    open_col: str = "open",
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
) -> pd.DataFrame:
    open_ = pd.to_numeric(data[open_col], errors="coerce")
    high = pd.to_numeric(data[high_col], errors="coerce")
    low = pd.to_numeric(data[low_col], errors="coerce")
    close = pd.to_numeric(data[close_col], errors="coerce")

    body = (close - open_).abs()
    candle_range = high - low
    body_for_ratio = body.where(body > 0, point_size)
    return pd.DataFrame(
        {
            "body": body,
            "upper_wick": high - pd.concat([open_, close], axis=1).max(axis=1),
            "lower_wick": pd.concat([open_, close], axis=1).min(axis=1) - low,
            "range": candle_range,
            "bullish": close > open_,
            "bearish": close < open_,
            "doji": (candle_range > 0) & (body <= 0.1 * candle_range),
            "body_for_ratio": body_for_ratio,
        },
        index=data.index,
    )


def bullish_engulfing(data: pd.DataFrame) -> pd.Series:
    components = candle_components(data, point_size=1e-12)
    open_ = pd.to_numeric(data["open"], errors="coerce")
    close = pd.to_numeric(data["close"], errors="coerce")
    previous_open = open_.shift(1)
    previous_close = close.shift(1)
    previous_body = components["body"].shift(1)
    return (
        components["bullish"]
        & components["bearish"].shift(1).fillna(False)
        & (close > previous_open)
        & (open_ < previous_close)
        & (components["body"] >= previous_body)
    ).fillna(False)


def bearish_engulfing(data: pd.DataFrame) -> pd.Series:
    components = candle_components(data, point_size=1e-12)
    open_ = pd.to_numeric(data["open"], errors="coerce")
    close = pd.to_numeric(data["close"], errors="coerce")
    previous_open = open_.shift(1)
    previous_close = close.shift(1)
    previous_body = components["body"].shift(1)
    return (
        components["bearish"]
        & components["bullish"].shift(1).fillna(False)
        & (close < previous_open)
        & (open_ > previous_close)
        & (components["body"] >= previous_body)
    ).fillna(False)


def bullish_pin_bar(data: pd.DataFrame, point_size: float) -> pd.Series:
    components = candle_components(data, point_size=point_size)
    open_ = pd.to_numeric(data["open"], errors="coerce")
    low = pd.to_numeric(data["low"], errors="coerce")
    close = pd.to_numeric(data["close"], errors="coerce")
    body_for_ratio = components["body_for_ratio"]
    return (
        (components["lower_wick"] >= 2.0 * body_for_ratio)
        & (components["upper_wick"] <= 1.0 * body_for_ratio)
        & ((close >= open_) | (close >= low + 0.60 * components["range"]))
    ).fillna(False)


def bearish_pin_bar(data: pd.DataFrame, point_size: float) -> pd.Series:
    components = candle_components(data, point_size=point_size)
    open_ = pd.to_numeric(data["open"], errors="coerce")
    high = pd.to_numeric(data["high"], errors="coerce")
    close = pd.to_numeric(data["close"], errors="coerce")
    body_for_ratio = components["body_for_ratio"]
    return (
        (components["upper_wick"] >= 2.0 * body_for_ratio)
        & (components["lower_wick"] <= 1.0 * body_for_ratio)
        & ((close <= open_) | (close <= high - 0.60 * components["range"]))
    ).fillna(False)
