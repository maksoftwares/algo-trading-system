from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]


def test_contract_is_read_only_and_maturity_locked() -> None:
    config = json.loads(
        (ROOT / "config" / "challenger.json").read_text(encoding="utf-8")
    )
    assert not any(config["authorization"].values())
    assert config["policy"]["source_id"] == "*"
    assert config["policy"]["minimum_prior_source_closed_trades"] == 50
    assert config["gates"]["minimum_trade_retention_fraction"] == 0.99


def test_shared_evaluator_is_hash_locked() -> None:
    config = json.loads(
        (ROOT / "config" / "challenger.json").read_text(encoding="utf-8")
    )
    locked = config["inputs"]["shared_evaluator"]
    assert hashlib.sha256((REPO_ROOT / locked["path"]).read_bytes()).hexdigest() == locked["sha256"]
