from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_contract_is_research_only_and_balance_independent() -> None:
    config = json.loads((ROOT / "config/experiment.json").read_text(encoding="utf-8"))
    assert not any(config["authorization"].values())
    policy = config["monthly_quality_policy"]
    assert policy["month_timezone"] == "UTC"
    assert policy["canonical_lot_size"] == 0.01
    assert not any("balance" in key.lower() or "equity" in key.lower() for key in policy)
    assert config["acceptance"]["minimum_trade_retention_fraction"] >= 0.98


def test_preregistration_discloses_exposed_selection() -> None:
    text = (ROOT / "PREREGISTRATION.md").read_text(encoding="utf-8")
    assert "All historical outcomes are exposed" in text
    assert "Clean prospective evidence is mandatory" in text
