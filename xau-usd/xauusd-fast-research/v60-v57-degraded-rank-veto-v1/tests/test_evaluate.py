from dataclasses import dataclass

import pandas as pd

from src.evaluate import (
    apply_additional_cost,
    attach_baseline_runtime_pnl,
    causal_virtual_profit_factors,
    profit_factor,
    should_veto,
)


POLICY = {
    "source_id": "V57_BREAK_SWING_H4ADX_HIGH",
    "lookback_closed_trades": 20,
    "maximum_prior_profit_factor_exclusive": 1.0,
    "maximum_causal_rank_exclusive": 0.1,
    "missing_rank_action": "RETAIN",
}


def test_profit_factor() -> None:
    assert profit_factor([2.0, -1.0, 3.0, -1.0]) == 2.5


def test_requires_full_prior_window() -> None:
    veto, recent_pf = should_veto(
        source_id=POLICY["source_id"],
        rank=0.01,
        prior_outcomes=[-1.0] * 19,
        policy=POLICY,
    )
    assert veto is False
    assert recent_pf is None


def test_veto_requires_both_degraded_health_and_bottom_decile() -> None:
    outcomes = [1.0] * 8 + [-1.0] * 12
    veto, recent_pf = should_veto(
        source_id=POLICY["source_id"],
        rank=0.09,
        prior_outcomes=outcomes,
        policy=POLICY,
    )
    assert recent_pf == 8.0 / 12.0
    assert veto is True

    assert should_veto(
        source_id=POLICY["source_id"],
        rank=0.10,
        prior_outcomes=outcomes,
        policy=POLICY,
    )[0] is False

    assert should_veto(
        source_id=POLICY["source_id"],
        rank=0.09,
        prior_outcomes=[1.0] * 12 + [-1.0] * 8,
        policy=POLICY,
    )[0] is False


def test_missing_rank_and_other_sources_retain() -> None:
    outcomes = [-1.0] * 20
    assert should_veto(
        source_id=POLICY["source_id"],
        rank=None,
        prior_outcomes=outcomes,
        policy=POLICY,
    )[0] is False
    assert should_veto(
        source_id="R4_CHOP",
        rank=0.0,
        prior_outcomes=outcomes,
        policy=POLICY,
    )[0] is False


def test_wildcard_policy_uses_each_source_health() -> None:
    policy = {**POLICY, "source_id": "*"}
    assert should_veto(
        source_id="R4_CHOP",
        rank=0.09,
        prior_outcomes=[-1.0] * 20,
        policy=policy,
    )[0] is True


def test_optional_source_maturity_gate() -> None:
    policy = {
        **POLICY,
        "source_id": "*",
        "minimum_prior_source_closed_trades": 50,
    }
    outcomes = [-1.0] * 20
    assert should_veto(
        source_id="R4_CHOP",
        rank=0.09,
        prior_outcomes=outcomes,
        prior_source_closed_count=49,
        policy=policy,
    )[0] is False
    assert should_veto(
        source_id="R4_CHOP",
        rank=0.09,
        prior_outcomes=outcomes,
        prior_source_closed_count=50,
        policy=policy,
    )[0] is True


def test_consecutive_loss_mode() -> None:
    policy = {
        **POLICY,
        "state_condition": "CONSECUTIVE_LOSSES",
        "minimum_consecutive_losses": 4,
    }
    assert should_veto(
        source_id=POLICY["source_id"],
        rank=0.09,
        prior_outcomes=[],
        consecutive_losses=4,
        policy=policy,
    )[0] is True
    assert should_veto(
        source_id=POLICY["source_id"],
        rank=0.10,
        prior_outcomes=[],
        consecutive_losses=4,
        policy=policy,
    )[0] is False
    assert should_veto(
        source_id=POLICY["source_id"],
        rank=0.09,
        prior_outcomes=[],
        consecutive_losses=3,
        policy=policy,
    )[0] is False


def test_virtual_profit_factor_mode() -> None:
    policy = {
        **POLICY,
        "state_condition": "VIRTUAL_ROLLING_PROFIT_FACTOR",
        "maximum_prior_profit_factor_exclusive": 0.7,
    }
    assert should_veto(
        source_id=POLICY["source_id"],
        rank=0.09,
        prior_outcomes=[],
        virtual_profit_factor=0.6,
        policy=policy,
    )[0] is True
    assert should_veto(
        source_id=POLICY["source_id"],
        rank=0.09,
        prior_outcomes=[],
        virtual_profit_factor=0.7,
        policy=policy,
    )[0] is False


@dataclass(frozen=True)
class CandidateStub:
    trade_id: str
    source_id: str
    entry_ms: int
    exit_ms: int
    pnl_usd: float


@dataclass(frozen=True)
class CostCandidateStub:
    trade_id: str
    pnl_usd: float
    open_cost_usd: float


def test_additional_cost_updates_normal_and_path_dependent_pnl_once() -> None:
    original = CostCandidateStub("a", pnl_usd=2.5, open_cost_usd=0.4)
    stressed = apply_additional_cost([original], 0.75)[0]
    assert original.pnl_usd == 2.5
    assert original.open_cost_usd == 0.4
    assert stressed.pnl_usd == 1.75
    assert stressed.open_cost_usd == 1.15


def test_additional_cost_rejects_negative_values() -> None:
    try:
        apply_additional_cost([], -0.01)
    except ValueError as error:
        assert "nonnegative" in str(error)
    else:
        raise AssertionError("Negative execution-cost stress was accepted")


def test_virtual_health_reveals_outcome_only_after_exit() -> None:
    source = POLICY["source_id"]
    candidates = [
        CandidateStub("a", source, 10, 30, -1.0),
        CandidateStub("b", source, 20, 40, 2.0),
        CandidateStub("c", source, 30, 50, -1.0),
        CandidateStub("d", "R4_CHOP", 5, 6, 100.0),
    ]
    health = causal_virtual_profit_factors(candidates, source, lookback=1)
    assert health["a"] is None
    assert health["b"] is None
    assert health["c"] == 0.0


def test_wildcard_virtual_health_is_source_local() -> None:
    candidates = [
        CandidateStub("a", "A", 10, 20, -1.0),
        CandidateStub("b", "B", 15, 16, 10.0),
        CandidateStub("c", "A", 30, 40, 1.0),
    ]
    health = causal_virtual_profit_factors(candidates, "*", lookback=1)
    assert health["a"] is None
    assert health["b"] is None
    assert health["c"] == 0.0


def test_veto_audit_uses_runtime_pnl_not_candidate_endpoint() -> None:
    rows = attach_baseline_runtime_pnl(
        [{"trade_id": "a", "candidate_endpoint_pnl_usd": -5.0}],
        pd.DataFrame([{"trade_id": "a", "pnl_usd": 2.0}]),
    )
    assert rows == [
        {
            "trade_id": "a",
            "candidate_endpoint_pnl_usd": -5.0,
            "baseline_runtime_executed": True,
            "baseline_runtime_pnl_usd": 2.0,
        }
    ]

    absent = attach_baseline_runtime_pnl(
        [{"trade_id": "b", "candidate_endpoint_pnl_usd": -1.0}],
        pd.DataFrame([{"trade_id": "a", "pnl_usd": 2.0}]),
    )
    assert absent[0]["baseline_runtime_executed"] is False
    assert absent[0]["baseline_runtime_pnl_usd"] is None
