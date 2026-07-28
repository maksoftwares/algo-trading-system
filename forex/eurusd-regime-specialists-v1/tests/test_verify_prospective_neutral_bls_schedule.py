from __future__ import annotations

from copy import deepcopy

import pandas as pd

from verify_prospective_neutral_bls_schedule import (
    compare_schedule,
    load_config,
    official_schedule,
    verify_official_evidence,
)


def _events() -> list[dict]:
    return [
        {
            "family": "NFP",
            "tradingview_event_id": "396495",
            "tradingview_ticker": "ECONOMICS:USNFP",
            "event_time_utc": pd.Timestamp("2026-08-07T12:30:00Z"),
        },
        {
            "family": "CPI",
            "tradingview_event_id": "398841",
            "tradingview_ticker": "ECONOMICS:USIRMM",
            "event_time_utc": pd.Timestamp("2026-08-12T12:30:00Z"),
        },
        {
            "family": "PPI",
            "tradingview_event_id": "399062",
            "tradingview_ticker": "ECONOMICS:USPPIMM",
            "event_time_utc": pd.Timestamp("2026-08-13T12:30:00Z"),
        },
    ]


def test_browser_observed_official_payload_hash_is_stable() -> None:
    config = load_config()
    assert verify_official_evidence(config) == (
        "03816009f06ff96b330486c3333e2b52"
        "fd3ce0949e72f0b1c0869d53df4eedee"
    )
    assert config["official_evidence"]["raw_html_archived"] is False
    assert config["official_evidence"]["scripted_http_status"] == 403


def test_eastern_release_rows_convert_to_exact_august_utc_times() -> None:
    rows = official_schedule(load_config())
    assert [(row["family"], row["official_event_time_utc"]) for row in rows] == [
        ("NFP", pd.Timestamp("2026-08-07T12:30:00Z")),
        ("CPI", pd.Timestamp("2026-08-12T12:30:00Z")),
        ("PPI", pd.Timestamp("2026-08-13T12:30:00Z")),
    ]


def test_exact_tradingview_watchlist_matches_official_bls_schedule() -> None:
    result = compare_schedule(_events(), load_config())
    assert result["matched"] is True
    assert result["mismatch_reasons"] == []
    assert len(result["rows"]) == 3
    assert all(row["matched"] for row in result["rows"])


def test_any_event_time_drift_blocks_the_schedule() -> None:
    events = _events()
    events[0]["event_time_utc"] += pd.Timedelta(minutes=5)
    result = compare_schedule(events, load_config())
    assert result["matched"] is False
    assert "NFP_UTC_TIMESTAMP_MISMATCH" in result["mismatch_reasons"]


def test_event_id_or_ticker_drift_blocks_the_schedule() -> None:
    events = _events()
    events[1]["tradingview_event_id"] = "revised"
    events[2]["tradingview_ticker"] = "ECONOMICS:WRONG"
    result = compare_schedule(events, load_config())
    assert result["matched"] is False
    assert "CPI_EVENT_ID_MISMATCH" in result["mismatch_reasons"]
    assert "PPI_TICKER_MISMATCH" in result["mismatch_reasons"]


def test_missing_extra_or_duplicate_family_fails_closed() -> None:
    events = _events()
    events.pop()
    events.append(
        {
            "family": "OTHER",
            "tradingview_event_id": "1",
            "tradingview_ticker": "ECONOMICS:OTHER",
            "event_time_utc": pd.Timestamp("2026-08-14T12:30:00Z"),
        }
    )
    events.append(deepcopy(events[0]))
    result = compare_schedule(events, load_config())
    assert result["matched"] is False
    assert "MISSING_TRADINGVIEW_FAMILY:PPI" in result["mismatch_reasons"]
    assert "EXTRA_TRADINGVIEW_FAMILY:OTHER" in result["mismatch_reasons"]
    assert "DUPLICATE_TRADINGVIEW_FAMILY:NFP" in result["mismatch_reasons"]


def test_offline_guardrail_has_no_frequency_or_broker_permission() -> None:
    config = load_config()
    assert config["network_requests_allowed"] is False
    assert config["broker_action_allowed"] is False
    assert config["verification_policy"][
        "official_schedule_mismatch_action"
    ] == "BLOCK_EVENT_NO_TRADE"
    assert config["verification_policy"][
        "offline_verifier_makes_network_requests"
    ] is False
