from __future__ import annotations

import pandas as pd

from phase0.levels import (
    add_latest_confirmed_swings,
    add_previous_completed_daily_levels,
    add_previous_completed_weekly_levels,
    confirmed_swing_highs,
    confirmed_swing_lows,
    drop_duplicate_levels,
)


def test_confirmed_swing_high_available_only_after_right_bars_close():
    bars = _swing_bars()

    swings = confirmed_swing_highs(bars, left=4, right=4)
    enriched = add_latest_confirmed_swings(bars, left=4, right=4)

    assert len(swings) == 1
    assert swings.loc[0, "level_price"] == 10
    assert swings.loc[0, "swing_time_utc"] == pd.Timestamp("2016-01-04T10:25:00Z")
    assert swings.loc[0, "available_time_utc"] == pd.Timestamp("2016-01-04T10:45:00Z")
    assert pd.isna(enriched.loc[7, "latest_swing_high"])
    assert enriched.loc[8, "latest_swing_high"] == 10


def test_confirmed_swing_low_available_only_after_right_bars_close():
    bars = _swing_bars()

    swings = confirmed_swing_lows(bars, left=4, right=4)

    assert len(swings) == 1
    assert swings.loc[0, "level_price"] == -10
    assert swings.loc[0, "available_time_utc"] == pd.Timestamp("2016-01-04T11:10:00Z")


def test_previous_daily_levels_do_not_include_current_day():
    bars = pd.DataFrame(
        {
            "timestamp_utc": [
                "2016-01-04T10:00:00Z",
                "2016-01-04T11:00:00Z",
                "2016-01-05T10:00:00Z",
                "2016-01-05T11:00:00Z",
            ],
            "high": [100.0, 105.0, 200.0, 210.0],
            "low": [90.0, 92.0, 180.0, 185.0],
        }
    )

    enriched = add_previous_completed_daily_levels(bars)

    assert pd.isna(enriched.loc[0, "previous_daily_high"])
    assert enriched.loc[2, "previous_daily_high"] == 105.0
    assert enriched.loc[3, "previous_daily_high"] == 105.0
    assert enriched.loc[2, "previous_daily_low"] == 90.0


def test_previous_weekly_levels_do_not_include_current_week():
    bars = pd.DataFrame(
        {
            "timestamp_utc": [
                "2016-01-04T10:00:00Z",
                "2016-01-08T11:00:00Z",
                "2016-01-11T10:00:00Z",
            ],
            "high": [100.0, 120.0, 999.0],
            "low": [80.0, 90.0, 1.0],
        }
    )

    enriched = add_previous_completed_weekly_levels(bars)

    assert pd.isna(enriched.loc[0, "previous_weekly_high"])
    assert enriched.loc[2, "previous_weekly_high"] == 120.0
    assert enriched.loc[2, "previous_weekly_low"] == 80.0


def test_drop_duplicate_levels_keeps_most_recent_within_tolerance():
    levels = pd.DataFrame(
        {
            "level_price": [100.00, 100.08, 101.00],
            "level_time_utc": [
                "2016-01-04T10:00:00Z",
                "2016-01-04T11:00:00Z",
                "2016-01-04T09:00:00Z",
            ],
        }
    )

    deduped = drop_duplicate_levels(levels, point_size=0.01, tolerance_points=10)

    assert deduped["level_price"].tolist() == [101.00, 100.08]


def _swing_bars() -> pd.DataFrame:
    timestamps = pd.date_range("2016-01-04T10:05:00Z", periods=18, freq="5min")
    highs = [1, 2, 3, 4, 10, 5, 4, 3, 2, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    lows = [0, -1, -2, -3, -4, -5, -6, -7, -8, -10, -8, -7, -6, -5, -4, -3, -2, -1]
    return pd.DataFrame({"timestamp_utc": timestamps, "high": highs, "low": lows})
