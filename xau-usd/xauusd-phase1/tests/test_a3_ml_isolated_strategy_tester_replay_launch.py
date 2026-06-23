from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c54_runs_bounded_launch_and_hashes_outputs(tmp_path: Path) -> None:
    from ml.a3_meta_v1.isolated_strategy_tester_replay_launch import run_isolated_strategy_tester_replay_launch
    from ml.a3_meta_v1.isolated_strategy_tester_terminal_root import LAUNCH_APPROVAL_TOKEN

    root = _root_with_c53(tmp_path)

    def fake_launcher(command: list[str], cwd: Path, timeout_seconds: int) -> dict:
        report = cwd / "tester_reports" / "A2_Phase2ExperimentalDemoExecutor_XAUUSD_M5.html"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text("<html>tester output</html>\n", encoding="utf-8")
        agent_csv = cwd / "Tester" / "Agent-127.0.0.1-3000" / "MQL5" / "Files" / "a3_ml_broker_shadow_tap.csv"
        agent_csv.parent.mkdir(parents=True, exist_ok=True)
        agent_csv.write_text("timestamp,signal\n2026.06.22,true\n", encoding="utf-8")
        return {
            "attempted": True,
            "command": command,
            "cwd": str(cwd),
            "returncode": 0,
            "timed_out": False,
            "duration_seconds": 0.1,
            "stdout": "",
            "stderr": "",
        }

    output = run_isolated_strategy_tester_replay_launch(
        root,
        approval_token=LAUNCH_APPROVAL_TOKEN,
        timeout_seconds=5,
        launcher=fake_launcher,
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "STRATEGY_TESTER_REPLAY_LAUNCH_COMPLETED_OUTPUTS_FOUND"
    assert any(str(arg).startswith("/config:") for arg in payload["launch_result"]["command"])
    assert not any(str(arg).startswith('/config:"') for arg in payload["launch_result"]["command"])
    assert payload["boundary"]["terminal_launch_attempted"] is True
    assert payload["boundary"]["strategy_tester_launch_attempted"] is True
    assert payload["boundary"]["mt5_connection_attempted"] is True
    assert payload["authorization"]["training_authorized"] is False
    assert payload["authorization"]["broker_action_authorized"] is False
    output_names = {Path(item["path"]).name for item in payload["replay_outputs"]}
    assert {"A2_Phase2ExperimentalDemoExecutor_XAUUSD_M5.html", "a3_ml_broker_shadow_tap.csv"} <= output_names
    assert all(len(item["sha256"]) == 64 for item in payload["replay_outputs"])
    assert pointer["c54_strategy_tester_replay_launch_status"] == "STRATEGY_TESTER_REPLAY_LAUNCH_COMPLETED_OUTPUTS_FOUND"
    assert pointer["broker_action_authorized"] is False


def test_c54_blocks_without_approval_token(tmp_path: Path) -> None:
    from ml.a3_meta_v1.isolated_strategy_tester_replay_launch import run_isolated_strategy_tester_replay_launch

    root = _root_with_c53(tmp_path)
    output = run_isolated_strategy_tester_replay_launch(root, approval_token="", timeout_seconds=5)
    payload = json.loads(output.read_text(encoding="utf-8"))
    checks = {check["check"]: check for check in payload["prechecks"]}

    assert payload["status"] == "STRATEGY_TESTER_REPLAY_LAUNCH_FAILED_PRECHECK"
    assert payload["launch_result"]["attempted"] is False
    assert checks["approval_token_valid"]["passed"] is False


def test_c54_blocks_isolated_account_context_without_explicit_flag(tmp_path: Path) -> None:
    from ml.a3_meta_v1.isolated_strategy_tester_replay_launch import run_isolated_strategy_tester_replay_launch
    from ml.a3_meta_v1.isolated_strategy_tester_terminal_root import LAUNCH_APPROVAL_TOKEN

    root = _root_with_c53(tmp_path)
    terminal_root = root / "outputs" / "reports" / "strategy_tester_replay" / "DATASET_C54" / "isolated_terminal_roots" / "A2_Phase2ExperimentalDemoExecutor_XAUUSD_M5"
    (terminal_root / "Config" / "accounts.dat").write_bytes(b"user-created-login-context")

    output = run_isolated_strategy_tester_replay_launch(root, approval_token=LAUNCH_APPROVAL_TOKEN, timeout_seconds=5)
    payload = json.loads(output.read_text(encoding="utf-8"))
    checks = {check["check"]: check for check in payload["prechecks"]}

    assert payload["status"] == "STRATEGY_TESTER_REPLAY_LAUNCH_FAILED_PRECHECK"
    assert payload["launch_result"]["attempted"] is False
    assert checks["account_context_absent_or_explicitly_allowed"]["passed"] is False
    assert payload["boundary"]["isolated_account_context_present"] is True
    assert payload["boundary"]["terminal_config_or_account_secret_copied"] is False


def test_c54_allows_isolated_account_context_with_explicit_flag(tmp_path: Path) -> None:
    from ml.a3_meta_v1.isolated_strategy_tester_replay_launch import run_isolated_strategy_tester_replay_launch
    from ml.a3_meta_v1.isolated_strategy_tester_terminal_root import LAUNCH_APPROVAL_TOKEN

    root = _root_with_c53(tmp_path)
    terminal_root = root / "outputs" / "reports" / "strategy_tester_replay" / "DATASET_C54" / "isolated_terminal_roots" / "A2_Phase2ExperimentalDemoExecutor_XAUUSD_M5"
    (terminal_root / "Config" / "accounts.dat").write_bytes(b"user-created-login-context")

    def fake_launcher(command: list[str], cwd: Path, timeout_seconds: int) -> dict:
        report = cwd / "tester_reports" / "A2_Phase2ExperimentalDemoExecutor_XAUUSD_M5.html"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text("<html>tester output</html>\n", encoding="utf-8")
        return {
            "attempted": True,
            "command": command,
            "cwd": str(cwd),
            "returncode": 0,
            "timed_out": False,
            "duration_seconds": 0.1,
            "stdout": "",
            "stderr": "",
        }

    output = run_isolated_strategy_tester_replay_launch(
        root,
        approval_token=LAUNCH_APPROVAL_TOKEN,
        timeout_seconds=5,
        allow_isolated_account_context=True,
        launcher=fake_launcher,
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    checks = {check["check"]: check for check in payload["prechecks"]}

    assert payload["status"] == "STRATEGY_TESTER_REPLAY_LAUNCH_COMPLETED_OUTPUTS_FOUND"
    assert checks["account_context_absent_or_explicitly_allowed"]["passed"] is True
    assert payload["authorization"]["isolated_account_context_allowed_for_this_run"] is True
    assert payload["boundary"]["isolated_account_context_present"] is True
    assert payload["boundary"]["terminal_config_or_account_secret_copied"] is False


def test_c54_script_loads() -> None:
    module = load_script("c54_run_isolated_strategy_tester_replay")

    assert hasattr(module, "main")


def _root_with_c53(tmp_path: Path) -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    terminal_root = root / "outputs" / "reports" / "strategy_tester_replay" / "DATASET_C54" / "isolated_terminal_roots" / "A2_Phase2ExperimentalDemoExecutor_XAUUSD_M5"
    terminal = terminal_root / "terminal64.exe"
    config = terminal_root / "Config" / "A2_Phase2ExperimentalDemoExecutor_XAUUSD_M5.ini"
    terminal.parent.mkdir(parents=True, exist_ok=True)
    config.parent.mkdir(parents=True, exist_ok=True)
    (terminal_root / "tester_reports").mkdir(parents=True, exist_ok=True)
    terminal.write_bytes(b"binary")
    config.write_text("[Tester]\n", encoding="utf-8")
    _write_json(
        reports / "C02_DATASET_POINTER.json",
        {
            "dataset_version": "DATASET_C54",
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
    )
    _write_json(
        reports / "A3_ML_ISOLATED_STRATEGY_TESTER_TERMINAL_ROOT_STATUS.json",
        {
            "status": "ISOLATED_STRATEGY_TESTER_TERMINAL_ROOT_READY",
            "dataset_version": "DATASET_C54",
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
