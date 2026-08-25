from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]


def test_contract_is_hash_locked_and_disarmed() -> None:
    config = json.loads((ROOT / "config" / "experiment.json").read_text())
    assert not any(config["authorization"].values())
    for item in config["inputs"].values():
        path = Path(item["path"])
        path = path if path.is_absolute() else REPO_ROOT / path
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]


def test_only_v2_health_margin_is_overridden() -> None:
    config = json.loads((ROOT / "config" / "experiment.json").read_text())
    assert config["v2_policy_overrides"] == {
        "maximum_prior_profit_factor_exclusive": 0.9
    }
    assert config["acceptance"]["minimum_trade_retention_fraction"] == 0.99
    assert config["acceptance"]["additional_cost_stress_usd_per_trade"] == [0.1, 0.2]
