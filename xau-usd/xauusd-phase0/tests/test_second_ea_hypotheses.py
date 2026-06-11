from __future__ import annotations

import json
from pathlib import Path

from phase0.constants import SECOND_EA_CAMPAIGN_CANDIDATES
from phase0.hashing import sha256_file
from phase0.second_ea_hypotheses import (
    validate_second_ea_campaign_hypotheses,
    validate_second_ea_hypothesis,
)


def test_second_ea_hypothesis_validator_accepts_complete_locked_doc(tmp_path: Path):
    hypothesis = tmp_path / "hypothesis_d1_momentum_h4_pullback_v1_fullhist.md"
    hypothesis.write_text(_complete_hypothesis("d1_momentum_h4_pullback_v1_fullhist"), encoding="utf-8")
    lock = tmp_path / "hypothesis_d1_momentum_h4_pullback_v1_fullhist.sha256.json"
    lock.write_text(
        json.dumps({"status": "LOCKED", "sha256_hash": sha256_file(hypothesis)}),
        encoding="utf-8",
    )

    result = validate_second_ea_hypothesis(hypothesis, lock)

    assert result.status == "PASS"
    assert result.errors == ()


def test_second_ea_hypothesis_validator_rejects_placeholders(tmp_path: Path):
    hypothesis = tmp_path / "hypothesis_xau_london_open_expansion_flow_v0.md"
    hypothesis.write_text(
        _complete_hypothesis("xau_london_open_expansion_flow_v0")
        + "\nThis field can be optimized later maybe tune.\n",
        encoding="utf-8",
    )

    result = validate_second_ea_hypothesis(hypothesis)

    assert result.status == "FAIL"
    assert any("placeholder/prohibited" in error for error in result.errors)


def test_second_ea_hypothesis_validator_rejects_missing_required_field(tmp_path: Path):
    hypothesis = tmp_path / "hypothesis_xau_lbma_am_fix_flow_v0.md"
    text = _complete_hypothesis("xau_lbma_am_fix_flow_v0").replace(
        "expected_median_stop_points: 450\n",
        "",
    )
    hypothesis.write_text(text, encoding="utf-8")

    result = validate_second_ea_hypothesis(hypothesis)

    assert result.status == "FAIL"
    assert "missing required field: expected_median_stop_points" in result.errors


def test_second_ea_hypothesis_validator_rejects_structurally_fragile_stop(tmp_path: Path):
    hypothesis = tmp_path / "hypothesis_xau_london_open_expansion_flow_v0.md"
    text = _complete_hypothesis("xau_london_open_expansion_flow_v0").replace(
        "expected_median_stop_points: 450\n",
        "expected_median_stop_points: 200 points\n",
    )
    hypothesis.write_text(text, encoding="utf-8")

    result = validate_second_ea_hypothesis(hypothesis)

    assert result.status == "FAIL"
    assert any(
        "G9A_pre_run_structural_cost" in error
        and "BLOCKED_COST_FRAGILE_BY_DESIGN" in error
        for error in result.errors
    )


def test_second_ea_hypothesis_validator_rejects_structurally_fragile_cost_r(tmp_path: Path):
    hypothesis = tmp_path / "hypothesis_xau_lbma_am_fix_flow_v0.md"
    text = _complete_hypothesis("xau_lbma_am_fix_flow_v0").replace(
        "expected_cost_R_at_measured_50_75_spread: 0.12\n",
        "expected_cost_R_at_measured_50_75_spread: 0.35R\n",
    )
    hypothesis.write_text(text, encoding="utf-8")

    result = validate_second_ea_hypothesis(hypothesis)

    assert result.status == "FAIL"
    assert any(
        "G9A_pre_run_structural_cost" in error
        and "BLOCKED_COST_FRAGILE_BY_DESIGN" in error
        for error in result.errors
    )


def test_second_ea_hypothesis_validator_rejects_stale_lock(tmp_path: Path):
    hypothesis = tmp_path / "hypothesis_xau_comex_settlement_flow_v0.md"
    hypothesis.write_text(_complete_hypothesis("xau_comex_settlement_flow_v0"), encoding="utf-8")
    lock = tmp_path / "hypothesis_xau_comex_settlement_flow_v0.sha256.json"
    lock.write_text(json.dumps({"status": "LOCKED", "sha256_hash": "0" * 64}), encoding="utf-8")

    result = validate_second_ea_hypothesis(hypothesis, lock)

    assert result.status == "FAIL"
    assert "lock SHA256 does not match current hypothesis file" in result.errors


