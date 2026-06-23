from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c13_dry_run_stages_fail_closed_handoff_files(tmp_path: Path) -> None:
    from ml.a3_meta_v1.fail_closed_handoff_rehearsal import publish_fail_closed_handoff_rehearsal

    root, reports = _root_with_registry(tmp_path)

    output = publish_fail_closed_handoff_rehearsal(root, publish=False)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "READY_DRY_RUN"
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert payload["authorization"]["ea_consumption_authorized"] is False
    assert payload["authorization"]["broker_action_authorized"] is False
    assert payload["authorization"]["mt5_file_publish_attempted"] is False
    assert len(payload["outputs"]["staged_files"]) == 3
    assert payload["outputs"]["published_files"] == []
    staged = Path(payload["outputs"]["staged_files"][0]["path"])
    assert staged.exists()
    rows = list(csv.DictReader(staged.open(encoding="utf-8")))
    assert rows[0]["action"] == "ABSTAIN"
    assert rows[0]["broker_action_authorized"] == "false"
    assert rows[0]["drift_status"] == "ML_HANDOFF_REHEARSAL_FAIL_CLOSED"
    assert (reports / "C02_DATASET_POINTER.json").exists()


def test_c13_publish_copies_abstain_file_to_all_account_files_roots(tmp_path: Path) -> None:
    from ml.a3_meta_v1.fail_closed_handoff_rehearsal import publish_fail_closed_handoff_rehearsal

    root, _reports = _root_with_registry(tmp_path)

    output = publish_fail_closed_handoff_rehearsal(root, publish=True)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "PUBLISHED_FAIL_CLOSED_REHEARSAL"
    assert payload["authorization"]["mt5_file_publish_attempted"] is True
    assert payload["boundary"]["ea_file_drop_authorized"] is True
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert len(payload["outputs"]["published_files"]) == 3
    for item in payload["outputs"]["published_files"]:
        target = Path(item["target_path"])
        assert target.exists()
        assert target.name == "A3_ML_EA_HANDOFF.csv"
        rows = list(csv.DictReader(target.open(encoding="utf-8")))
        assert len(rows) == 1
        assert rows[0]["account_scope"] == item["account_scope"]
        assert rows[0]["symbol"] == "XAUUSD"
        assert rows[0]["action"] == "ABSTAIN"
        assert rows[0]["model_id"] == ""
        assert rows[0]["broker_action_authorized"] == "false"


def test_c13_refuses_unsafe_terminal_file_name(tmp_path: Path) -> None:
    from ml.a3_meta_v1.fail_closed_handoff_rehearsal import publish_fail_closed_handoff_rehearsal

    root, _reports = _root_with_registry(tmp_path)

    output = publish_fail_closed_handoff_rehearsal(root, publish=True, terminal_file_name="../unsafe.csv")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "REFUSED_UNSAFE"
    assert payload["outputs"]["published_files"] == []
    assert any(item["check"] == "terminal_file_name_safe" and not item["passed"] for item in payload["validations"])


def test_c13_script_loads() -> None:
    module = load_script("c13_publish_fail_closed_handoff_rehearsal")

    assert hasattr(module, "main")


def _root_with_registry(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    config = root / "config" / "ml"
    reports.mkdir(parents=True)
    config.mkdir(parents=True)
    _write_registry(config / "mt5_accounts.yaml", tmp_path)
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})
    _write_json(reports / "C03_TRAINING_READINESS_REPORT.json", {"status": "NO_GO"})
    return root, reports


def _write_registry(path: Path, tmp_path: Path) -> None:
    _write_json(
        path,
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
                "A1": _account("1025742", "A1", tmp_path / "A1" / "MQL5" / "Files"),
                "A2": _account("1033030", "A2", tmp_path / "A2" / "MQL5" / "Files"),
                "A3": _account("1033669", "A3", tmp_path / "A3" / "MQL5" / "Files"),
            },
        },
    )


def _account(scope: str, label: str, files_root: Path) -> dict:
    return {
        "account_scope": scope,
        "account_label": label,
        "expected_login": scope,
        "terminal_exe": f"C:/{label}/terminal64.exe",
        "expected_data_path": f"C:/{label}",
        "portable": label != "A1",
        "role": "test",
        "symbol": "XAUUSD",
        "files_roots": [str(files_root)],
        "log_catalog": f"config/ml/log_catalog_{label.lower()}.yaml",
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
