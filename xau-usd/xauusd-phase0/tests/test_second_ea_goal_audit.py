from __future__ import annotations

import json
from pathlib import Path

from phase0.second_ea_goal_audit import generate_second_ea_goal_audit


def test_second_ea_goal_audit_reports_campaign_complete_state(project_root: Path):
    # The campaign completed on 2026-06-10: all six locked candidates carry final
    # verdicts from the corrected locked full-window runs, the doc-review input
    # exists, and the final report carries the Changed Files And Commands section,
    # so the live-project audit must be PASS. (This test previously pinned the
    # mid-campaign BLOCKED state.)
    audit = generate_second_ea_goal_audit(project_root)
    statuses = {item.requirement_id: item.status for item in audit.requirements}

    assert audit.status == "PASS"
    assert statuses["PRE-1"] == "PASS"
    assert statuses["DOD-1"] == "PASS"
    assert statuses["DOD-2"] == "PASS"
    assert statuses["DOD-3"] == "PASS"
    assert statuses["DOD-4"] == "PASS"
    assert statuses["DOD-5"] == "PASS"
    assert statuses["DOD-6"] == "PASS"
    assert statuses["DOD-7"] == "PASS"
    assert statuses["DOD-8"] == "PASS"
    assert statuses["DOD-9"] == "PASS"
    assert statuses["DOD-10"] == "PASS"
    assert statuses["DOD-11"] == "PASS"
    assert statuses["DOD-12"] == "PASS"
    assert statuses["DOD-13"] == "PASS"

    report_text = audit.report_path.read_text(encoding="utf-8")
    assert "A status other than `PASS` means the full second-EA goal remains incomplete." in report_text
    assert "matrix_runs_allowed=true" in report_text
    assert "hash_status=LOCKED" in report_text
    assert "FAIL_REJECTED_VERSION_FINAL" in report_text
    assert "vacuously satisfied" in report_text


def test_second_ea_goal_audit_writes_json(project_root: Path):
    audit = generate_second_ea_goal_audit(project_root)
    payload = json.loads(audit.json_path.read_text(encoding="utf-8"))

    assert payload["status"] == "PASS"
    assert len(payload["requirements"]) == 14
    assert {item["requirement_id"] for item in payload["requirements"]} == {
        "PRE-1",
        *(f"DOD-{index}" for index in range(1, 14)),
    }
