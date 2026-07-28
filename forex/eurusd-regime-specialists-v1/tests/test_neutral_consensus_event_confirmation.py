from __future__ import annotations

import pandas as pd

from eurusd_regime_specialists.neutral_consensus_event_confirmation import (
    build_candidates,
)


def _config() -> dict:
    return {
        "strategy": {
            "families": ["CPI", "PPI", "NFP"],
            "observation_bars": 3,
            "observation_minutes": 15,
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


def _points() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                ["2022-12-13T00:00:00Z"], utc=True
            ),
            "eligible_date": ["2022-12-13"],
            "clock_minute": [0],
            "decision_id": ["neutral"],
        }
    )


def _consensus(side: str = "SHORT") -> pd.DataFrame:
    if side == "SHORT":
        actual, forecast = 0.5, 0.3
    else:
        actual, forecast = 0.1, 0.3
    return pd.DataFrame(
        {
            "family": ["CPI"],
            "event_time_utc": pd.to_datetime(
                ["2022-12-13T13:30:00Z"], utc=True
            ),
            "official_initial_value": [actual],
            "forecast_value": [forecast],
            "official_pdf_sha256": ["a"],
            "tradingview_event_id": ["1"],
            "tradingview_ticker": ["CPI"],
            "retrieval_semantics": ["post"],
        }
    )


def _prices(down: bool = True) -> pd.DataFrame:
    index = pd.date_range(
        "2022-12-13T13:30:00Z",
        "2022-12-13T13:45:00Z",
        freq="5min",
    )
    mids = (
        [1.1000, 1.0995, 1.0990, 1.0985]
        if down
        else [1.1000, 1.1005, 1.1010, 1.1015]
    )
    return pd.DataFrame(
        {
            "bid_open": [value - 0.00005 for value in mids],
            "ask_open": [value + 0.00005 for value in mids],
            "bid_close": [value - 0.00010 for value in mids],
            "ask_close": [value for value in mids],
        },
        index=index,
    )


def test_macro_and_completed_price_agreement_selects_trade() -> None:
    candidates, census = build_candidates(
        _points(), _prices(down=True), _consensus("SHORT"), _config()
    )
    assert len(candidates) == 1
    assert candidates["side"].iloc[0] == "SHORT"
    assert candidates["entry_time_utc"].iloc[0] == pd.Timestamp(
        "2022-12-13T13:45:00Z"
    )
    assert census["passed"] is True


def test_disagreement_stays_in_cash() -> None:
    candidates, census = build_candidates(
        _points(), _prices(down=False), _consensus("SHORT"), _config()
    )
    assert candidates.empty
    assert census["cash_reasons"]["macro_price_disagreement"] == 1


def test_entry_bar_cannot_change_confirmation() -> None:
    prices = _prices(down=True)
    first, _ = build_candidates(
        _points(), prices, _consensus("SHORT"), _config()
    )
    altered = prices.copy()
    entry = pd.Timestamp("2022-12-13T13:45:00Z")
    altered.loc[entry, [
        "bid_open",
        "ask_open",
        "bid_close",
        "ask_close",
    ]] = [9.0, 9.1, 10.0, 10.1]
    second, _ = build_candidates(
        _points(), altered, _consensus("SHORT"), _config()
    )
    assert len(first) == len(second) == 1
    assert first["price_reaction_pips"].iloc[0] == (
        second["price_reaction_pips"].iloc[0]
    )


def test_non_neutral_date_is_cash() -> None:
    points = _points()
    points["eligible_date"] = "2022-12-12"
    candidates, census = build_candidates(
        points, _prices(down=True), _consensus("SHORT"), _config()
    )
    assert candidates.empty
    assert census["cash_reasons"]["release_not_on_neutral_date"] == 1
