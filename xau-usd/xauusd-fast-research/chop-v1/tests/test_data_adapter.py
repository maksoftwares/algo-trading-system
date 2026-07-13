from __future__ import annotations

import pandas as pd

from data_adapter import PRICE_COLUMNS, SPREAD_COLUMNS, aggregate_m30


def test_m30_requires_six_unique_contiguous_m5_offsets() -> None:
    starts = list(pd.date_range("2020-01-01 00:00", periods=6, freq="5min", tz="UTC"))
    starts += [pd.Timestamp("2020-01-01 00:30", tz="UTC")] * 6
    frame = pd.DataFrame({"bar_start_utc": starts})
    frame["timestamp_utc"] = frame["bar_start_utc"] + pd.Timedelta(minutes=5)
    frame["bar_end_utc"] = frame["timestamp_utc"]
    for column in PRICE_COLUMNS:
        frame[column] = 100.0
    for column in SPREAD_COLUMNS:
        frame[column] = 1.0
    frame["tick_count"] = 1; frame["volume_sum"] = 1.0
    result = aggregate_m30(frame)
    assert len(result) == 1
    assert result.iloc[0]["timestamp_utc"] == pd.Timestamp("2020-01-01 00:30", tz="UTC")
    assert result.attrs["incomplete_m30_buckets_dropped"] == 1
