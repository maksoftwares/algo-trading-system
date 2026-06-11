from __future__ import annotations

from pathlib import Path

from phase0.second_ea_campaign_status import (
    CampaignMilestone,
    CampaignStatusReport,
    evaluate_second_ea_campaign_milestones,
    render_campaign_status,
)


def test_second_ea_campaign_status_reflects_completed_campaign_state(project_root: Path):
    # Campaign completed 2026-06-10: Lane B hypotheses are locked and run, and the
    # goal audit is PASS, so M7 onward must reflect completion. (This test
    # previously pinned the mid-campaign state where Lane B was blocked.)
    milestones = evaluate_second_ea_campaign_milestones(
        project_root,
        "2026-06-10T00:00:00+00:00",
    )
    by_id = {milestone.milestone_id: milestone for milestone in milestones}

    assert list(by_id) == [f"M{index}" for index in range(11)]
    assert by_id["M0"].status == "PASS"
    assert by_id["M1"].status == "OWNER_ACCEPTED_PARTIAL"
    assert "Owner accepted partial data" in by_id["M1"].blocking_reason
    assert by_id["M2"].status == "PASS"
    assert "generated low-frequency gate-test evidence is PASS" in by_id["M2"].blocking_reason
    assert by_id["M3"].status == "PASS"
    assert by_id["M4"].status == "PASS"
    assert by_id["M5"].status == "PASS"
    assert by_id["M6"].status == "PASS"
    assert by_id["M7"].status == "PASS"
    assert by_id["M8"].status == "PASS"


def test_second_ea_campaign_status_render_includes_required_columns_and_boundary(tmp_path: Path):
    report = CampaignStatusReport(
        status="BLOCKED",
        generated_at_utc="2026-06-10T00:00:00+00:00",
        report_path=tmp_path / "status.md",
        milestones=(
            CampaignMilestone(
                milestone_id="M0",
                milestone_name="Safety boundary and no-runtime-touch audit",
                status="PASS",
                blocking_reason="Static safety audit status is PASS.",
                last_updated_utc="2026-06-10T00:00:00+00:00",
                output_file="outputs/reports/SECOND_EA_NO_RUNTIME_TOUCH_AUDIT.md",
            ),
        ),
    )

    text = render_campaign_status(report)

    assert "Status: BLOCKED" in text
    assert "| milestone_id | milestone_name | status | blocking_reason | last_updated_utc | output_file |" in text
    assert "scripts/generate_second_ea_campaign_status.py" in text
    assert "no observer deployment" in text
    assert "MT5 runtime access" in text
