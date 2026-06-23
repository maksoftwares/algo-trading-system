from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c56_imports_replay_as_quarantined_observer_only(tmp_path: Path) -> None:
    from ml.a3_meta_v1.strategy_tester_replay_observer_import import (
        import_strategy_tester_replay_observer_evidence,
    )

    root = _root_with_replay(tmp_path)

    output = import_strategy_tester_replay_observer_evidence(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))
    observer_csv = Path(payload["outputs"]["quarantined_observer_csv"])
    rows = list(csv.DictReader(observer_csv.open("r", encoding="utf-8", newline="")))

    assert payload["status"] == "REPLAY_OBSERVER_IMPORT_QUARANTINED"
    assert payload["source_type"] == "strategy_tester_replay"
    assert payload["label_status"] == "REPLAY_OBSERVER_ONLY"
    assert payload["row_counts"]["signal_rows_imported"] == 2
    assert payload["row_counts"]["signal_would_signal_rows"] == 1
    assert payload["row_counts"]["order_rows"] == 0
    assert payload["authorization"]["training_authorized"] is False
    assert payload["authorization"]["broker_action_authorized"] is False
    assert rows[0]["source_type"] == "strategy_tester_replay"
    assert rows[0]["label_status"] == "REPLAY_OBSERVER_ONLY"
    assert rows[0]["candidate_trainable"] == "false"
    assert rows[0]["training_authorized"] == "false"
    assert Path(payload["outputs"]["raw_replay_root"], "Tester", "logs", "20260622.log").exists()
    assert pointer["c56_replay_import_status"] == "REPLAY_OBSERVER_IMPORT_QUARANTINED"
    assert pointer["python_demo_predictions_authorized"] is False
    assert pointer["ea_consumption_authorized"] is False
    assert pointer["broker_action_authorized"] is False


