from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase2_transition_artifact_verifier_passes_committed_artifacts():
    module = _load_module()

    errors = module.verify_phase2_transition_artifacts(ROOT, ROOT.parents[1], ROOT.parents[1] / "status.html")

    assert errors == []


def test_phase2_transition_artifact_verifier_ignores_generated_timestamps(tmp_path: Path):
    module = _load_module()
    committed = tmp_path / "committed.json"
    generated = tmp_path / "generated.json"
    committed.write_text(json.dumps({"status": "PENDING", "created_at_utc": "old"}), encoding="utf-8")
    generated.write_text(json.dumps({"status": "PENDING", "created_at_utc": "new"}), encoding="utf-8")

    assert module._compare_json("sample", committed, generated) == []


def test_phase2_transition_artifact_verifier_detects_stale_payload(tmp_path: Path):
    module = _load_module()
    committed = tmp_path / "committed.json"
    generated = tmp_path / "generated.json"
    committed.write_text(json.dumps({"status": "PENDING", "checks": [{"status": "PENDING"}]}), encoding="utf-8")
    generated.write_text(json.dumps({"status": "PENDING", "checks": [{"status": "PASS"}]}), encoding="utf-8")

    errors = module._compare_json("sample", committed, generated)

    assert errors == ["sample is stale relative to canonical inputs; regenerate and commit it."]


def test_phase2_transition_artifact_verifier_detects_unsafe_authorization_flag(tmp_path: Path):
    module = _load_module()
    repo = tmp_path / "repo"
    root = repo / "xau-usd" / "xauusd-phase1"
    reports = root / "outputs" / "reports"
    phase3_reports = repo / "xau-usd" / "xauusd-phase3-experimental" / "outputs" / "reports"
    reports.mkdir(parents=True)
    phase3_reports.mkdir(parents=True)
    _write_transition_boundary_jsons(reports, phase3_reports)
    (reports / "PHASE2_OWNER_ACTION_PACKET.json").write_text(
        json.dumps({"paper_mode_authorized": False, "demo_trading_authorized": True}),
        encoding="utf-8",
    )

    errors = module._authorization_boundary_errors(root, repo)

    assert "PHASE2_OWNER_ACTION_PACKET.json must keep demo_trading_authorized=False; found True." in errors


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "verify_phase2_transition_artifacts.py"
    spec = importlib.util.spec_from_file_location("verify_phase2_transition_artifacts", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["verify_phase2_transition_artifacts"] = module
    spec.loader.exec_module(module)
    return module


def _write_transition_boundary_jsons(reports: Path, phase3_reports: Path) -> None:
    files = {
        reports / "PHASE2_DEMO_PREFLIGHT.json": {
            "status": "PENDING",
            "paper_mode_implementation_authorized": False,
            "demo_trading_authorized": False,
            "live_trading_authorized": False,
        },
        reports / "PHASE2_OWNER_ACTION_PACKET.json": {
            "paper_mode_authorized": False,
            "demo_trading_authorized": False,
            "broker_execution_authorized": False,
            "live_trading_authorized": False,
        },
        reports / "PHASE2_DEMO_COUNTDOWN.json": {
            "paper_mode_authorized": False,
            "broker_execution_authorized": False,
            "live_trading_authorized": False,
        },
        reports / "PHASE2_VPS_BOOTSTRAP_PACKET.json": {
            "paper_mode_authorized": False,
            "demo_trading_authorized": False,
            "broker_execution_authorized": False,
            "live_trading_authorized": False,
        },
        reports / "PHASE2_VPS_FIRST_DAY_VERIFICATION.json": {
            "phase2_paper_mode_authorized": False,
            "demo_trading_authorized": False,
            "live_trading_authorized": False,
        },
        phase3_reports / "PHASE3_EXPERIMENTAL_STATUS.json": {
            "authorized_for_deployment": False,
            "broker_action_code_allowed": False,
            "mt5_runtime_touched": False,
            "owner_approval_flow": "excluded_from_real_phase2_phase3_approval_flow",
        },
    }
    for path, payload in files.items():
        path.write_text(json.dumps(payload), encoding="utf-8")
