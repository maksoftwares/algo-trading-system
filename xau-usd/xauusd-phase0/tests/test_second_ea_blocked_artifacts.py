from __future__ import annotations

import csv
from pathlib import Path

from phase0.constants import SECOND_EA_CAMPAIGN_CANDIDATES
from phase0.second_ea_d2_manifest import build_second_ea_d2_universe_rows


def test_second_ea_final_artifacts_exist_for_every_campaign_candidate(project_root: Path):
    # The campaign completed 2026-06-10: every candidate carries a final verdict
    # from the corrected locked full-window runs, and the pre-run placeholder CSVs
    # are marked superseded. (This test previously pinned the blocked-placeholder
    # state.)
    for candidate in SECOND_EA_CAMPAIGN_CANDIDATES:
        report = project_root / "outputs" / "reports" / f"FIRST_PASS_{candidate}.md"
        text = report.read_text(encoding="utf-8")

        assert "Final verdict:" in text
        assert (
            "Final verdict: FAIL_REJECTED_VERSION_FINAL" in text
            or "Final verdict: PASS_APPROVED_FUTURE_EXPERT_CANDIDATE" in text
        )
        assert "NOT_RUN" not in text

        matrix = project_root / "outputs" / "matrix" / f"matrix_{candidate}.csv"
        era = project_root / "outputs" / "reports" / f"era_slices_{candidate}.csv"
        cost = project_root / "outputs" / "reports" / f"cost_r_{candidate}.csv"
        stops = project_root / "outputs" / "reports" / f"stop_distribution_{candidate}.csv"
        for path in (matrix, era, cost, stops):
            rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
            assert rows
            assert rows[0]["candidate_id"] == candidate
            assert rows[0]["status"] == "SUPERSEDED_SEE_FIRST_PASS"


def test_second_ea_lane_specific_blocked_reports_exist(project_root: Path):
    required = {
        "A1_FULLHIST_FAILURE_MODE_REVIEW.md": "BLOCKED_DATA_READINESS",
        "A2_DIRECTIONAL_BIAS_REPORT.md": "BLOCKED_DATA_READINESS",
        "A3_CROSS_VENUE_WEAKNESS_REPORT.md": "BLOCKED_DATA_READINESS",
        "B1_ANCESTRY_COMPARISON_REPORT.md": "BLOCKED_LANE_A_NOT_COMPLETE",
    }
    for filename, status in required.items():
        text = (project_root / "outputs" / "reports" / filename).read_text(encoding="utf-8")
        assert f"Status: {status}" in text
        assert "No observer/demo/live deployment is authorized." in text

    b1_text = (project_root / "outputs" / "reports" / "B1_ANCESTRY_COMPARISON_REPORT.md").read_text(
        encoding="utf-8"
    )
    assert "SAME_MECHANIC_RETEST" in b1_text
    assert "overlap exceeds 50%" in b1_text


def test_second_ea_d2_manifest_includes_completed_campaign_candidates(project_root: Path):
    # After the 2026-06-10 locked full-window runs, all six campaign candidates
    # have real (rejected) result ledgers and must enter the D2 rejected-candidate
    # universe for future multiplicity accounting. (This test previously asserted
    # their exclusion as blocked placeholders.)
    rows = {row.candidate_id: row for row in build_second_ea_d2_universe_rows(project_root)}

    for candidate in SECOND_EA_CAMPAIGN_CANDIDATES:
        row = rows[candidate]
        assert row.matrix_ledger_status == "NON_EMPTY_RESULT_LEDGER"
        assert row.d2_included == "true"
        assert row.reason == "NON_EMPTY_RESULT_LEDGER_INCLUDED_FOR_D2_UNIVERSE"


def test_second_ea_d2_manifest_includes_rejected_and_same_family_ledgers(project_root: Path):
    rows = {row.candidate_id: row for row in build_second_ea_d2_universe_rows(project_root)}

    rejected = rows["d1_w1_momentum_h4_pullback_v0"]
    assert rejected.matrix_ledger_status == "NON_EMPTY_RESULT_LEDGER"
    assert rejected.d2_included == "true"
    assert rejected.lane == "PRIOR_PHASE0_OR_0R"

    same_family = rows["breakout_retest"]
    assert same_family.matrix_ledger_status == "NON_EMPTY_RESULT_LEDGER"
    assert same_family.d2_included == "true"
    assert same_family.family == "breakout_retest_family"
