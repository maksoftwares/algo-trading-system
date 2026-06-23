from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


NOW = datetime(2026, 6, 22, 0, 0, tzinfo=timezone.utc)


def test_c33_reports_collecting_while_waiting_for_data(tmp_path: Path) -> None:
    from ml.a3_meta_v1.demo_shadow_collection_health import check_demo_shadow_collection_health

    root = _root_with_accounts(tmp_path, c03_status="NO_GO", c23_authorized=False)

    output = check_demo_shadow_collection_health(root, now_utc=NOW, max_stale_seconds=3600)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "COLLECTING_LIVE_WAITING_FOR_DATA"
    assert payload["collection_health"]["all_accounts_collecting"] is True
    assert payload["collection_health"]["total_handoff_rows"] == 6
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert pointer["c33_demo_shadow_collection_health_status"] == "COLLECTING_LIVE_WAITING_FOR_DATA"
    assert pointer["c33_all_accounts_collecting"] is True
    assert pointer["broker_action_authorized"] is False


def test_c33_reports_stale_or_partial_collection(tmp_path: Path) -> None:
    from ml.a3_meta_v1.demo_shadow_collection_health import check_demo_shadow_collection_health

    root = _root_with_accounts(tmp_path, c03_status="NO_GO", c23_authorized=False)
    stale_path = tmp_path / "A2" / "MQL5" / "Files" / "a3_ml_prediction_observer_log.csv"
    _set_mtime(stale_path, NOW - timedelta(hours=2))

    output = check_demo_shadow_collection_health(root, now_utc=NOW, max_stale_seconds=300)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "STALE_OR_PARTIAL_COLLECTION"
    assert payload["collection_health"]["observer_prediction_fresh_all_accounts"] is False
    assert payload["collection_health"]["all_accounts_collecting"] is False


def test_c33_reports_official_pipeline_review_when_c03_passes_but_c23_does_not_authorize(tmp_path: Path) -> None:
    from ml.a3_meta_v1.demo_shadow_collection_health import check_demo_shadow_collection_health

    root = _root_with_accounts(tmp_path, c03_status="PASS", c23_authorized=False)

    output = check_demo_shadow_collection_health(root, now_utc=NOW, max_stale_seconds=3600)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "READY_FOR_OFFICIAL_PIPELINE_REVIEW"
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert payload["authorization"]["ea_consumption_authorized"] is False


def test_c33_only_mirrors_c23_authorization_when_collection_is_healthy(tmp_path: Path) -> None:
    from ml.a3_meta_v1.demo_shadow_collection_health import check_demo_shadow_collection_health

    root = _root_with_accounts(tmp_path, c03_status="PASS", c23_authorized=True)

    output = check_demo_shadow_collection_health(root, now_utc=NOW, max_stale_seconds=3600)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "READY_FOR_DEMO_PYTHON_PREDICTIONS"
    assert payload["authorization"]["python_demo_predictions_authorized"] is True
    assert payload["authorization"]["ea_consumption_authorized"] is True
    assert payload["authorization"]["broker_action_authorized"] is False


def test_c33_blocks_missing_handoff(tmp_path: Path) -> None:
    from ml.a3_meta_v1.demo_shadow_collection_health import check_demo_shadow_collection_health

    root = _root_with_accounts(tmp_path, c03_status="NO_GO", c23_authorized=False)
    (tmp_path / "A3" / "MQL5" / "Files" / "A3_ML_EA_HANDOFF.csv").unlink()

    output = check_demo_shadow_collection_health(root, now_utc=NOW, max_stale_seconds=3600)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "PREFLIGHT_BLOCKED"


def test_c33_script_loads() -> None:
    module = load_script("c33_check_demo_shadow_collection_health")

    assert hasattr(module, "main")


