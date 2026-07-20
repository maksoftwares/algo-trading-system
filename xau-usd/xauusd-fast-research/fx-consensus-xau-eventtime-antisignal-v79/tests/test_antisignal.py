from __future__ import annotations

import pandas as pd

from antisignal import invert_candidates, without_minimum_sample


def test_inversion_is_exactly_once() -> None:
    source = pd.DataFrame(
        {
            "candidate_id": ["a", "b"],
            "policy_id": ["LOCKED", "LOCKED"],
            "decision_timestamp_ms": [1, 2],
            "direction": ["LONG", "SHORT"],
            "source_move_bps": [-1.0, 1.0],
        }
    )
    result = invert_candidates(source, family="ANTI")
    assert result["direction"].tolist() == ["SHORT", "LONG"]
    assert result["source_direction"].tolist() == ["LONG", "SHORT"]
    assert result["source_move_bps"].tolist() == source["source_move_bps"].tolist()
    assert result["candidate_id"].str.startswith("V79:").all()


def test_gate_comparison_excludes_only_window_sample() -> None:
    assert without_minimum_sample({"minimum_resolved_trades": {}, "pf": 1.2}) == {
        "pf": 1.2
    }
