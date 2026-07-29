from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.neutral_subregime_consensus import (
    consensus_direction,
)


def test_consensus_requires_two_groups_and_no_opposite_vote() -> None:
    agreeing = [
        {
            "direction": "LONG",
            "expert_id": "momentum",
            "mechanism_group": "price_momentum",
        },
        {
            "direction": "LONG",
            "expert_id": "macro",
            "mechanism_group": "macro",
        },
    ]
    direction, votes = consensus_direction(agreeing, 2, 2)
    assert direction == "LONG"
    assert len(votes) == 2

    with_veto = agreeing + [
        {
            "direction": "SHORT",
            "expert_id": "fade",
            "mechanism_group": "price_reversion",
        }
    ]
    assert consensus_direction(with_veto, 2, 2)[0] is None

    one_group = [agreeing[0], {**agreeing[0], "expert_id": "momentum_two"}]
    assert consensus_direction(one_group, 2, 2)[0] is None
