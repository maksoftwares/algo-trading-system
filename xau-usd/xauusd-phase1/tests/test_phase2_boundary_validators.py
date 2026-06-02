from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_no_cost_suspended_family_promotion_passes_when_block_is_preserved(tmp_path):
    module = _load_module("verify_no_cost_suspended_family_promotion")
    root = _phase1_fixture(tmp_path)

    result = module.verify_no_cost_suspended_family_promotion(root)

    assert result == 0
    payload = json.loads((root / "outputs" / "reports" / "COST_SUSPENDED_PROMOTION_BLOCKER_REPORT.json").read_text())
    assert payload["status"] == "PASS"


def test_no_cost_suspended_family_promotion_fails_on_positive_authorization(tmp_path):
    module = _load_module("verify_no_cost_suspended_family_promotion")
    root = _phase1_fixture(tmp_path)
    (root / "docs" / "BAD_PROMOTION.md").write_text(
        "COST_SUSPENDED_CANONICAL is execution eligible for paper-mode approved rollout.\n"
        "paper_mode_execution_allowed=true\n",
        encoding="utf-8",
    )

    result = module.verify_no_cost_suspended_family_promotion(root)

    assert result == 1
    payload = json.loads((root / "outputs" / "reports" / "COST_SUSPENDED_PROMOTION_BLOCKER_REPORT.json").read_text())
    assert payload["status"] == "FAIL"
    assert payload["violations"]


def test_phase3_proxy_non_authoritative_passes_with_negative_boundary(tmp_path):
    module = _load_module("verify_phase3_proxy_non_authoritative")
    root = _phase1_fixture(tmp_path)
    phase3 = root.parent / "xauusd-phase3-experimental" / "outputs" / "reports"
    phase3.mkdir(parents=True)
    (phase3 / "PHASE3_COST_MODE_COMPARISON.md").write_text(
        "# Phase 3\n\nOverall status: REVIEW_READY\n\nThis report does not authorize Phase 2.\n",
        encoding="utf-8",
    )

    result = module.verify_phase3_proxy_non_authoritative(root)

    assert result == 0
    payload = json.loads((root / "outputs" / "reports" / "PHASE3_PROXY_NON_AUTHORITATIVE_VERIFICATION.json").read_text())
    assert payload["status"] == "PASS"
    assert payload["canonical_phase2_authorized"] is False


def test_phase3_proxy_non_authoritative_fails_on_phase2_authorization_leak(tmp_path):
    module = _load_module("verify_phase3_proxy_non_authoritative")
    root = _phase1_fixture(tmp_path)
    phase3 = root.parent / "xauusd-phase3-experimental" / "outputs" / "reports"
    phase3.mkdir(parents=True)
    (phase3 / "BAD_PROXY.md").write_text(
        "# Bad\n\nPHASE2_READINESS_REPORT = PASS\ncanonical_phase2_authorized=true\n",
        encoding="utf-8",
    )

    result = module.verify_phase3_proxy_non_authoritative(root)

    assert result == 1
    payload = json.loads((root / "outputs" / "reports" / "PHASE3_PROXY_NON_AUTHORITATIVE_VERIFICATION.json").read_text())
    assert payload["status"] == "FAIL"
    assert payload["violations"]


def test_cost_aware_v2_hypothesis_draft_is_not_locked():
    text = (ROOT.parent / "xauusd-phase0" / "docs" / "hypothesis_breakout_retest_cost_aware_v2_DRAFT.md").read_text(
        encoding="utf-8"
    )

    assert "Status: DRAFT - NOT HASH LOCKED" in text
    assert "Why v1.0 Is Cost-Suspended" in text
    assert "Required Stop-Distance Gate" in text
    assert "Required Cost_R Gate" in text
    assert "Explicit Same-Family Classification" in text
    assert "Measured-Cost Revalidation Requirement" in text


def _phase1_fixture(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    root = repo / "xau-usd" / "xauusd-phase1"
    phase0 = repo / "xau-usd" / "xauusd-phase0"
    (root / "docs").mkdir(parents=True)
    (root / "outputs" / "reports").mkdir(parents=True)
    (phase0 / "outputs" / "reports").mkdir(parents=True)
    _write_status(phase0 / "outputs" / "reports" / "MEASURED_COST_MODEL.md", "PASS")
    _write_status(phase0 / "outputs" / "reports" / "BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md", "FAIL")
    _write_status(phase0 / "outputs" / "reports" / "MEASURED_COST_ASSUMPTION_DELTA.md", "FAIL")
    _write_status(phase0 / "outputs" / "reports" / "MEASURED_COST_REVALIDATION_SANITY_CHECK.md", "CALCULATION_CONFIRMED")
    _write_status(root / "outputs" / "reports" / "PHASE1_ACCEPTANCE_REPORT.md", "PASS")
    _write_status(root / "outputs" / "reports" / "PHASE2_READINESS_REPORT.md", "FAIL")
    (root / "docs" / "EXPERT_LIFECYCLE.md").write_text(
        "breakout_retest_family COST_SUSPENDED_CANONICAL not independent execution eligibility\n",
        encoding="utf-8",
    )
    return root


def _write_status(path: Path, status: str) -> None:
    path.write_text(f"# Report\n\nOverall status: {status}\n", encoding="utf-8")


def _load_module(name: str):
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
