from __future__ import annotations

import inspect

import pandas as pd

from eurusd_regime_specialists import (
    neutral_0608_range_breakout_transfer_v1_1 as module,
)


def _config() -> dict:
    return {
        "strategy": {"family": "FRESH_TEST"},
        "eligibility_revision": {
            "maximum_state_known_lag_hours": 4.0,
        },
    }


def test_freshness_boundary_is_inclusive_and_causal() -> None:
    frame = pd.DataFrame(
        {
            "family": ["PARENT"] * 4,
            "risk_eligible": [True, True, True, False],
            "state_known_lag_hours": [0.0, 4.0, 4.25, 1.0],
        }
    )
    revised = module.apply_freshness_eligibility(frame, _config())

    assert revised["state_fresh"].tolist() == [
        True,
        True,
        False,
        True,
    ]
    assert revised["risk_eligible"].tolist() == [
        True,
        True,
        False,
        False,
    ]
    assert revised["family"].eq("FRESH_TEST").all()


def test_missing_state_age_cannot_be_eligible() -> None:
    frame = pd.DataFrame(
        {
            "family": ["PARENT"],
            "risk_eligible": [True],
            "state_known_lag_hours": [float("nan")],
        }
    )
    revised = module.apply_freshness_eligibility(frame, _config())

    assert not bool(revised.loc[0, "state_fresh"])
    assert not bool(revised.loc[0, "risk_eligible"])


def test_v1_1_census_source_has_no_outcome_loader() -> None:
    source = inspect.getsource(module)
    forbidden_calls = (
        "load_oracle",
        "simulate_trade",
        "evaluate_trade",
        "load_forward_path",
    )

    assert all(call not in source for call in forbidden_calls)


def test_preregistration_lock_verifies() -> None:
    checked = module.verify_lock()

    assert len(checked) >= 7
