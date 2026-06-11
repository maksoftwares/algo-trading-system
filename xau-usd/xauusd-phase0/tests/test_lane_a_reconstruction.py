from __future__ import annotations

import json
from pathlib import Path

from phase0.lane_a_reconstruction import generate_lane_a_reconstruction_notes


def test_lane_a_reconstruction_notes_capture_v0_baselines(project_root: Path):
    notes = generate_lane_a_reconstruction_notes(project_root)

    assert notes.status == "PASS_RECONSTRUCTED_FOR_PARTIAL_PASS"
    assert len(notes.rows) == 3
    assert {row.source_status for row in notes.rows} == {"PASS"}
    assert {row.reconstruction_status for row in notes.rows} == {"COMPLETE_BYTE_IDENTICAL_ALIAS"}
    for row in notes.rows:
        assert len(row.source_hypothesis_sha256) == 64
        assert len(row.source_strategy_sha256) == 64
        assert row.v1_hypothesis_path.startswith("docs/hypothesis_")
        assert row.v1_strategy_path.startswith("src/phase0/strategies/")

    report = notes.report_path.read_text(encoding="utf-8")
    assert "Status: PASS_RECONSTRUCTED_FOR_PARTIAL_PASS" in report
    assert "byte-identically where possible" in report


def test_lane_a_reconstruction_notes_write_json(project_root: Path):
    notes = generate_lane_a_reconstruction_notes(project_root)
    payload = json.loads(notes.json_path.read_text(encoding="utf-8"))

    assert payload["status"] == "PASS_RECONSTRUCTED_FOR_PARTIAL_PASS"
    assert len(payload["rows"]) == 3
    assert payload["rows"][0]["candidate_id"] == "d1_momentum_h4_pullback_v1_fullhist"
