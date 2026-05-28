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


def test_owner_approval_docs_reject_mixed_live_scope_wording():
    template = (ROOT / "docs" / "PHASE2_OWNER_APPROVAL_TEMPLATE.md").read_text(encoding="utf-8")
    draft = (ROOT / "docs" / "PHASE2_OWNER_APPROVAL_DRAFT.md").read_text(encoding="utf-8")

    for text in (template, draft):
        assert "no live capital" in text
        assert "before every objective gate is PASS" in text
        assert "early/invalid" in text
        assert "plus live capital" in text
        assert "live trading" in text
        assert "broker execution" in text
        assert "broker-side execution" in text
        assert "order execution" in text
        assert "real money" in text


def test_authorization_checklist_keeps_first_day_verification_as_phase2_gate():
    checklist = (ROOT / "docs" / "PHASE2_AUTHORIZATION_CHECKLIST.md").read_text(encoding="utf-8")

    assert "| VPS first-day verification | PENDING |" in checklist
    assert "periodic scheduler" in checklist
    assert "AND VPS first-day verification = PASS" in checklist


def test_demo_transition_runbook_keeps_phase2_go_no_go_boundary():
    runbook = (ROOT / "docs" / "PHASE2_DEMO_TRANSITION_RUNBOOK.md").read_text(encoding="utf-8")

    assert "Status: PREPARED_NOT_AUTHORIZED" in runbook
    assert "outputs/reports/PHASE2_READINESS_REPORT.md is the sole readiness authority" in runbook
    assert "Phase 3 experimental reports may be used only as design input" in runbook
    assert "Do not proceed unless every item above is PASS" in runbook
    assert "paper-shadow only" in runbook
    assert "OrderSend" in runbook
    assert "Live-capital authorization requires a later phase" in runbook