def _root_with_accounts(tmp_path: Path, *, c03_status: str, c23_authorized: bool) -> Path:
    root = tmp_path / "phase1"
    config = root / "config" / "ml"
    reports = root / "outputs" / "reports"
    config.mkdir(parents=True)
    reports.mkdir(parents=True)
    _write_json(config / "mt5_accounts.yaml", _registry(tmp_path))
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "DATASET_A"})
    _write_json(reports / "C03_TRAINING_READINESS_REPORT.json", {"status": c03_status, "dataset_version": "DATASET_A"})
    _write_json(reports / "A3_ML_READINESS_GAP_REPORT.json", {"status": "GAP_REMAINS", "dataset_version": "DATASET_A"})
    _write_json(
        reports / "A3_ML_DEMO_PYTHON_LAUNCH_CONTROLLER_STATUS.json",
        {
            "status": "READY_FOR_DEMO_PYTHON_PREDICTIONS" if c23_authorized else "WAITING_FOR_DATA",
            "authorization": {
                "python_demo_predictions_authorized": c23_authorized,
                "ea_consumption_authorized": c23_authorized,
                "broker_action_authorized": False,
            },
        },
    )
    _write_json(
        reports / "A3_ML_RESEARCH_PREVIEW_HANDOFF_REHEARSAL_STATUS.json",
        {"status": "PUBLISHED_RESEARCH_PREVIEW_FAIL_CLOSED", "dataset_version": "DATASET_A"},
    )
    _write_json(
        reports / "A3_ML_RESEARCH_PREVIEW_RUNTIME_VERIFIER_STATUS.json",
        {"status": "RESEARCH_PREVIEW_READ_PATH_CONFIRMED_ALL_ACCOUNTS", "dataset_version": "DATASET_A"},
    )
    _write_json(
        reports / "A3_ML_DEMO_SHADOW_POST_ATTACH_MONITOR_STATUS.json",
        {"status": "DEMO_SHADOW_RUNTIME_CONFIRMED_ALL_ACCOUNTS", "dataset_version": "DATASET_A"},
    )
    for label, scope in (("A1", "1025742"), ("A2", "1033030"), ("A3", "1033669")):
        files = tmp_path / label / "MQL5" / "Files"
        files.mkdir(parents=True)
        _write_handoff(files / "A3_ML_EA_HANDOFF.csv", label, scope)
        (files / "a3_ml_prediction_observer_startup.csv").write_text("event,time\nstarted,2026-06-21T23:59:00Z\n", encoding="utf-8")
        (files / "a3_ml_prediction_observer_log.csv").write_text(
            "schema,time,account,dataset_version,action\n"
            f"observer,2026-06-21T23:59:00Z,{scope},DATASET_A,ABSTAIN\n",
            encoding="utf-8",
        )
        (files / "a3_ml_broker_shadow_tap.csv").write_text(
            "timestamp_utc,account_login,ml_action,ml_broker_action_authorized\n"
            f"2026-06-21T23:59:00Z,{scope},ABSTAIN,false\n",
            encoding="utf-8",
        )
        for item in files.iterdir():
            _set_mtime(item, NOW - timedelta(minutes=1))
    return root


def _write_handoff(path: Path, label: str, scope: str) -> None:
    path.write_text(
        "\n".join(
            [
                "schema_version,generated_at_utc,expires_at_utc,dataset_version,account_scope,account_label,symbol,exact_signal_id,setup_group_id,decision_time_utc,direction,p_win_calibrated,threshold,action,reason,model_id,model_hash,feature_schema_hash,drift_status,broker_action_authorized",
                f"a3_ml_ea_handoff_v1,2026-06-21T23:59:00Z,2026-06-29T00:00:00Z,DATASET_A,{scope},{label},XAUUSD,{scope}-1,G1,2026-06-21T23:59:00Z,LONG,0.4,,ABSTAIN,TEST,m,h,f,ML_RESEARCH_PREVIEW_FAIL_CLOSED,false",
                f"a3_ml_ea_handoff_v1,2026-06-21T23:59:00Z,2026-06-29T00:00:00Z,DATASET_A,{scope},{label},XAUUSD,{scope}-2,G2,2026-06-21T23:59:30Z,SHORT,0.3,,ABSTAIN,TEST,m,h,f,ML_RESEARCH_PREVIEW_FAIL_CLOSED,false",
                "",
            ]
        ),
        encoding="utf-8",
    )


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


def _set_mtime(path: Path, value: datetime) -> None:
    timestamp = value.timestamp()
    os.utime(path, (timestamp, timestamp))
