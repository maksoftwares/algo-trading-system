from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_retrospective_fragility_is_supportive_but_never_authorizing() -> None:
    result = json.loads((ROOT / "GOAL_RESULT.json").read_text(encoding="utf-8"))
    challenger = result["best_historical_challenger"]
    fragility = challenger["retrospective_veto_fragility"]

    assert fragility["beneficial_vetoes"] == 12
    assert fragility["executed_vetoes"] == 13
    assert fragility["beneficial_months"] == fragility["active_months"] == 9
    assert fragility["avoided_pnl_after_removing_largest_benefit_usd"] > 0.0
    assert fragility["selection_adjusted"] is False
    assert fragility["deployment_evidence"] is False
    assert challenger["deployment_authorized"] is False
    assert result["decision"] == (
        "KEEP_V60_DEPLOYED_COLLECT_DYNAMIC_V6_FORWARD_EVIDENCE"
    )
