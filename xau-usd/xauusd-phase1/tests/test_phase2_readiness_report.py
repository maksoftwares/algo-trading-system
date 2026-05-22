from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase2_readiness_is_pending_until_soak_and_approval_pass(tmp_path):
    module = _load_module()
    root = tmp_path / "phase1"
    report_dir = root / "outputs" / "reports"
    (root / "docs").mkdir(parents=True)
    report_dir.mkdir(parents=True)
    _write_phase0_cost_artifacts(root)
    _write_phase2_docs(root)
    _write_markdown_status(report_dir / "PHASE1_ACCEPTANCE_REPORT.md", "PENDING")
    _write_markdown_status(report_dir / "PHASE1_REVIEW_INDEX.md", "PENDING")
    _write_summary(report_dir / "PHASE1_STATUS_SUMMARY.json", progress=5.28)

    output = module.generate_phase2_readiness_report(root, report_dir / "PHASE2_READINESS_REPORT.md")

    report = output.report_path.read_text(encoding="utf-8")
    assert output.status == "PENDING"
    assert "Phase 2 preparation may continue" in report
    assert any(item.gate == "Five trading day soak" and item.status == "PENDING" for item in output.items)
    assert any(item.gate == "Project owner approval" and item.status == "PENDING" for item in output.items)


def test_phase2_readiness_passes_when_all_gates_pass(tmp_path):
    module = _load_module()
    root = tmp_path / "phase1"
    report_dir = root / "outputs" / "reports"
    (root / "docs").mkdir(parents=True)
    report_dir.mkdir(parents=True)
    _write_phase0_cost_artifacts(root, include_measured=True)
    approval = report_dir / "PHASE2_OWNER_APPROVAL.md"
    _write_phase2_docs(root)
    _write_markdown_status(report_dir / "PHASE1_ACCEPTANCE_REPORT.md", "PASS")
    _write_markdown_status(report_dir / "PHASE1_REVIEW_INDEX.md", "PASS")
    _write_summary(report_dir / "PHASE1_STATUS_SUMMARY.json", progress=100.0)
    approval.write_text("PHASE2_PAPER_PREP_APPROVED\n", encoding="utf-8")

    output = module.generate_phase2_readiness_report(root, report_dir / "PHASE2_READINESS_REPORT.md", approval)

    assert output.status == "PASS"
    assert all(item.status == "PASS" for item in output.items)


def test_phase2_readiness_fails_when_latest_boundary_is_not_locked(tmp_path):
    module = _load_module()
    root = tmp_path / "phase1"
    report_dir = root / "outputs" / "reports"
    (root / "docs").mkdir(parents=True)
    report_dir.mkdir(parents=True)
    _write_phase0_cost_artifacts(root, include_measured=True)
    _write_phase2_docs(root)
    _write_markdown_status(report_dir / "PHASE1_ACCEPTANCE_REPORT.md", "PASS")
    _write_markdown_status(report_dir / "PHASE1_REVIEW_INDEX.md", "PASS")
    _write_summary(report_dir / "PHASE1_STATUS_SUMMARY.json", progress=100.0, permission="true")

    output = module.generate_phase2_readiness_report(root, report_dir / "PHASE2_READINESS_REPORT.md")

    assert output.status == "FAIL"
    assert any(item.gate == "Latest dry-run boundary" and item.status == "FAIL" for item in output.items)


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_phase2_readiness_report.py"
    spec = importlib.util.spec_from_file_location("generate_phase2_readiness_report", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_phase2_readiness_report"] = module
    spec.loader.exec_module(module)
    return module


def _write_markdown_status(path: Path, status: str) -> None:
    path.write_text(f"# Report\n\nOverall status: {status}\n", encoding="utf-8")


def _write_summary(path: Path, progress: float, permission: str = "false") -> None:
    path.write_text(
        json.dumps(
            {
                "status": {
                    "log_verification": "PASS",
                    "soak_analysis": "PASS",
                    "runtime_health": "PASS",
                    "would_signal": "PASS",
                    "acceptance": "PENDING" if progress < 100 else "PASS",
                },
                "runtime": {
                    "decision_rows": 82,
                    "latest_row": {
                        "bar_time": "2026.05.21 20:05:00",
                        "dry_run": "true",
                        "trade_permission": permission,
                        "server_time_status": "CLOCK_OK",
                    },
                },
                "soak": {
                    "progress_pct": progress,
                    "observed_days": 5 if progress >= 100 else 0.26,
                    "required_days": 5,
                },
                "would_signal": {
                    "rows": 4,
                    "clusters": 4,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_phase0_cost_artifacts(phase1_root: Path, include_measured: bool = False) -> None:
    phase0_root = phase1_root.parent / "xauusd-phase0"
    docs = phase0_root / "docs"
    reports = phase0_root / "outputs" / "reports"
    docs.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    (docs / "COST_REPORTING_POLICY.md").write_text("# Cost policy\n", encoding="utf-8")
    (reports / "FIXED_NOTIONAL_REPORT.md").write_text("# Fixed notional\n\nOverall status: PASS\n", encoding="utf-8")
    if include_measured:
        (reports / "MEASURED_COST_MODEL.md").write_text("# Measured cost\n\nOverall status: PASS\n", encoding="utf-8")
        (reports / "BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md").write_text(
            "# Revalidation\n\nOverall status: PASS\n",
            encoding="utf-8",
        )


def _write_phase2_docs(root: Path) -> None:
    docs = root / "docs"
    (docs / "PHASE2_DRY_RUN_TO_PAPER_PREP_SPEC.md").write_text("# Phase 2\n", encoding="utf-8")
    (docs / "PHASE2_COST_MEASUREMENT_PROTOCOL.md").write_text(
        "# Cost\n\ncost-measurement experiment\n\nMIN_NET_EXPECTANCY_R_AFTER_MEASURED_COST = +0.10R\n",
        encoding="utf-8",
    )
    (docs / "PHASE2_SINGLE_EDGE_RISK_PLAN.md").write_text(
        "# Risk\n\nsingle-edge same-family +0.10R\n",
        encoding="utf-8",
    )
    (docs / "PHASE2_OPERATIONS_PREP.md").write_text(
        "# Ops\n\nExternal Health Monitor Spec\n\nDisaster Recovery Runbook\n\nCapital Allocation Ladder\n",
        encoding="utf-8",
    )
