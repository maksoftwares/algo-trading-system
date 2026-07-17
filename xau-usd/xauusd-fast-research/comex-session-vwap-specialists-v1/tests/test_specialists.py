import numpy as np
import pandas as pd

from specialists import prepare_frame


def test_join_requires_exact_completed_timestamp() -> None:
    times = pd.date_range("2024-01-02T13:00:00Z", periods=60, freq="5min")
    close = pd.Series(np.linspace(2000.0, 2010.0, len(times)))
    spot = pd.DataFrame(
        {
            "bar_start_utc": times - pd.Timedelta(minutes=5),
            "timestamp_utc": times,
            "mid_open": close - 0.1,
            "mid_high": close + 0.2,
            "mid_low": close - 0.2,
            "mid_close": close,
        }
    )
    comex = pd.DataFrame(
        {
            "available_time_utc": times[::2],
            "session_date": "2024-01-02",
            "session_vwap": np.linspace(1999.0, 2009.0, len(times[::2])),
            "vwap_deviation": 1.0,
            "volume": 100,
        }
    )
    geometry = {
        "spot_atr_period": 14,
        "spot_fast_ema_period": 20,
        "spot_slow_ema_period": 50,
        "comex_vwap_slope_bars": 6,
        "comex_volume_median_bars": 20,
        "ny_session_start": "08:30",
        "ny_session_end": "13:30",
    }

    frame = prepare_frame(spot, comex, geometry)

    assert len(frame) == len(comex)
    assert frame["timestamp_utc"].equals(frame["available_time_utc"])
