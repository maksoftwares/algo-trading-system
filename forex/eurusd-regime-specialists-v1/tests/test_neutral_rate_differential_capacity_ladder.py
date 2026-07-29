from __future__ import annotations

from eurusd_regime_specialists.neutral_rate_differential_capacity_ladder import (
    select_highest_passing,
    verify_lock,
)


def test_contract_is_frozen_before_threshold_screen() -> None:
    lock = verify_lock()
    assert lock["frozen_before_threshold_screen"] is True
    assert lock["eurusd_outcome_use_allowed"] is False


def test_selector_chooses_first_descending_threshold_that_passes() -> None:
    rows = [
        {
            "threshold_bps": 5.0,
            "census": {"all_capacity_gates_passed": False},
        },
        {
            "threshold_bps": 4.0,
            "census": {"all_capacity_gates_passed": True},
        },
        {
            "threshold_bps": 3.0,
            "census": {"all_capacity_gates_passed": True},
        },
    ]
    selected = select_highest_passing(rows)
    assert selected is not None
    assert selected["threshold_bps"] == 4.0


def test_selector_returns_none_when_every_threshold_fails() -> None:
    rows = [
        {
            "threshold_bps": value,
            "census": {"all_capacity_gates_passed": False},
        }
        for value in (5.0, 4.0, 3.0)
    ]
    assert select_highest_passing(rows) is None
