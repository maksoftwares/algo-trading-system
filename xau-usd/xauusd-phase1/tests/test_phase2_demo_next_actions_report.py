from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_demo_next_actions_groups_owner_vps_wait_and_signature_steps(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "xauusd-phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    _write_status(reports / "PHASE2_READINESS_REPORT.md", "PENDING")
    _write_status(reports / "PHASE2_DEMO_PREFLIGHT_REPORT.md", "PENDING")
    _write_countdown(reports / "PHASE2_DEMO_COUNTDOWN.json")
    _write_owner_packet(reports / "PHASE2_OWNER_ACTION_PACKET.json")
    _write_vps_selection_check(reports / "PHASE2_VPS_SELECTION_DECISION_CHECK.json")
    _write_bootstrap(reports / "PHASE2_VPS_BOOTSTRAP_PACKET.json")

    output = module.generate_phase2_demo_next_actions_report(root)

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    markdown = output.markdown_path.read_text(encoding="utf-8")
    assert output.status == "OWNER_ACTION_AND_WAIT_GATES_PENDING"
    assert output.do_now_count >= 3
    assert payload["paper_mode_authorized"] is False
    assert payload["demo_trading_authorized"] is False
    assert payload["broker_execution_authorized"] is False
    assert payload["live_trading_authorized"] is False
    assert any(row["step"] == "keep_collectors_running" for row in payload["do_now"])
    assert any(row["step"] == "vps_selection" for row in payload["do_now"])
    assert any(row["step"] == "run_vps_selection_decision_check" for row in payload["do_now"])
    assert any(row["step"] == "prepare_vps_evidence_workspace" for row in payload["after_vps_is_provisioned"])
    assert any(row["step"] == "capture_vps_latency" for row in payload["after_vps_is_provisioned"])
    assert any(row["step"] == "rerun_vps_selection_decision_check" for row in payload["after_vps_is_provisioned"])
    assert payload["source_reports"]["phase2_vps_selection_decision_check"].endswith(
        "PHASE2_VPS_SELECTION_DECISION_CHECK.json"
    )
    assert payload["vps_selection_decision_check"]["status"] == "PENDING"
    assert any(row["step"] == "active_market_72_hour_soak" for row in payload["after_wait_gates_pass"])
    assert payload["earliest_gate_targets"][0]["gate"] == "Active-market 72-hour soak"
    assert payload["earliest_gate_targets"][0]["earliest_target_utc"].endswith("Z")
    assert "Assumes no restart" in payload["earliest_gate_targets"][0]["condition"]
    closure = {row["gate"]: row for row in payload["gate_closure_map"]}
    assert closure["VPS selection"]["category"] == "OWNER_DECISION"
    assert closure["VPS selection"]["owner"] == "Project owner"
    assert "explicit owner-approved host" in closure["VPS selection"]["why_required"]
    assert closure["VPS selection"]["proof_artifact"].endswith("PHASE2_VPS_SELECTION_MATRIX.md")
    assert "generate_phase2_vps_selection_decision_check.py" in closure["VPS selection"]["verification_command"]
    assert closure["Active-market 72-hour soak"]["category"] == "WALL_CLOCK_EVIDENCE"
    assert "observe live active-market bars continuously" in closure["Active-market 72-hour soak"]["why_required"]
    assert "current=29.0" in closure["Active-market 72-hour soak"]["pass_condition"]
    assert "run_phase1_periodic_checks.py" in closure["Active-market 72-hour soak"]["verification_command"]
    assert payload["owner_signature_sequence"][0]["status"] == "NOT_READY_TO_SIGN"
    assert "Do Now" in markdown
    assert "After VPS Is Provisioned" in markdown
    assert "Earliest Gate Targets" in markdown
    assert "Gate Closure Map" in markdown
    assert "OWNER_DECISION" in markdown
    assert "why_required" in markdown
    assert "verification_command" in markdown
    assert "Owner Signature Sequence" in markdown
    assert "This report is an operational next-action aid only" in markdown


def test_demo_next_actions_ready_for_owner_approval_when_countdown_ready(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "xauusd-phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    _write_status(reports / "PHASE2_READINESS_REPORT.md", "PASS")
    _write_status(reports / "PHASE2_DEMO_PREFLIGHT_REPORT.md", "PASS")
    _write_countdown(
        reports / "PHASE2_DEMO_COUNTDOWN.json",
        status="DEMO_READY_TO_REQUEST_OWNER_APPROVAL",
        owner_actions=[],
        wait_status="PASS",
        pending_gates=[],
    )
    _write_owner_packet(reports / "PHASE2_OWNER_ACTION_PACKET.json", owner_readiness="READY_TO_SIGN")
    _write_vps_selection_check(reports / "PHASE2_VPS_SELECTION_DECISION_CHECK.json", status="PASS")
    _write_bootstrap(reports / "PHASE2_VPS_BOOTSTRAP_PACKET.json", status="READY_FOR_OWNER_APPROVAL_REVIEW")

    output = module.generate_phase2_demo_next_actions_report(root)

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    assert output.status == "READY_FOR_OWNER_APPROVAL_REVIEW"
    assert payload["pending_gate_count"] == 0
    assert payload["owner_signature_sequence"][0]["status"] == "READY_TO_SIGN"


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_phase2_demo_next_actions_report.py"
    spec = importlib.util.spec_from_file_location("generate_phase2_demo_next_actions_report", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_phase2_demo_next_actions_report"] = module
    spec.loader.exec_module(module)
    return module


def _write_status(path: Path, status: str) -> None:
    path.write_text(f"# Report\n\nOverall status: {status}\n", encoding="utf-8")


def _write_countdown(
    path: Path,
    status: str = "DEMO_NOT_READY",
    owner_actions: list[dict[str, str]] | None = None,
    wait_status: str = "PENDING",
    pending_gates: list[dict[str, str]] | None = None,
) -> None:
    if owner_actions is None:
        owner_actions = [
            {"gate": "VPS selection", "status": "PENDING", "action": "select VPS"},
            {"gate": "VPS latency evidence", "status": "PENDING", "action": "capture latency"},
            {"gate": "Project owner approval", "status": "PENDING", "action": "sign after objective gates"},
        ]
    if pending_gates is None:
        pending_gates = [
            {"Gate": "VPS selection", "Status": "PENDING", "Evidence": "missing"},
            {"Gate": "Active-market 72-hour soak", "Status": "PENDING", "Evidence": "waiting"},
        ]
    path.write_text(
        json.dumps(
            {
                "status": status,
                "pending_gate_count": len(pending_gates),
                "pending_gates": pending_gates,
                "paper_mode_authorized": False,
                "owner_actions_now": owner_actions,
                "wait_gates": [
                    {
                        "gate": "Active-market 72-hour soak",
                        "status": wait_status,
                        "current": 29.0,
                        "required": 72.0,
                        "remaining": 43.0 if wait_status != "PASS" else 0.0,
                        "unit": "hours",
                    }
                ],
                "forbidden_until_ready": ["paper-mode implementation", "live capital"],
            }
        ),
        encoding="utf-8",
    )


def _write_owner_packet(path: Path, owner_readiness: str = "NOT_READY_TO_SIGN") -> None:
    path.write_text(
        json.dumps(
            {
                "owner_approval_readiness": {"status": owner_readiness},
                "one_screen_vps_decision_sheet": {
                    "status": "WAITING_OWNER_SELECTION",
                    "after_vps_is_provisioned": ["capture latency"],
                },
            }
        ),
        encoding="utf-8",
    )


def _write_vps_selection_check(path: Path, status: str = "PENDING") -> None:
    path.write_text(
        json.dumps(
            {
                "status": status,
                "paper_mode_authorized": False,
                "demo_trading_authorized": False,
                "broker_execution_authorized": False,
                "live_trading_authorized": False,
                "next_action": "Fill the VPS matrix." if status != "PASS" else "VPS selection evidence is ready.",
                "checks": [{"check": "matrix_readiness_gate", "status": status, "evidence": "matrix"}],
            }
        ),
        encoding="utf-8",
    )


def _write_bootstrap(path: Path, status: str = "WAITING_AND_VPS_BOOTSTRAP_PENDING") -> None:
    path.write_text(json.dumps({"status": status}), encoding="utf-8")
