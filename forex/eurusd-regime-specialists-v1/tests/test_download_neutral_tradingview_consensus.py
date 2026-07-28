from __future__ import annotations

import pandas as pd

from download_neutral_tradingview_consensus import (
    extract_calendar_candidates,
    reconcile_with_bls,
)


def _bls(value: float = 0.2) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "family": ["PPI"],
            "event_time_utc": pd.to_datetime(
                ["2026-01-14T13:30:00Z"], utc=True
            ),
            "metric": [
                "final_demand_ppi_monthly_percent_change"
            ],
            "unit": ["percent"],
            "initial_value": [value],
            "source_pdf_sha256": ["official-sha"],
        }
    )


def _payload() -> dict:
    return {
        "status": "ok",
        "result": [
            {
                "id": "wrong-period",
                "date": "2026-01-14T13:30:00.000Z",
                "country": "US",
                "currency": "USD",
                "title": "PPI MoM",
                "ticker": "ECONOMICS:USPPIMM",
                "actualRaw": 0.1,
                "forecastRaw": None,
                "previousRaw": 0.6,
            },
            {
                "id": "right-period",
                "date": "2026-01-14T13:30:00.000Z",
                "country": "US",
                "currency": "USD",
                "title": "PPI MoM",
                "ticker": "ECONOMICS:USPPIMM",
                "actualRaw": 0.2,
                "forecastRaw": 0.2,
                "previousRaw": 0.1,
            },
        ],
    }


def test_duplicate_timestamp_uses_only_official_initial_match() -> None:
    candidates = extract_calendar_candidates([_payload()])
    result, audit = reconcile_with_bls(candidates, _bls())
    assert len(result) == 1
    assert result.iloc[0]["tradingview_event_id"] == "right-period"
    assert result.iloc[0]["forecast_value"] == 0.2
    assert not audit["ambiguous_exact_matches"]
    assert not audit["actual_mismatches"]


def test_mismatched_actual_is_never_used() -> None:
    candidates = extract_calendar_candidates([_payload()])
    result, audit = reconcile_with_bls(candidates, _bls(0.3))
    assert result.empty
    assert len(audit["actual_mismatches"]) == 1


def test_only_frozen_tickers_enter_source() -> None:
    payload = _payload()
    payload["result"].append(
        {
            "id": "core",
            "date": "2026-01-14T13:30:00.000Z",
            "country": "US",
            "currency": "USD",
            "title": "Core PPI MoM",
            "ticker": "ECONOMICS:USCPPMM",
            "actualRaw": 0.0,
            "forecastRaw": 0.2,
        }
    )
    candidates = extract_calendar_candidates([payload])
    assert set(candidates["tradingview_event_id"]) == {
        "wrong-period",
        "right-period",
    }
