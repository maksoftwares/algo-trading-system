from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase2_demo_preflight_stays_pending_until_real_gates_pass(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "xauusd-phase1"
    reports = root / "outputs" / "reports"
    phase3_reports = root.parent / "xauusd-phase3-experimental" / "outputs" / "reports"
    reports.mkdir(parents=True)
    phase3_reports.mkdir(parents=True)
    _write_readiness(reports / "PHASE2_READINESS_REPORT.md", status="PENDING", pending=True)
    _write_countdown(reports / "PHASE2_DEMO_COUNTDOWN.json", status="DEMO_NOT_READY", pending_gate_count=3)
    _write_summary(reports / "PHASE1_STATUS_SUMMARY.json")
    _write_phase3_status(phase3_reports / "PHASE3_EXPERIMENTAL_STATUS.json")

    output = module.generate_phase2_demo_preflight_report(root)

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    markdown = output.markdown_path.read_text(encoding="utf-8")
    assert output.status == "PENDING"
    assert payload["paper_mode_implementation_authorized"] is False
    assert payload["demo_trading_authorized"] is False
    assert payload["live_trading_authorized"] is False
    assert any(check.name == "phase2_readiness" and check.status == "PENDING" for check in output.checks)
    assert any(check.name == "latest_runtime_boundary" and check.status == "PASS" for check in output.checks)
    assert "Overall status: PENDING" in markdown


def test_phase2_demo_preflight_passes_when_transition_inputs_pass(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "xauusd-phase1"
    reports = root / "outputs" / "reports"
    phase3_reports = root.parent / "xauusd-phase3-experimental" / "outputs" / "reports"
    reports.mkdir(parents=True)
    phase3_reports.mkdir(parents=True)
    _write_readiness(reports / "PHASE2_READINESS_REPORT.md", status="PASS", pending=False)
    _write_countdown(reports / "PHASE2_DEMO_COUNTDOWN.json", status="DEMO_READY_TO_REQUEST_OWNER_APPROVAL", pending_gate_count=0)
    _write_summary(reports / "PHASE1_STATUS_SUMMARY.json")
    _write_phase3_status(phase3_reports / "PHASE3_EXPERIMENTAL_STATUS.json")

    output = module.generate_phase2_demo_preflight_report(root)

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    assert output.status == "PASS"
    assert payload["paper_mode_implementation_authorized"] is True
    assert payload["demo_trading_authorized"] is False
    assert all(check.status == "PASS" for check in output.checks)


def test_phase2_demo_preflight_fails_on_unsafe_runtime_boundary(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "xauusd-phase1"
    reports = root / "outputs" / "reports"
    phase3_reports = root.parent / "xauusd-phase3-experimental" / "outputs" / "reports"
    reports.mkdir(parents=True)
    phase3_reports.mkdir(parents=True)
    _write_readiness(reports / "PHASE2_READINESS_REPORT.md", status="PASS", pending=False)
    _write_countdown(reports / "PHASE2_DEMO_COUNTDOWN.json", status="DEMO_READY_TO_REQUEST_OWNER_APPROVAL", pending_gate_count=0)
    _write_summary(reports / "PHASE1_STATUS_SUMMARY.json", permission="true")
    _write_phase3_status(phase3_reports / "PHASE3_EXPERIMENTAL_STATUS.json")

    output = module.generate_phase2_demo_preflight_report(root)

    assert output.status == "FAIL"
    assert any(check.name == "latest_runtime_boundary" and check.status == "FAIL" for check in output.checks)


def test_phase2_demo_preflight_fails_on_phase3_promotion_leakage(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "xauusd-phase1"
    reports = root / "outputs" / "reports"
    phase3_reports = root.parent / "xauusd-phase3-experimental" / "outputs" / "reports"
    reports.mkdir(parents=True)
    phase3_reports.mkdir(parents=True)
    _write_readiness(reports / "PHASE2_READINESS_REPORT.md", status="PASS", pending=False)
    _write_countdown(reports / "PHASE2_DEMO_COUNTDOWN.json", status="DEMO_READY_TO_REQUEST_OWNER_APPROVAL", pending_gate_count=0)
    _write_summary(reports / "PHASE1_STATUS_SUMMARY.json")
    _write_phase3_status(
        phase3_reports / "PHASE3_EXPERIMENTAL_STATUS.json",
        authorized_for_deployment=True,
    )

    output = module.generate_phase2_demo_preflight_report(root)

    assert output.status == "FAIL"
    assert any(check.name == "phase3_separation" and check.status == "FAIL" for check in output.checks)


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_phase2_demo_preflight_report.py"
    spec = importlib.util.spec_from_file_location("generate_phase2_demo_preflight_report", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_phase2_demo_preflight_report"] = module
    spec.loader.exec_module(module)
    return module


def _write_readiness(path: Path, status: str, pending: bool) -> None:
    gate_status = "PENDING" if pending else "PASS"
    path.write_text(
        "\n".join(
            [
                "# Phase 2 Readiness Report",
                "",
                f"Overall status: {status}",
                "",
                "## Gates",
                "",
                "| Gate | Status | Evidence |",
                "| --- | --- | --- |",
                f"| Project owner approval | {gate_status} | owner approval evidence |",
                f"| VPS selection | {gate_status} | vps selection evidence |",
                f"| VPS latency evidence | {gate_status} | latency evidence |",
                f"| VPS first-day verification | {gate_status} | first-day evidence |",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_countdown(path: Path, status: str, pending_gate_count: int) -> None:
    path.write_text(
        json.dumps(
            {
                "status": status,
                "pending_gate_count": pending_gate_count,
                "broker_execution_authorized": False,
                "live_trading_authorized": False,
            }
        ),
        encoding="utf-8",
    )


def _write_summary(path: Path, permission: str = "false") -> None:
    path.write_text(
        json.dumps(
            {
                "runtime": {
                    "latest_row": {
                        "bar_time": "2026.05.28 13:30:00",
                        "dry_run": "true",
                        "trade_permission": permission,
                        "server_time_status": "CLOCK_OK",
                    }
                }
            }
        ),
        encoding="utf-8",
    )


def _write_phase3_status(path: Path, authorized_for_deployment: bool = False) -> None:
    path.write_text(
        json.dumps(
            {
                "real_phase2_readiness": "PENDING",
                "authorized_for_deployment": authorized_for_deployment,
                "broker_action_code_allowed": False,
                "mt5_runtime_touched": False,
                "owner_approval_flow": "excluded_from_real_phase2_phase3_approval_flow",
                "demo_rehearsal": {"can_start_real_demo": False},
                "completion_audit": {"demo_authorized": False},
            }
        ),
        encoding="utf-8",
    )
