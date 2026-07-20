from __future__ import annotations

import numpy as np
import pandas as pd

from src.basis import (
    apply_policy,
    candidate_signals,
    rolling_median_mad,
    simulate_signal,
)


def _arrays(low: list[float], high: list[float]) -> dict[str, np.ndarray]:
    starts = pd.date_range("2025-01-01", periods=len(low), freq="5min", tz="UTC")
    ends = starts + pd.Timedelta(minutes=5)
    arrays: dict[str, np.ndarray] = {
        "starts": starts.tz_localize(None).to_numpy(dtype="datetime64[ns]"),
        "ends": ends.tz_localize(None).to_numpy(dtype="datetime64[ns]"),
    }
    for side, offset in (("bid", 0.0), ("ask", 0.1)):
        arrays[f"{side}_open"] = np.array([100.0 + offset] * len(low))
        arrays[f"{side}_high"] = np.array(high) + offset
        arrays[f"{side}_low"] = np.array(low) + offset
        arrays[f"{side}_close"] = np.array([100.0 + offset] * len(low))
    return arrays


def _execution() -> dict:
    return {
        "maximum_entry_gap_minutes": 10,
        "maximum_spread_price": 0.75,
        "maximum_spread_r": 0.15,
        "ticket_cost_usd": 0.0,
        "holding_cost_per_24h_usd": 0.0,
        "stress_slippage_r": 0.0,
        "maximum_hold_bars": 12,
    }


def test_rolling_basis_uses_only_prior_values() -> None:
    values = pd.Series([1.0, 1.0, 1.0, 100.0])
    center, mad = rolling_median_mad(values, lookback=3)
    assert np.isnan(center.iloc[2])
    assert center.iloc[3] == 1.0
    assert mad.iloc[3] == 0.0


def test_candidate_requires_same_session_widening() -> None:
    frame = pd.DataFrame(
        {
            "available_time_utc": pd.to_datetime(
                ["2024-01-01T12:25:00Z", "2024-01-02T12:25:00Z"]
            ),
            "session_date": ["2024-01-01", "2024-01-02"],
            "instrument_id": [1, 1],
            "basis": [0.0, 2.0],
            "basis_z": [0.0, 3.0],
            "gc_close": [100.0, 102.0],
            "mid_close": [100.0, 100.0],
            "atr": [1.0, 1.0],
        }
    )
    params = {
        "widening_bars": 1,
        "basis_z_threshold": 2.0,
        "minimum_return_gap_atr": 0.1,
        "action_mode": "CATCHUP",
        "stop_atr": 0.5,
        "target_r": 1.5,
    }
    assert candidate_signals(frame, params).empty


def test_long_same_bar_ambiguity_is_stop_first() -> None:
    outcome = simulate_signal(
        _arrays([98.0], [104.0]),
        pd.Timestamp("2025-01-01", tz="UTC"),
        "LONG",
        1.0,
        2.0,
        _execution(),
    )
    assert outcome is not None
    assert outcome["exit_reason"] == "AMBIGUOUS_STOP_FIRST"
    assert outcome["net_r"] == -1.0


def test_policy_enforces_cooldown_and_one_open_position() -> None:
    trades = pd.DataFrame(
        {
            "signal_time": pd.to_datetime(
                ["2025-01-01T00:00:00Z", "2025-01-01T00:05:00Z"]
            ),
            "entry_time": pd.to_datetime(
                ["2025-01-01T00:00:00Z", "2025-01-01T00:05:00Z"]
            ),
            "exit_time": pd.to_datetime(
                ["2025-01-01T01:00:00Z", "2025-01-01T00:30:00Z"]
            ),
        }
    )
    accepted = apply_policy(trades, maximum_open=1, maximum_daily=2, cooldown_bars=6)
    assert len(accepted) == 1
