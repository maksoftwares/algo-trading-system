from __future__ import annotations

import pandas as pd

from phase0.config import ConfigError


def add_previous_completed_daily_levels(
    bars: pd.DataFrame,
    timestamp_col: str = "timestamp_utc",
    high_col: str = "high",
    low_col: str = "low",
) -> pd.DataFrame:
    result = bars.copy()
    timestamps = _utc_timestamps(result, timestamp_col)
    day = timestamps.dt.floor("D")
    daily = result.assign(_day=day).groupby("_day").agg(
        previous_daily_high_source=(high_col, "max"),
        previous_daily_low_source=(low_col, "min"),
    )
    result["previous_daily_high"] = day.map(daily["previous_daily_high_source"].shift(1))
    result["previous_daily_low"] = day.map(daily["previous_daily_low_source"].shift(1))
    return result


def add_previous_completed_weekly_levels(
    bars: pd.DataFrame,
    timestamp_col: str = "timestamp_utc",
    high_col: str = "high",
    low_col: str = "low",
) -> pd.DataFrame:
    result = bars.copy()
    timestamps = _utc_timestamps(result, timestamp_col)
    week_start = _week_start(timestamps)
    weekly = result.assign(_week_start=week_start).groupby("_week_start").agg(
        previous_weekly_high_source=(high_col, "max"),
        previous_weekly_low_source=(low_col, "min"),
    )
    result["previous_weekly_high"] = week_start.map(weekly["previous_weekly_high_source"].shift(1))
    result["previous_weekly_low"] = week_start.map(weekly["previous_weekly_low_source"].shift(1))
    return result


def confirmed_swing_highs(
    bars: pd.DataFrame,
    left: int = 4,
    right: int = 4,
    timestamp_col: str = "timestamp_utc",
    high_col: str = "high",
) -> pd.DataFrame:
    return _confirmed_swings(bars, "HIGH", left, right, timestamp_col, high_col)


def confirmed_swing_lows(
    bars: pd.DataFrame,
    left: int = 4,
    right: int = 4,
    timestamp_col: str = "timestamp_utc",
    low_col: str = "low",
) -> pd.DataFrame:
    return _confirmed_swings(bars, "LOW", left, right, timestamp_col, low_col)


def add_latest_confirmed_swings(
    bars: pd.DataFrame,
    left: int = 4,
    right: int = 4,
    timestamp_col: str = "timestamp_utc",
) -> pd.DataFrame:
    result = bars.copy()
    timestamps = _utc_timestamps(result, timestamp_col)
    result["_timestamp_for_merge"] = timestamps
    result["_original_order"] = range(len(result))

    high_swings = confirmed_swing_highs(result, left, right, timestamp_col)
    low_swings = confirmed_swing_lows(result, left, right, timestamp_col)
    result = _merge_latest_swing(result, high_swings, "high")
    result = _merge_latest_swing(result, low_swings, "low")
    return result.drop(columns=["_timestamp_for_merge", "_original_order"])


def drop_duplicate_levels(
    levels: pd.DataFrame,
    point_size: float,
    tolerance_points: float = 10.0,
    price_col: str = "level_price",
    time_col: str = "level_time_utc",
) -> pd.DataFrame:
    if levels.empty:
        return levels.copy()
    tolerance_price = tolerance_points * point_size
    ordered = levels.copy()
    ordered[time_col] = pd.to_datetime(ordered[time_col], utc=True, errors="coerce")
    ordered = ordered.sort_values(time_col, ascending=False)

    kept_indices: list[int] = []
    kept_prices: list[float] = []
    for index, row in ordered.iterrows():
        price = float(row[price_col])
        if all(abs(price - kept) > tolerance_price for kept in kept_prices):
            kept_indices.append(index)
            kept_prices.append(price)

    return levels.loc[kept_indices].sort_values(time_col).reset_index(drop=True)


def _confirmed_swings(
    bars: pd.DataFrame,
    kind: str,
    left: int,
    right: int,
    timestamp_col: str,
    price_col: str,
) -> pd.DataFrame:
    if left <= 0 or right <= 0:
        raise ConfigError("Swing left and right lookbacks must be positive.")

    timestamps = _utc_timestamps(bars, timestamp_col)
    prices = pd.to_numeric(bars[price_col], errors="coerce")
    mask = pd.Series(True, index=bars.index)
    for offset in range(1, left + 1):
        if kind == "HIGH":
            mask &= prices > prices.shift(offset)
        else:
            mask &= prices < prices.shift(offset)
    for offset in range(1, right + 1):
        if kind == "HIGH":
            mask &= prices > prices.shift(-offset)
        else:
            mask &= prices < prices.shift(-offset)

    rows: list[dict[str, object]] = []
    positions = {index: position for position, index in enumerate(bars.index)}
    for index in bars.index[mask.fillna(False)]:
        position = positions[index]
        available_position = position + right
        if available_position >= len(bars):
            continue
        rows.append(
            {
                "kind": kind,
                "level_price": prices.loc[index],
                "swing_time_utc": timestamps.iloc[position],
                "available_time_utc": timestamps.iloc[available_position],
                "source_index": index,
            }
        )

    return pd.DataFrame(
        rows,
        columns=("kind", "level_price", "swing_time_utc", "available_time_utc", "source_index"),
    )


def _merge_latest_swing(bars: pd.DataFrame, swings: pd.DataFrame, label: str) -> pd.DataFrame:
    price_col = f"latest_swing_{label}"
    time_col = f"latest_swing_{label}_time_utc"
    available_col = f"latest_swing_{label}_available_time_utc"
    if swings.empty:
        bars[price_col] = pd.NA
        bars[time_col] = pd.NaT
        bars[available_col] = pd.NaT
        return bars

    right = swings.sort_values("available_time_utc").rename(
        columns={
            "level_price": price_col,
            "swing_time_utc": time_col,
            "available_time_utc": available_col,
        }
    )
    merged = pd.merge_asof(
        bars.sort_values("_timestamp_for_merge"),
        right[[available_col, price_col, time_col]].sort_values(available_col),
        left_on="_timestamp_for_merge",
        right_on=available_col,
        direction="backward",
    )
    return merged.sort_values("_original_order").reset_index(drop=True)


def _utc_timestamps(df: pd.DataFrame, timestamp_col: str) -> pd.Series:
    timestamps = pd.to_datetime(df[timestamp_col], utc=True, errors="coerce")
    if timestamps.isna().any():
        raise ConfigError(f"{timestamp_col} contains invalid timestamps.")
    return timestamps


def _week_start(timestamps: pd.Series) -> pd.Series:
    normalized = timestamps.dt.floor("D")
    return normalized - pd.to_timedelta(timestamps.dt.weekday, unit="D")
