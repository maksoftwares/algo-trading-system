from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c18_rehearses_from_diagnostic_rows_without_authorizing_demo(tmp_path: Path) -> None:
    from ml.a3_meta_v1.exploratory_training_rehearsal import run_exploratory_training_rehearsal

    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    config = root / "config" / "ml"
    reports.mkdir(parents=True)
    config.mkdir(parents=True)
    _write_contract(config / "a3_ml_training_contract.json")
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})
    _write_json(
        reports / "C03_TRAINING_READINESS_REPORT.json",
        {
            "status": "NO_GO",
            "checks": [{"gate": "active_weeks", "passed": False, "observed": "3.0", "required": ">=8"}],
        },
    )
    _write_json(
        reports / "C02_C01_DATA_AUDIT.json",
        {
            "status": "PIPELINE_ONLY",
            "selected_features": [],
            "feature_availability": [{"feature_name": "f1", "present_pct": 1.0}],
            "training_decision": {"supervised_training_allowed": False, "reason": "feature_budget=0"},
            "raw_source_row_counts": {"snapshot_rows": 4},
        },
    )
    _write_snapshot(
        reports / "A3_ML_C01_SNAPSHOT_ROWS.csv",
        [
            _snapshot_row("1025742", "A1", "LONG", "1"),
            _snapshot_row("1025742", "A1", "SHORT", "0"),
            _snapshot_row("1033030", "A2", "LONG", "1"),
            _snapshot_row("1033669", "A3", "SHORT", "0"),
        ],
    )

    output = run_exploratory_training_rehearsal(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    artifact = json.loads((reports / "A3_ML_EXPLORATORY_MODEL_REHEARSAL_ARTIFACT.json").read_text(encoding="utf-8"))
    preview_rows = list(csv.DictReader((reports / "A3_ML_EXPLORATORY_SHADOW_PREVIEW.csv").open("r", encoding="utf-8")))
    pointer = json.loads((reports / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "REHEARSED_RESEARCH_ONLY"
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert payload["authorization"]["ea_consumption_authorized"] is False
    assert payload["authorization"]["broker_action_authorized"] is False
    assert payload["training_population"]["diagnostic_labeled_rows"] == 4
    assert payload["training_population"]["official_candidate_trainable_rows"] == 0
    assert artifact["official_model_artifact"] is False
    assert artifact["eligible_for_c04_shadow_bridge"] is False
    assert artifact["training_summary"]["minority"] == 2
    assert len(preview_rows) == 4
    assert {row["preview_action"] for row in preview_rows} == {"ABSTAIN"}
    assert {row["broker_action_authorized"] for row in preview_rows} == {"false"}
    assert not (reports / "A3_ML_MODEL_ARTIFACT.json").exists()
    assert pointer["c18_exploratory_training_rehearsal_status"] == "REHEARSED_RESEARCH_ONLY"
    assert pointer["python_demo_predictions_authorized"] is False


def test_c18_refuses_when_snapshot_has_no_diagnostic_labels(tmp_path: Path) -> None:
    from ml.a3_meta_v1.exploratory_training_rehearsal import run_exploratory_training_rehearsal

    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    config = root / "config" / "ml"
    reports.mkdir(parents=True)
    config.mkdir(parents=True)
    _write_contract(config / "a3_ml_training_contract.json")
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})
    _write_json(reports / "C03_TRAINING_READINESS_REPORT.json", {"status": "NO_GO", "checks": []})
    _write_json(reports / "C02_C01_DATA_AUDIT.json", {"status": "PIPELINE_ONLY", "training_decision": {"supervised_training_allowed": False}})
    _write_snapshot(reports / "A3_ML_C01_SNAPSHOT_ROWS.csv", [_snapshot_row("1025742", "A1", "LONG", "")])

    output = run_exploratory_training_rehearsal(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "REHEARSAL_REFUSED_NO_DIAGNOSTIC_ROWS"
    assert payload["authorization"]["exploratory_rehearsal_executed"] is False
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert not (reports / "A3_ML_EXPLORATORY_MODEL_REHEARSAL_ARTIFACT.json").exists()


def test_c18_script_loads() -> None:
    module = load_script("c18_run_exploratory_training_rehearsal")

    assert hasattr(module, "main")


def _write_contract(path: Path) -> None:
    _write_json(
        path,
        {
            "schema_version": "a3_ml_training_contract_v1",
            "readiness_report_json": "outputs/reports/C03_TRAINING_READINESS_REPORT.json",
            "data_audit_json": "outputs/reports/C02_C01_DATA_AUDIT.json",
            "snapshot_csv": "outputs/reports/A3_ML_C01_SNAPSHOT_ROWS.csv",
        },
    )


def _snapshot_row(account: str, label: str, direction: str, y_win: str) -> dict[str, str]:
    return {
        "account_scope": account,
        "account_label": label,
        "symbol": "XAUUSD",
        "source_signal_id": f"{account}-{direction}-{y_win}",
        "setup_group_id": f"G-{account}-{direction}-{y_win}",
        "decision_time_utc": "2026-06-01T00:00:00Z",
        "direction": direction,
        "regime": "FALLING",
        "session_bucket": "Morning",
        "candidate_trainable": "false",
        "y_win_expected": y_win,
    }


def _write_snapshot(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "account_scope",
        "account_label",
        "symbol",
        "source_signal_id",
        "setup_group_id",
        "decision_time_utc",
        "direction",
        "regime",
        "session_bucket",
        "candidate_trainable",
        "y_win_expected",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
