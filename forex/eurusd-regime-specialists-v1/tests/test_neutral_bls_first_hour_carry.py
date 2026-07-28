from __future__ import annotations

import pandas as pd

from eurusd_regime_specialists.neutral_bls_first_hour_carry import (
    attach_latest_release,
)


def _config() -> dict:
    return {
        "strategy": {
            "families": ["CPI", "PPI", "NFP"],
            "minimum_predecessor_calendar_days": 20,
            "maximum_predecessor_calendar_days": 45,
            "minimum_release_age_hours_exclusive": 0,
            "maximum_release_age_hours": 72,
            "entry_minutes_utc": [0, 15, 30, 45],
        },
        "windows": {
            "development_2019_2022": [
                "2019-01-01T00:00:00Z",
                "2022-12-31T23:59:59Z",
            ],
            "chronological_2023": [
                "2023-01-01T00:00:00Z",
                "2023-12-31T23:59:59Z",
            ],
            "chronological_2024": [
                "2024-01-01T00:00:00Z",
                "2024-12-31T23:59:59Z",
            ],
            "chronological_2025": [
                "2025-01-01T00:00:00Z",
                "2025-12-31T23:59:59Z",
            ],
            "recent_2026_h1": [
                "2026-01-01T00:00:00Z",
                "2026-06-30T23:59:59Z",
            ],
        },
        "outcome_blind_census": {
            "minimum_candidates_total": 1,
            "minimum_candidates_development": 1,
            "minimum_candidates_each_full_forward_year": 0,
            "minimum_candidates_recent_half_year": 0,
            "minimum_candidates_each_side": 0,
            "minimum_families_represented": 1,
        },
    }


def test_latest_release_is_carried_to_first_hour_clocks() -> None:
    releases = pd.DataFrame(
        {
            "family": ["CPI", "CPI"],
            "event_time_utc": pd.to_datetime(
                [
                    "2022-11-10T13:30:00Z",
                    "2022-12-13T13:30:00Z",
                ],
                utc=True,
            ),
            "initial_value": [0.4, 0.2],
            "source_pdf_sha256": ["a", "b"],
        }
    )
    entries = pd.to_datetime(
        [
            "2022-12-14T00:00:00Z",
            "2022-12-14T00:15:00Z",
            "2022-12-14T00:30:00Z",
            "2022-12-14T00:45:00Z",
        ],
        utc=True,
    )
    points = pd.DataFrame(
        {
            "entry_time_utc": entries,
            "eligible_date": ["2022-12-14"] * 4,
            "clock_minute": [0, 15, 30, 45],
            "decision_id": [f"d{i}" for i in range(4)],
        }
    )
    candidates, census = attach_latest_release(
        points, releases, _config()
    )
    assert len(candidates) == 4
    assert candidates["side"].eq("LONG").all()
    assert candidates["macro_family"].eq("CPI").all()
    assert census["by_clock_minute"] == {
        "0": 1,
        "15": 1,
        "30": 1,
        "45": 1,
    }


def test_release_older_than_72_hours_is_cash() -> None:
    releases = pd.DataFrame(
        {
            "family": ["NFP", "NFP"],
            "event_time_utc": pd.to_datetime(
                [
                    "2022-10-07T12:30:00Z",
                    "2022-11-04T12:30:00Z",
                ],
                utc=True,
            ),
            "initial_value": [300_000, 200_000],
            "source_pdf_sha256": ["a", "b"],
        }
    )
    points = pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                ["2022-11-08T00:00:00Z"], utc=True
            ),
            "eligible_date": ["2022-11-08"],
            "clock_minute": [0],
            "decision_id": ["old"],
        }
    )
    candidates, census = attach_latest_release(
        points, releases, _config()
    )
    assert candidates.empty
    assert census["cash_no_release_within_72h"] == 1
