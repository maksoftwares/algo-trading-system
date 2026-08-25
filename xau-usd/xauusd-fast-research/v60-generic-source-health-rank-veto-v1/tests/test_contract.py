from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]


def test_contract_is_read_only_and_generic() -> None:
    config = json.loads(
        (ROOT / "config" / "challenger.json").read_text(encoding="utf-8")
    )
    assert not any(config["authorization"].values())
    assert config["policy"]["source_id"] == "*"
    assert config["policy"]["source_scope"] == "EACH_SOURCE_INDEPENDENT"


def test_shared_evaluator_is_hash_locked() -> None:
    config = json.loads(
        (ROOT / "config" / "challenger.json").read_text(encoding="utf-8")
    )
    locked = config["inputs"]["shared_evaluator"]
    path = REPO_ROOT / locked["path"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == locked["sha256"]
