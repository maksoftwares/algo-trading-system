from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]


def test_contract_inputs_are_locked_and_actions_disarmed() -> None:
    config = json.loads((ROOT / "config" / "experiment.json").read_text())
    assert not any(config["authorization"].values())
    for item in config["inputs"].values():
        path = Path(item["path"])
        path = path if path.is_absolute() else REPO_ROOT / path
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]


def test_acceptance_gates_and_dynamic_policy_are_frozen() -> None:
    config = json.loads((ROOT / "config" / "experiment.json").read_text())
    assert config["schema_version"] == "v60_rank_independent_followthrough_union_v9"
    assert config["acceptance"]["minimum_trade_retention_fraction"] == 0.98
    assert config["acceptance"]["minimum_antichase_executed_vetoes"] == 10
    assert config["acceptance"]["minimum_union_executed_vetoes"] == 20
    assert config["acceptance"]["additional_cost_stress_usd_per_trade"] == [0.1, 0.2]
    assert config["anti_chase"]["maximum_ret_4h_to_ret_24h_exclusive"] == 0.7
    assert "maximum_causal_rank_exclusive" not in config["anti_chase"]
