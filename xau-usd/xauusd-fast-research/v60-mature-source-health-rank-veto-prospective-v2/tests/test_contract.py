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
    source_config = REPO_ROOT / config["read_only_inputs"]["candidate_source_config"]
    assert hashlib.sha256(source_config.read_bytes()).hexdigest() == config["lock"][
        "candidate_source_config_sha256"
    ]
    sources = json.loads(source_config.read_text(encoding="utf-8"))["sources"]
    assert {source["source_id"] for source in sources} == set(
        config["account"]["source_magics"]
    )
    ranker = ROOT / "src" / "ranker.py"
    assert hashlib.sha256(ranker.read_bytes()).hexdigest() == config["lock"][
        "observer_ranker_sha256"
    ]
    evidence = ROOT / "src" / "evidence.py"
    assert hashlib.sha256(evidence.read_bytes()).hexdigest() == config["lock"][
        "evidence_recorder_sha256"
    ]
    ranker_config = config["observer_ranker"]
    assert ranker_config["observer_only"] is True
    assert ranker_config["broker_action_authorized"] is False
    for item in (ranker_config["ml_overlay"], ranker_config["ml_runtime_source"]):
        path = REPO_ROOT / item["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    acceptance = config["acceptance"]
    assert acceptance["minimum_resolved_baseline_executions"] >= 100
    assert acceptance["minimum_resolved_rank_coverage"] == 1.0
    assert acceptance["minimum_trade_retention"] >= 0.95
    assert acceptance["minimum_equity_marks"] >= 5000
