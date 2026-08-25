from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from src.experiment import load_locked_config


def test_all_inputs_are_hash_locked() -> None:
    config = load_locked_config(ROOT / "config" / "experiment.json", REPO_ROOT)
    assert config["inputs"]
    assert all(len(item["sha256"]) == 64 for item in config["inputs"].values())


def test_research_cannot_authorize_broker_or_deployment() -> None:
    config = json.loads((ROOT / "config" / "experiment.json").read_text())
    assert not any(config["authorization"].values())


def test_locked_retention_gate_is_not_weakened() -> None:
    config = json.loads((ROOT / "config" / "experiment.json").read_text())
    assert config["acceptance"]["minimum_trade_retention_fraction"] == 0.99
    assert config["acceptance"]["minimum_frequency_retention_fraction"] == 0.99
    assert config["composition"]["maximum_vetoes_per_source_utc_day"] == 1
