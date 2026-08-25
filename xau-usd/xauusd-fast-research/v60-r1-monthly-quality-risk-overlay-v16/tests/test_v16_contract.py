from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


def load_scenario():
    spec = importlib.util.spec_from_file_location("v16_test_scenario", ROOT / "src/scenario.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_policy_is_r1_only_and_research_only() -> None:
    config = json.loads((ROOT / "config/experiment.json").read_text(encoding="utf-8"))
    assert not any(config["authorization"].values())
    policy = config["monthly_quality_policy"]
    assert policy["eligible_source_ids"] == ["R1_PULLBACK", "R1_BOX"]
    assert policy["maximum_causal_rank_exclusive"] == 0.2
    assert policy["minimum_closed_trades_in_month"] == 8
    assert policy["maximum_month_pnl_usd_exclusive"] == -20.0


def test_source_eligibility_is_exact() -> None:
    scenario = load_scenario()
    policy = {"eligible_source_ids": ["R1_PULLBACK", "R1_BOX"]}
    assert scenario.source_is_eligible("R1_PULLBACK", policy)
    assert scenario.source_is_eligible("R1_BOX", policy)
    assert not scenario.source_is_eligible("V57_BREAK_SWING_H4ADX_HIGH", policy)


def test_preregistration_preserves_strict_gates() -> None:
    text = (ROOT / "PREREGISTRATION.md").read_text(encoding="utf-8")
    assert "post-result mechanism repair" in text
    assert "every year not worse than V6" in text
    assert "Clean prospective evidence is mandatory" in text
