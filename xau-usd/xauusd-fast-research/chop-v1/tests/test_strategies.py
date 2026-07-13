from __future__ import annotations

import numpy as np
import pandas as pd

from strategies import clock_bars, rolling_exact_mad, rotation_signals


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
    assert 'center.loc[idx] + 1.25 * std.loc[idx]' in source
    assert 'center.loc[idx] - 1.25 * std.loc[idx]' in source


def test_strategy_parameters_vary_only_by_clock_conversion() -> None:
    for minutes in (5, 15, 30, 60):
        cb = clock_bars(minutes)
        assert cb.day * minutes == 1440
        assert cb.atr * minutes == 840
        assert cb.cooldown * minutes == 360
