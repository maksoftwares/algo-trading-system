from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_v15_is_less_aggressive_and_research_only() -> None:
    config = json.loads((ROOT / "config/experiment.json").read_text(encoding="utf-8"))
    assert not any(config["authorization"].values())
    policy = config["monthly_quality_policy"]
    assert policy["minimum_closed_trades_in_month"] == 8
    assert policy["maximum_month_pnl_usd_exclusive"] == -20.0
    assert policy["maximum_causal_rank_exclusive"] == 0.3
    assert config["acceptance"]["minimum_trade_retention_fraction"] == 0.98


def test_v14_artifacts_are_hash_locked() -> None:
    config = json.loads((ROOT / "config/experiment.json").read_text(encoding="utf-8"))
    assert len(config["inputs"]["v14_runner"]["sha256"]) == 64
    assert len(config["inputs"]["v14_result"]["sha256"]) == 64


def test_preregistration_discloses_post_result_repair() -> None:
    text = (ROOT / "PREREGISTRATION.md").read_text(encoding="utf-8")
    assert "post-result repair" in text
    assert "no independent historical holdout" in text
