from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.scenario import (
    ProtectionState,
    protection_threshold,
    update_protection,
)


POLICY = {
    "enabled": True,
    "arm_r": 1.5,
    "retain_r": 0.25,
    "giveback_r": None,
}


def test_frozen_lock_arms_then_closes_at_fixed_floor() -> None:
    state = ProtectionState()
    assert update_protection(state, POLICY, 10.0, 14.99) == "HOLD"
    assert update_protection(state, POLICY, 10.0, 15.0) == "ARM"
    assert update_protection(state, POLICY, 10.0, 3.0) == "HOLD"
    assert update_protection(state, POLICY, 10.0, 2.5) == "CLOSE"
    assert protection_threshold(POLICY, 10.0, 15.0) == 2.5


def test_peak_does_not_create_an_unregistered_trailing_stop() -> None:
    state = ProtectionState()
    assert update_protection(state, POLICY, 10.0, 25.0) == "ARM"
    assert update_protection(state, POLICY, 10.0, 4.0) == "HOLD"


def test_invalid_values_fail_closed() -> None:
    for risk, pnl in ((0.0, 1.0), (10.0, float("nan"))):
        try:
            update_protection(ProtectionState(), POLICY, risk, pnl)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid protection input was accepted")
