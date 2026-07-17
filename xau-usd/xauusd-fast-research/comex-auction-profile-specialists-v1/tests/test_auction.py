from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from auction import contiguous_value_area, generate_candidates  # noqa: E402


def test_value_area_is_contiguous_and_volume_centered() -> None:
    prices = pd.Series([99.9, 100.0, 100.0, 100.1, 100.2, 100.3])
    sizes = pd.Series([1, 10, 10, 8, 2, 1])

    poc, low, high = contiguous_value_area(prices, sizes, price_bin=0.1, fraction=0.70)

    assert poc == 100.0
    assert low == 100.0
    assert high == 100.1


def test_acceptance_candidate_requires_completed_three_bar_hold() -> None:
    config = json.loads(
        (ROOT / "config" / "comex_auction_profile_specialists_v1.json").read_text(
            encoding="utf-8"
        )
    )
    periods = 24
    times = pd.date_range("2024-01-02T13:20:00Z", periods=periods, freq="5min")
    spot = pd.DataFrame(
        {
            "timestamp_utc": times,
            "bar_start_utc": times - pd.Timedelta(minutes=5),
            "mid_open": [2000.0] * periods,
            "mid_high": [2002.0] * periods,
            "mid_low": [1998.0] * periods,
            "mid_close": [2000.0] * periods,
            "bid_open": [1999.9] * periods,
            "bid_high": [2001.9] * periods,
            "bid_low": [1997.9] * periods,
            "bid_close": [1999.9] * periods,
            "ask_open": [2000.1] * periods,
            "ask_high": [2002.1] * periods,
            "ask_low": [1998.1] * periods,
            "ask_close": [2000.1] * periods,
        }
    )
    futures = pd.DataFrame(
        {
            "available_time_utc": times,
            "bucket": times - pd.Timedelta(minutes=5),
            "session_date": ["2024-01-02"] * periods,
            "available_local_time": times.tz_convert("America/New_York").strftime("%H:%M"),
            "open": [2000.0] * periods,
            "high": [2001.0] * periods,
            "low": [1999.0] * periods,
            "close": [2000.0] * (periods - 3) + [2001.5, 2001.6, 2001.7],
            "running_poc": [2000.0] * periods,
            "prior_session_poc": [2000.0] * periods,
            "prior_session_value_low": [1999.0] * periods,
            "prior_session_value_high": [2001.0] * periods,
            "cumulative_delta_ratio": [0.2] * periods,
            "cumulative_volume_ratio": [1.0] * periods,
        }
    )

    candidates = generate_candidates(spot, futures, config)

    accepted = candidates.loc[
        candidates["family_id"].eq("COMEX_PRIOR_VALUE_ACCEPTANCE_CONTINUATION_V1")
    ]
    assert len(accepted) == 1
    assert accepted.iloc[0]["signal_time"] == times[-1]
    assert accepted.iloc[0]["direction"] == "LONG"
