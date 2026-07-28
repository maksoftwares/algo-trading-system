from __future__ import annotations

import pandas as pd

from eurusd_regime_specialists.neutral_event_crossasset_rates import (
    _completed_market_bar,
    _state_join,
)


def test_completed_market_bar_requires_both_exact_quotes() -> None:
    timestamp = pd.Timestamp("2026-01-02T13:25:00Z")
    frame = pd.DataFrame(
        {
            "dollaridxusd_available": [True],
            "ustbondtrusd_available": [False],
            "dollaridxusd_mid_close": [100.0],
            "ustbondtrusd_mid_close": [120.0],
        },
        index=pd.DatetimeIndex([timestamp]),
    )
    assert _completed_market_bar(frame, timestamp) is None
    frame.loc[timestamp, "ustbondtrusd_available"] = True
    assert _completed_market_bar(frame, timestamp) is not None
    assert (
        _completed_market_bar(
            frame, timestamp + pd.Timedelta(minutes=5)
        )
        is None
    )


def test_state_join_never_uses_future_state() -> None:
    candidates = pd.DataFrame(
        {
            "state_time_utc": [
                pd.Timestamp("2026-01-02T12:00:00Z")
            ],
            "entry_time_utc": [
                pd.Timestamp("2026-01-02T13:45:00Z")
            ],
        }
    )
    index = pd.DatetimeIndex(
        [
            pd.Timestamp("2026-01-02T11:00:00Z"),
            pd.Timestamp("2026-01-02T13:00:00Z"),
        ],
        name="timestamp_utc",
    )
    state = pd.DataFrame(
        {
            "direction": ["NEUTRAL", "USD_UP"],
            "phase": ["TRANSITION", "ESTABLISHED"],
            "shock": [False, False],
            "DXY_compressed": [False, False],
            "EURUSD_compressed": [False, False],
        },
        index=index,
    )
    joined = _state_join(candidates, state)
    assert joined.loc[0, "matched_state_time_utc"] == index[0]
    assert joined.loc[0, "direction"] == "NEUTRAL"
