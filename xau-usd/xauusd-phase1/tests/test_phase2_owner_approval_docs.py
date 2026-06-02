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

    assert "| Local runtime first-day verification | PENDING |" in checklist
    assert "periodic scheduler" in checklist
    assert "AND local runtime first-day verification = PASS" in checklist


def test_demo_transition_runbook_keeps_phase2_go_no_go_boundary():
    runbook = (ROOT / "docs" / "PHASE2_DEMO_TRANSITION_RUNBOOK.md").read_text(encoding="utf-8")

    assert "Status: PREPARED_NOT_AUTHORIZED" in runbook
    assert "outputs/reports/PHASE2_READINESS_REPORT.md is the sole readiness authority" in runbook
    assert "Phase 3 experimental reports may be used only as design input" in runbook
    assert "Do not proceed unless every item above is PASS" in runbook
    assert "paper-shadow only" in runbook
    assert "OrderSend" in runbook
    assert "Live-capital authorization requires a later phase" in runbook


def test_owner_vps_readiness_package_tracks_remaining_phase2_blockers():
    package = (ROOT / "docs" / "PHASE2_OWNER_VPS_READINESS_PACKAGE.md").read_text(encoding="utf-8")

    assert "Overall status: LOCAL_RUNTIME_SELECTED_OBJECTIVE_GATES_PENDING" in package
    assert "outputs/reports/PHASE2_READINESS_REPORT.md" in package
    assert "Can canonical Phase 2 be marked approved now? | NO" in package
    assert "Measured cost model | PASS" in package
    assert "Measured-cost revalidation | FAIL" in package
    assert "Measured-cost assumption delta | FAIL" in package
    assert "Cost sanity check | CALCULATION_CONFIRMED" in package
    assert "Formal Phase 2 | BLOCKED_BY_CONFIRMED_COST_FAILURE" in package
    assert "LOCAL_SYSTEM_RUNTIME" in package
    assert "Local runtime first-day verification | PENDING" in package
    assert "Project owner approval | PENDING" in package
    assert "PHASE2_VPS_SELECTION_MATRIX.md" in package
    assert "generate_phase2_vps_latency_report.py --provider LOCAL_SYSTEM_RUNTIME" in package
    assert "PHASE2_OWNER_APPROVAL.md" in package
    assert "PHASE2_PAPER_PREP_APPROVED" in package
    assert "no live capital" in package
    assert "broker execution" in package
