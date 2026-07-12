from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DIRECTION = ROOT / "docs" / "A1_XAU_INDEPENDENT_SPECIALIST_PRIMARY_DIRECTION_2026_07_12.md"
LOCK = (
    ROOT
    / "outputs"
    / "manifests"
    / "A1_XAU_INDEPENDENT_SPECIALIST_PRIMARY_DIRECTION_LOCK_V1.json"
)
DIRECTION_SHA256 = "c68a669f160b7469f8204101d05d38c36cf46f0501ca1f11c77ff3f91659b9af"
REQUIRED_STATEMENTS = {
    "R6 = primary independent specialist lane",
    "NP1-A = next action",
    "R1+R2 = research control only",
    "R3 = excluded",
    "R4 = no survivor",
    "router entry/hold audit = deferred control diagnostic",
    "parallel specialist lane = false",
    "all history through 2026-06-30 = DEVELOPMENT_DATA",
    "no demo/live/broker authorization",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_primary_direction_and_all_dependency_hashes_are_exact():
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    assert _sha256(DIRECTION) == DIRECTION_SHA256
    assert lock["schema_version"] == "a1_xau_independent_specialist_primary_direction_lock_v1"
    assert lock["phase"] == "IS1-A_OWNER_DIRECTION_SUPERSESSION_AND_R6_PRIMARY_LANE_LOCK"
    assert lock["primary_lane"] == "R6"
    assert lock["primary_specialist"] == "R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1"
    assert lock["next_action"] == "NP1-A"

    for relative, expected in lock["artifacts"].items():
        artifact = ROOT / relative
        assert artifact.is_file(), relative
        assert artifact.stat().st_size == expected["size_bytes"], relative
        assert _sha256(artifact) == expected["sha256"], relative

    assert lock["authority"] == {
        "controlling_c2r4_review_sha256": (
            "d7824eca268f3fb2443406d929e7565723e79ec4bafef6b501c3eab49bb4fb7b"
        ),
        "independent_specialist_direction_sha256": DIRECTION_SHA256,
        "native_parity_acquisition_direction_sha256": (
            "a2d10661e58e95c516291b7e1d9b07b8b59904b94cff8474e28b16d569f0c1ca"
        ),
        "reviewed_head": "c9873c2693872f41ce17c1ee31c35a8a4fc36fcb",
        "reviewed_tree": "211bba5389e25ba5779dd39663366ac6a871f31f",
    }


def test_direction_freezes_one_lane_and_preserves_every_phase_boundary():
    text = DIRECTION.read_text(encoding="utf-8")
    compact = " ".join(text.split())
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    boundary = lock["boundary"]

    assert "PRIMARY INDEPENDENT-SPECIALIST LANE: R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1" in compact
    assert "SEPARATE PARALLEL SPECIALIST LANE: NOT AUTHORIZED" in compact
    assert "Census variants: 1" in compact
    assert "Standalone exact-MT5 variants: 1" in compact
    assert "Native maximum relative floating-equity DD: <=8.00%" in compact
    assert "No historical result generated under this direction is deployment authorization" in compact
    assert "NO DEMO ATTACH" in text
    assert "NO LIVE ATTACH" in text
    assert "NO BROKER ACTION" in text

    assert boundary["historical_data_status"] == "DEVELOPMENT_DATA"
    assert boundary["separate_parallel_specialist_authorized"] is False
    assert boundary["detector_change_authorized_in_this_commit"] is False
    assert boundary["mt5_execution_authorized_in_this_commit"] is False
    assert boundary["census_authorized_in_this_commit"] is False
    assert boundary["pnl_authorized_in_this_commit"] is False
    assert boundary["demo_authorized"] is False
    assert boundary["live_authorized"] is False
    assert boundary["broker_action_authorized"] is False


def test_all_authoritative_status_surfaces_agree_on_r6_and_np1a():
    summary = json.loads((REPO_ROOT / "status_summary.json").read_text(encoding="utf-8"))
    current = summary["current"]
    program = current["independent_specialist_program"]

    assert current["overall_status"] == "NO_GO_RESEARCH_ONLY"
    assert set(current["owner_direction_current_statements"]) == REQUIRED_STATEMENTS
    assert program == {
        "historical_pnl_authorized": False,
        "id": "R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1",
        "next_action": "NP1-A",
        "np1_status": "MANDATORY_PREREQUISITE_WITHIN_R6",
        "parallel_specialist_lane_authorized": False,
        "range_box_status": "BACKLOG_ONLY_IF_R6_CLOSES",
        "status": "PRIMARY_INDEPENDENT_SPECIALIST_LANE",
    }
    assert current["portfolio_control"]["admission_status"] == (
        "RESEARCH_CONTROL_NOT_DEPLOYMENT_AUTHORIZED"
    )
    assert current["specialists"]["R1"]["primary_program_status"] == "RESEARCH_CONTROL_ONLY"
    assert current["specialists"]["R2"]["primary_program_status"] == "RESEARCH_CONTROL_ONLY"
    assert current["specialists"]["R3"]["primary_program_status"] == "EXCLUDED"
    assert current["specialists"]["R4"]["status"] == "NO_SURVIVOR"
    assert current["router_entry_hold_audit"]["status"] == "DEFERRED_CONTROL_DIAGNOSTIC"
    assert current["primary_next_task"] == {
        "ea_trading_logic_change": "NONE",
        "id": "R6-NP1-A_MARKET_ONLY_NATIVE_PARITY_ACQUISITION_LOCKS",
        "status": "AUTHORIZED_NOT_STARTED",
        "strategy_change_authorized": False,
    }
    assert current["historical_evidence"] == {
        "classification": "DEVELOPMENT_DATA",
        "through": "2026-06-30",
        "untouched_holdout": False,
    }
    assert current["authorization"] == {
        "broker_action_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
        "runtime_touched": False,
    }
    source = summary["source_documents"]["independent_specialist_primary_direction"]
    assert source["sha256"] == DIRECTION_SHA256
    assert _sha256(REPO_ROOT / source["path"]) == DIRECTION_SHA256

    surfaces = {
        "status_summary.md": (REPO_ROOT / "status_summary.md").read_text(encoding="utf-8"),
        "status.html": (REPO_ROOT / "status.html").read_text(encoding="utf-8"),
        "agent.md": (REPO_ROOT / "agent.md").read_text(encoding="utf-8"),
    }
    for name, text in surfaces.items():
        assert "NO_GO_RESEARCH_ONLY" in text, name
        assert "R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1" in text, name
        assert "PRIMARY_INDEPENDENT_SPECIALIST_LANE" in text, name
        assert "NP1-A" in text, name
        assert "DEFERRED_CONTROL_DIAGNOSTIC" in text, name
        assert "DEVELOPMENT_DATA" in text, name
        assert "parallel specialist" in text.lower(), name
        assert "broker_action_authorized: true" not in text, name
        assert "demo_authorized: true" not in text, name
        assert "live_authorized: true" not in text, name
