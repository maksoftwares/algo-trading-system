from __future__ import annotations

import numpy as np
import pandas as pd

from regime import apply_hysteresis, attach_regime, classify_chop


SETTINGS = {
    "atr_period_h4": 14, "adx_period_h4": 14, "lookback_h4": 24,
    "adx_max": 25.0, "er_max": 0.38, "displacement_atr_max": 1.75,
    "range_width_atr_min": 1.0, "range_width_atr_max": 8.0,
    "entry_consecutive": 2, "exit_consecutive": 2,
    "exit_adx": 30.0, "exit_er": 0.55, "exit_displacement_atr": 2.5,
}


def h4_frame(count: int = 900) -> pd.DataFrame:
    times = pd.date_range("2020-01-01 04:00", periods=count, freq="4h", tz="UTC")
    close = 1500 + np.sin(np.arange(count) / 2.0) * 5
    return pd.DataFrame({
        "timestamp_utc": times, "bar_start_utc": times - pd.Timedelta(hours=4), "bar_end_utc": times,
        "mid_open": close, "mid_high": close + 2, "mid_low": close - 2, "mid_close": close,
    })


def test_future_h4_mutation_does_not_change_earlier_labels() -> None:
    original = h4_frame()
    first = classify_chop(original, SETTINGS).bars
    mutated = original.copy()
    mutated.loc[700:, ["mid_open", "mid_high", "mid_low", "mid_close"]] *= 2
    second = classify_chop(mutated, SETTINGS).bars
    pd.testing.assert_series_equal(first.loc[:699, "chop_active"], second.loc[:699, "chop_active"])


def test_hysteresis_exact_entry_exit_and_hard_exit() -> None:
    core = pd.Series([False, True, True, True, False, True, False, False, True, True])
    hard = pd.Series([False, False, False, False, False, True, False, False, False, False])
    active, ids = apply_hysteresis(core, hard, 2, 2)
    assert active.tolist() == [False, False, True, True, True, False, False, False, False, True]
    assert ids.tolist() == [0, 0, 1, 1, 1, 0, 0, 0, 0, 2]


def test_h4_label_activates_only_after_h4_close() -> None:
    h4 = pd.DataFrame({
        "timestamp_utc": pd.to_datetime(["2020-01-01 04:00Z"]), "chop_active": [True], "chop_episode_id": [1],
        "adx14_h4": [20.0], "er24": [0.2], "displacement_atr24": [1.0], "range_width_atr24": [3.0],
        "volatility_subtype": ["MEDIUM_VOL_CHOP"], "range_width_subtype": ["MEDIUM_WIDTH_CHOP"], "drift_subtype": ["FLAT_CHOP"],
    })
    times = pd.to_datetime(["2020-01-01 03:55Z", "2020-01-01 04:00Z", "2020-01-01 04:05Z"])
    bars = pd.DataFrame({"timestamp_utc": times, "bar_start_utc": times - pd.Timedelta(minutes=5)})
    attached = attach_regime(bars, h4)
    assert attached["chop_active"].tolist() == [False, True, True]
    assert attached["chop_active_at_open"].tolist() == [False, False, True]


def test_diagnostic_subtypes_never_change_active_flag() -> None:
    result = classify_chop(h4_frame(), SETTINGS).bars
    assert result["chop_active"].dtype == bool
    assert result.loc[result["chop_active"], "volatility_subtype"].notna().all()
