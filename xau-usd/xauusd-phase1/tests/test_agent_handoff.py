from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
AGENT_MD = REPO_ROOT / "agent.md"


def test_agent_handoff_points_to_current_governance_packet() -> None:
    text = AGENT_MD.read_text(encoding="utf-8")

    for required in (
        "A1_XAU_PROFITABLE_SYSTEM_MASTER_DIRECTION_2026_07_10.md",
        "A1_XAU_CURRENT_RESEARCH_FREEZE_2026_07_10.md",
        "A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_PREREG_2026_07_10.md",
        "current_r1_r2_baseline",
        "A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_V1",
        "DEVELOPMENT_DATA",
        "STANDALONE_SHADOW_ONLY",
        "BLOCKED_LEGACY_RULE_ADMISSIBILITY",
        "REPAIR_REQUIRED_NATIVE_POSITION_JOIN",
    ):
        assert required in text


def test_agent_handoff_is_current_only_and_non_authorizing() -> None:
    text = AGENT_MD.read_text(encoding="utf-8")

    for required in (
        "demo_authorized: false",
        "live_authorized: false",
        "broker_action_authorized: false",
        "All inspected history through `2026-06-30` is `DEVELOPMENT_DATA`",
        "No demo/live attach or broker order outside the isolated Strategy Tester",
    ):
        assert required in text

    for stale in (
        "OWNER_AUTHORIZED_DEMO_BROKER_ACTION",
        "BROKER_ACTION_ENABLED",
        "PASS_ATTACHED",
        "event_reaction_v0_exact_mt5",
        "short_hedge_v2_breakdown_retest",
    ):
        assert stale not in text
