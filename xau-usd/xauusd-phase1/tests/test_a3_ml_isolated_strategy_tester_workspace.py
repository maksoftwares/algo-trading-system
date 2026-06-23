from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c52_prepares_isolated_strategy_tester_workspaces(tmp_path: Path) -> None:
    from ml.a3_meta_v1.isolated_strategy_tester_workspace import prepare_isolated_strategy_tester_workspace

    root = _root_with_c51(tmp_path)

    output = prepare_isolated_strategy_tester_workspace(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "ISOLATED_STRATEGY_TESTER_WORKSPACE_READY"
    assert payload["ready_lane_count"] == 2
    assert payload["boundary"]["terminal_launch_attempted"] is False
    assert payload["boundary"]["strategy_tester_launch_attempted"] is False
    assert payload["boundary"]["terminal_config_or_account_secret_copied"] is False
    assert payload["boundary"]["broker_action_authorized"] is False
    assert pointer["c52_isolated_strategy_tester_workspace_status"] == "ISOLATED_STRATEGY_TESTER_WORKSPACE_READY"
    assert pointer["python_demo_predictions_authorized"] is False
    for lane in payload["lanes"]:
        workspace = Path(lane["workspace_path"])
        assert lane["workspace_ready"] is True
        assert (workspace / "MQL5" / "Experts").exists()
        assert (workspace / "MQL5" / "Presets").exists()
        assert (workspace / "MQL5" / "Profiles" / "Tester").exists()
        assert Path(lane["copied_expert_path"]).exists()
        assert Path(lane["copied_preset_path"]).exists()
        assert Path(lane["copied_tester_profile_preset_path"]).exists()
        config = Path(lane["isolated_config_path"]).read_text(encoding="utf-8")
        assert "Optimization=0" in config
        assert "ShutdownTerminal=1" in config
        assert "FromDate=2026.02.22" in config
        assert "ToDate=2026.06.22" in config
        launch_stub = Path(lane["review_only_launch_stub"]).read_text(encoding="utf-8")
        assert "IsolatedTerminalExe" in launch_stub
        assert "Refusing active/non-isolated terminal path" in launch_stub
        assert "$configShort" in launch_stub
        assert "'/config:' + $configShort" in launch_stub
        assert len(lane["artifacts"]) == 5
        assert all(len(artifact["sha256"]) == 64 for artifact in lane["artifacts"])


def test_c52_blocks_when_c51_lane_is_not_ready(tmp_path: Path) -> None:
    from ml.a3_meta_v1.isolated_strategy_tester_workspace import prepare_isolated_strategy_tester_workspace

    root = _root_with_c51(tmp_path)
    c51_path = root / "outputs" / "reports" / "A3_ML_STRATEGY_TESTER_REPLAY_PACKET_STATUS.json"
    c51 = json.loads(c51_path.read_text(encoding="utf-8"))
    c51["lanes"][0]["config_ready"] = False
    c51_path.write_text(json.dumps(c51, indent=2), encoding="utf-8")

    output = prepare_isolated_strategy_tester_workspace(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "ISOLATED_STRATEGY_TESTER_WORKSPACE_BLOCKED"
    assert payload["ready_lane_count"] == 1
    assert payload["lanes"][0]["workspace_ready"] is False
    assert payload["lanes"][0]["workspace_path"] == ""


def test_c52_script_loads() -> None:
    module = load_script("c52_prepare_isolated_strategy_tester_workspace")

    assert hasattr(module, "main")


def _root_with_c51(tmp_path: Path) -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    _write_json(
        reports / "C02_DATASET_POINTER.json",
        {
            "dataset_version": "DATASET_C51",
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
    )
    lanes = [
        _lane(root, "A1", "1025742", "Phase2ExperimentalDemoExecutor"),
        _lane(root, "A2", "1033030", "Phase2ExperimentalDemoExecutor"),
    ]
    _write_json(
        reports / "A3_ML_STRATEGY_TESTER_REPLAY_PACKET_STATUS.json",
        {
            "status": "STRATEGY_TESTER_REPLAY_PACKET_READY",
            "dataset_version": "DATASET_C51",
            "window": {
                "historical_start_utc": "2026-02-22T05:47:00Z",
                "snapshot_cutoff_utc": "2026-06-22T05:47:00Z",
                "symbol": "XAUUSD",
            },
            "outputs": {
                "packet_dir": str(root / "outputs" / "reports" / "strategy_tester_replay" / "DATASET_C51"),
            },
            "lanes": lanes,
        },
    )
    return root


def _lane(root: Path, account: str, login: str, expert: str) -> dict:
    terminal = root / "_terminal_sources" / account
    expert_path = terminal / "MQL5" / "Experts" / f"{expert}.ex5"
    preset_path = terminal / "MQL5" / "Presets" / f"{expert}.{account}.a3_ml_shadow_readonly.set"
    expert_path.parent.mkdir(parents=True, exist_ok=True)
    preset_path.parent.mkdir(parents=True, exist_ok=True)
    expert_path.write_bytes(f"{expert}-compiled".encode("ascii"))
    preset_path.write_text(
        "\n".join(
            [
                "InpDryRunOnly=true",
                "InpBrokerActionAllowed=false",
                "InpTargetSymbol=XAUUSD",
                f"InpAllowedAccountLoginsCsv={login}",
            ]
        ),
        encoding="utf-8",
    )
    return {
        "account_label": account,
        "account_scope": login,
        "symbol": "XAUUSD",
        "timeframe": "M5",
        "expert_name": expert,
        "expert_deployed_path": str(expert_path),
        "preset_path": str(preset_path),
        "config_ready": True,
        "config_path": str(root / "outputs" / "reports" / "strategy_tester_replay" / "DATASET_C51" / "configs" / f"{account}_{expert}_XAUUSD_M5.ini"),
        "preset_guard_checks": [
            {"check": "preset_exists", "passed": True, "detail": str(preset_path)},
            {"check": "dry_run_only_true", "passed": True, "detail": "InpDryRunOnly=true"},
            {"check": "broker_action_allowed_false", "passed": True, "detail": "InpBrokerActionAllowed=false"},
        ],
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
