from __future__ import annotations

from eurusd_regime_specialists import (
    neutral_late_session_inventory_unwind_v1_1 as census,
)
from eurusd_regime_specialists import (
    neutral_late_session_inventory_unwind_v1_1_execution as execution,
)


def test_execution_gates_equal_frozen_census_gates() -> None:
    census_config = census.load_config()
    execution_config = execution.load_config()
    assert (
        execution_config["performance_gates"]
        == census_config["performance_gates_if_capacity_passes"]
    )


def test_candidate_manifest_loads_without_outcomes() -> None:
    candidates = execution.load_candidates(execution.load_config())
    assert len(candidates) == 89
    assert candidates["entry_time_utc"].is_monotonic_increasing
    assert candidates["risk_eligible"].all()
    assert candidates["entry_time_utc"].is_unique
    assert candidates["displacement_threshold_pips"].eq(4.0).all()


def test_execution_preregistration_lock_verifies() -> None:
    checked = execution.verify_lock()
    assert len(checked) >= 10
