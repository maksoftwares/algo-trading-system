from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c27_waits_when_handoff_ready_but_tap_logs_missing(tmp_path: Path) -> None:
    from ml.a3_meta_v1.research_preview_runtime_verifier import verify_research_preview_runtime_read_path

    root = _root_with_runtime_state(tmp_path, tap_logs=False)

    output = verify_research_preview_runtime_read_path(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "WAITING_FOR_MT5_RUNTIME_ATTACH"
    assert payload["runtime_evidence"]["handoff_research_preview_ready_all_accounts"] is True
    assert payload["runtime_evidence"]["research_preview_read_path_confirmed_all_accounts"] is False
    assert payload["authorization"]["broker_action_authorized"] is False


def test_c27_confirms_research_preview_read_path_when_all_taps_log(tmp_path: Path) -> None:
    from ml.a3_meta_v1.research_preview_runtime_verifier import verify_research_preview_runtime_read_path

    root = _root_with_runtime_state(tmp_path, tap_logs=True)

    output = verify_research_preview_runtime_read_path(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "RESEARCH_PREVIEW_READ_PATH_CONFIRMED_ALL_ACCOUNTS"
    assert all(item["research_preview_read_path_confirmed"] for item in payload["accounts"])
    assert payload["runtime_evidence"]["research_preview_read_path_confirmed_all_accounts"] is True
    assert pointer["c27_research_preview_read_path_confirmed_all_accounts"] is True


def test_c27_blocks_when_handoff_is_not_fail_closed(tmp_path: Path) -> None:
    from ml.a3_meta_v1.research_preview_runtime_verifier import verify_research_preview_runtime_read_path

    root = _root_with_runtime_state(tmp_path, tap_logs=False)
    handoff = tmp_path / "A1" / "MQL5" / "Files" / "A3_ML_EA_HANDOFF.csv"
    rows = list(csv.DictReader(handoff.open(encoding="utf-8")))
    rows[0]["action"] = "TAKE"
    _write_csv(handoff, rows, list(rows[0].keys()))

    output = verify_research_preview_runtime_read_path(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "PREFLIGHT_BLOCKED"
    assert any(item["check"] == "A1_handoff_research_preview_ready" and not item["passed"] for item in payload["validations"])


def test_c27_script_loads() -> None:
    module = load_script("c27_verify_research_preview_runtime_read_path")

    assert hasattr(module, "main")


def _root_with_runtime_state(tmp_path: Path, *, tap_logs: bool) -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    config = root / "config" / "ml"
    reports.mkdir(parents=True)
    config.mkdir(parents=True)
    _write_json(config / "mt5_accounts.yaml", _registry(tmp_path))
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})
    _write_json(
        reports / "A3_ML_RESEARCH_PREVIEW_HANDOFF_REHEARSAL_STATUS.json",
        {
            "status": "PUBLISHED_RESEARCH_PREVIEW_FAIL_CLOSED",
            "authorization": {
                "python_demo_predictions_authorized": False,
                "ea_consumption_authorized": False,
                "broker_action_authorized": False,
            },
        },
    )
    _write_json(reports / "A3_ML_BROKER_SHADOW_MANUAL_ATTACH_PACKET.json", {"status": "MANUAL_ATTACH_REQUIRED"})
    for scope, label in (("1025742", "A1"), ("1033030", "A2"), ("1033669", "A3")):
        files = tmp_path / label / "MQL5" / "Files"
        files.mkdir(parents=True)
        _write_csv(
            files / "A3_ML_EA_HANDOFF.csv",
            [_handoff_row(scope, label)],
            _handoff_fields(),
        )
        if tap_logs:
            _write_csv(
                files / "a3_ml_broker_shadow_tap.csv",
                [_tap_row(scope)],
                _tap_fields(),
            )
    return root


def _handoff_row(scope: str, label: str) -> dict[str, str]:
    return {
        "schema_version": "a3_ml_ea_handoff_v1",
        "generated_at_utc": "2026-06-21T12:00:00Z",
        "expires_at_utc": "2026-06-28T12:00:00Z",
        "dataset_version": "TEST",
        "account_scope": scope,
        "account_label": label,
        "symbol": "XAUUSD",
        "exact_signal_id": f"{scope}-preview",
        "setup_group_id": "G1",
        "decision_time_utc": "2026-06-21T12:00:00Z",
        "direction": "LONG",
        "p_win_calibrated": "0.5100000000",
        "threshold": "",
        "action": "ABSTAIN",
        "reason": "C26_RESEARCH_PREVIEW_NOT_AUTHORIZED_FOR_DEMO",
        "model_id": "a3_m0_exploratory_TEST",
        "model_hash": "abc",
        "feature_schema_hash": "def",
        "drift_status": "ML_RESEARCH_PREVIEW_FAIL_CLOSED",
        "broker_action_authorized": "false",
    }


def _tap_row(scope: str) -> dict[str, str]:
    return {
        "timestamp_broker": "2026.06.21 12:00:00",
        "timestamp_utc": "2026.06.21 12:00:00",
        "timestamp_local": "2026.06.21 12:00:00",
        "account_server": "Capital.ComMena-Demo",
        "account_login": scope,
        "symbol": "XAUUSD",
        "event_source": "STARTUP",
        "run_id": "TEST",
        "ea_dry_run": "true",
        "ea_broker_action_allowed": "false",
        "ml_shadow_read_enabled": "true",
        "ml_handoff_file": "A3_ML_EA_HANDOFF.csv",
        "ml_available": "true",
        "ml_action": "ABSTAIN",
        "ml_probability": "0.510000",
        "ml_threshold": "",
        "ml_direction": "LONG",
        "ml_reason": "C26_RESEARCH_PREVIEW_NOT_AUTHORIZED_FOR_DEMO",
        "ml_model_id": "a3_m0_exploratory_TEST",
        "ml_drift_status": "ML_RESEARCH_PREVIEW_FAIL_CLOSED",
        "ml_broker_action_authorized": "false",
        "candidate_or_comment": "TEST",
        "signal_stage": "ON_INIT",
        "signal_direction": "NONE",
        "signal_would_signal": "false",
        "reason_code": "PASS",
        "guard_reason": "PASS",
    }


def _handoff_fields() -> list[str]:
    return [
        "schema_version",
        "generated_at_utc",
        "expires_at_utc",
        "dataset_version",
        "account_scope",
        "account_label",
        "symbol",
        "exact_signal_id",
        "setup_group_id",
        "decision_time_utc",
        "direction",
        "p_win_calibrated",
        "threshold",
        "action",
        "reason",
        "model_id",
        "model_hash",
        "feature_schema_hash",
        "drift_status",
        "broker_action_authorized",
    ]


def _tap_fields() -> list[str]:
    return [
        "timestamp_broker",
        "timestamp_utc",
        "timestamp_local",
        "account_server",
        "account_login",
        "symbol",
        "event_source",
        "run_id",
        "ea_dry_run",
        "ea_broker_action_allowed",
        "ml_shadow_read_enabled",
        "ml_handoff_file",
        "ml_available",
        "ml_action",
        "ml_probability",
        "ml_threshold",
        "ml_direction",
        "ml_reason",
        "ml_model_id",
        "ml_drift_status",
        "ml_broker_action_authorized",
        "candidate_or_comment",
        "signal_stage",
        "signal_direction",
        "signal_would_signal",
        "reason_code",
        "guard_reason",
    ]


def _registry(tmp_path: Path) -> dict:
    return {
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
            "A1": _account("1025742", "A1", tmp_path / "A1"),
            "A2": _account("1033030", "A2", tmp_path / "A2"),
            "A3": _account("1033669", "A3", tmp_path / "A3"),
        },
    }


def _account(scope: str, label: str, data_root: Path) -> dict:
    return {
        "account_scope": scope,
        "account_label": label,
        "expected_login": scope,
        "terminal_exe": str(data_root / "terminal64.exe"),
        "expected_data_path": str(data_root),
        "portable": label != "A1",
        "role": "test",
        "symbol": "XAUUSD",
        "files_roots": [str(data_root / "MQL5" / "Files")],
        "log_catalog": f"config/ml/log_catalog_{label.lower()}.yaml",
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
