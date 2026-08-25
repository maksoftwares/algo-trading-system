from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.scenario import anti_chase_veto


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


def test_either_extension_signal_is_sufficient() -> None:
    assert anti_chase_veto(feature(atr_ratio=1.3, dist_hi_24h=2.0), 50, RULE)
    assert anti_chase_veto(feature(atr_ratio=1.0, dist_hi_24h=0.2), 50, RULE)
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