def test_second_ea_hypothesis_validator_rejects_lane_b_missing_ancestry_comparison(tmp_path: Path):
    hypothesis = tmp_path / "hypothesis_xau_london_open_expansion_flow_v0.md"
    text = _complete_hypothesis("xau_london_open_expansion_flow_v0").replace(
        "ancestry_comparison: distinct event-clock thesis; compared against rejected Asia/London breakout variants.\n",
        "",
    )
    hypothesis.write_text(text, encoding="utf-8")

    result = validate_second_ea_hypothesis(hypothesis)

    assert result.status == "FAIL"
    assert any("ancestry_comparison" in error for error in result.errors)


def test_second_ea_hypothesis_validator_rejects_lane_b_m5_entry_trigger(tmp_path: Path):
    hypothesis = tmp_path / "hypothesis_xau_comex_settlement_flow_v0.md"
    text = _complete_hypothesis("xau_comex_settlement_flow_v0").replace(
        "execution_timeframe: H1\n",
        "execution_timeframe: M5\n",
    )
    hypothesis.write_text(text, encoding="utf-8")

    result = validate_second_ea_hypothesis(hypothesis)

    assert result.status == "FAIL"
    assert any("must not use an M1/M5 entry trigger" in error for error in result.errors)


def test_second_ea_campaign_hypothesis_validation_passes_project_files(project_root: Path):
    # All six campaign hypotheses (Lane A 2026-06-10 by Codex, Lane B 2026-06-10
    # by the reviewer) are authored and SHA256-locked in docs/, so the live
    # project validation must PASS. This test previously pinned the pre-Lane-B
    # BLOCKED state.
    result = validate_second_ea_campaign_hypotheses(project_root)

    assert result.status == "PASS"
    assert len(result.candidate_results) == 6
    assert all(candidate.status == "PASS" for candidate in result.candidate_results)
    assert "hypothesis file not found" not in result.report_path.read_text(encoding="utf-8")


def test_second_ea_campaign_hypothesis_validation_passes_all_locked_files(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()
    for candidate in SECOND_EA_CAMPAIGN_CANDIDATES:
        hypothesis = docs / f"hypothesis_{candidate}.md"
        hypothesis.write_text(_complete_hypothesis(candidate), encoding="utf-8")
        lock = docs / f"hypothesis_{candidate}.sha256.json"
        lock.write_text(
            json.dumps({"status": "LOCKED", "sha256_hash": sha256_file(hypothesis)}),
            encoding="utf-8",
        )

    result = validate_second_ea_campaign_hypotheses(tmp_path)

    assert result.status == "PASS"
    assert all(candidate.status == "PASS" for candidate in result.candidate_results)
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))
    assert payload["status"] == "PASS"


def _complete_hypothesis(candidate_id: str) -> str:
    return "\n".join(
        [
            f"# Hypothesis {candidate_id}",
            "",
            f"candidate_id: {candidate_id}",
            "candidate_version: v0",
            "mechanic_family: structural_flow",
            "same_family_as_breakout_retest: no",
            "entry_decision_timeframe: H1",
            "execution_timeframe: H1",
            "expected_median_hold_hours: 8",
            "expected_decisions_per_week: 5",
            "expected_trades_per_year: 80",
            "expected_median_stop_points: 450",
            "expected_cost_R_at_measured_50_75_spread: 0.12",
            "market_behavior_thesis: flow anchored movement can persist after the event.",
            "participants_or_flow_mechanism: institutional benchmark or session flow.",
            "event_clock_id: xau_london_open",
            "ancestry_comparison: distinct event-clock thesis; compared against rejected Asia/London breakout variants.",
            "mechanical_entry_rules: fixed event-clock rule with completed H1 confirmation.",
            "mechanical_exit_rules: exit at stop, target, or fixed time limit.",
            "stop_model: ATR anchored stop with absolute minimum distance.",
            "target_model: fixed R target.",
            "risk_model: fixed notional R accounting.",
            "forbidden_filters: no post-result filters, no news discretion, no session cherry-pick.",
            "falsification_criteria: fail if locked low-frequency gates fail.",
            "data_window: broker-specific windows ending no later than 2025-06-30.",
            "true_holdout_exclusion: true",
            "expected_failure_modes: dead modern era, broker-only strength, cost fragility.",
            "D2_family_label: second_ea_structural_flow",
            "author: Codex",
            "created_utc: 2026-06-10T00:00:00Z",
            "sha256_hash: SELF_HASH_EXCLUDED",
            "status: LOCKED",
            "",
        ]
    )
