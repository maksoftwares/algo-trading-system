from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_contract_hashes_and_authorization() -> None:
    config = json.loads((ROOT / "config" / "experiment.json").read_text())
    assert not any(config["authorization"].values())
    for item in config["inputs"].values():
        path = Path(item["path"])
        path = path if path.is_absolute() else REPO_ROOT / path
        assert sha256(path) == item["sha256"]


def test_acceptance_gates_remain_strict() -> None:
    config = json.loads((ROOT / "config" / "experiment.json").read_text())
    assert config["acceptance"]["minimum_trade_retention_fraction"] == 0.99
    assert config["acceptance"]["additional_cost_stress_usd_per_trade"] == [0.1, 0.2]
    assert config["followthrough"]["maximum_ret_4h_to_ret_24h_exclusive"] == 0.7