def test_c56_blocks_if_signal_log_is_not_dry_run(tmp_path: Path) -> None:
    from ml.a3_meta_v1.strategy_tester_replay_observer_import import (
        import_strategy_tester_replay_observer_evidence,
    )

    root = _root_with_replay(tmp_path, signal_dry_run="false")

    output = import_strategy_tester_replay_observer_evidence(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    checks = {check["check"]: check for check in payload["validation"]["checks"]}

    assert payload["status"] == "REPLAY_OBSERVER_IMPORT_BLOCKED"
    assert checks["signal_log_all_dry_run_true"]["passed"] is False
    assert payload["outputs"]["quarantined_observer_csv"] == ""
    assert payload["authorization"]["training_authorized"] is False


def test_c56_script_loads() -> None:
    module = load_script("c56_import_strategy_tester_replay_observer")

    assert hasattr(module, "main")


def _root_with_replay(tmp_path: Path, *, signal_dry_run: str = "true") -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    dataset_root = root / "data" / "ml" / "a3_meta_v1" / "c02" / "DATASET_C56"
    terminal_root = tmp_path / "terminal"
    files = terminal_root / "Tester" / "Agent-127.0.0.1-3000" / "MQL5" / "Files"
    logs = terminal_root / "Tester" / "logs"
    agent_logs = terminal_root / "Tester" / "Agent-127.0.0.1-3000" / "logs"
    signal = files / "a3_breakout_tier1_compat_signal_log.csv"
    shadow = files / "a3_ml_broker_shadow_tap.csv"
    order = files / "a3_breakout_tier1_compat_order_log.csv"
    management = files / "a3_breakout_tier1_compat_management_log.csv"
    startup = files / "a3_breakout_tier1_compat_startup.csv"
    tester_log = logs / "20260622.log"
    agent_log = agent_logs / "20260622.log"
    _write_csv(
        signal,
        [
            {
                "timestamp_utc": "2026.02.22 23:10:00",
                "timestamp_broker": "2026.02.22 23:10:00",
                "account_server": "Capital.ComMena-Demo",
                "account_login": "1033669",
                "symbol": "XAUUSD",
                "run_id": "A3_BREAKOUT_TIER1_COMPAT_V1",
                "would_signal": "true",
                "dry_run": signal_dry_run,
                "broker_action_allowed": "false",
                "m5_bar_time": "2026.02.22 23:10:00",
                "direction": "LONG",
                "stage": "WOULD_SIGNAL",
            },
            {
                "timestamp_utc": "2026.02.22 23:15:00",
                "timestamp_broker": "2026.02.22 23:15:00",
                "account_server": "Capital.ComMena-Demo",
                "account_login": "1033669",
                "symbol": "XAUUSD",
                "run_id": "A3_BREAKOUT_TIER1_COMPAT_V1",
                "would_signal": "false",
                "dry_run": "true",
                "broker_action_allowed": "false",
                "m5_bar_time": "2026.02.22 23:15:00",
                "direction": "SHORT",
                "stage": "WAIT_LEVEL_BREAK_RETEST",
            },
        ],
    )
    _write_csv(
        shadow,
        [
            {
                "timestamp_utc": "2026.02.22 23:10:00",
                "account_server": "Capital.ComMena-Demo",
                "account_login": "1033669",
                "symbol": "XAUUSD",
                "event_source": "SIGNAL",
                "run_id": "A3_BREAKOUT_TIER1_COMPAT_V1",
                "ea_dry_run": "true",
                "ea_broker_action_allowed": "false",
                "ml_shadow_read_enabled": "true",
                "ml_broker_action_authorized": "false",
            }
        ],
    )
    _write_csv(order, [])
    _write_csv(management, [])
    _write_csv(startup, [{"timestamp_utc": "2026.02.22 00:00:00", "dry_run": "true", "broker_action_allowed": "false"}])
    tester_log.parent.mkdir(parents=True, exist_ok=True)
    tester_log.write_text("automatic testing finished\n", encoding="utf-8")
    agent_log.parent.mkdir(parents=True, exist_ok=True)
    agent_log.write_text("test passed\n", encoding="utf-8")
    replay_outputs = []
    for path in (signal, shadow, order, management, startup, tester_log, agent_log):
        replay_outputs.append({"path": str(path), "size_bytes": path.stat().st_size, "sha256": _sha256(path)})
    _write_json(
        reports / "C02_DATASET_POINTER.json",
        {
            "dataset_version": "DATASET_C56",
            "output_root": str(dataset_root),
            "snapshot_cutoff_utc": "2026-06-22T05:47:00Z",
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
    )
    dataset_root.mkdir(parents=True, exist_ok=True)
    _write_json(
        reports / "A3_ML_ISOLATED_STRATEGY_TESTER_TERMINAL_ROOT_STATUS.json",
        {
            "status": "ISOLATED_STRATEGY_TESTER_TERMINAL_ROOT_READY",
            "dataset_version": "DATASET_C56",
            "selected_lane_id": "A3_Account3BreakoutTier1CompatExecutor_XAUUSD_M5",
            "selected_lane": {
                "account_label": "A3",
                "account_scope": "1033669",
                "terminal_root": str(terminal_root),
            },
        },
    )
    _write_json(
        reports / "A3_ML_STRATEGY_TESTER_REPLAY_LAUNCH_STATUS.json",
        {
            "status": "STRATEGY_TESTER_REPLAY_LAUNCH_COMPLETED_OUTPUTS_FOUND",
            "dataset_version": "DATASET_C56",
            "selected_lane_id": "A3_Account3BreakoutTier1CompatExecutor_XAUUSD_M5",
            "replay_outputs": replay_outputs,
        },
    )
    _write_json(
        reports / "A3_ML_STRATEGY_TESTER_ACCOUNT_CONTEXT_DECISION_STATUS.json",
        {
            "status": "STRATEGY_TESTER_ACCOUNT_CONTEXT_DECISION_NOT_REQUIRED",
            "dataset_version": "DATASET_C56",
        },
    )
    return root


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else ["timestamp_utc"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()
