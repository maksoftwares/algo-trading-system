from __future__ import annotations

import subprocess
from pathlib import Path

from phase0r.candidate_registry import (
    CANDIDATES,
    candidate_ids,
    validate_candidate_registry,
    validate_status_transition,
)


def test_candidate_ids_are_unique():
    ids = candidate_ids()

    assert len(ids) == len(set(ids))


def test_candidates_default_to_passive_only_and_same_family_is_classified():
    assert validate_candidate_registry() == []
    for candidate in CANDIDATES:
        assert candidate.dry_run is True
        assert candidate.trade_permission is False
        assert candidate.broker_action_allowed is False
        assert candidate.phase2_execution_authorized is False
        assert candidate.same_family_as_breakout_retest is not None


def test_candidate_status_cannot_move_directly_from_draft_to_paper_approved():
    assert validate_status_transition("DRAFT", "LOCKED")
    assert not validate_status_transition("DRAFT", "PAPER_APPROVED")
    assert not validate_status_transition("OBSERVER_ONLY", "PAPER_APPROVED")
    assert validate_status_transition("PHASE0R_PASS", "PAPER_APPROVED")


def test_current_canonical_ea_logic_files_are_not_modified():
    repo_root = Path(__file__).resolve().parents[3]
    protected_paths = [
        "xau-usd/xauusd-phase1/mt5/Experts/Phase1DryRunShell.mq5",
        "xau-usd/xauusd-phase1/mt5/Experts/Phase2ExperimentalDemoExecutor.mq5",
        "xau-usd/xauusd-phase0/src/phase0/strategies/breakout_retest.py",
        "xau-usd/xauusd-phase0/src/phase0/strategies/trend_pullback.py",
        "xau-usd/xauusd-phase0/src/phase0/strategies/range_mr.py",
    ]
    result = subprocess.run(
        ["git", "diff", "--name-only", "--", *protected_paths],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == ""
