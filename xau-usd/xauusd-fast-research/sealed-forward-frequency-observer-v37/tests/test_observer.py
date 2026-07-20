from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from observer import (  # noqa: E402
    build_failure_status,
    candidate_count,
    load_config,
    should_refresh,
    verify_locked_dependencies,
)


def test_dictionary_candidate_count() -> None:
    assert (
        candidate_count({"counts": {"R2": 3, "R3": 2}}, "counts", "dictionary_sum") == 5
    )


def test_integer_candidate_count() -> None:
    assert candidate_count({"count": 7}, "count", "integer") == 7


def test_refresh_stops_before_twentieth_eligible_day() -> None:
    assert should_refresh([18, 18], 19) is True
    assert should_refresh([19, 18], 19) is False
    assert should_refresh([19, 19], 19) is False


def test_refresh_requires_inventory_sources() -> None:
    assert should_refresh([], 19) is False


def test_authority_is_read_only_and_outcome_sealed() -> None:
    authorization = load_config()["authorization"]
    assert authorization["research_only"] is True
    assert authorization["candidate_inventory_only"] is True
    assert all(
        authorization[name] is False
        for name in (
            "economic_outcomes_authorized",
            "python_predictions_authorized",
            "ea_consumption_authorized",
            "demo_authorized",
            "live_authorized",
            "broker_action_authorized",
        )
    )


def test_locked_dependencies_match() -> None:
    observed = verify_locked_dependencies(load_config())
    assert len(observed) == 6


def test_cycle_exception_produces_explicit_fail_closed_status() -> None:
    config = load_config()
    payload = build_failure_status(
        config, "2026-07-20T04:00:00Z", FileNotFoundError("missing status")
    )
    assert payload["status"] == "FAIL_CLOSED"
    assert payload["failures"] == ["OBSERVER_CYCLE_ERROR"]
    assert payload["candidate_frequency_authorized"] is False
    assert payload["raw_component_candidate_supply"] is None
    assert payload["economic_outcomes_opened"] is None
    assert len(payload["status_sha256"]) == 64
