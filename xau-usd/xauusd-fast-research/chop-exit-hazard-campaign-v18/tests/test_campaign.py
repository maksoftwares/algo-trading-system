from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from campaign import (  # noqa: E402
    add_h4_state_features,
    parameter_space,
    signal_mask_direction,
    simulate_trade,
)


def _h4_frame() -> pd.DataFrame:
    timestamps = pd.date_range("2024-01-01T04:00:00Z", periods=6, freq="4h")
    return pd.DataFrame(
        {
            "timestamp_utc": timestamps,
            "regime": ["TREND_UP", "CHOP", "CHOP", "CHOP", "TREND_DOWN", "CHOP"],
            "mid_close": [100.0, 101.0, 102.0, 103.0, 99.0, 101.0],
            "ema_h4": [100.0] * 6,
            "atr_h4": [2.0] * 6,
            "adx_h4": [20.0, 16.0, 17.0, 19.0, 24.0, 18.0],
            "er_h4": [0.3, 0.15, 0.2, 0.25, 0.35, 0.2],
            "ema_slope_atr_h4": [0.1, 0.02, 0.05, 0.09, -0.2, 0.04],
            "range_width_atr_h4": [4.0, 3.0, 3.2, 3.5, 5.0, 3.1],
            "displacement_atr_h4": [1.0, 0.5, 0.7, 0.9, 1.4, 0.6],
            "atr_ratio_h4": [1.0, 0.8, 0.85, 0.9, 1.1, 0.85],
        }
    )


def _signal_frame() -> pd.DataFrame:
    starts = pd.date_range("2024-01-01T09:00:00Z", periods=6, freq="5min")
    return pd.DataFrame(
        {
            "bar_start_utc": starts,
            "bar_end_utc": starts + pd.Timedelta(minutes=5),
            "timestamp_utc": starts + pd.Timedelta(minutes=5),
            "regime": ["TREND_UP", "CHOP", "CHOP", "CHOP", "TREND_DOWN", "CHOP"],
            "hour_utc_custom": 9,
            "risk_atr": 2.0,
            "spread_ratio": 1.0,
            "h4_state_age_m5": [0, 0, 1, 2, 0, 0],
            "chop_episode_age_h4": [0, 1, 2, 3, 0, 1],
            "h4_price_ema_atr": [0.2] * 6,
            "adx_h4": [19.0] * 6,
            "adx_h4_delta": [1.0] * 6,
            "er_h4": [0.25] * 6,
            "er_h4_delta": [0.03] * 6,
            "ema_slope_atr_h4": [0.08] * 6,
            "ema_slope_atr_h4_delta": [0.04] * 6,
            "range_width_atr_h4": [4.0] * 6,
            "range_width_atr_h4_delta": [0.2] * 6,
            "displacement_atr_h4": [1.0] * 6,
            "atr_ratio_h4": [0.9] * 6,
            "atr_ratio_h4_delta": [0.05] * 6,
            "tick_imbalance_15m": [0.1] * 6,
            "quote_intensity_ratio": [1.2] * 6,
            "variance_ratio": [1.2] * 6,
            "return_3": [0.2] * 6,
            "return_12": [0.3] * 6,
        }
    )


def _pressure_params() -> dict[str, object]:
    return {
        "adx_min": 18.0,
        "adx_delta_min": 0.6,
        "er_min": 0.22,
        "er_delta_min": 0.01,
        "slope_alignment_min": 0.04,
        "m5_window": 3,
        "m5_move_h1_atr_min": 0.03,
        "imbalance_min": 0.01,
        "h4_state_age_m5_max": 3,
        "chop_episode_age_h4_min": 1,
        "session": "ALL",
        "geometry_id": "FAST",
    }


def test_h4_chop_age_resets_and_deltas_are_backward_looking() -> None:
    frame = add_h4_state_features(_h4_frame())
    assert frame["chop_episode_age_h4"].tolist() == [0, 1, 2, 3, 0, 1]
    assert frame.loc[2, "adx_h4_delta"] == 1.0
    assert np.isclose(frame.loc[2, "er_h4_delta"], 0.05)


def test_deterministic_design_has_400_unique_rows() -> None:
    rows = parameter_space("CHOP_ADX_ER_EXIT_PRESSURE", 400)
    assert len(rows) == 400
    assert len({repr(sorted(row.items())) for row in rows}) == 400


def test_exit_pressure_signal_is_restricted_to_chop() -> None:
    mask, direction = signal_mask_direction(
        _signal_frame(), "CHOP_ADX_ER_EXIT_PRESSURE", _pressure_params()
    )
    assert mask.tolist() == [False, True, True, True, False, True]
    assert direction.loc[mask].eq(1).all()


def test_future_state_does_not_change_prior_signals() -> None:
    frame = _signal_frame()
    before, _ = signal_mask_direction(
        frame, "CHOP_ADX_ER_EXIT_PRESSURE", _pressure_params()
    )
    changed = frame.copy()
    changed.loc[4:, "adx_h4"] = 0.0
    changed.loc[4:, "tick_imbalance_15m"] = -1.0
    after, _ = signal_mask_direction(
        changed, "CHOP_ADX_ER_EXIT_PRESSURE", _pressure_params()
    )
    assert before.loc[:3].equals(after.loc[:3])


def _arrays() -> dict[str, np.ndarray]:
    starts = pd.date_range("2024-01-02T10:00:00Z", periods=15, freq="5min")
    naive = starts.tz_localize(None).to_numpy()
    bid_high = np.full(15, 100.2)
    bid_low = np.full(15, 99.8)
    bid_high[1] = 102.0
    bid_low[1] = 98.8
    return {
        "starts": naive,
        "ends": naive + np.timedelta64(5, "m"),
        "atr": np.ones(15),
        "bid_open": np.full(15, 100.0),
        "bid_high": bid_high,
        "bid_low": bid_low,
        "bid_close": np.full(15, 100.0),
        "ask_open": np.full(15, 100.1),
        "ask_high": bid_high + 0.1,
        "ask_low": bid_low + 0.1,
        "ask_close": np.full(15, 100.1),
    }


def _execution() -> dict[str, float]:
    return {
        "maximum_entry_spread_r": 0.15,
        "maximum_research_risk_usd": 50.0,
        "ounces_at_lot_size": 1.0,
        "extra_execution_cost_usd": 0.3,
        "holding_cost_per_24h_usd": 0.35,
        "stress_slippage_r": 0.05,
    }


def test_m5_same_bar_collision_is_stop_first() -> None:
    geometry = {"stop_atr": 1.0, "target_r": 1.5, "hold_bars": 12}
    result = simulate_trade(
        _arrays(),
        0,
        1,
        geometry,
        _execution(),
        pd.Timestamp("2024-01-03T00:00:00Z"),
    )
    assert result is not None
    assert result["exit_reason"] == "AMBIGUOUS_M5_STOP_FIRST"
    assert result["gross_r"] == -1.0


def test_noncontiguous_next_m5_bar_rejects_entry() -> None:
    arrays = _arrays()
    arrays["starts"] = arrays["starts"].copy()
    arrays["starts"][1] += np.timedelta64(5, "m")
    result = simulate_trade(
        arrays,
        0,
        1,
        {"stop_atr": 1.0, "target_r": 1.5, "hold_bars": 12},
        _execution(),
        pd.Timestamp("2024-01-03T00:00:00Z"),
    )
    assert result is None
