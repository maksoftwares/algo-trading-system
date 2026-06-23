from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c51_generates_safe_strategy_tester_replay_packet(tmp_path: Path) -> None:
    from ml.a3_meta_v1.strategy_tester_replay_packet import generate_strategy_tester_replay_packet

    root = _root_with_strategy_tester_assets(tmp_path)

    output = generate_strategy_tester_replay_packet(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "STRATEGY_TESTER_REPLAY_PACKET_READY"
    assert payload["ready_lane_count"] == 6
    assert payload["lane_count"] == 6
    assert payload["authorization"]["strategy_tester_launch_authorized"] is False
    assert payload["authorization"]["training_authorized"] is False
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert payload["authorization"]["ea_consumption_authorized"] is False
    assert payload["authorization"]["broker_action_authorized"] is False
    assert payload["boundary"]["strategy_tester_launch_attempted"] is False
    assert payload["boundary"]["terminal_data_root_write_attempted"] is False
    assert pointer["c51_strategy_tester_replay_packet_status"] == "STRATEGY_TESTER_REPLAY_PACKET_READY"
    assert pointer["broker_action_authorized"] is False
    for lane in payload["lanes"]:
        assert lane["config_ready"] is True
        assert Path(lane["config_path"]).exists()
        config = Path(lane["config_path"]).read_text(encoding="utf-8")
        assert "ShutdownTerminal=1" in config
        assert "Optimization=0" in config
        assert "FromDate=2026.02.22" in config
        assert "ToDate=2026.06.22" in config


def test_c51_blocks_unsafe_or_missing_preset(tmp_path: Path) -> None:
    from ml.a3_meta_v1.strategy_tester_replay_packet import generate_strategy_tester_replay_packet

    root = _root_with_strategy_tester_assets(tmp_path)
    unsafe = root / "_terminals" / "A2" / "MQL5" / "Presets" / "Phase2ExperimentalDemoExecutor.A2.a3_ml_shadow_readonly.set"
    unsafe.write_text(
        "\n".join(
            [
                "InpDryRunOnly=false",
                "InpBrokerActionAllowed=true",
                "InpTargetSymbol=XAUUSD",
                "InpAllowedAccountLoginsCsv=1033030",
            ]
        ),
        encoding="utf-8",
    )

    output = generate_strategy_tester_replay_packet(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    a2_lane = next(lane for lane in payload["lanes"] if lane["account_label"] == "A2")
    checks = {check["check"]: check for check in a2_lane["preset_guard_checks"]}

    assert payload["status"] == "STRATEGY_TESTER_REPLAY_PACKET_BLOCKED_MISSING_SAFE_EVIDENCE"
    assert a2_lane["config_ready"] is False
    assert a2_lane["config_path"] == ""
    assert checks["dry_run_only_true"]["passed"] is False
    assert checks["broker_action_allowed_false"]["passed"] is False


def test_c51_script_loads() -> None:
    module = load_script("c51_generate_strategy_tester_replay_packet")

    assert hasattr(module, "main")


def _root_with_strategy_tester_assets(tmp_path: Path) -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    _write_json(
        reports / "C02_DATASET_POINTER.json",
        {
            "dataset_version": "xauusd_c02_multiacct_TEST",
            "snapshot_cutoff_utc": "2026-06-22T05:47:00Z",
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
    )
    _write_json(
        reports / "A3_ML_HISTORICAL_BACKFILL_REPLAY_PLAN_STATUS.json",
        {
            "status": "HISTORICAL_BACKFILL_REPLAY_PLAN_READY",
            "dataset_version": "xauusd_c02_multiacct_TEST",
            "window": {
                "historical_start_utc": "2026-02-22T05:47:00Z",
                "snapshot_cutoff_utc": "2026-06-22T05:47:00Z",
            },
        },
    )
    terminals = root / "_terminals"
    _write_registry(root, terminals)
    _write_lane(terminals / "A1", "Phase2ExperimentalDemoExecutor", "Phase2ExperimentalDemoExecutor.A1.a3_ml_shadow_readonly.set", "1025742")
    _write_lane(terminals / "A2", "Phase2ExperimentalDemoExecutor", "Phase2ExperimentalDemoExecutor.A2.a3_ml_shadow_readonly.set", "1033030")
    for expert in (
        "Account3BreakoutPlainExecutor",
        "Account3BreakoutImprovedExecutor",
        "Account3BreakoutTier1CompatExecutor",
        "Account3SoftRetestExecutor",
    ):
        _write_lane(terminals / "A3", expert, f"{expert}.A3.a3_ml_shadow_readonly.set", "1033669")
    return root


def _write_lane(terminal_root: Path, expert: str, preset_name: str, login: str) -> None:
    expert_path = terminal_root / "MQL5" / "Experts" / f"{expert}.ex5"
    expert_path.parent.mkdir(parents=True, exist_ok=True)
    expert_path.write_bytes(b"compiled")
    preset_path = terminal_root / "MQL5" / "Presets" / preset_name
    preset_path.parent.mkdir(parents=True, exist_ok=True)
    preset_path.write_text(
        "\n".join(
            [
                "InpDryRunOnly=true",
                "InpBrokerActionAllowed=false",
                "InpMlShadowReadEnabled=true",
                "InpTargetSymbol=XAUUSD",
                "InpExpectedServerMarker=Demo",
                f"InpAllowedAccountLoginsCsv={login}",
            ]
        ),
        encoding="utf-8",
    )


def _write_registry(root: Path, terminals: Path) -> None:
    _write_json(
        root / "config" / "ml" / "mt5_accounts.yaml",
        {
            "schema_version": "mt5_multi_account_registry_v1",
            "common": {
                "symbol": "XAUUSD",
                "expected_server_regex": "^Capital\\.ComMena-Demo$",
                "require_demo_trade_mode": True,
                "require_existing_terminal_process": True,
                "allow_mt5_login_call": False,
                "allow_symbol_select_call": False,
                "export_timezone": "UTC",
                "snapshot_safety_lag_minutes": 5,
            },
            "accounts": {
                "A1": {
                    "account_scope": "1025742",
                    "account_label": "A1",
                    "expected_login": "1025742",
                    "terminal_exe": str(terminals / "A1" / "terminal64.exe"),
                    "expected_data_path": str(terminals / "A1"),
                    "portable": False,
                    "role": "standard_experimental_demo",
                    "symbol": "XAUUSD",
                    "files_roots": [str(terminals / "A1" / "MQL5" / "Files")],
                    "log_catalog": "config/ml/log_catalog_a1.yaml",
                },
                "A2": {
                    "account_scope": "1033030",
                    "account_label": "A2",
                    "expected_login": "1033030",
                    "terminal_exe": str(terminals / "A2" / "terminal64.exe"),
                    "expected_data_path": str(terminals / "A2"),
                    "portable": True,
                    "role": "tier1_breakout_only",
                    "symbol": "XAUUSD",
                    "files_roots": [str(terminals / "A2" / "MQL5" / "Files")],
                    "log_catalog": "config/ml/log_catalog_a2.yaml",
                },
                "A3": {
                    "account_scope": "1033669",
                    "account_label": "A3",
                    "expected_login": "1033669",
                    "terminal_exe": str(terminals / "A3" / "terminal64.exe"),
                    "expected_data_path": str(terminals / "A3"),
                    "portable": True,
                    "role": "paused_repair_lane",
                    "symbol": "XAUUSD",
                    "files_roots": [str(terminals / "A3" / "MQL5" / "Files")],
                    "log_catalog": "config/ml/log_catalog_a3.yaml",
                },
            },
        },
    )


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
