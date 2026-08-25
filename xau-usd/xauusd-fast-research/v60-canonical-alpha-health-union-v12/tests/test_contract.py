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
    assert config["schema_version"] == "v60_canonical_alpha_health_union_v12"
    assert config["acceptance"]["minimum_trade_retention_fraction"] == 0.99
    assert config["acceptance"]["minimum_v2_executed_vetoes"] == 10
    assert config["acceptance"]["minimum_antichase_executed_vetoes"] == 1
    assert config["acceptance"]["minimum_union_executed_vetoes"] == 10
    assert config["acceptance"]["additional_cost_stress_usd_per_trade"] == [0.1, 0.2]
    assert config["anti_chase"]["maximum_ret_4h_to_ret_24h_exclusive"] == 0.7
    assert config["anti_chase"]["maximum_causal_rank_exclusive"] == 0.1
    assert config["v2_health_outcome"][
        "source_health_pnl_excludes_incremental_cost_stress"
    ]
    assert config["v2_health_outcome"]["state_recomputed_from_retained_path"]
