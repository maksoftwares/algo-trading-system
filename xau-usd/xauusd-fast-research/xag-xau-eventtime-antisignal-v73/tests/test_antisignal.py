from __future__ import annotations

import pandas as pd
import pytest

from antisignal import invert_candidates, without_minimum_sample


def test_inversion_changes_only_direction_identity_and_family() -> None:
    source = pd.DataFrame(
        {
            "candidate_id": ["old-a", "old-b"],
            "policy_id": ["LOCKED", "LOCKED"],
            "decision_timestamp_ms": [1, 2],
            "direction": ["LONG", "SHORT"],
            "xag_move_bps": [4.2, -4.5],
        }
    )
    result = invert_candidates(source, family="ANTI")
    assert result["direction"].tolist() == ["SHORT", "LONG"]
    assert result["source_direction"].tolist() == ["LONG", "SHORT"]
    assert result["xag_move_bps"].tolist() == source["xag_move_bps"].tolist()
    assert (result["family"] == "ANTI").all()


def test_inversion_rejects_unknown_direction() -> None:
    source = pd.DataFrame(
        {
            "candidate_id": ["old"],
            "policy_id": ["LOCKED"],
            "decision_timestamp_ms": [1],
            "direction": ["FLAT"],
        }
    )
    with pytest.raises(ValueError, match="source direction"):
        invert_candidates(source, family="ANTI")


def test_only_minimum_sample_is_removed_for_gate_comparison() -> None:
    gates = {"minimum_resolved_trades": {"development": 1}, "pf": 1.2}
    assert without_minimum_sample(gates) == {"pf": 1.2}

