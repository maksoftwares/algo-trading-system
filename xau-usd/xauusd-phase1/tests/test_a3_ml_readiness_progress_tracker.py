from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c46_tracks_delta_between_latest_and_previous_dataset(tmp_path: Path) -> None:
    from ml.a3_meta_v1.readiness_progress_tracker import generate_readiness_progress_tracker

    root = _root_with_datasets(tmp_path)

    output = generate_readiness_progress_tracker(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "COLLECTING_LIVE_PROGRESS_TRACKED"
    assert payload["latest_dataset"]["dataset_version"] == "xauusd_c02_multiacct_202606220118_test"
    assert payload["previous_dataset"]["dataset_version"] == "xauusd_c02_multiacct_202606220057_test"
    assert payload["delta_from_previous"]["snapshot_cutoff_delta_minutes"] == 21
    assert payload["delta_from_previous"]["signal_instances"] == 5
    assert payload["delta_from_previous"]["market_setup_groups"] == 1
    assert payload["delta_from_previous"]["labels"] == 2
    assert payload["delta_from_previous"]["mature_labels"] == 2
    assert payload["delta_from_previous"]["fill_rows"] == 2
    assert payload["latest_dataset_completeness"]["complete"] is True
    assert payload["completeness_warnings"] == []
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert pointer["c46_readiness_progress_tracker_status"] == "COLLECTING_LIVE_PROGRESS_TRACKED"
    assert pointer["broker_action_authorized"] is False


def test_c46_reports_waiting_when_only_one_dataset_exists(tmp_path: Path) -> None:
    from ml.a3_meta_v1.readiness_progress_tracker import generate_readiness_progress_tracker

    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "xauusd_c02_multiacct_202606220118_test"})
    _write_dataset(root, "xauusd_c02_multiacct_202606220118_test", "2026-06-22T01:18:00Z", 10, 3, 2, 2)

    output = generate_readiness_progress_tracker(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "WAITING_FOR_MORE_DATASETS"
    assert payload["delta_from_previous"] == {}


def test_c46_flags_negative_evidence_delta_for_review(tmp_path: Path) -> None:
    from ml.a3_meta_v1.readiness_progress_tracker import generate_readiness_progress_tracker

    root = _root_with_datasets(tmp_path)
    _write_json(
        root / "outputs" / "reports" / "C02_DATASET_POINTER.json",
        {
            "dataset_version": "xauusd_c02_multiacct_202606220145_test",
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
    )
    _write_dataset(root, "xauusd_c02_multiacct_202606220145_test", "2026-06-22T01:45:00Z", 20, 4, 1, 1)

    output = generate_readiness_progress_tracker(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "DATA_REGRESSION_REVIEW_REQUIRED"
    assert payload["delta_from_previous"]["labels"] == -3
    assert payload["delta_from_previous"]["fill_rows"] == -3
    assert any("Labels decreased" in item for item in payload["regression_warnings"])
    assert any("Fill rows decreased" in item for item in payload["regression_warnings"])


def test_c46_flags_incomplete_latest_dataset_artifacts(tmp_path: Path) -> None:
    from ml.a3_meta_v1.readiness_progress_tracker import generate_readiness_progress_tracker

    root = _root_with_datasets(tmp_path)
    (root / "data" / "ml" / "a3_meta_v1" / "c02" / "xauusd_c02_multiacct_202606220118_test" / "normalized" / "labels" / "diagnostic_tick_labels.csv").unlink()

    output = generate_readiness_progress_tracker(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "DATASET_ARTIFACTS_INCOMPLETE"
    assert payload["latest_dataset_completeness"]["complete"] is False
    assert payload["latest_dataset_completeness"]["missing_artifacts"] == ["diagnostic_labels"]
    assert any("diagnostic_labels" in item for item in payload["completeness_warnings"])
    assert payload["authorization"]["python_demo_predictions_authorized"] is False


def test_c46_script_loads() -> None:
    module = load_script("c46_track_readiness_progress")

    assert hasattr(module, "main")


def _root_with_datasets(tmp_path: Path) -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    _write_json(
        reports / "C02_DATASET_POINTER.json",
        {
            "dataset_version": "xauusd_c02_multiacct_202606220118_test",
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
    )
    _write_json(
        reports / "C03_TRAINING_READINESS_REPORT.json",
        {
            "status": "NO_GO",
            "checks": [
                {"gate": "market_setup_groups", "passed": False, "observed": "11", "required": ">=300"},
                {"gate": "active_weeks", "passed": False, "observed": "3.37", "required": ">=8"},
            ],
        },
    )
    _write_json(
        reports / "A3_ML_DEMO_SHADOW_COLLECTION_HEALTH_STATUS.json",
        {"collection_health": {"all_accounts_collecting": True}},
    )
    _write_json(
        reports / "C02_SLIPPAGE_READINESS.json",
        {
            "requirements": {"entry_fills": 200, "sl_exits": 100, "tp_exits": 50, "request_price_resolved": 200},
            "accounts": [{"account_label": "A2", "entry_fills": 12, "sl_exits": 8, "tp_exits": 4, "request_price_resolved": 12, "slippage_status": "INSUFFICIENT"}],
        },
    )
    _write_dataset(root, "xauusd_c02_multiacct_202606220057_test", "2026-06-22T00:57:00Z", 10, 3, 2, 2)
    _write_dataset(root, "xauusd_c02_multiacct_202606220118_test", "2026-06-22T01:18:00Z", 15, 4, 4, 4)
    return root


def _write_dataset(
    root: Path,
    version: str,
    snapshot_cutoff: str,
    signal_instances: int,
    market_groups: int,
    labels: int,
    fills: int,
) -> None:
    dataset = root / "data" / "ml" / "a3_meta_v1" / "c02" / version
    _write_json(
        dataset / "ROOT_BAR_TICK_EXPORT_MANIFEST.json",
        {
            "dataset_version": version,
            "created_at_utc": snapshot_cutoff,
            "snapshot_cutoff_utc": snapshot_cutoff,
            "account_records": [],
        },
    )
    _write_json(
        dataset / "normalized" / "NORMALIZATION_MANIFEST.json",
        {
            "dataset_version": version,
            "signal_instances_csv": {"row_count": signal_instances},
        },
    )
    _write_csv(
        dataset / "normalized" / "signals" / "signal_instances.csv",
        ["signal_id"],
        [{"signal_id": str(index)} for index in range(signal_instances)],
    )
    _write_csv(dataset / "normalized" / "signals" / "market_setup_groups.csv", ["market_setup_group_id"], [{"market_setup_group_id": str(index)} for index in range(market_groups)])
    label_rows = [
        {
            "decision_time_utc": f"2026-06-{10 + index:02d}T00:00:00Z",
            "label_status": "TP" if index % 2 == 0 else "SL",
            "label_mature": "true",
        }
        for index in range(labels)
    ]
    _write_csv(dataset / "normalized" / "labels" / "diagnostic_tick_labels.csv", ["decision_time_utc", "label_status", "label_mature"], label_rows)
    fill_rows = [{"account_label": "A1" if index % 2 == 0 else "A2"} for index in range(fills)]
    _write_csv(dataset / "normalized" / "fills" / "fill_reconciliation.csv", ["account_label"], fill_rows)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
