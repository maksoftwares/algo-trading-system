from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c26_dry_run_stages_research_preview_abstain_rows(tmp_path: Path) -> None:
    from ml.a3_meta_v1.research_preview_handoff_rehearsal import publish_research_preview_handoff_rehearsal

    root, reports = _root_with_research_preview(tmp_path)

    output = publish_research_preview_handoff_rehearsal(root, publish=False)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((reports / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "READY_DRY_RUN"
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert payload["authorization"]["ea_consumption_authorized"] is False
    assert payload["authorization"]["broker_action_authorized"] is False
    assert payload["outputs"]["handoff_rows"] == 3
    assert len(payload["outputs"]["staged_files"]) == 3
    staged = Path(payload["outputs"]["staged_files"][0]["path"])
    rows = list(csv.DictReader(staged.open(encoding="utf-8")))
    assert rows[0]["action"] == "ABSTAIN"
    assert rows[0]["p_win_calibrated"]
    assert rows[0]["model_id"] == "a3_m0_exploratory_TEST"
    assert rows[0]["broker_action_authorized"] == "false"
    assert pointer["c26_research_preview_handoff_rehearsal_status"] == "READY_DRY_RUN"
    assert pointer["python_demo_predictions_authorized"] is False


def test_c26_publish_copies_research_preview_to_all_account_files_roots(tmp_path: Path) -> None:
    from ml.a3_meta_v1.research_preview_handoff_rehearsal import publish_research_preview_handoff_rehearsal

    root, _reports = _root_with_research_preview(tmp_path)

    output = publish_research_preview_handoff_rehearsal(root, publish=True)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "PUBLISHED_RESEARCH_PREVIEW_FAIL_CLOSED"
    assert payload["authorization"]["mt5_file_publish_attempted"] is True
    assert payload["boundary"]["ea_file_drop_authorized"] is True
    assert len(payload["outputs"]["published_files"]) == 3
    for item in payload["outputs"]["published_files"]:
        target = Path(item["target_path"])
        assert target.exists()
        assert target.name == "A3_ML_EA_HANDOFF.csv"
        rows = list(csv.DictReader(target.open(encoding="utf-8")))
        assert rows
        assert {row["action"] for row in rows} == {"ABSTAIN"}
        assert {row["broker_action_authorized"] for row in rows} == {"false"}
        assert {row["reason"] for row in rows} == {"C26_RESEARCH_PREVIEW_NOT_AUTHORIZED_FOR_DEMO"}


def test_c26_refuses_preview_that_does_not_force_abstain(tmp_path: Path) -> None:
    from ml.a3_meta_v1.research_preview_handoff_rehearsal import publish_research_preview_handoff_rehearsal

    root, reports = _root_with_research_preview(tmp_path)
    rows = list(csv.DictReader((reports / "A3_ML_EXPLORATORY_SHADOW_PREVIEW.csv").open(encoding="utf-8")))
    rows[0]["preview_action"] = "TAKE"
    _write_csv(reports / "A3_ML_EXPLORATORY_SHADOW_PREVIEW.csv", rows, list(rows[0].keys()))

    output = publish_research_preview_handoff_rehearsal(root, publish=True)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "REFUSED_NOT_READY"
    assert payload["outputs"]["published_files"] == []
    assert any(item["check"] == "preview_rows_force_abstain" and not item["passed"] for item in payload["validations"])


def test_c26_script_loads() -> None:
    module = load_script("c26_publish_research_preview_handoff_rehearsal")

    assert hasattr(module, "main")


def _root_with_research_preview(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    config = root / "config" / "ml"
    reports.mkdir(parents=True)
    config.mkdir(parents=True)
    _write_json(config / "mt5_accounts.yaml", _registry(tmp_path))
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})
    _write_json(
        reports / "A3_ML_EXPLORATORY_TRAINING_REHEARSAL_STATUS.json",
        {
            "status": "REHEARSED_RESEARCH_ONLY",
            "authorization": {
                "python_demo_predictions_authorized": False,
                "ea_consumption_authorized": False,
                "broker_action_authorized": False,
            },
        },
    )
    _write_json(
        reports / "A3_ML_EXPLORATORY_MODEL_REHEARSAL_ARTIFACT.json",
        {
            "schema_version": "a3_ml_exploratory_model_rehearsal_artifact_v1",
            "status": "REHEARSED_RESEARCH_ONLY",
            "model_id": "a3_m0_exploratory_TEST",
            "official_model_artifact": False,
            "eligible_for_c04_shadow_bridge": False,
            "eligible_for_c06_ea_handoff": False,
            "dataset_version": "TEST",
            "feature_schema_hash": "abc123",
        },
    )
    rows = [
        _preview_row("1025742", "A1", "LONG", "0.6100000000"),
        _preview_row("1033030", "A2", "SHORT", "0.4200000000"),
        _preview_row("1033669", "A3", "LONG", "0.5500000000"),
    ]
    _write_csv(reports / "A3_ML_EXPLORATORY_SHADOW_PREVIEW.csv", rows, list(rows[0].keys()))
    return root, reports


def _preview_row(account: str, label: str, direction: str, p_win: str) -> dict[str, str]:
    return {
        "schema_version": "a3_ml_exploratory_shadow_preview_v1",
        "model_id": "a3_m0_exploratory_TEST",
        "dataset_version": "TEST",
        "account_scope": account,
        "account_label": label,
        "symbol": "XAUUSD",
        "source_signal_id": f"{account}-{direction}",
        "setup_group_id": f"G-{account}-{direction}",
        "decision_time_utc": "2026-06-01T00:00:00Z",
        "direction": direction,
        "regime": "FALLING",
        "session_bucket": "Morning",
        "p_win_rehearsal": p_win,
        "model_group": "test",
        "preview_action": "ABSTAIN",
        "authorization_status": "RESEARCH_ONLY_NOT_AUTHORIZED",
        "reason": "EXPLORATORY_REHEARSAL_NOT_AUTHORIZED_FOR_DEMO",
        "broker_action_authorized": "false",
    }


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
            "A1": _account("1025742", "A1", tmp_path / "A1" / "MQL5" / "Files"),
            "A2": _account("1033030", "A2", tmp_path / "A2" / "MQL5" / "Files"),
            "A3": _account("1033669", "A3", tmp_path / "A3" / "MQL5" / "Files"),
        },
    }


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


def _write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
