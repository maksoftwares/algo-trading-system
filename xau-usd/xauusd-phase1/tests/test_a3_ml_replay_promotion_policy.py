from __future__ import annotations

from pathlib import Path

from phase2x_test_helpers import ROOT


POLICY = ROOT / "docs" / "A3_ML_REPLAY_PROMOTION_POLICY_V1.md"


def test_replay_promotion_policy_defines_empty_research_tier_only() -> None:
    text = _policy_text()

    assert "REPLAY_PROMOTION_CANDIDATE" in text
    assert "must not be assigned to any row until a separate promotion review" in text
    assert "research-only" in text
    assert "non-gating" in text
    assert "non-label-bearing" in text


def test_replay_promotion_policy_permanently_excludes_replay_from_labels_and_gates() -> None:
    text = _policy_text()

    for phrase in (
        "Replay rows must never supply execution labels.",
        "Replay rows must never count toward C03 gates:",
        "market setup groups",
        "active weeks",
        "regime diversity",
        "feature budget",
        "slippage readiness",
        "Replay rows must never enter live out-of-sample validation.",
    ):
        assert phrase in text


def test_replay_promotion_policy_keeps_runtime_authorizations_false() -> None:
    text = _policy_text()

    for phrase in (
        "training authorized: false",
        "Python demo predictions authorized: false",
        "EA consumption authorized: false",
        "broker action authorized: false",
    ):
        assert phrase in text


def _policy_text() -> str:
    assert POLICY.exists()
    return POLICY.read_text(encoding="utf-8")
