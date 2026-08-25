from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]


def test_contract_is_disarmed_and_inputs_are_hash_locked() -> None:
    config = json.loads((ROOT / "config" / "parity.json").read_text())
    assert not any(config["authorization"].values())
    for item in config["inputs"].values():
        path = Path(item["path"])
        if not path.is_absolute():
            path = REPO_ROOT / path
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]


def test_frozen_cost_scenarios_are_not_a_threshold_search() -> None:
    config = json.loads((ROOT / "config" / "parity.json").read_text())
    assert config["additional_cost_usd_per_trade"] == [0.0, 0.1, 0.2]
    assert config["acceptance"]["minimum_trade_retention_fraction"] == 0.99
    assert config["acceptance"]["minimum_frequency_retention_fraction"] == 0.99
