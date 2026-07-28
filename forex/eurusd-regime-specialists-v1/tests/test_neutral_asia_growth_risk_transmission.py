from __future__ import annotations

import pandas as pd

from eurusd_regime_specialists.neutral_asia_growth_risk_transmission import (
    add_transmission_confirmation,
)


def _config() -> dict:
    return {
        "expert": "ASIA_HANDOFF_0300",
        "strategy": {
            "eurusd_confirmation_completed_m5_bars": 3,
        },
    }


def _candidate(side: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "family": ["PARENT"],
            "eligible_date": ["2023-01-03"],
            "expert": ["ASIA_HANDOFF_0300"],
            "side": [side],
            "entry_time_utc": [
                pd.Timestamp("2023-01-03T03:00:00Z")
            ],
        }
    )


def _m5() -> pd.DataFrame:
    index = pd.date_range(
        "2023-01-03T02:45:00Z", periods=4, freq="5min"
    )
    return pd.DataFrame(
        {
            "bid_open": [1.1000, 1.1001, 1.1002, 1.1003],
            "bid_close": [1.1001, 1.1002, 1.1003, 1.1004],
            "ask_open": [1.1001, 1.1002, 1.1003, 1.1004],
            "ask_close": [1.1002, 1.1003, 1.1004, 1.1005],
        },
        index=index,
    )


def test_long_requires_prior_completed_eurusd_alignment() -> None:
    candidates, reasons = add_transmission_confirmation(
        _candidate("LONG"), _m5(), _config()
    )
    assert len(candidates) == 1
    assert candidates["family"].iloc[0].startswith("N48_")
    assert reasons["opposite_or_zero_transmission"] == 0
    short, reasons = add_transmission_confirmation(
        _candidate("SHORT"), _m5(), _config()
    )
    assert short.empty
    assert reasons["opposite_or_zero_transmission"] == 1


def test_entry_bar_is_excluded_from_confirmation() -> None:
    first, _ = add_transmission_confirmation(
        _candidate("LONG"), _m5(), _config()
    )
    altered = _m5()
    entry = pd.Timestamp("2023-01-03T03:00:00Z")
    altered.loc[
        entry,
        ["bid_open", "bid_close", "ask_open", "ask_close"],
    ] = [9.0, 1.0, 9.1, 1.1]
    second, _ = add_transmission_confirmation(
        _candidate("LONG"), altered, _config()
    )
    assert len(first) == len(second) == 1
    assert first[
        "eurusd_confirmation_displacement_pips"
    ].iloc[0] == second[
        "eurusd_confirmation_displacement_pips"
    ].iloc[0]
