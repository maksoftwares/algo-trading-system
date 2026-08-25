from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.scenario import anti_chase_veto, canonical_alpha_health_pnl


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


def test_canonical_alpha_health_removes_only_incremental_stress() -> None:
    assert canonical_alpha_health_pnl(-10.2, 0.2) == -10.0
    assert canonical_alpha_health_pnl(5.0, 0.0) == 5.0


def test_canonical_alpha_health_rejects_invalid_cost() -> None:
    try:
        canonical_alpha_health_pnl(1.0, -0.1)
    except ValueError as error:
        assert "nonnegative" in str(error)
    else:
        raise AssertionError("Negative incremental cost was accepted")


def test_canonical_alpha_health_rejects_nonfinite_values() -> None:
    for pnl, cost in ((float("nan"), 0.0), (1.0, float("inf"))):
        try:
            canonical_alpha_health_pnl(pnl, cost)
        except ValueError:
            pass
        else:
            raise AssertionError("Nonfinite value was accepted")
