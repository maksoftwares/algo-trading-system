from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c38_reports_diagnostic_labels_but_zero_c01_trainable_rows(tmp_path: Path) -> None:
    from ml.a3_meta_v1.label_trainability_blocker_audit import generate_label_trainability_blocker_audit

    root = _root_with_label_state(tmp_path)

    output = generate_label_trainability_blocker_audit(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "LABEL_PROMOTION_REVIEW_REQUIRED_SLIPPAGE_BLOCKED"
    assert payload["summary"]["c02_mature_labels"] == 2
    assert payload["summary"]["c01_candidate_trainable_rows"] == 0
    assert payload["summary"]["c01_global_feature_budget"] == 0
    assert "C02 labels are explicitly diagnostic-only." in payload["blockers"]
    assert any(row["account_label"] == "A2" and row["entry_fills_deficit"] == 188 for row in payload["slippage_deficits"])
    assert payload["authorization"]["label_promotion_authorized"] is False
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert pointer["c38_label_trainability_blocker_status"] == "LABEL_PROMOTION_REVIEW_REQUIRED_SLIPPAGE_BLOCKED"
    assert pointer["broker_action_authorized"] is False


def test_c38_waits_for_mature_labels_when_none_exist(tmp_path: Path) -> None:
    from ml.a3_meta_v1.label_trainability_blocker_audit import generate_label_trainability_blocker_audit

    root = _root_with_label_state(tmp_path, mature=0, positive=0, negative=0)

    output = generate_label_trainability_blocker_audit(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "WAITING_FOR_MATURE_LABELS"
    assert payload["authorization"]["training_authorized"] is False


def test_c38_script_loads() -> None:
    module = load_script("c38_audit_label_trainability_blockers")

    assert hasattr(module, "main")


def _root_with_label_state(
    tmp_path: Path,
    *,
    mature: int = 2,
    positive: int = 1,
    negative: int = 1,
) -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "DATASET_A"})
    _write_json(
        reports / "C02_LABEL_AUDIT.json",
        {
            "status": "PASS",
            "dataset_version": "DATASET_A",
            "boundary": {"diagnostic_labels_only": True},
            "counts": {
                "labels": mature,
                "mature": mature,
                "positive": positive,
                "negative": negative,
                "unresolved": 0,
            },
        },
    )
    _write_json(
        reports / "C02_C01_DATA_AUDIT.json",
        {
            "status": "PIPELINE_ONLY",
            "labeled_and_trainable_setup_groups": {"candidate_trainable_groups": 0},
            "global_feature_budget": 0,
        },
    )
    _write_json(
        reports / "C02_SLIPPAGE_READINESS.json",
        {
            "status": "INSUFFICIENT",
            "requirements": {
                "entry_fills": 200,
                "sl_exits": 100,
                "tp_exits": 50,
                "request_price_resolved": 200,
            },
            "accounts": [
                {
                    "account_label": "A1",
                    "entry_fills": 200,
                    "sl_exits": 100,
                    "tp_exits": 50,
                    "request_price_resolved": 200,
                    "slippage_status": "ADEQUATE",
                },
                {
                    "account_label": "A2",
                    "entry_fills": 12,
                    "sl_exits": 8,
                    "tp_exits": 4,
                    "request_price_resolved": 12,
                    "slippage_status": "INSUFFICIENT",
                },
            ],
        },
    )
    _write_csv(
        reports / "C02_LABELED_DECISIONS.csv",
        ["signal_id", "label_status", "candidate_trainable"],
        [
            {"signal_id": "a", "label_status": "TP", "candidate_trainable": "false"},
            {"signal_id": "b", "label_status": "SL", "candidate_trainable": "false"},
        ][:mature],
    )
    _write_csv(
        reports / "A3_ML_C01_SNAPSHOT_ROWS.csv",
        ["exact_signal_id", "label_status", "candidate_trainable"],
        [
            {"exact_signal_id": "a", "label_status": "OPTIMISTIC_DIAGNOSTIC_ONLY", "candidate_trainable": "false"},
            {"exact_signal_id": "b", "label_status": "OPTIMISTIC_DIAGNOSTIC_ONLY", "candidate_trainable": "false"},
        ][: max(mature, 1)],
    )
    return root


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
