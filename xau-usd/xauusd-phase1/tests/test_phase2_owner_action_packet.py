from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_owner_action_packet_summarizes_wait_gates_and_owner_steps(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "xauusd-phase1"
    report_dir = root / "outputs" / "reports"
    docs = root / "docs"
    report_dir.mkdir(parents=True)
    docs.mkdir(parents=True)
    _write_countdown(report_dir / "PHASE2_DEMO_COUNTDOWN.json")
    _write_status(report_dir / "PHASE2_READINESS_REPORT.md", "PENDING")
    _write_status(report_dir / "PHASE2_DEMO_PREFLIGHT_REPORT.md", "PENDING")
    _write_status(report_dir / "PHASE2_VPS_FIRST_DAY_VERIFICATION.md", "PENDING")
    _write_status(docs / "PHASE2_VPS_SELECTION_MATRIX.md", "PENDING")
    (docs / "PHASE2_OWNER_APPROVAL_DRAFT.md").write_text("# Draft\n", encoding="utf-8")

    output = module.generate_phase2_owner_action_packet(root)

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    markdown = output.markdown_path.read_text(encoding="utf-8")
    assert output.status == "WAITING_AND_OWNER_ACTION_REQUIRED"
    assert output.owner_action_count == 4
    assert payload["paper_mode_authorized"] is False
    assert payload["demo_trading_authorized"] is False
    assert any(item["title"] == "Select VPS provider, region, and plan" for item in payload["owner_checklist"])
    assert payload["owner_templates"]["vps_selection_decision"].endswith(
        "docs\\templates\\phase2_vps_selection_decision.template.md"
    ) or payload["owner_templates"]["vps_selection_decision"].endswith(
        "docs/templates/phase2_vps_selection_decision.template.md"
    )
    assert "capture_phase2_vps_latency_evidence.ps1" in payload["commands"]["capture_vps_latency"]
    assert "-SampleCount 20" in payload["commands"]["capture_vps_latency"]
    assert "Copy-Item docs\\templates\\vps_ntp_sync.template.txt" in markdown
    assert "phase2_vps_selection_decision.template.md" in markdown
    assert "This packet is an owner handoff only" in markdown


def test_owner_action_packet_ready_for_approval_when_wait_and_owner_actions_clear(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "xauusd-phase1"
    report_dir = root / "outputs" / "reports"
    docs = root / "docs"
    report_dir.mkdir(parents=True)
    docs.mkdir(parents=True)
    _write_countdown(
        report_dir / "PHASE2_DEMO_COUNTDOWN.json",
        owner_actions=[],
        wait_status="PASS",
        countdown_status="DEMO_READY_TO_REQUEST_OWNER_APPROVAL",
    )
    _write_status(report_dir / "PHASE2_READINESS_REPORT.md", "PENDING")
    _write_status(report_dir / "PHASE2_DEMO_PREFLIGHT_REPORT.md", "PENDING")
    _write_status(report_dir / "PHASE2_VPS_FIRST_DAY_VERIFICATION.md", "PASS")
    _write_status(docs / "PHASE2_VPS_SELECTION_MATRIX.md", "PASS")

    output = module.generate_phase2_owner_action_packet(root)

    assert output.status == "READY_FOR_OWNER_APPROVAL_REVIEW"


def test_owner_action_packet_prefers_readiness_gate_over_document_status(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "xauusd-phase1"
    report_dir = root / "outputs" / "reports"
    docs = root / "docs"
    report_dir.mkdir(parents=True)
    docs.mkdir(parents=True)
    _write_countdown(
        report_dir / "PHASE2_DEMO_COUNTDOWN.json",
        owner_actions=[],
        wait_status="PASS",
        countdown_status="DEMO_READY_TO_REQUEST_OWNER_APPROVAL",
    )
    _write_readiness_with_vps_gate(report_dir / "PHASE2_READINESS_REPORT.md", vps_selection_status="PENDING")
    _write_status(report_dir / "PHASE2_DEMO_PREFLIGHT_REPORT.md", "PENDING")
    _write_status(report_dir / "PHASE2_VPS_FIRST_DAY_VERIFICATION.md", "PASS")
    _write_status(docs / "PHASE2_VPS_SELECTION_MATRIX.md", "PASS")

    output = module.generate_phase2_owner_action_packet(root)

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    assert payload["vps_selection_status"] == "PENDING"
    assert any(item["gate"] == "VPS selection" and item["status"] == "PENDING" for item in payload["owner_actions_now"])
    assert any(
        item["title"] == "Select VPS provider, region, and plan" and item["status"] == "PENDING"
        for item in payload["owner_checklist"]
    )


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_phase2_owner_action_packet.py"
    spec = importlib.util.spec_from_file_location("generate_phase2_owner_action_packet", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_phase2_owner_action_packet"] = module
    spec.loader.exec_module(module)
    return module


def _write_status(path: Path, status: str) -> None:
    path.write_text(f"# Report\n\nOverall status: {status}\n", encoding="utf-8")


def _write_readiness_with_vps_gate(path: Path, vps_selection_status: str) -> None:
    path.write_text(
        "\n".join(
            [
                "# Phase 2 Readiness Report",
                "",
                "Overall status: PENDING",
                "",
                "## Gates",
                "",
                "| Gate | Status | Evidence |",
                "| --- | --- | --- |",
                f"| VPS selection | {vps_selection_status} | readiness gate evidence |",
                "| VPS latency evidence | PASS | latency captured |",
                "| VPS first-day verification | PASS | first day verified |",
                "| Project owner approval | PENDING | approval missing |",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_countdown(
    path: Path,
    owner_actions: list[dict[str, str]] | None = None,
    wait_status: str = "PENDING",
    countdown_status: str = "DEMO_NOT_READY",
) -> None:
    if owner_actions is None:
        owner_actions = [
            {"gate": "VPS selection", "status": "PENDING", "action": "select a VPS"},
            {"gate": "VPS latency evidence", "status": "PENDING", "action": "capture latency"},
            {"gate": "VPS first-day verification", "status": "PENDING", "action": "verify first day"},
            {"gate": "Project owner approval", "status": "PENDING", "action": "sign approval"},
        ]
    path.write_text(
        json.dumps(
            {
                "status": countdown_status,
                "owner_actions_now": owner_actions,
                "wait_gates": [
                    {
                        "gate": "Active-market 72-hour soak",
                        "status": wait_status,
                        "current": 26.0,
                        "required": 72.0,
                        "remaining": 46.0 if wait_status != "PASS" else 0.0,
                        "unit": "hours",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
