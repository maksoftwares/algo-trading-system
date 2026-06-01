from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_readiness_consistency_passes_for_owner_accepted_soak_and_pending_phase2(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "xauusd-phase1"
    reports = root / "outputs" / "reports"
    phase0_reports = root.parent / "xauusd-phase0" / "outputs" / "reports"
    reports.mkdir(parents=True)
    phase0_reports.mkdir(parents=True)
    _write_summary(reports / "PHASE1_STATUS_SUMMARY.json")
    _write_acceptance(reports / "PHASE1_ACCEPTANCE_REPORT.md", "PASS")
    _write_readiness(reports / "PHASE2_READINESS_REPORT.md")
    _write_markdown_status(phase0_reports / "MEASURED_COST_MODEL.md", "PENDING")
    _write_markdown_status(phase0_reports / "BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md", "PENDING")
    _write_markdown_status(phase0_reports / "MEASURED_COST_ASSUMPTION_DELTA.md", "PENDING")
    (reports / "PHASE2_DEMO_COUNTDOWN.json").write_text(
        json.dumps(
            {
                "paper_mode_authorized": False,
                "demo_trading_authorized": False,
                "live_trading_authorized": False,
                "broker_execution_authorized": False,
            }
        ),
        encoding="utf-8",
    )
    (reports / "PHASE2_DEMO_PREFLIGHT.json").write_text(
        json.dumps({"paper_mode_implementation_authorized": False}),
        encoding="utf-8",
    )
    (reports / "PHASE2_DEMO_ACCOUNT_ISOLATION.json").write_text(
        json.dumps(
            {
                "paper_mode_authorized": False,
                "demo_trading_authorized": False,
                "live_trading_authorized": False,
                "broker_execution_authorized": False,
            }
        ),
        encoding="utf-8",
    )

    output = module.verify_readiness_consistency(root)

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    assert output.status == "PASS"
    assert payload["phase2_readiness_status"] == "PENDING"
    assert all(check.status == "PASS" for check in output.checks)


def test_readiness_consistency_fails_if_demo_gets_authorized_while_phase2_pending(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "xauusd-phase1"
    reports = root / "outputs" / "reports"
    phase0_reports = root.parent / "xauusd-phase0" / "outputs" / "reports"
    reports.mkdir(parents=True)
    phase0_reports.mkdir(parents=True)
    _write_summary(reports / "PHASE1_STATUS_SUMMARY.json")
    _write_acceptance(reports / "PHASE1_ACCEPTANCE_REPORT.md", "PASS")
    _write_readiness(reports / "PHASE2_READINESS_REPORT.md")
    _write_markdown_status(phase0_reports / "MEASURED_COST_MODEL.md", "PENDING")
    _write_markdown_status(phase0_reports / "BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md", "PENDING")
    _write_markdown_status(phase0_reports / "MEASURED_COST_ASSUMPTION_DELTA.md", "PENDING")
    (reports / "PHASE2_DEMO_COUNTDOWN.json").write_text(
        json.dumps({"paper_mode_authorized": True, "demo_trading_authorized": False}),
        encoding="utf-8",
    )
    (reports / "PHASE2_DEMO_PREFLIGHT.json").write_text(
        json.dumps({"paper_mode_implementation_authorized": False}),
        encoding="utf-8",
    )

    output = module.verify_readiness_consistency(root)

    assert output.status == "FAIL"
    assert any(check.name == "demo_authorization_boundary" and check.status == "FAIL" for check in output.checks)


def _write_summary(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "status": {"acceptance": "PASS"},
                "soak": {
                    "owner_accepted_active_market_soak_pass": True,
                    "original_active_market_target_hours": 72.0,
                    "owner_accepted_active_market_target_hours": 56.0,
                    "observed_longest_active_market_hours": 56.08,
                    "phase1_active_market_acceptance_status": "PASS_OWNER_ACCEPTED_THRESHOLD",
                    "original_required_uninterrupted_streak_hours": 72.0,
                    "required_uninterrupted_streak_hours": 56.0,
                    "active_market_streak_hours": 56.08,
                    "code_freeze_pass": True,
                    "process_code_freeze_pass": False,
                    "process_uptime_streak_hours": 6.38,
                    "required_code_freeze_hours": 96.0,
                },
            }
        ),
        encoding="utf-8",
    )


def _write_acceptance(path: Path, status: str) -> None:
    path.write_text(
        "\n".join(
            [
                "# Phase 1 Acceptance",
                "",
                f"Overall status: {status}",
                "",
                "Active-market soak: PASS via owner-accepted 56h threshold; original 72h target waived for Phase 1 dry-run closure only.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_readiness(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Phase 2 Readiness",
                "",
                "Overall status: PENDING",
                "",
                "## Gates",
                "",
                "| Gate | Status | Evidence |",
                "| --- | --- | --- |",
                "| Active-market 72-hour soak | PASS | Active-market soak: PASS via owner-accepted 56h threshold; original 72h target waived for Phase 1 dry-run closure only. |",
                "| Code-freeze 96-hour gate | PASS | Current gate is code-freeze marker age only; process uptime after restart is informational. |",
                "| Measured cost model | PENDING | waiting |",
                "| Measured-cost revalidation | PENDING | waiting |",
                "| Measured-cost assumption delta | PENDING | waiting |",
                "| Project owner approval | PENDING | waiting |",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_markdown_status(path: Path, status: str) -> None:
    path.write_text(f"# Report\n\nOverall status: {status}\n", encoding="utf-8")


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "verify_readiness_consistency.py"
    spec = importlib.util.spec_from_file_location("verify_readiness_consistency", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["verify_readiness_consistency"] = module
    spec.loader.exec_module(module)
    return module
