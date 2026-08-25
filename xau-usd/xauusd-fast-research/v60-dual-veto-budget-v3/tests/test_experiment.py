from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.experiment import apply_source_day_budget, normalize_proposals


def proposals() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"trade_id": "a", "entry_time_utc": "2026-08-01T01:00:00Z", "source_id": "V57", "proposal_rule": "V2"},
            {"trade_id": "b", "entry_time_utc": "2026-08-01T02:00:00Z", "source_id": "V57", "proposal_rule": "ANTI"},
            {"trade_id": "c", "entry_time_utc": "2026-08-01T03:00:00Z", "source_id": "R1", "proposal_rule": "V2"},
            {"trade_id": "d", "entry_time_utc": "2026-08-02T01:00:00Z", "source_id": "V57", "proposal_rule": "V2"},
        ]
    )


def test_budget_selects_first_proposal_without_using_outcomes() -> None:
    result = apply_source_day_budget(proposals(), 1).set_index("trade_id")
    assert bool(result.loc["a", "selected_veto"])
    assert not bool(result.loc["b", "selected_veto"])
    assert result.loc["b", "budget_action"] == "RETAIN_SOURCE_DAY_BUDGET"


def test_budget_is_independent_by_source_and_day() -> None:
    result = apply_source_day_budget(proposals(), 1).set_index("trade_id")
    assert bool(result.loc["c", "selected_veto"])
    assert bool(result.loc["d", "selected_veto"])


def test_duplicate_trade_proposals_consume_one_slot() -> None:
    frame = proposals()
    duplicate = frame.iloc[[0]].copy()
    duplicate["proposal_rule"] = "ANTI"
    result = apply_source_day_budget(pd.concat([frame, duplicate]), 1)
    first = result.loc[result["trade_id"].eq("a")].iloc[0]
    assert len(result.loc[result["trade_id"].eq("a")]) == 1
    assert first["proposal_rule"] == "ANTI+V2"


def test_conflicting_duplicate_identity_fails_closed() -> None:
    frame = proposals()
    conflict = frame.iloc[[0]].copy()
    conflict["source_id"] = "R1"
    with pytest.raises(ValueError, match="Conflicting proposal identity"):
        normalize_proposals(pd.concat([frame, conflict]).to_dict("records"))


def test_invalid_budget_is_rejected() -> None:
    with pytest.raises(ValueError, match="must be positive"):
        apply_source_day_budget(proposals(), 0)
