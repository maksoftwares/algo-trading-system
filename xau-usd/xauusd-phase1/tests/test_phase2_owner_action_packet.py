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
    _write_readiness_with_vps_gate(report_dir / "PHASE2_READINESS_REPORT.md", vps_selection_status="PENDING")
    _write_status(report_dir / "PHASE2_DEMO_PREFLIGHT_REPORT.md", "PENDING")
    _write_status(report_dir / "PHASE2_VPS_FIRST_DAY_VERIFICATION.md", "PENDING")
    _write_network_baseline(report_dir / "PHASE2_LOCAL_MT5_NETWORK_BASELINE.md")
    _write_vps_workspace_manifest(report_dir / "vps_evidence_workspace_manifest.json")
    _write_vps_matrix(docs / "PHASE2_VPS_SELECTION_MATRIX.md", "PENDING")
    (docs / "PHASE2_OWNER_APPROVAL_DRAFT.md").write_text("# Draft\n", encoding="utf-8")

    output = module.generate_phase2_owner_action_packet(root)

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    markdown = output.markdown_path.read_text(encoding="utf-8")
    assert output.status == "WAITING_AND_OWNER_ACTION_REQUIRED"
    assert output.owner_action_count == 4
    assert payload["paper_mode_authorized"] is False
    assert payload["demo_trading_authorized"] is False
    assert payload["owner_approval_readiness"]["status"] == "NOT_READY_TO_SIGN"
    assert payload["owner_approval_readiness"]["pending_objective_gate_count"] == 1
    assert any(item["title"] == "Select VPS provider, region, and plan" for item in payload["owner_checklist"])
    assert payload["owner_templates"]["vps_selection_decision"].endswith(
        "docs\\templates\\phase2_vps_selection_decision.template.md"
    ) or payload["owner_templates"]["vps_selection_decision"].endswith(
        "docs/templates/phase2_vps_selection_decision.template.md"
    )
    assert "capture_phase2_vps_latency_evidence.ps1" in payload["commands"]["capture_vps_latency"]
    assert "-SampleCount 20" in payload["commands"]["capture_vps_latency"]
    assert "generate_phase2_vps_selection_decision_check.py" in payload["commands"]["check_vps_selection_decision"]
    assert payload["source_reports"]["phase2_vps_bootstrap"].endswith("PHASE2_VPS_BOOTSTRAP_PACKET.md")
    assert payload["source_reports"]["vps_evidence_workspace_manifest"].endswith(
        "vps_evidence_workspace_manifest.json"
    )
    assert payload["source_reports"]["vps_selection_decision_check"].endswith("PHASE2_VPS_SELECTION_DECISION_CHECK.md")
    assert payload["source_reports"]["local_mt5_network_baseline"].endswith("PHASE2_LOCAL_MT5_NETWORK_BASELINE.md")
    assert payload["local_mt5_network_baseline"]["median_ping"] == "129.78 ms"
    assert payload["local_mt5_network_baseline"]["samples"] == "5755"
    assert payload["vps_evidence_workspace"]["status"] == "PREPARED_PENDING_OWNER_VERIFICATION"
    assert payload["vps_evidence_workspace"]["items"][0]["action"] == "CREATED"
    assert payload["vps_selection_recommendation"]["primary_trial"] == "FXVM Advanced VPS in Dubai, Mumbai, or Singapore"
    assert payload["vps_selection_recommendation"]["backup_trial"] == "ForexVPS.net Core in the lowest-latency available region"
    assert payload["vps_selection_decision_check_status"] == "UNKNOWN"
    decision_sheet = payload["one_screen_vps_decision_sheet"]
    assert decision_sheet["status"] == "WAITING_OWNER_SELECTION"
    assert decision_sheet["recommended_first_trial"] == "FXVM Advanced VPS in Dubai, Mumbai, or Singapore"
    assert decision_sheet["decision_record_path"].endswith("docs\\PHASE2_VPS_SELECTION_MATRIX.md") or decision_sheet[
        "decision_record_path"
    ].endswith("docs/PHASE2_VPS_SELECTION_MATRIX.md")
    assert "Owner acceptance that Phase 2 is paper-mode only" in decision_sheet["required_decision_fields"]
    assert "median ping <= 50 ms: preferred" in decision_sheet["pass_preferences"]
    assert "VPS Selection Recommendation" in markdown
    assert "One-Screen VPS Decision Sheet" in markdown
    assert "Prepared VPS Evidence Workspace" in markdown
    assert "PREPARED_PENDING_OWNER_VERIFICATION" in markdown
    assert "vps_ntp_sync.txt" in markdown
    assert "Required owner fields:" in markdown
    assert "After VPS is provisioned:" in markdown
    assert "FXVM Advanced VPS in Dubai, Mumbai, or Singapore" in markdown
    assert "median ping <= 50 ms: preferred" in markdown
    assert "Owner Approval Readiness" in markdown
    assert "NOT_READY_TO_SIGN" in markdown
    assert "Owner may sign only after every objective gate except Project owner approval is PASS." in markdown
    assert payload["owner_templates"]["vps_periodic_task"].endswith(
        "docs\\templates\\vps_periodic_task.template.txt"
    ) or payload["owner_templates"]["vps_periodic_task"].endswith(
        "docs/templates/vps_periodic_task.template.txt"
    )
    assert "install_phase2_periodic_checks_task.ps1" in payload["commands"]["install_periodic_checks_task_dry_run"]
    assert "prepare_phase2_vps_evidence_workspace.ps1" in payload["commands"]["prepare_vps_evidence_workspace"]
    assert "-WhatIfOnly" in payload["commands"]["install_periodic_checks_task_dry_run"]
    assert "-WriteEvidence" in payload["commands"]["install_periodic_checks_task_dry_run"]
    assert "-Provider <selected_provider>" in payload["commands"]["install_periodic_checks_task_dry_run"]
    assert "-Region <selected_region>" in payload["commands"]["install_periodic_checks_task_dry_run"]
    assert "Copy-Item docs\\templates\\vps_ntp_sync.template.txt" in markdown
    assert "prepare_phase2_vps_evidence_workspace.ps1" in markdown
    assert "Copy-Item docs\\templates\\vps_periodic_task.template.txt" in markdown
    assert "--scheduler-evidence outputs\\reports\\vps_periodic_task.txt" in markdown
    assert "PHASE2_VPS_BOOTSTRAP_PACKET.md" in markdown
    assert "Local MT5 Network Baseline" in markdown
    assert "VPS decision check" in markdown
    assert "129.78 ms" in markdown
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
    _write_readiness_with_vps_gate(report_dir / "PHASE2_READINESS_REPORT.md", vps_selection_status="PASS")
    _write_status(report_dir / "PHASE2_DEMO_PREFLIGHT_REPORT.md", "PENDING")
    _write_status(report_dir / "PHASE2_VPS_FIRST_DAY_VERIFICATION.md", "PASS")
    _write_vps_matrix(docs / "PHASE2_VPS_SELECTION_MATRIX.md", "PASS")

    output = module.generate_phase2_owner_action_packet(root)

    assert output.status == "READY_FOR_OWNER_APPROVAL_REVIEW"

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    assert payload["owner_approval_readiness"]["status"] == "READY_TO_SIGN"
    assert payload["owner_approval_readiness"]["pending_objective_gate_count"] == 0


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
    _write_vps_matrix(docs / "PHASE2_VPS_SELECTION_MATRIX.md", "PASS")

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


