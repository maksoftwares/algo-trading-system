from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_contract_is_read_only_and_virtual_health_only() -> None:
    config = json.loads((ROOT / "config" / "challenger.json").read_text(encoding="utf-8"))
    assert not any(config["authorization"].values())
    assert config["policy"]["state_condition"] == "VIRTUAL_ROLLING_PROFIT_FACTOR"
    assert config["policy"]["minimum_prior_source_closed_trades"] == 50
