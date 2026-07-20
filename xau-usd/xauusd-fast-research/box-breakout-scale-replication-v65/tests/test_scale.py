from __future__ import annotations

import numpy as np
import pandas as pd

from src.scale import apply_policy, simulate_signal


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
    }


def test_long_same_bar_ambiguity_is_stop_first() -> None:
    outcome = simulate_signal(
        _arrays([98.0], [104.0]),
        pd.Timestamp("2025-01-01", tz="UTC"),
        "LONG",
        1.0,
        2.0,
        1.0,
        _execution(),
    )
    assert outcome is not None
    assert outcome["exit_reason"] == "AMBIGUOUS_STOP_FIRST"
    assert outcome["net_r"] == -1.0


def test_short_uses_ask_side_for_stop() -> None:
    outcome = simulate_signal(
        _arrays([99.5], [101.1]),
        pd.Timestamp("2025-01-01", tz="UTC"),
        "SHORT",
        1.0,
        2.0,
        1.0,
        _execution(),
    )
    assert outcome is not None
    assert outcome["exit_reason"] == "STOP"
    assert outcome["net_r"] == -1.0


def test_policy_enforces_one_open_position() -> None:
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
    accepted = apply_policy(trades, maximum_open=1, maximum_daily=2)
    assert len(accepted) == 1
