from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]


def test_v2_observer_is_read_only_and_hash_locked() -> None:
    config = json.loads(
        (ROOT / "config" / "prospective.json").read_text(encoding="utf-8")
    )
    authorization = config["authorization"]
    assert authorization["read_only_mt5"] is True
    assert not any(
        authorization[key]
        for key in ("broker_actions", "runtime_changes", "demo_deployment", "live_deployment")
    )
    for path_key, hash_key in (
        ("challenger_config", "challenger_config_sha256"),
        ("shared_observer", "shared_observer_sha256"),
    ):
        path = REPO_ROOT / config["lock"][path_key]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == config["lock"][hash_key]
    warm_start = REPO_ROOT / config["read_only_inputs"]["warm_start"]
    assert hashlib.sha256(warm_start.read_bytes()).hexdigest() == config["lock"]["warm_start_sha256"]
