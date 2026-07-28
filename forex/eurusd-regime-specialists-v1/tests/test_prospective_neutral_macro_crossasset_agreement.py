from __future__ import annotations

import pytest

from eurusd_regime_specialists.prospective_neutral_macro_crossasset_agreement import (
    decide_side,
)


def _inputs() -> dict:
    return {
        "family": "CPI",
        "is_neutral": True,
        "neutral_known_at_utc": "2026-08-12T00:00:00Z",
        "event_time_utc": "2026-08-12T12:30:00Z",
        "forecast_observed_at_utc": "2026-08-12T12:00:00Z",
        "actual_observed_at_utc": "2026-08-12T12:31:00Z",
        "observation_completed_at_utc": "2026-08-12T12:45:00Z",
        "entry_time_utc": "2026-08-12T12:45:00Z",
        "forecast_value": 0.2,
        "actual_value": 0.3,
        "eurusd_pre_mid": 1.1000,
        "eurusd_post_mid": 1.0990,
        "dxy_pre_mid": 100.0,
        "dxy_post_mid": 100.2,
        "treasury_pre_mid": 110.0,
        "treasury_post_mid": 109.8,
    }


def test_all_short_components_emit_short() -> None:
    signal = decide_side(**_inputs())
    assert signal["side"] == "SHORT"
    assert signal["agreement"] is True


def test_all_long_components_emit_long() -> None:
    values = _inputs()
    values.update(
        {
            "actual_value": 0.1,
            "eurusd_post_mid": 1.1010,
            "dxy_post_mid": 99.8,
            "treasury_post_mid": 110.2,
        }
    )
    signal = decide_side(**values)
    assert signal["side"] == "LONG"
    assert signal["agreement"] is True


def test_any_directional_disagreement_stays_cash() -> None:
    values = _inputs()
    values["dxy_post_mid"] = 99.8
    values["treasury_post_mid"] = 110.2
    signal = decide_side(**values)
    assert signal["side"] == "CASH"
    assert signal["reason"] == "THREE_WAY_DISAGREEMENT"


def test_forecast_without_sixty_second_lead_is_rejected() -> None:
    values = _inputs()
    values["forecast_observed_at_utc"] = "2026-08-12T12:29:01Z"
    with pytest.raises(ValueError, match="pre-release lead"):
        decide_side(**values)


def test_actual_observed_after_entry_is_rejected() -> None:
    values = _inputs()
    values["actual_observed_at_utc"] = "2026-08-12T12:46:00Z"
    with pytest.raises(ValueError, match="observable by entry"):
        decide_side(**values)


def test_actual_inside_sixty_second_lag_is_rejected() -> None:
    values = _inputs()
    values["actual_observed_at_utc"] = "2026-08-12T12:30:59Z"
    with pytest.raises(ValueError, match="post-release lag"):
        decide_side(**values)


def test_uncompleted_observation_is_rejected() -> None:
    values = _inputs()
    values["observation_completed_at_utc"] = (
        "2026-08-12T12:50:00Z"
    )
    with pytest.raises(ValueError, match="not complete"):
        decide_side(**values)


def test_neutral_ownership_known_after_midnight_is_rejected() -> None:
    values = _inputs()
    values["neutral_known_at_utc"] = "2026-08-12T00:00:01Z"
    with pytest.raises(ValueError, match="UTC midnight"):
        decide_side(**values)


def test_non_neutral_date_stays_cash() -> None:
    values = _inputs()
    values["is_neutral"] = False
    signal = decide_side(**values)
    assert signal["side"] == "CASH"
    assert signal["reason"] == "DATE_NOT_NEUTRAL"


def test_entry_bar_is_not_a_confirmation_input() -> None:
    assert "entry_bar" not in decide_side.__annotations__
