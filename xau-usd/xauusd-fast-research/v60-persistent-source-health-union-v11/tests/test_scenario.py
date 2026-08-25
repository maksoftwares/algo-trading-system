from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.scenario import anti_chase_veto, persistent_profit_factor_state


RULE = {
    "source_id": "V57",
    "direction": "LONG",
    "minimum_prior_source_closed_trades": 50,
    "maximum_causal_rank_exclusive": 0.1,
    "minimum_atr_ratio_inclusive": 1.2,
    "maximum_distance_to_24h_high_atr_exclusive": 1.0,
    "minimum_ret_24h_exclusive": 0.0,
    "maximum_ret_4h_to_ret_24h_exclusive": 0.7,
}


def feature(**overrides):
    row = {
        "execution_source_id": "V57",
        "direction": "LONG",
        "rank": 0.09,
        "atr_ratio": 1.3,
        "dist_hi_24h": 0.2,
        "ret_4h": 6.0,
        "ret_24h": 10.0,
    }
    row.update(overrides)
    return row


def test_complete_mature_weak_followthrough_vetoes() -> None:
    assert anti_chase_veto(feature(), 50, RULE)


def test_both_extension_signals_are_required() -> None:
    assert not anti_chase_veto(feature(atr_ratio=1.3, dist_hi_24h=2.0), 50, RULE)
    assert not anti_chase_veto(feature(atr_ratio=1.0, dist_hi_24h=0.2), 50, RULE)
    assert not anti_chase_veto(feature(atr_ratio=1.0, dist_hi_24h=2.0), 50, RULE)


def test_immature_missing_or_strong_followthrough_retains() -> None:
    assert not anti_chase_veto(feature(), 49, RULE)
    assert not anti_chase_veto(None, 100, RULE)
    assert not anti_chase_veto(feature(atr_ratio=float("nan")), 100, RULE)
    assert not anti_chase_veto(feature(ret_4h=7.0), 100, RULE)
    assert not anti_chase_veto(feature(rank=0.1), 100, RULE)


def test_wrong_source_direction_and_nonpositive_anchor_retain() -> None:
    assert not anti_chase_veto(feature(execution_source_id="R1"), 100, RULE)
    assert not anti_chase_veto(feature(direction="SHORT"), 100, RULE)
    assert not anti_chase_veto(feature(ret_24h=0.0), 100, RULE)


def test_pf_threshold_crossing_on_latest_close_is_not_persistent() -> None:
    outcomes = [1.0] * 10 + [-0.5] * 10 + [-10.0]
    persistent, current, previous = persistent_profit_factor_state(outcomes, 20, 1.0)
    assert not persistent
    assert current is not None and current < 1.0
    assert previous is not None and previous > 1.0


def test_two_degraded_windows_are_persistent() -> None:
    outcomes = [1.0] * 10 + [-2.0] * 10 + [-1.0]
    persistent, current, previous = persistent_profit_factor_state(outcomes, 20, 1.0)
    assert persistent
    assert current is not None and current < 1.0
    assert previous is not None and previous < 1.0


def test_persistence_requires_one_more_outcome_than_lookback() -> None:
    assert persistent_profit_factor_state([-1.0] * 20, 20, 1.0) == (
        False,
        None,
        None,
    )
