from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from src.evidence import immutable_events


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_all_executable_sources_are_hash_locked() -> None:
    config = json.loads(
        (ROOT / "config" / "prospective.json").read_text(encoding="utf-8")
    )
    locks = config["lock"]
    paths = {
        "research_config_sha256": REPO_ROOT / locks["research_config"],
        "shared_observer_sha256": REPO_ROOT / locks["shared_observer"],
        "observer_ranker_sha256": ROOT.parent
        / "v60-mature-source-health-rank-veto-prospective-v2"
        / "src"
        / "ranker.py",
        "policy_source_sha256": ROOT / "src" / "policy.py",
        "observer_runner_sha256": ROOT / "run_observer.py",
        "base_evidence_recorder_sha256": ROOT.parent
        / "v60-mature-source-health-rank-veto-prospective-v2"
        / "src"
        / "evidence.py",
        "evidence_recorder_sha256": ROOT / "src" / "evidence.py",
        "base_tick_replay_sha256": ROOT.parent
        / "v60-mature-source-health-rank-veto-prospective-v2"
        / "src"
        / "tick_replay.py",
        "tick_replay_sha256": ROOT / "src" / "tick_replay.py",
        "tick_replay_runner_sha256": ROOT / "run_exact_tick_equity_replay.py",
    }
    for key, path in paths.items():
        assert digest(path) == locks[key]


def test_contract_is_read_only_and_boundary_is_frozen() -> None:
    config = json.loads(
        (ROOT / "config" / "prospective.json").read_text(encoding="utf-8")
    )
    assert config["lock"]["evidence_start_inclusive_utc"] == "2026-08-26T00:00:00Z"
    assert config["authorization"] == {
        "read_only_mt5": True,
        "broker_actions": False,
        "runtime_changes": False,
        "demo_deployment": False,
        "live_deployment": False,
    }
    assert config["acceptance"]["minimum_resolved_causal_feature_coverage"] == 1.0
    assert config["acceptance"]["minimum_trade_retention"] == 0.99


def test_score_evidence_freezes_policy_features() -> None:
    row = {
        "candidate_id": "candidate",
        "event_id": "event",
        "source_id": "V57_BREAK_SWING_H4ADX_HIGH",
        "entry_time_utc": "2026-08-26T00:00:00Z",
        "causal_score": 0.2,
        "causal_rank": 0.09,
        "candidate_direction": "LONG",
        "feature_bar_time_utc": "2026-08-26T00:00:00Z",
        "atr_ratio": 1.2,
        "dist_hi_24h": 0.9,
        "causal_policy_features_complete": True,
        "baseline_executed": False,
        "broker_outcome_resolved": False,
    }
    event_type, payload = immutable_events(row)[0]
    assert event_type == "SCORE_DECISION"
    assert payload["candidate_direction"] == "LONG"
    assert payload["atr_ratio"] == 1.2
    assert payload["dist_hi_24h"] == 0.9


def test_missing_policy_feature_is_recorded_as_null() -> None:
    row = {
        "candidate_id": "candidate",
        "event_id": "event",
        "source_id": "V57_BREAK_SWING_H4ADX_HIGH",
        "entry_time_utc": "2026-08-26T00:00:00Z",
        "causal_score": 0.2,
        "causal_rank": 0.09,
        "candidate_direction": None,
        "feature_bar_time_utc": None,
        "atr_ratio": None,
        "dist_hi_24h": None,
        "causal_policy_features_complete": False,
        "baseline_executed": False,
        "broker_outcome_resolved": False,
    }
    _, payload = immutable_events(row)[0]
    assert payload["atr_ratio"] is None
    assert payload["dist_hi_24h"] is None
    assert payload["causal_policy_features_complete"] is False
