import numpy as np
import pandas as pd

from specialist import generate_candidates


def test_candidate_uses_only_macro_state_available_at_signal() -> None:
    timestamps = pd.date_range("2024-01-01", periods=60, freq="4h", tz="UTC")
    close = pd.Series(np.linspace(2000.0, 2060.0, len(timestamps)))
    h4 = pd.DataFrame(
        {
            "timestamp_utc": timestamps,
            "mid_open": close - 0.5,
            "mid_high": close + 1.0,
            "mid_low": close - 1.0,
            "mid_close": close,
        }
    )
    macro = pd.DataFrame(
        {
            "available_at": [timestamps[0], timestamps[-1] + pd.Timedelta(hours=1)],
            "macro_bull_votes": [4, 0],
            "macro_bear_votes": [0, 4],
            "macro_composite_score": [4, -4],
            "real_yield_change_20d": [-0.2, 0.2],
            "dollar_change_20d": [-1.1, 1.1],
            "breakeven_5y_change_20d": [0.2, -0.2],
            "dgs2_change_20d": [-0.2, 0.2],
            "treasury_10y2y_change_20d": [0.04, -0.04],
            "baa10y_change_20d": [0.2, -0.2],
            "vix_change_20d": [4.0, -4.0],
            "gvz_change_20d": [4.0, -4.0],
            "nfci_change_4obs": [0.2, -0.2],
        }
    )
    settings = {
        "atr_period": 14,
        "ema_period": 40,
        "return_bars": 6,
        "composite_threshold": 3,
        "stop_atr": 1.2,
        "target_r": 1.65,
        "maximum_hold_hours": 36,
        "one_candidate_per_day_and_direction": True,
    }

    candidates = generate_candidates(h4, macro, settings)

    assert not candidates.empty
    assert candidates["direction"].eq("LONG").all()
    assert (candidates["available_at"] <= candidates["signal_time"]).all()
    assert not candidates["signal_time"].dt.date.duplicated().any()
