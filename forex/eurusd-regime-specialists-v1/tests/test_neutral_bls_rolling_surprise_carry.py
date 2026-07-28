from __future__ import annotations

import pandas as pd

from eurusd_regime_specialists.neutral_bls_rolling_surprise_carry import (
    attach_latest_release,
    build_release_surprises,
)


def _config() -> dict:
    return {
        "strategy": {
            "families": ["CPI", "PPI", "NFP"],
            "rolling_expectation_releases": 6,
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


def _releases(values: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "family": ["CPI"] * len(values),
            "event_time_utc": pd.date_range(
                "2022-01-01T13:30:00Z",
                periods=len(values),
                freq="30D",
            ),
            "initial_value": values,
            "source_pdf_sha256": [
                f"sha-{index}" for index in range(len(values))
            ],
        }
    )


def test_six_prior_releases_form_causal_median_surprise() -> None:
    releases = _releases([1, 2, 3, 4, 5, 6, 10, -10])
    signals, census = build_release_surprises(releases, _config())
    assert len(signals) == 2
    first = signals.iloc[0]
    assert first["rolling_median_initial_value"] == 3.5
    assert first["release_gap_from_rolling_median"] == 6.5
    assert first["side"] == "SHORT"
    assert census["directional_release_surprises"] == 2


def test_missing_month_breaks_consecutive_history() -> None:
    releases = _releases([1, 2, 3, 4, 5, 6, 10])
    releases.loc[3:, "event_time_utc"] += pd.Timedelta(days=31)
    signals, census = build_release_surprises(releases, _config())
    assert signals.empty
    assert census["incomplete_six_release_history"] == 7


def test_latest_surprise_is_carried_only_after_release() -> None:
    releases = _releases([1, 2, 3, 4, 5, 6, 10])
    release_time = releases.iloc[-1]["event_time_utc"]
    entries = pd.DatetimeIndex(
        [
            release_time,
            release_time + pd.Timedelta(minutes=15),
            release_time + pd.Timedelta(hours=73),
        ]
    )
    points = pd.DataFrame(
        {
            "entry_time_utc": entries,
            "eligible_date": [
                timestamp.strftime("%Y-%m-%d") for timestamp in entries
            ],
            "clock_minute": [30, 45, 30],
            "decision_id": ["exact", "after", "old"],
        }
    )
    candidates, census = attach_latest_release(
        points, releases, _config()
    )
    assert candidates["decision_id"].tolist() == ["after"]
    assert candidates.iloc[0]["side"] == "SHORT"
    assert census["cash_no_release_within_72h"] == 2
