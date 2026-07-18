from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from campaign import (  # noqa: E402
    add_anchor_features,
    signal_mask_direction_target,
    simulate_anchor_outcome,
)


def _base_frame() -> pd.DataFrame:
    starts = pd.date_range("2024-01-01T00:00:00Z", periods=16, freq="30min")
    close = np.linspace(100.0, 101.5, len(starts))
    frame = pd.DataFrame(
        {
            "bar_start_utc": starts,
            "timestamp_utc": starts + pd.Timedelta(minutes=30),
            "tick_count": 10,
            "mid_open": close - 0.05,
            "mid_high": close + 0.2,
            "mid_low": close - 0.2,
            "mid_close": close,
            "atr14": 1.0,
            "upper_wick": 0.3,
            "lower_wick": 0.3,
            "candle_direction": 1,
            "regime": "CHOP",
        }
    )
    return frame


def test_previous_day_values_use_only_completed_day() -> None:
    frame = pd.concat(
        [
            _base_frame(),
            _base_frame().assign(
                bar_start_utc=lambda x: x["bar_start_utc"] + pd.Timedelta(days=1),
                timestamp_utc=lambda x: x["timestamp_utc"] + pd.Timedelta(days=1),
                mid_high=lambda x: x["mid_high"] + 20.0,
                mid_low=lambda x: x["mid_low"] + 20.0,
                mid_close=lambda x: x["mid_close"] + 20.0,
                mid_open=lambda x: x["mid_open"] + 20.0,
            ),
        ],
        ignore_index=True,
    )
    enriched = add_anchor_features(frame)
    second = enriched.loc[enriched["utc_day"].eq(pd.Timestamp("2024-01-02T00:00:00Z"))]
    assert second["previous_day_high"].nunique() == 1
    assert second["previous_day_high"].iat[0] == frame.iloc[:16]["mid_high"].max()


def test_asian_anchor_is_unavailable_before_six_utc() -> None:
    enriched = add_anchor_features(_base_frame())
    assert enriched.loc[enriched["hour"].lt(6), "asia_mid"].isna().all()
    assert enriched.loc[enriched["hour"].ge(6), "asia_mid"].notna().all()


def test_future_prices_do_not_change_prior_vwap_anchor() -> None:
    frame = _base_frame()
    before = add_anchor_features(frame)
    changed = frame.copy()
    changed.loc[changed.index[-2:], ["mid_open", "mid_high", "mid_low", "mid_close"]] += 100.0
    after = add_anchor_features(changed)
    assert np.allclose(before["day_vwap"].iloc[:-2], after["day_vwap"].iloc[:-2])


def test_week_open_partial_rotation_uses_frozen_fraction() -> None:
    frame = add_anchor_features(_base_frame())
    signal_index = 12
    anchor = frame.loc[signal_index, "week_open"]
    frame.loc[signal_index, "mid_close"] = anchor + 1.0
    frame.loc[signal_index, "candle_direction"] = -1
    params = {
        "deviation_atr_min": 0.4,
        "deviation_atr_max": 2.5,
        "target_fraction": 0.5,
        "confirmation": "CANDLE",
        "wick_min": 0.1,
        "minimum_week_bars": 8,
        "hour_window": "ALL_LIQUID",
        "geometry_id": "C_FAST",
    }
    mask, direction, target = signal_mask_direction_target(
        frame, "CHOP_WEEK_OPEN_PARTIAL_ROTATION", params
    )
    assert mask.iat[signal_index]
    assert direction.iat[signal_index] == -1
    assert target.iat[signal_index] == anchor + 0.5


def test_prior_week_midpoint_is_shifted_by_completed_week() -> None:
    first = _base_frame()
    second = _base_frame().assign(
        bar_start_utc=lambda x: x["bar_start_utc"] + pd.Timedelta(days=7),
        timestamp_utc=lambda x: x["timestamp_utc"] + pd.Timedelta(days=7),
        mid_high=lambda x: x["mid_high"] + 20.0,
        mid_low=lambda x: x["mid_low"] + 20.0,
        mid_close=lambda x: x["mid_close"] + 20.0,
        mid_open=lambda x: x["mid_open"] + 20.0,
    )
    enriched = add_anchor_features(pd.concat([first, second], ignore_index=True))
    second_week = enriched.loc[enriched["utc_week"].eq(pd.Timestamp("2024-01-08T00:00:00Z"))]
    expected = (first["mid_high"].max() + first["mid_low"].min()) / 2.0
    assert second_week["prior_week_mid"].nunique() == 1
    assert second_week["prior_week_mid"].iat[0] == expected


def _execution_frame() -> pd.DataFrame:
    starts = pd.date_range("2024-01-02T10:00:00Z", periods=4, freq="30min")
    frame = pd.DataFrame(
        {
            "bar_start_utc": starts,
            "timestamp_utc": starts + pd.Timedelta(minutes=30),
            "atr14": 1.0,
            "bid_open": [100.0, 100.0, 100.0, 100.0],
            "ask_open": [100.1, 100.1, 100.1, 100.1],
            "bid_high": [100.2, 101.0, 100.2, 100.2],
            "bid_low": [99.8, 99.0, 99.8, 99.8],
            "ask_high": [100.3, 101.1, 100.3, 100.3],
            "ask_low": [99.9, 99.1, 99.9, 99.9],
            "bid_close": [100.0, 100.0, 100.0, 100.0],
            "ask_close": [100.1, 100.1, 100.1, 100.1],
        }
    )
    return frame


def test_same_bar_stop_wins_over_anchor_target() -> None:
    frame = _execution_frame()
    geometry = {
        "stop_atr": 0.75,
        "maximum_hold_hours": 4.0,
        "minimum_target_r": 0.35,
        "maximum_target_r": 2.5,
    }
    execution = {
        "maximum_entry_gap_minutes": 40,
        "maximum_entry_spread_r": 0.2,
        "maximum_research_risk_usd": 50.0,
        "ounces_at_lot_size": 1.0,
        "ticket_cost_usd": 0.3,
        "holding_cost_per_24h_usd": 0.35,
        "stress_slippage_r": 0.05,
    }
    result = simulate_anchor_outcome(frame, 0, 1, 100.8, geometry, execution)
    assert result is not None
    assert result["exit_reason"] == "STOP"
    assert result["gross_r"] == -1.0
