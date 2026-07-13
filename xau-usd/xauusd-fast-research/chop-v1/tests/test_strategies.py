from __future__ import annotations

import numpy as np
import pandas as pd

from strategies import _rotation_memory, clock_bars, equilibrium_signals, impulse_signals, rolling_exact_mad, rotation_signals


def _signal_frame(closes: list[float]) -> pd.DataFrame:
    count = len(closes)
    frame = pd.DataFrame({
        "timestamp_utc": pd.date_range("2020-01-01 00:30", periods=count, freq="30min", tz="UTC"),
        "mid_close": closes,
        "chop_active": [True] * count,
    })
    frame["mid_open"] = frame["mid_close"].shift(1).fillna(frame["mid_close"])
    frame["mid_high"] = frame[["mid_open", "mid_close"]].max(axis=1) + 0.2
    frame["mid_low"] = frame[["mid_open", "mid_close"]].min(axis=1) - 0.2
    frame["bid_close"] = frame["mid_close"] - 0.05
    frame["ask_close"] = frame["mid_close"] + 0.05
    return frame


def test_frozen_clock_hour_conversions() -> None:
    expected = {5: (288, 36, 24, 72, 144, 108, 72), 15: (96, 12, 8, 24, 48, 36, 24), 30: (48, 6, 4, 12, 24, 18, 12), 60: (24, 3, 2, 6, 12, 9, 6)}
    for minutes, values in expected.items():
        cb = clock_bars(minutes)
        assert (cb.day, cb.impulse, cb.confirmation, cb.memory, cb.hold_standard, cb.hold_impulse, cb.cooldown) == values


def test_exact_rolling_mad_uses_only_completed_prefix() -> None:
    values = pd.Series([1.0, 2.0, 100.0, 4.0, 5.0])
    first = rolling_exact_mad(values, 3)
    mutated = values.copy(); mutated.iloc[4] = 9999
    second = rolling_exact_mad(mutated, 3)
    assert first.iloc[3] == second.iloc[3]
    assert first.iloc[2] == np.median(np.abs(np.array([1.0, 2.0, 100.0]) - 2.0))


def test_long_short_rotation_rules_are_exact_mirrors_in_source() -> None:
    import inspect
    source = inspect.getsource(rotation_signals)
    assert 'two_hour_return > 0' in source and 'two_hour_return < 0' in source
    assert 'mid_close"] > work["mid_open' in source and 'mid_close"] < work["mid_open' in source
    assert 'center.loc[idx] + target_band_z * std.loc[idx]' in source
    assert 'center.loc[idx] - target_band_z * std.loc[idx]' in source


def test_rotation_excursion_threshold_controls_memory_numerically() -> None:
    z = pd.Series([0.0, -1.6, -1.4, 0.0])
    active = pd.Series([True] * 4)
    permissive, _ = _rotation_memory(z, active, 3, "LONG", 1.5)
    strict, _ = _rotation_memory(z, active, 3, "LONG", 1.7)
    assert permissive.iloc[2]
    assert not strict.iloc[2]


def test_equilibrium_signal_fixture_is_numerically_triggered() -> None:
    closes = [100.0 + (1.0 if i % 2 else -1.0) for i in range(55)]
    closes[-2:] = [96.0, 98.0]
    frame = _signal_frame(closes)
    frame.loc[frame.index[-1], "mid_open"] = 97.0
    frame.loc[frame.index[-1], "mid_low"] = 96.8
    frame.loc[frame.index[-1], "mid_high"] = 98.2
    result = equilibrium_signals(frame, clock_bars(30), {"z": 2.0, "stop_atr": 1.25, "max_hold_hours": 12})
    assert result["signal_accepted_pre_execution"].any()
    assert (result["max_hold_hours"] == 12.0).all()


def test_impulse_signal_fixture_is_numerically_triggered() -> None:
    closes = [100.0 + 0.2 * np.sin(i) for i in range(54)] + [100.0, 98.0, 96.0, 94.0, 92.0, 92.5]
    frame = _signal_frame(closes)
    frame.loc[frame.index[-1], "mid_open"] = 91.5
    frame.loc[frame.index[-1], "mid_low"] = 91.3
    frame.loc[frame.index[-1], "mid_high"] = 92.7
    settings = {"z": 2.25, "stop_buffer_atr": 0.25, "min_stop_atr": 0.5, "max_stop_atr": 2.0, "max_hold_hours": 9}
    result = impulse_signals(frame, clock_bars(30), settings)
    assert result["signal_accepted_pre_execution"].any()
    assert (result["min_stop_atr"] == 0.5).all() and (result["max_stop_atr"] == 2.0).all()
    assert (result["max_hold_hours"] == 9.0).all()


def test_rotation_signal_fixture_is_numerically_triggered() -> None:
    closes = [100.0 + 0.5 * np.sin(i) for i in range(50)] + [96.0, 97.0, 98.0, 99.0, 99.5, 99.8, 100.6]
    frame = _signal_frame(closes)
    frame.loc[frame.index[-1], "mid_open"] = 99.8
    settings = {"excursion_z": 1.5, "target_band_z": 1.25, "stop_atr": 1.25, "max_hold_hours": 12}
    result = rotation_signals(frame, clock_bars(30), settings)
    assert result["signal_accepted_pre_execution"].any()
    assert (result["max_hold_hours"] == 12.0).all()


def test_strategy_parameters_vary_only_by_clock_conversion() -> None:
    for minutes in (5, 15, 30, 60):
        cb = clock_bars(minutes)
        assert cb.day * minutes == 1440
        assert cb.atr * minutes == 840
        assert cb.cooldown * minutes == 360
