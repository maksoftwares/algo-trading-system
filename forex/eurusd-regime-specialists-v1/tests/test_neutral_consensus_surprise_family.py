from __future__ import annotations

import pandas as pd

from eurusd_regime_specialists.neutral_consensus_surprise_family import (
    AGREEMENT_VARIANT,
    CARRY_VARIANT,
    add_price_confirmation,
    attach_latest_surprise,
    build_directional_surprises,
)


def _config() -> dict:
    return {
        "strategy": {
            "families": ["CPI", "PPI", "NFP"],
            "variants": [CARRY_VARIANT, AGREEMENT_VARIANT],
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


def _consensus() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "family": ["CPI", "PPI", "NFP"],
            "event_time_utc": pd.to_datetime(
                [
                    "2022-12-12T13:30:00Z",
                    "2022-12-13T13:30:00Z",
                    "2022-12-13T14:00:00Z",
                ],
                utc=True,
            ),
            "official_initial_value": [0.5, -0.2, 200_000.0],
            "forecast_value": [0.3, -0.1, 200_000.0],
            "official_pdf_sha256": ["a", "b", "c"],
            "tradingview_event_id": ["1", "2", "3"],
            "tradingview_ticker": ["CPI", "PPI", "NFP"],
            "retrieval_semantics": ["post"] * 3,
        }
    )


def _prices() -> pd.DataFrame:
    index = pd.date_range(
        "2022-12-13T23:30:00Z",
        "2022-12-14T00:15:00Z",
        freq="5min",
    )
    return pd.DataFrame(
        {
            "bid_close": [
                1.0000,
                1.0001,
                1.0002,
                1.0003,
                1.0004,
                1.0005,
                1.0006,
                1.0007,
                1.0008,
                1.0009,
            ]
        },
        index=index,
    )


def test_surprise_side_mapping_and_zero_cash() -> None:
    selected, census = build_directional_surprises(
        _consensus(), _config()
    )
    assert selected["family"].tolist() == ["CPI", "PPI"]
    assert selected["side"].tolist() == ["SHORT", "LONG"]
    assert census["zero_surprise"] == 1


def test_price_confirmation_never_reads_entry_bar() -> None:
    points = pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                ["2022-12-14T00:00:00Z"], utc=True
            )
        }
    )
    prices = _prices()
    first = add_price_confirmation(points, prices)
    altered = prices.copy()
    altered.loc[
        pd.Timestamp("2022-12-14T00:00:00Z"), "bid_close"
    ] = -999.0
    second = add_price_confirmation(points, altered)
    assert first["prior_15m_return"].iloc[0] == (
        second["prior_15m_return"].iloc[0]
    )
    assert first["price_side"].iloc[0] == "LONG"
    assert second["price_side"].iloc[0] == "LONG"


def test_variants_are_censused_independently() -> None:
    points = pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                ["2022-12-14T00:00:00Z"], utc=True
            ),
            "eligible_date": ["2022-12-14"],
            "clock_minute": [0],
            "decision_id": ["d0"],
        }
    )
    consensus = _consensus().iloc[[0]].copy()
    candidates, census = attach_latest_surprise(
        points, consensus, _prices(), _config()
    )
    assert candidates["variant"].tolist() == [CARRY_VARIANT]
    assert census["variants"][CARRY_VARIANT]["passed"] is True
    assert census["variants"][AGREEMENT_VARIANT]["passed"] is False


def test_release_at_exact_entry_is_not_available() -> None:
    points = pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                ["2022-12-14T00:00:00Z"], utc=True
            ),
            "eligible_date": ["2022-12-14"],
            "clock_minute": [0],
            "decision_id": ["d0"],
        }
    )
    consensus = _consensus().iloc[[0]].copy()
    consensus["event_time_utc"] = points["entry_time_utc"].iloc[0]
    candidates, census = attach_latest_surprise(
        points, consensus, _prices(), _config()
    )
    assert candidates.empty
    assert census["cash_no_release_within_72h"] == 1
