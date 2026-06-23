from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c05_training_refuses_when_c03_is_no_go(tmp_path: Path) -> None:
    from ml.a3_meta_v1.model_training import train_or_refuse_model

    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    config = root / "config" / "ml"
    reports.mkdir(parents=True)
    config.mkdir(parents=True)
    _write_contract(config / "a3_ml_training_contract.json", minimum_train_rows=2, minimum_minority_labels=1)
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})
    _write_json(reports / "C03_TRAINING_READINESS_REPORT.json", {"status": "NO_GO"})
    _write_json(
        reports / "C02_C01_DATA_AUDIT.json",
        {
            "status": "PIPELINE_ONLY",
            "selected_features": [],
            "training_decision": {
                "supervised_training_allowed": False,
                "reason": "global_feature_budget=0 is below the contract minimum of 5",
            },
        },
    )
    _write_snapshot(reports / "A3_ML_C01_SNAPSHOT_ROWS.csv", [])

    output = train_or_refuse_model(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "REFUSED_NOT_READY"
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert "C03 readiness is NO_GO" in payload["refusal_reasons"][0]
    assert not (reports / "A3_ML_MODEL_ARTIFACT.json").exists()


def test_c05_training_writes_shadow_only_base_rate_artifact_when_ready(tmp_path: Path) -> None:
    from ml.a3_meta_v1.model_training import train_or_refuse_model

    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    config = root / "config" / "ml"
    reports.mkdir(parents=True)
    config.mkdir(parents=True)
    _write_contract(config / "a3_ml_training_contract.json", minimum_train_rows=4, minimum_minority_labels=2)
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})
    _write_json(reports / "C03_TRAINING_READINESS_REPORT.json", {"status": "PASS"})
    _write_json(
        reports / "C02_C01_DATA_AUDIT.json",
        {
            "status": "EXPLORATORY_MODEL",
            "selected_features": ["f1", "f2", "f3", "f4", "f5"],
            "training_decision": {
                "supervised_training_allowed": True,
                "reason": "Eligible only for offline research; live authority remains disabled.",
            },
        },
    )
    _write_snapshot(
        reports / "A3_ML_C01_SNAPSHOT_ROWS.csv",
        [
            _snapshot_row("1025742", "LONG", "1"),
            _snapshot_row("1025742", "LONG", "0"),
            _snapshot_row("1033030", "SHORT", "1"),
            _snapshot_row("1033669", "SHORT", "0"),
        ],
    )

    output = train_or_refuse_model(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    artifact = json.loads((reports / "A3_ML_MODEL_ARTIFACT.json").read_text(encoding="utf-8"))

    assert payload["status"] == "TRAINED_SHADOW_ONLY"
    assert payload["authorization"]["python_demo_predictions_authorized"] is True
    assert artifact["schema_version"] == "a3_ml_model_artifact_v1"
    assert artifact["training_summary"]["rows"] == 4
    assert artifact["rates"]["by_account_direction"]["1025742|LONG"]["rows"] == 2
    assert artifact["boundary"]["broker_action_authorized"] is False


def test_c05_training_script_loads() -> None:
    module = load_script("c05_train_or_refuse_model")

    assert hasattr(module, "main")


def _write_contract(path: Path, *, minimum_train_rows: int, minimum_minority_labels: int) -> None:
    _write_json(
        path,
        {
            "schema_version": "a3_ml_training_contract_v1",
            "readiness_report_json": "outputs/reports/C03_TRAINING_READINESS_REPORT.json",
            "data_audit_json": "outputs/reports/C02_C01_DATA_AUDIT.json",
            "snapshot_csv": "outputs/reports/A3_ML_C01_SNAPSHOT_ROWS.csv",
            "model_artifact_json": "outputs/reports/A3_ML_MODEL_ARTIFACT.json",
            "model_card_md": "outputs/reports/A3_ML_MODEL_CARD.md",
            "training_status_json": "outputs/reports/A3_ML_TRAINING_STATUS.json",
            "minimum_train_rows": minimum_train_rows,
            "minimum_minority_labels": minimum_minority_labels,
            "minimum_selected_features": 5,
            "decision_threshold": 0.5,
        },
    )


def _snapshot_row(account: str, direction: str, label: str) -> dict[str, str]:
    return {
        "account_scope": account,
        "account_label": {"1025742": "A1", "1033030": "A2", "1033669": "A3"}.get(account, "UNKNOWN"),
        "direction": direction,
        "candidate_trainable": "true",
        "y_win_expected": label,
    }


def _write_snapshot(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["account_scope", "account_label", "direction", "candidate_trainable", "y_win_expected"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