def _write_network_baseline(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Phase 2 Local MT5 Network Baseline",
                "",
                "Overall status: PASS",
                "",
                "| Samples | Latest Ping | Median Ping | Best Ping | Worst Ping | Latest Access Point |",
                "| --- | --- | --- | --- | --- | --- |",
                "| 5755 | 185.76 ms | 129.78 ms | 121.76 ms | 312.50 ms | 1 |",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_vps_workspace_manifest(path: Path) -> None:
    path.write_text(
        "\ufeff"
        + json.dumps(
            {
                "status": "PREPARED_PENDING_OWNER_VERIFICATION",
                "authority": (
                    "Evidence workspace preparation only; does not authorize Phase 2, demo trading, "
                    "broker execution, live capital, or MT5 runtime changes."
                ),
                "reports_dir": str(path.parent),
                "allow_overwrite_verified": False,
                "items": [
                    {
                        "target": str(path.parent / "vps_ntp_sync.txt"),
                        "source": "docs/templates/vps_ntp_sync.template.txt",
                        "action": "CREATED",
                        "reason": "Pending evidence template is ready to fill.",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_vps_matrix(path: Path, status: str) -> None:
    path.write_text(
        "\n".join(
            [
                "# Phase 2 VPS Selection Matrix",
                "",
                f"Overall status: {status}",
                "",
                "## Recommended Selection",
                "",
                "Current recommendation for owner review:",
                "",
                "```text",
                "Primary trial: FXVM Advanced VPS in Dubai, Mumbai, or Singapore.",
                "Backup trial: ForexVPS.net Core in the lowest-latency available region.",
                "Defer: QuantVPS unless broker latency testing favors US/Chicago.",
                "```",
                "",
                "Reasoning:",
                "",
                "- FXVM Advanced meets the minimum 2 CPU / 4 GB / 60 GB requirement and offers Dubai/Mumbai/Singapore regions to test against the current broker account geography.",
                "- ForexVPS.net Core is a clean minimum-spec alternative with stronger entry resources than FXVM Basic and an explicit 4 GB / 100 GB profile.",
                "- QuantVPS has excellent specs but is more expensive and appears more Chicago/futures oriented, so it should not be chosen for XAU/Capital.com paper mode unless latency proves it.",
                "",
                "## Latency Test Plan",
                "",
                "Latency testing follows after VPS provisioning.",
            ]
        ),
        encoding="utf-8",
    )


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
