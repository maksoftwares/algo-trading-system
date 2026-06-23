from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_shadow_bridge_emits_abstain_when_c03_no_go(tmp_path: Path) -> None:
    from ml.a3_meta_v1.shadow_bridge import generate_shadow_bridge_outputs

    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    config = root / "config" / "ml"
    reports.mkdir(parents=True)
    config.mkdir(parents=True)
    (config / "a3_ml_shadow_bridge_contract.json").write_text(
        json.dumps(
            {
                "schema_version": "a3_ml_shadow_bridge_contract_v1",
                "input_scores_csv": "outputs/reports/a3_ml_offline_scores.csv",
                "output_predictions_csv": "outputs/reports/A3_ML_SHADOW_PREDICTIONS.csv",
                "status_report_json": "outputs/reports/A3_ML_SHADOW_BRIDGE_STATUS.json",
                "stale_after_minutes": 15,
            }
        ),
        encoding="utf-8",
    )
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})
    _write_json(
        reports / "C03_TRAINING_READINESS_REPORT.json",
        {
            "status": "NO_GO",
            "authorization": {"training_authorized": False},
            "checks": [{"gate": "market_setup_groups", "passed": False, "observed": "121", "required": ">=300"}],
        },
    )
    _write_csv(
        reports / "a3_ml_offline_scores.csv",
        [
            "account_scope",
            "account_label",
            "exact_signal_id",
            "setup_group_id",
            "decision_time_utc",
            "symbol",
            "direction",
        ],
        [
            {
                "account_scope": "1025742",
                "account_label": "A1",
                "exact_signal_id": "abc",
                "setup_group_id": "g1",
                "decision_time_utc": "2026-06-01T00:00:00Z",
                "symbol": "XAUUSD",
                "direction": "LONG",
            }
        ],
    )

    output = generate_shadow_bridge_outputs(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    rows = list(csv.DictReader((reports / "A3_ML_SHADOW_PREDICTIONS.csv").open(encoding="utf-8")))

    assert payload["status"] == "DISABLED_FAIL_CLOSED"
    assert payload["authorization"]["ea_consumption_authorized"] is False
    assert rows[0]["action"] == "ABSTAIN"
    assert rows[0]["drift_status"] == "ML_SHADOW_DISABLED"
    assert rows[0]["broker_action_authorized"] == "false"


def test_shadow_bridge_uses_model_artifact_only_when_c03_passes(tmp_path: Path) -> None:
    from ml.a3_meta_v1.shadow_bridge import generate_shadow_bridge_outputs

    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    config = root / "config" / "ml"
    reports.mkdir(parents=True)
    config.mkdir(parents=True)
    (config / "a3_ml_shadow_bridge_contract.json").write_text(
        json.dumps(
            {
                "schema_version": "a3_ml_shadow_bridge_contract_v1",
                "input_scores_csv": "outputs/reports/a3_ml_offline_scores.csv",
                "model_artifact_json": "outputs/reports/A3_ML_MODEL_ARTIFACT.json",
                "training_status_json": "outputs/reports/A3_ML_TRAINING_STATUS.json",
                "output_predictions_csv": "outputs/reports/A3_ML_SHADOW_PREDICTIONS.csv",
                "status_report_json": "outputs/reports/A3_ML_SHADOW_BRIDGE_STATUS.json",
                "stale_after_minutes": 15,
            }
        ),
        encoding="utf-8",
    )
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST"})
    _write_json(reports / "C03_TRAINING_READINESS_REPORT.json", {"status": "PASS", "authorization": {"training_authorized": True}, "checks": []})
    artifact_path = reports / "A3_ML_MODEL_ARTIFACT.json"
    _write_json(
        artifact_path,
        {
            "schema_version": "a3_ml_model_artifact_v1",
            "status": "TRAINED_SHADOW_ONLY",
            "model_id": "m0-test",
            "feature_schema_hash": "abc123",
            "action_policy": {"threshold": 0.5},
            "rates": {
                "global": 0.4,
                "by_direction": {"LONG": {"p_win": 0.6}},
                "by_account_direction": {"1025742|LONG": {"p_win": 0.8}},
            },
        },
    )
    _write_json(
        reports / "A3_ML_TRAINING_STATUS.json",
        {
            "status": "TRAINED_SHADOW_ONLY",
            "outputs": {
                "model_artifact_json": str(artifact_path.resolve()),
                "model_artifact_sha256": _sha256_file(artifact_path),
            },
        },
    )
    _write_csv(
        reports / "a3_ml_offline_scores.csv",
        [
            "account_scope",
            "account_label",
            "exact_signal_id",
            "setup_group_id",
            "decision_time_utc",
            "symbol",
            "direction",
        ],
        [
            {
                "account_scope": "1025742",
                "account_label": "A1",
                "exact_signal_id": "abc",
                "setup_group_id": "g1",
                "decision_time_utc": "2026-06-01T00:00:00Z",
                "symbol": "XAUUSD",
                "direction": "LONG",
            }
        ],
    )

    output = generate_shadow_bridge_outputs(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    rows = list(csv.DictReader((reports / "A3_ML_SHADOW_PREDICTIONS.csv").open(encoding="utf-8")))

    assert payload["status"] == "READY_SHADOW_ONLY"
    assert payload["authorization"]["python_demo_predictions_authorized"] is True
    assert rows[0]["action"] == "TAKE"
    assert rows[0]["p_win_calibrated"] == "0.8000000000"
    assert rows[0]["model_id"] == "m0-test"
    assert rows[0]["broker_action_authorized"] == "false"


def test_shadow_bridge_script_loads() -> None:
    module = load_script("c04_generate_shadow_bridge")

    assert hasattr(module, "main")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
