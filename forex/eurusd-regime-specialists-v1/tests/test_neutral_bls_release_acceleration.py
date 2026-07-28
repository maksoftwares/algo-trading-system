from __future__ import annotations

import pandas as pd
import pytest

from eurusd_regime_specialists.neutral_bls_release_acceleration import (
    build_release_signals,
)


def _config() -> dict:
    return {
        "strategy": {
            "families": ["CPI", "PPI", "NFP"],
            "minimum_predecessor_calendar_days": 20,
            "maximum_predecessor_calendar_days": 45,
        }
    }


def test_release_acceleration_maps_to_inverse_eurusd_side() -> None:
    releases = pd.DataFrame(
        {
            "family": ["CPI", "CPI", "CPI"],
            "event_time_utc": pd.to_datetime(
                [
                    "2026-01-10T13:30:00Z",
                    "2026-02-10T13:30:00Z",
                    "2026-03-10T13:30:00Z",
                ],
                utc=True,
            ),
            "initial_value": [0.2, 0.4, 0.1],
        }
    )
    signals, census = build_release_signals(releases, _config())
    assert signals["side"].tolist() == ["SHORT", "LONG"]
    assert signals["acceleration"].tolist() == pytest.approx([0.2, -0.3])
    assert census["directional_release_signals"] == 2


def test_equal_or_stale_predecessor_is_cash() -> None:
    releases = pd.DataFrame(
        {
            "family": ["PPI", "PPI", "PPI"],
            "event_time_utc": pd.to_datetime(
                [
                    "2026-01-01T13:30:00Z",
                    "2026-02-01T13:30:00Z",
                    "2026-04-15T13:30:00Z",
                ],
                utc=True,
            ),
            "initial_value": [0.2, 0.2, 0.5],
        }
    )
    signals, census = build_release_signals(releases, _config())
    assert signals.empty
    assert census["zero_acceleration"] == 1
    assert census["missing_or_out_of_interval_predecessor"] == 2
