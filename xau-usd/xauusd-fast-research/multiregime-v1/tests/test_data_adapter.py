from __future__ import annotations

import pandas as pd

from data_adapter import _month_boundaries


def test_mt5_m5_tail_is_requested_in_month_sized_chunks() -> None:
    start = pd.Timestamp("2025-07-01", tz="UTC"); end = pd.Timestamp("2026-07-01", tz="UTC")
    chunks = _month_boundaries(start, end)
    assert len(chunks) == 12
    assert chunks[0] == (start, pd.Timestamp("2025-08-01", tz="UTC"))
    assert chunks[-1][1] == end
