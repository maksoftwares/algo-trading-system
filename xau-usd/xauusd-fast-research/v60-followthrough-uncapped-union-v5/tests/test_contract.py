from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]


def load_policy(path: Path):
    spec = importlib.util.spec_from_file_location("v5_test_policy", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["v5_test_policy"] = module
    spec.loader.exec_module(module)
    return module


def test_contract_is_locked_and_disarmed() -> None:
    config = json.loads((ROOT / "config" / "experiment.json").read_text())
    assert not any(config["authorization"].values())
    for item in config["inputs"].values():
        path = Path(item["path"])
        path = path if path.is_absolute() else REPO_ROOT / path
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]


def test_followthrough_rule_and_retention_gate_are_frozen() -> None:
    config = json.loads((ROOT / "config" / "experiment.json").read_text())
    assert config["acceptance"]["minimum_trade_retention_fraction"] == 0.99
    assert config["followthrough"]["maximum_ret_4h_to_ret_24h_exclusive"] == 0.7
    policy_path = REPO_ROOT / config["inputs"]["followthrough_policy_source"]["path"]
    policy = load_policy(policy_path)
    mask = policy.followthrough_mask(
        pd.DataFrame({"ret_4h": [6.0, 8.0], "ret_24h": [10.0, 10.0]}),
        config["followthrough"],
    )
    assert mask.tolist() == [True, False]
