from __future__ import annotations

import numpy as np
import pandas as pd

from diagnostics import _boundary_return_probabilities, _decision, _episode_safe_mean_reversion


def test_boundary_return_is_counted_before_one_atr_extension() -> None:
    frame = pd.DataFrame({
        "timestamp_utc": pd.date_range("2020-01-01 01:00", periods=5, freq="1h", tz="UTC"),
        "chop_active": [True] * 5,
        "chop_episode_id": [1] * 5,
        "mid_close": [100.0, 101.2, 100.8, 100.1, 100.0],
        "mid_high": [100.1, 101.3, 101.0, 100.3, 100.2],
        "mid_low": [99.9, 101.0, 100.5, 99.9, 99.8],
    })
    equilibrium = pd.Series([100.0] * 5)
    zscore = pd.Series([0.0, 1.2, 0.8, 0.1, 0.0])
    atr14 = pd.Series([1.0] * 5)

    result = _boundary_return_probabilities(frame, equilibrium, zscore, atr14, 60)

    assert result["boundary_events_1sd"] == 1
    assert result["equilibrium_return_before_1atr_extension_1sd_pct"] == 100.0
    assert result["boundary_events_1p5sd"] == 0
    assert result["equilibrium_return_before_1atr_extension_1p5sd_pct"] is None


def test_episode_safe_statistics_ignore_cross_episode_price_jump() -> None:
    times = pd.date_range("2020-01-01 01:00", periods=60, freq="1h", tz="UTC")
    episode = [1] * 30 + [2] * 30
    base = [100.0 + (0.5 if i % 2 else -0.5) for i in range(60)]
    frame = pd.DataFrame({"timestamp_utc": times, "mid_close": base, "chop_active": True, "chop_episode_id": episode})
    equilibrium = pd.Series([100.0] * 60)
    first = _episode_safe_mean_reversion(frame, equilibrium, 60)
    shifted = frame.copy()
    shifted.loc[30:, "mid_close"] *= 10.0
    shifted_equilibrium = equilibrium.copy(); shifted_equilibrium.loc[30:] *= 10.0
    second = _episode_safe_mean_reversion(shifted, shifted_equilibrium, 60)
    assert (np.isnan(first[0]) and np.isnan(second[0])) or first[0] == second[0]
    assert first[1] == second[1]


def test_advancement_gate_does_not_round_later_profit_factor() -> None:
    base = {
        "baseline_net_r": 20.0, "baseline_expectancy": 0.10, "baseline_profit_factor": 1.25,
        "accepted_trades": 120, "unique_setup_episodes": 80, "chop_episodes_traded": 70,
        "later_profit_factor": 1.099, "stress_net_r": 5.0, "stress_profit_factor": 1.10,
        "max_closed_drawdown_r": 10.0, "top_ten_winner_share": 0.30,
    }
    segments = {name: {"net_r": value} for name, value in (("A", 10.0), ("B", 5.0), ("C", 5.0))}
    yearly = pd.DataFrame({"net_r": [5.0, 5.0, 5.0, 5.0]})
    assert _decision(base, segments, [], yearly) == "BORDERLINE_DO_NOT_ENGINEER"
    base["later_profit_factor"] = 1.10
    assert _decision(base, segments, [], yearly) == "PROMISING_CONFIRMATION_REQUIRED"
