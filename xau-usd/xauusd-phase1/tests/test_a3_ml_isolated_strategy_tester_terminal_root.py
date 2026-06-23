from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c53_prepares_one_isolated_terminal_root_without_secrets(tmp_path: Path) -> None:
    from ml.a3_meta_v1.isolated_strategy_tester_terminal_root import prepare_isolated_strategy_tester_terminal_root

    root = _root_with_c51_c52(tmp_path)

    output = prepare_isolated_strategy_tester_terminal_root(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    selected = payload["selected_lane"]
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "ISOLATED_STRATEGY_TESTER_TERMINAL_ROOT_READY"
    assert payload["selected_lane_id"] == "A2_Phase2ExperimentalDemoExecutor_XAUUSD_M5"
    assert payload["authorization"]["strategy_tester_launch_authorized"] is False
    assert payload["boundary"]["terminal_launch_attempted"] is False
    assert payload["boundary"]["strategy_tester_launch_attempted"] is False
    assert payload["boundary"]["terminal_config_or_account_secret_copied"] is False
    assert payload["boundary"]["account_dat_copied"] is False
    assert payload["boundary"]["server_dat_copied"] is False
    assert pointer["c53_isolated_strategy_tester_terminal_root_status"] == "ISOLATED_STRATEGY_TESTER_TERMINAL_ROOT_READY"
    assert pointer["broker_action_authorized"] is False
    terminal_root = Path(selected["terminal_root"])
    assert (terminal_root / "terminal64.exe").exists()
    assert (terminal_root / "MQL5" / "Experts" / "Phase2ExperimentalDemoExecutor.ex5").exists()
    assert (terminal_root / "MQL5" / "Presets" / "Phase2ExperimentalDemoExecutor.A2.a3_ml_shadow_readonly.set").exists()
    assert (terminal_root / "MQL5" / "Profiles" / "Tester" / "Phase2ExperimentalDemoExecutor.A2.a3_ml_shadow_readonly.set").exists()
    assert (terminal_root / "Config" / "NO_ACCOUNT_SECRETS_COPIED.txt").exists()
    assert not (terminal_root / "Config" / "accounts.dat").exists()
    assert not (terminal_root / "Config" / "servers.dat").exists()
    config = Path(selected["tester_config_path"]).read_text(encoding="utf-8")
    assert "FromDate=2026.02.22" in config
    assert "ToDate=2026.06.22" in config
    assert "ExpertParameters=Phase2ExperimentalDemoExecutor.A2.a3_ml_shadow_readonly.set" in config
    launch_stub = Path(selected["review_only_launch_stub"]).read_text(encoding="utf-8")
    assert "ApprovalToken" in launch_stub
    assert "RUN_ISOLATED_TESTER_REVIEW_ONLY" in launch_stub
    assert "$configShort = $fso.GetFile($config).ShortPath" in launch_stub
    assert "$configArg = '/config:' + $configShort" in launch_stub
    assert "Start-Process" in launch_stub
    assert all(len(artifact["sha256"]) == 64 for artifact in selected["artifacts"])


def test_c53_blocks_terminal_root_outside_strategy_tester_outputs(tmp_path: Path) -> None:
    from ml.a3_meta_v1.isolated_strategy_tester_terminal_root import prepare_isolated_strategy_tester_terminal_root

    root = _root_with_c51_c52(tmp_path)

    output = prepare_isolated_strategy_tester_terminal_root(root, terminal_root=tmp_path / "outside")
    payload = json.loads(output.read_text(encoding="utf-8"))
    checks = {check["check"]: check for check in payload["selected_lane"]["checks"]}

    assert payload["status"] == "ISOLATED_STRATEGY_TESTER_TERMINAL_ROOT_BLOCKED"
    assert checks["terminal_root_inside_allowed_isolated_roots"]["passed"] is False


def test_c53_script_loads() -> None:
    module = load_script("c53_prepare_isolated_strategy_tester_terminal_root")

    assert hasattr(module, "main")


def _root_with_c51_c52(tmp_path: Path) -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    _write_json(
        reports / "C02_DATASET_POINTER.json",
        {
            "dataset_version": "DATASET_C53",
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
    )
    source_terminal = root / "_source_terminal"
    for name in ("terminal64.exe", "MetaEditor64.exe", "metatester64.exe", "Terminal.ico"):
        path = source_terminal / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"{name}-binary".encode("ascii"))
    workspace_root = root / "outputs" / "reports" / "strategy_tester_replay" / "DATASET_C53" / "isolated_workspaces"
    lane_names = ("A1_Phase2ExperimentalDemoExecutor_XAUUSD_M5", "A2_Phase2ExperimentalDemoExecutor_XAUUSD_M5")
    c51_lanes = []
    c52_lanes = []
    for lane_name in lane_names:
        account = lane_name.split("_", 1)[0]
        login = "1025742" if account == "A1" else "1033030"
        workspace = workspace_root / lane_name
        expert_path = workspace / "MQL5" / "Experts" / "Phase2ExperimentalDemoExecutor.ex5"
        preset_path = workspace / "MQL5" / "Presets" / f"Phase2ExperimentalDemoExecutor.{account}.a3_ml_shadow_readonly.set"
        expert_path.parent.mkdir(parents=True, exist_ok=True)
        preset_path.parent.mkdir(parents=True, exist_ok=True)
        expert_path.write_bytes(b"compiled")
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
        isolated_config = workspace / "Config" / f"{lane_name}.ini"
        isolated_config.parent.mkdir(parents=True, exist_ok=True)
        isolated_config.write_text("[Tester]\n", encoding="utf-8")
        c51_lanes.append(
            {
                "account_label": account,
                "account_scope": login,
                "terminal_exe": str(source_terminal / "terminal64.exe"),
                "expert_name": "Phase2ExperimentalDemoExecutor",
                "symbol": "XAUUSD",
                "timeframe": "M5",
                "config_ready": True,
                "config_path": str(root / "outputs" / "reports" / "strategy_tester_replay" / "DATASET_C53" / "configs" / f"{lane_name}.ini"),
            }
        )
        c52_lanes.append(
            {
                "account_label": account,
                "account_scope": login,
                "expert_name": "Phase2ExperimentalDemoExecutor",
                "symbol": "XAUUSD",
                "timeframe": "M5",
                "workspace_ready": True,
                "workspace_path": str(workspace),
                "copied_expert_path": str(expert_path),
                "copied_preset_path": str(preset_path),
                "isolated_config_path": str(isolated_config),
            }
        )
    _write_json(
        reports / "A3_ML_STRATEGY_TESTER_REPLAY_PACKET_STATUS.json",
        {
            "status": "STRATEGY_TESTER_REPLAY_PACKET_READY",
            "dataset_version": "DATASET_C53",
            "window": {
                "historical_start_utc": "2026-02-22T05:47:00Z",
                "snapshot_cutoff_utc": "2026-06-22T05:47:00Z",
            },
            "lanes": c51_lanes,
        },
    )
    _write_json(
        reports / "A3_ML_ISOLATED_STRATEGY_TESTER_WORKSPACE_STATUS.json",
        {
            "status": "ISOLATED_STRATEGY_TESTER_WORKSPACE_READY",
            "dataset_version": "DATASET_C53",
            "workspace_root": str(workspace_root),
            "lanes": c52_lanes,
        },
    )
    return root


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
