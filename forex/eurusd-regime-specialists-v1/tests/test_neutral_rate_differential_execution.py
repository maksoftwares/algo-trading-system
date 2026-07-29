from __future__ import annotations

from eurusd_regime_specialists.neutral_rate_differential_execution import (
    load_candidates,
    load_config,
    verify_lock,
)


def test_contract_is_frozen_before_eurusd_price_paths() -> None:
    lock = verify_lock()
    assert lock["frozen_before_eurusd_price_paths"] is True
    assert lock["oracle_decision_use_allowed"] is False


def test_candidate_manifest_is_exact_and_unique() -> None:
    candidates = load_candidates(load_config())
    assert len(candidates) == 202
    assert candidates["eligible_date"].is_unique
    assert candidates["spread_change_bps"].abs().min() >= 4.0
    assert candidates["observation_lag_calendar_days"].min() >= 2


def test_candidate_sides_are_balanced_enough_for_frozen_gates() -> None:
    candidates = load_candidates(load_config())
    counts = candidates["side"].value_counts()
    assert counts["LONG"] == 95
    assert counts["SHORT"] == 107
