from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from campaign import (  # noqa: E402
    add_chop_episode_age,
    signal_mask_direction,
    simulate_trade,
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
            "atr14": 1.0,
            "tick_imbalance_5m": [0.1] * 6,
            "tick_imbalance_15m": [0.1] * 6,
            "tick_book_imbalance_mean": [0.1] * 6,
            "quote_intensity_ratio": [1.2] * 6,
            "price_efficiency_5m": [0.5] * 6,
            "spread_ratio": [1.0] * 6,
            "prior_spread_ratio": [1.2] * 6,
            "variance_ratio": [1.0] * 6,
            "body_move": [0.2] * 6,
            "return_1": [0.2] * 6,
            "return_3": [0.3] * 6,
            "return_6": [0.4] * 6,
            "return_12": [0.5] * 6,
            "close_location_custom": [0.8] * 6,
        }
    )


def _flow_params() -> dict[str, object]:
    return {
        "imbalance_window": "5m",
        "imbalance_min": 0.015,
        "book_min": 0.0,
        "intensity_min": 0.3,
        "efficiency_min": 0.0,
        "spread_ratio_max": 1.15,
        "require_body_alignment": False,
        "require_trend_alignment": False,
        "session": "ALL",
        "chop_age_min": 1,
        "chop_age_max": 48,
    }


def test_chop_age_resets_on_regime_change() -> None:
    frame = add_chop_episode_age(_signal_frame())
    assert frame["chop_age_m5"].tolist() == [0, 1, 2, 3, 0, 1]


def test_flow_signal_is_restricted_to_chop_and_reversed() -> None:
    frame = add_chop_episode_age(_signal_frame())
    mask, direction = signal_mask_direction(
        frame, "CHOP_FLOW_CONTINUATION_REVERSE", _flow_params()
    )
    assert mask.tolist() == [False, True, True, True, False, True]
    assert direction.loc[mask].eq(-1).all()


def test_future_microstructure_does_not_change_prior_signals() -> None:
    frame = add_chop_episode_age(_signal_frame())
    before, _ = signal_mask_direction(
        frame, "CHOP_FLOW_CONTINUATION_REVERSE", _flow_params()
    )
    changed = frame.copy()
    changed.loc[4:, "tick_imbalance_5m"] = -1.0
    after, _ = signal_mask_direction(
        changed, "CHOP_FLOW_CONTINUATION_REVERSE", _flow_params()
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
