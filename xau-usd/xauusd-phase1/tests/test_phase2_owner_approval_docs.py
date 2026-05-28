from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_owner_approval_docs_require_vps_first_day_scheduler_evidence():
    template = (ROOT / "docs" / "PHASE2_OWNER_APPROVAL_TEMPLATE.md").read_text(encoding="utf-8")
    draft = (ROOT / "docs" / "PHASE2_OWNER_APPROVAL_DRAFT.md").read_text(encoding="utf-8")

    assert "VPS first-day verification" in template
    assert "outputs/reports/PHASE2_VPS_FIRST_DAY_VERIFICATION.md" in template
    assert "outputs/reports/vps_periodic_task.txt" in template
    assert "symbol_normalized_round_retest_v0" in template

    assert "| VPS first-day verification | PENDING | PASS |" in draft
    assert "verified periodic readiness task" in draft
    assert "outputs/reports/PHASE2_VPS_FIRST_DAY_VERIFICATION.md" in draft


def test_authorization_checklist_keeps_first_day_verification_as_phase2_gate():
    checklist = (ROOT / "docs" / "PHASE2_AUTHORIZATION_CHECKLIST.md").read_text(encoding="utf-8")

    assert "| VPS first-day verification | PENDING |" in checklist
    assert "periodic scheduler" in checklist
    assert "AND VPS first-day verification = PASS" in checklist
