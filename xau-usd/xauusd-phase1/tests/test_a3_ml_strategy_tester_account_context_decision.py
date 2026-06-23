from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c55_detects_account_context_blocker_and_keeps_authorization_false(tmp_path: Path) -> None:
    from ml.a3_meta_v1.strategy_tester_account_context_decision import (
        generate_strategy_tester_account_context_decision,
    )

    root = _root_with_c53_c54(tmp_path, include_account_blocker=True)

    output = generate_strategy_tester_account_context_decision(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "STRATEGY_TESTER_ACCOUNT_CONTEXT_DECISION_REQUIRED"
    assert payload["account_context_blocker_detected"] is True
    assert payload["recommended_decision"] == "MANUAL_LOGIN_TO_ISOLATED_ROOT"
    assert payload["authorization"]["training_authorized"] is False
    assert payload["authorization"]["broker_action_authorized"] is False
    assert payload["boundary"]["account_dat_copied"] is False
    assert payload["boundary"]["server_dat_copied"] is False
    assert any(item["decision"] == "MANUAL_LOGIN_TO_ISOLATED_ROOT" for item in payload["decision_options"])
    assert "account is not specified" in payload["detected_log_evidence"][0]["excerpt"]
    assert pointer["c55_strategy_tester_account_context_decision_status"] == "STRATEGY_TESTER_ACCOUNT_CONTEXT_DECISION_REQUIRED"
    assert pointer["broker_action_authorized"] is False


def test_c55_reports_pending_before_replay_evidence(tmp_path: Path) -> None:
    from ml.a3_meta_v1.strategy_tester_account_context_decision import (
        generate_strategy_tester_account_context_decision,
    )

    root = _root_with_c53_only(tmp_path)

    output = generate_strategy_tester_account_context_decision(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "STRATEGY_TESTER_ACCOUNT_CONTEXT_PENDING_REPLAY_EVIDENCE"
    assert payload["account_context_blocker_detected"] is False
    assert "Run the bounded C54" in payload["next_allowed_stage"]


def test_c55_script_loads() -> None:
    module = load_script("c55_generate_strategy_tester_account_context_decision")

    assert hasattr(module, "main")


def _root_with_c53_c54(tmp_path: Path, *, include_account_blocker: bool) -> Path:
    root = _root_with_c53_only(tmp_path)
    reports = root / "outputs" / "reports"
    log = root / "isolated" / "Tester" / "logs" / "20260622.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(
        "2026.06.22 10:01:00.000 Tester tester not started because the account is not specified\n"
        if include_account_blocker
        else "2026.06.22 10:01:00.000 Tester finished normally\n",
        encoding="utf-16",
    )
    _write_json(
        reports / "A3_ML_STRATEGY_TESTER_REPLAY_LAUNCH_STATUS.json",
        {
            "status": "STRATEGY_TESTER_REPLAY_LAUNCH_COMPLETED_OUTPUTS_FOUND",
            "dataset_version": "DATASET_C55",
            "selected_lane_id": "A2_Phase2ExperimentalDemoExecutor_XAUUSD_M5",
            "launch_result": {
                "attempted": True,
                "returncode": 3294954943,
                "timed_out": False,
                "duration_seconds": 14.2,
            },
            "replay_outputs": [
                {
                    "path": str(log),
                    "size_bytes": log.stat().st_size,
                    "sha256": "0" * 64,
                }
            ],
        },
    )
    return root


def _root_with_c53_only(tmp_path: Path) -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    terminal_root = root / "isolated"
    terminal = terminal_root / "terminal64.exe"
    config = terminal_root / "Config" / "A2_Phase2ExperimentalDemoExecutor_XAUUSD_M5.ini"
    terminal.parent.mkdir(parents=True, exist_ok=True)
    config.parent.mkdir(parents=True, exist_ok=True)
    terminal.write_bytes(b"terminal")
    config.write_text("[Tester]\n", encoding="utf-8")
    _write_json(
        reports / "C02_DATASET_POINTER.json",
        {
            "dataset_version": "DATASET_C55",
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
    )
    _write_json(
        reports / "A3_ML_ISOLATED_STRATEGY_TESTER_TERMINAL_ROOT_STATUS.json",
        {
            "status": "ISOLATED_STRATEGY_TESTER_TERMINAL_ROOT_READY",
            "dataset_version": "DATASET_C55",
            "selected_lane_id": "A2_Phase2ExperimentalDemoExecutor_XAUUSD_M5",
            "selected_lane": {
                "terminal_root_ready": True,
                "terminal_root": str(terminal_root),
                "isolated_terminal_exe": str(terminal),
                "tester_config_path": str(config),
            },
        },
    )
    return root


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
