from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_vps_selection_decision_check_is_pending_for_unselected_matrix(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "phase1"
    docs = root / "docs"
    docs.mkdir(parents=True)
    _write_matrix(docs / "PHASE2_VPS_SELECTION_MATRIX.md", "PENDING", pending=True)

    output = module.generate_phase2_vps_selection_decision_check(root)

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    markdown = output.markdown_path.read_text(encoding="utf-8")
    assert output.status == "PENDING"
    assert payload["demo_trading_authorized"] is False
    assert payload["broker_execution_authorized"] is False
    assert any(check["check"] == "matrix_readiness_gate" and check["status"] == "PENDING" for check in payload["checks"])
    latency = next(check for check in payload["checks"] if check["check"] == "latency_evidence_report")
    assert "PHASE2_VPS_LATENCY_REPORT.md" in latency["evidence"]
    assert "after VPS provision`" not in latency["evidence"]
    assert "This report validates the owner VPS-selection record only" in markdown


def test_vps_selection_decision_check_passes_completed_selection(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "phase1"
    docs = root / "docs"
    reports = root / "outputs" / "reports"
    docs.mkdir(parents=True)
    reports.mkdir(parents=True)
    _write_matrix(docs / "PHASE2_VPS_SELECTION_MATRIX.md", "PASS", pending=False)
    _write_latency_report(reports / "PHASE2_VPS_LATENCY_REPORT.md", provider="FXVM", region="Dubai")

    output = module.generate_phase2_vps_selection_decision_check(root)

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    assert output.status == "PASS"
    assert {check["status"] for check in payload["checks"]} == {"PASS"}
    assert payload["next_action"] == "VPS selection evidence is ready for the broader Phase 2 readiness report."


def test_vps_selection_decision_check_requires_owner_boundary_text(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "phase1"
    docs = root / "docs"
    reports = root / "outputs" / "reports"
    docs.mkdir(parents=True)
    reports.mkdir(parents=True)
    _write_matrix(
        docs / "PHASE2_VPS_SELECTION_MATRIX.md",
        "PASS",
        pending=False,
        owner_acceptance="Approved for paper only.",
    )
    _write_latency_report(reports / "PHASE2_VPS_LATENCY_REPORT.md", provider="FXVM", region="Dubai")

    output = module.generate_phase2_vps_selection_decision_check(root)

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    assert output.status == "PENDING"
    boundary = next(check for check in payload["checks"] if check["check"] == "owner_acceptance_boundary")
    assert boundary["status"] == "PENDING"
    assert "no live capital" in boundary["evidence"]


def test_vps_selection_decision_check_rejects_latency_provider_mismatch(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "phase1"
    docs = root / "docs"
    reports = root / "outputs" / "reports"
    docs.mkdir(parents=True)
    reports.mkdir(parents=True)
    _write_matrix(docs / "PHASE2_VPS_SELECTION_MATRIX.md", "PASS", pending=False)
    _write_latency_report(reports / "PHASE2_VPS_LATENCY_REPORT.md", provider="ForexVPS.net", region="London")

    output = module.generate_phase2_vps_selection_decision_check(root)

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    assert output.status == "FAIL"
    consistency = next(check for check in payload["checks"] if check["check"] == "latency_selection_consistency")
    assert consistency["status"] == "FAIL"
    assert "selected_provider" in consistency["evidence"]
    assert "selected_region" in consistency["evidence"]


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_phase2_vps_selection_decision_check.py"
    spec = importlib.util.spec_from_file_location("generate_phase2_vps_selection_decision_check", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_phase2_vps_selection_decision_check"] = module
    spec.loader.exec_module(module)
    return module


def _write_matrix(
    path: Path,
    status: str,
    pending: bool,
    owner_acceptance: str = "Phase 2 paper-mode only accepted; no live capital; no broker execution until readiness PASS",
) -> None:
    if pending:
        values = {
            "Selected provider": "Pending owner selection",
            "Selected region": "Pending owner selection",
            "Selected plan": "Pending owner selection",
            "Monthly cost": "Pending owner selection",
            "Backup method": "Pending owner selection",
            "Monitoring endpoint or scheduler": "Pending owner selection",
            "Recovery access owner": "Pending owner selection",
            "Latency evidence path": "outputs/reports/PHASE2_VPS_LATENCY_REPORT.md",
            "Decision date": "Pending owner selection",
            "Owner acceptance": "Pending owner selection",
        }
    else:
        values = {
            "Selected provider": "FXVM",
            "Selected region": "Dubai",
            "Selected plan": "Advanced VPS",
            "Monthly cost": "50 USD/month",
            "Backup method": "weekly image backup",
            "Monitoring endpoint or scheduler": "Windows Task Scheduler hourly checks",
            "Recovery access owner": "Project owner",
            "Latency evidence path": "outputs/reports/PHASE2_VPS_LATENCY_REPORT.md",
            "Decision date": "2026-05-28",
            "Owner acceptance": owner_acceptance,
        }
    rows = [f"| {key} | {value} |" for key, value in values.items()]
    path.write_text(
        "\n".join(
            [
                "# Phase 2 VPS Selection Matrix",
                "",
                f"Overall status: {status}",
                "",
                "## Decision Record",
                "",
                "| Field | Value |",
                "| --- | --- |",
                *rows,
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_latency_report(path: Path, provider: str, region: str) -> None:
    path.write_text(
        "\n".join(
            [
                "# Phase 2 VPS Latency Report",
                "",
                "Overall status: PASS",
                "",
                "## Candidate",
                "",
                "| Provider | Region | Endpoint | Average Ping | Packet Loss |",
                "| --- | --- | --- | --- | --- |",
                f"| {provider} | {region} | broker.example | 40.00 ms | 0.00% |",
                "",
            ]
        ),
        encoding="utf-8",
    )
