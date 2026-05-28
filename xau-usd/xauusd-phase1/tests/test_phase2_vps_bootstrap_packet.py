from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_vps_bootstrap_packet_sequences_demo_handoff_without_authorization(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "xauusd-phase1"
    report_dir = root / "outputs" / "reports"
    docs = root / "docs"
    report_dir.mkdir(parents=True)
    docs.mkdir(parents=True)
    _write_countdown(report_dir / "PHASE2_DEMO_COUNTDOWN.json")
    _write_owner_packet(report_dir / "PHASE2_OWNER_ACTION_PACKET.json")
    _write_readiness(report_dir / "PHASE2_READINESS_REPORT.md", vps_selection_status="PENDING")
    _write_status(report_dir / "PHASE2_DEMO_PREFLIGHT_REPORT.md", "PENDING")
    _write_status(report_dir / "PHASE2_VPS_FIRST_DAY_VERIFICATION.md", "PENDING")
    _write_network_baseline(report_dir / "PHASE2_LOCAL_MT5_NETWORK_BASELINE.md")
    _write_status(docs / "PHASE2_VPS_SELECTION_MATRIX.md", "PENDING")

    output = module.generate_phase2_vps_bootstrap_packet(root)

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    markdown = output.markdown_path.read_text(encoding="utf-8")
    assert output.status == "WAITING_AND_VPS_BOOTSTRAP_PENDING"
    assert output.phase_count == 4
    assert payload["paper_mode_authorized"] is False
    assert payload["demo_trading_authorized"] is False
    assert payload["broker_execution_authorized"] is False
    assert payload["live_trading_authorized"] is False
    assert payload["source_status"]["vps_selection"] == "PENDING"
    assert payload["local_mt5_network_baseline"]["median_ping"] == "129.78 ms"
    assert payload["source_reports"]["local_mt5_network_baseline"].endswith("PHASE2_LOCAL_MT5_NETWORK_BASELINE.md")
    assert payload["evidence_paths"]["local_mt5_network_baseline"].endswith("PHASE2_LOCAL_MT5_NETWORK_BASELINE.md")
    assert [phase["phase"] for phase in payload["bootstrap_phases"]] == [
        "Before VPS Purchase",
        "On VPS First Login",
        "After MT5 Dry-Run Deploy",
        "Before Owner Approval",
    ]
    assert "-SampleCount 20" in payload["commands"]["capture_vps_latency"]
    assert "trade_permission=false" in markdown
    assert "PHASE2_OWNER_APPROVAL.md" in markdown
    assert "Local MT5 Network Baseline" in markdown
    assert "129.78 ms" in markdown
    assert "install_phase2_periodic_checks_task.ps1" in markdown
    assert "prepare_phase2_vps_evidence_workspace.ps1" in markdown
    assert "prepare_phase2_vps_evidence_workspace.ps1" in payload["commands"]["prepare_vps_evidence_workspace"]
    assert "-WhatIfOnly" in payload["commands"]["install_periodic_checks_task"]
    assert "-WriteEvidence" in payload["commands"]["install_periodic_checks_task"]
    assert "-Provider <selected_provider>" in payload["commands"]["install_periodic_checks_task"]
    assert "-Region <selected_region>" in payload["commands"]["install_periodic_checks_task"]
    assert "Copy-Item docs\\templates\\vps_periodic_task.template.txt" in markdown
    assert "--scheduler-evidence outputs\\reports\\vps_periodic_task.txt" in markdown
    assert any(
        str(path).endswith("outputs\\reports\\vps_periodic_task.txt")
        or str(path).endswith("outputs/reports/vps_periodic_task.txt")
        for phase in payload["bootstrap_phases"]
        for path in phase["evidence"]
    )
    assert "This packet is an operational VPS bootstrap handoff only" in markdown


def test_vps_bootstrap_packet_ready_when_waits_and_owner_actions_clear(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "xauusd-phase1"
    report_dir = root / "outputs" / "reports"
    docs = root / "docs"
    report_dir.mkdir(parents=True)
    docs.mkdir(parents=True)
    _write_countdown(report_dir / "PHASE2_DEMO_COUNTDOWN.json", wait_status="PASS", owner_actions=[])
    _write_owner_packet(report_dir / "PHASE2_OWNER_ACTION_PACKET.json", owner_actions=[])
    _write_readiness(
        report_dir / "PHASE2_READINESS_REPORT.md",
        vps_selection_status="PASS",
        vps_latency_status="PASS",
        vps_first_day_status="PASS",
    )
    _write_status(report_dir / "PHASE2_DEMO_PREFLIGHT_REPORT.md", "PENDING")
    _write_status(report_dir / "PHASE2_VPS_FIRST_DAY_VERIFICATION.md", "PASS")
    _write_status(docs / "PHASE2_VPS_SELECTION_MATRIX.md", "PASS")

    output = module.generate_phase2_vps_bootstrap_packet(root)

    assert output.status == "READY_FOR_OWNER_APPROVAL_REVIEW"


def test_vps_bootstrap_packet_prefers_readiness_gate_status(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "xauusd-phase1"
    report_dir = root / "outputs" / "reports"
    docs = root / "docs"
    report_dir.mkdir(parents=True)
    docs.mkdir(parents=True)
    _write_countdown(report_dir / "PHASE2_DEMO_COUNTDOWN.json", wait_status="PASS", owner_actions=[])
    _write_owner_packet(report_dir / "PHASE2_OWNER_ACTION_PACKET.json", owner_actions=[])
    _write_readiness(report_dir / "PHASE2_READINESS_REPORT.md", vps_selection_status="PENDING")
    _write_status(report_dir / "PHASE2_DEMO_PREFLIGHT_REPORT.md", "PENDING")
    _write_status(report_dir / "PHASE2_VPS_FIRST_DAY_VERIFICATION.md", "PASS")
    _write_status(docs / "PHASE2_VPS_SELECTION_MATRIX.md", "PASS")

    output = module.generate_phase2_vps_bootstrap_packet(root)

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    assert payload["source_status"]["vps_selection"] == "PENDING"
    assert output.status == "VPS_BOOTSTRAP_ACTION_REQUIRED"


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_phase2_vps_bootstrap_packet.py"
    spec = importlib.util.spec_from_file_location("generate_phase2_vps_bootstrap_packet", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_phase2_vps_bootstrap_packet"] = module
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


def _write_readiness(
    path: Path,
    vps_selection_status: str,
    vps_latency_status: str = "PENDING",
    vps_first_day_status: str = "PENDING",
) -> None:
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
                f"| VPS latency evidence | {vps_latency_status} | latency evidence |",
                f"| VPS first-day verification | {vps_first_day_status} | first day evidence |",
                "| Project owner approval | PENDING | approval missing |",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_countdown(
    path: Path,
    wait_status: str = "PENDING",
    owner_actions: list[dict[str, str]] | None = None,
) -> None:
    if owner_actions is None:
        owner_actions = [
            {"gate": "VPS selection", "status": "PENDING", "action": "select a VPS"},
            {"gate": "VPS latency evidence", "status": "PENDING", "action": "capture latency"},
        ]
    path.write_text(
        json.dumps(
            {
                "status": "DEMO_NOT_READY",
                "owner_actions_now": owner_actions,
                "runtime_snapshot": {
                    "decision_rows": 10,
                    "latest_bar": "2026.05.28 14:15:00",
                    "dry_run": "true",
                    "trade_permission": "false",
                    "server_time_status": "CLOCK_OK",
                },
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


def _write_owner_packet(path: Path, owner_actions: list[dict[str, str]] | None = None) -> None:
    if owner_actions is None:
        owner_actions = [{"gate": "VPS selection", "status": "PENDING", "action": "select a VPS"}]
    path.write_text(
        json.dumps({"status": "WAITING_AND_OWNER_ACTION_REQUIRED", "owner_actions_now": owner_actions}),
        encoding="utf-8",
    )
