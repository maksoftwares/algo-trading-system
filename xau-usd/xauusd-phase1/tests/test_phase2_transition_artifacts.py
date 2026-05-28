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


def test_phase2_transition_artifact_verifier_normalizes_machine_local_paths(tmp_path: Path):
    module = _load_module()
    committed = tmp_path / "committed.json"
    generated = tmp_path / "generated.json"
    committed.write_text(
        json.dumps(
            {
                "source_reports": {
                    "readiness": (
                        "C:\\Users\\ZHAO ZHU INFORMATION\\Downloads\\algo-trading-system\\"
                        "xau-usd\\xauusd-phase1\\outputs\\reports\\PHASE2_READINESS_REPORT.md"
                    )
                },
                "evidence": (
                    "`C:\\Users\\ZHAO ZHU INFORMATION\\Downloads\\algo-trading-system\\"
                    "xau-usd\\xauusd-phase1\\outputs\\reports\\PHASE2_READINESS_REPORT.md` status is PENDING."
                ),
            }
        ),
        encoding="utf-8",
    )
    generated.write_text(
        json.dumps(
            {
                "source_reports": {
                    "readiness": (
                        "/home/runner/work/algo-trading-system/algo-trading-system/"
                        "xau-usd/xauusd-phase1/outputs/reports/PHASE2_READINESS_REPORT.md"
                    )
                },
                "evidence": (
                    "`/home/runner/work/algo-trading-system/algo-trading-system/"
                    "xau-usd/xauusd-phase1/outputs/reports/PHASE2_READINESS_REPORT.md` status is PENDING."
                ),
            }
        ),
        encoding="utf-8",
    )

    assert module._compare_json("sample", committed, generated) == []


def test_phase2_transition_artifact_verifier_normalizes_machine_local_markdown_paths(tmp_path: Path):
    module = _load_module()
    committed = tmp_path / "committed.md"
    generated = tmp_path / "generated.md"
    committed.write_text(
        (
            "| Gate | Evidence |\n"
            "| --- | --- |\n"
            "| Readiness | `C:\\Users\\ZHAO ZHU INFORMATION\\Downloads\\algo-trading-system\\"
            "xau-usd\\xauusd-phase1\\outputs\\reports\\PHASE2_READINESS_REPORT.md` status is PENDING. |\n"
        ),
        encoding="utf-8",
    )
    generated.write_text(
        (
            "| Gate | Evidence |\n"
            "| --- | --- |\n"
            "| Readiness | `/home/runner/work/algo-trading-system/algo-trading-system/"
            "xau-usd/xauusd-phase1/outputs/reports/PHASE2_READINESS_REPORT.md` status is PENDING. |\n"
        ),
        encoding="utf-8",
    )

    assert module._compare_text("sample.md", committed, generated) == []


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


def test_phase2_transition_artifact_verifier_requires_vps_latency_baseline_comparison(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    (reports / "PHASE2_LOCAL_MT5_NETWORK_BASELINE.md").write_text(
        "# Baseline\n\nOverall status: PASS\n",
        encoding="utf-8",
    )
    (reports / "PHASE2_VPS_LATENCY_REPORT.md").write_text(
        "# VPS Latency\n\nOverall status: PASS\n",
        encoding="utf-8",
    )

    errors = module._vps_latency_baseline_errors(root)

    assert "PHASE2_VPS_LATENCY_REPORT.md must include a local_baseline_comparison check." in errors
    assert "PHASE2_VPS_LATENCY_REPORT.md must include the Local MT5 baseline evidence path." in errors
    assert "PHASE2_VPS_LATENCY_REPORT.md status=PASS must prove local_baseline_comparison PASS." in errors


def test_phase2_transition_artifact_verifier_requires_owner_packet_vps_recommendation(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    (reports / "PHASE2_OWNER_ACTION_PACKET.json").write_text(
        json.dumps(
            {
                "paper_mode_authorized": False,
                "demo_trading_authorized": False,
                "broker_execution_authorized": False,
                "live_trading_authorized": False,
            }
        ),
        encoding="utf-8",
    )
    (reports / "PHASE2_OWNER_ACTION_PACKET.md").write_text(
        "# Phase 2 Owner Action Packet\n\nOverall status: PENDING\n",
        encoding="utf-8",
    )

    errors = module._owner_packet_recommendation_errors(root)

    assert "PHASE2_OWNER_ACTION_PACKET.json must include vps_selection_recommendation." in errors


def test_phase2_transition_artifact_verifier_accepts_owner_packet_vps_recommendation(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    recommendation = {
        "status": "PENDING",
        "primary_trial": "FXVM Advanced VPS in Dubai, Mumbai, or Singapore",
        "backup_trial": "ForexVPS.net Core in the lowest-latency available region",
        "defer": "QuantVPS unless broker latency testing favors US/Chicago",
    }
    decision_sheet = {
        "status": "WAITING_OWNER_SELECTION",
        "recommended_first_trial": "FXVM Advanced VPS in Dubai, Mumbai, or Singapore",
        "backup_trial": "ForexVPS.net Core in the lowest-latency available region",
        "decision_record_path": "docs/PHASE2_VPS_SELECTION_MATRIX.md",
    }
    (reports / "PHASE2_OWNER_ACTION_PACKET.json").write_text(
        json.dumps(
            {
                "vps_selection_recommendation": recommendation,
                "one_screen_vps_decision_sheet": decision_sheet,
            }
        ),
        encoding="utf-8",
    )
    (reports / "PHASE2_OWNER_ACTION_PACKET.md").write_text(
        "\n".join(
            [
                "# Phase 2 Owner Action Packet",
                "",
                "## VPS Selection Recommendation",
                "",
                "| Field | Value |",
                "| --- | --- |",
                "| Matrix status | PENDING |",
                "| Primary trial | FXVM Advanced VPS in Dubai, Mumbai, or Singapore |",
                "| Backup trial | ForexVPS.net Core in the lowest-latency available region |",
                "| Defer | QuantVPS unless broker latency testing favors US/Chicago |",
                "",
                "## One-Screen VPS Decision Sheet",
                "",
                "| Field | Value |",
                "| --- | --- |",
                "| Status | WAITING_OWNER_SELECTION |",
                "| Recommended first trial | FXVM Advanced VPS in Dubai, Mumbai, or Singapore |",
                "| Backup trial | ForexVPS.net Core in the lowest-latency available region |",
                "| Decision record | docs/PHASE2_VPS_SELECTION_MATRIX.md |",
            ]
        ),
        encoding="utf-8",
    )

    assert module._owner_packet_recommendation_errors(root) == []


def test_phase2_transition_artifact_verifier_accepts_pending_vps_latency_with_baseline_schema(tmp_path: Path):
    module = _load_module()
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    (reports / "PHASE2_LOCAL_MT5_NETWORK_BASELINE.md").write_text(
        "# Baseline\n\nOverall status: PASS\n",
        encoding="utf-8",
    )
    (reports / "PHASE2_VPS_LATENCY_REPORT.md").write_text(
        "\n".join(
            [
                "# VPS Latency",
                "",
                "Overall status: PENDING",
                "",
                "| Check | Status | Evidence |",
                "| --- | --- | --- |",
                "| local_baseline_comparison | PENDING | waiting for VPS ping evidence |",
                "",
                "- Local MT5 baseline: `outputs/reports/PHASE2_LOCAL_MT5_NETWORK_BASELINE.md`",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assert module._vps_latency_baseline_errors(root) == []


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
