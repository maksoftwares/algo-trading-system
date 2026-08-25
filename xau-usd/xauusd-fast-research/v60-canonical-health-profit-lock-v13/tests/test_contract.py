from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]


def test_inputs_are_locked_and_actions_disarmed() -> None:
    config = json.loads((ROOT / "config" / "experiment.json").read_text())
    assert not any(config["authorization"].values())
    for item in config["inputs"].values():
        path = Path(item["path"])
        path = path if path.is_absolute() else REPO_ROOT / path
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]


def test_policy_and_hard_gates_are_frozen() -> None:
    config = json.loads((ROOT / "config" / "experiment.json").read_text())
    assert config["schema_version"] == "v60_canonical_health_profit_lock_v13"
    assert config["individual_profit_lock"] == {
        "enabled": True,
        "arm_r": 1.5,
        "retain_r": 0.25,
        "giveback_r": None,
        "poll_seconds": 5,
        "missing_quote_action": "PRESERVE_SOURCE_EXIT",
    }
    acceptance = config["acceptance"]
    assert acceptance["minimum_trade_retention_fraction"] == 0.99
    assert acceptance["minimum_frequency_retention_fraction"] == 0.99
    assert acceptance["additional_cost_stress_usd_per_trade"] == [0.1, 0.2]
    assert acceptance["august_minimum_net_pnl_usd"] > 0.0
