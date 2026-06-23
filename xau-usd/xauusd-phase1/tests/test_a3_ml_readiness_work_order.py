from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c40_reports_waiting_for_data_and_review_without_authorizing_demo(tmp_path: Path) -> None:
    from ml.a3_meta_v1.readiness_work_order import generate_demo_readiness_work_order

    root = _root_with_reports(tmp_path, all_accounts_collecting=True)

    output = generate_demo_readiness_work_order(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "WAITING_FOR_DATA_AND_REVIEW"
    assert payload["go_no_go"]["can_start_official_python_demo_predictions"] is False
    assert payload["summary"]["all_accounts_collecting"] is True
    assert payload["blocking_gates"][0]["gate"] == "market_setup_groups"
    assert payload["per_account_slippage_deficits"][1]["account_label"] == "A2"
    assert pointer["c40_demo_readiness_work_order_status"] == "WAITING_FOR_DATA_AND_REVIEW"
    assert pointer["python_demo_predictions_authorized"] is False


def test_c40_prioritizes_collection_health_when_runtime_is_not_collecting(tmp_path: Path) -> None:
    from ml.a3_meta_v1.readiness_work_order import generate_demo_readiness_work_order

    root = _root_with_reports(tmp_path, all_accounts_collecting=False)

    output = generate_demo_readiness_work_order(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "RESTORE_COLLECTION_HEALTH"
    assert "Restore all-account collection health" in payload["critical_path"][0]
    assert payload["authorization"]["broker_action_authorized"] is False


def test_c40_reports_ready_only_when_pointer_and_controller_authorize(tmp_path: Path) -> None:
    from ml.a3_meta_v1.readiness_work_order import generate_demo_readiness_work_order

    root = _root_with_reports(tmp_path, all_accounts_collecting=True, ready=True)

    output = generate_demo_readiness_work_order(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "READY_FOR_DEMO_PYTHON_PREDICTIONS"
    assert payload["go_no_go"]["can_start_official_python_demo_predictions"] is True
    assert payload["authorization"]["ea_consumption_authorized"] is True
    assert payload["authorization"]["broker_action_authorized"] is False


def test_c40_script_loads() -> None:
    module = load_script("c40_generate_demo_readiness_work_order")

    assert hasattr(module, "main")


def _root_with_reports(tmp_path: Path, *, all_accounts_collecting: bool, ready: bool = False) -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    _write_json(
        reports / "C02_DATASET_POINTER.json",
        {
            "dataset_version": "DATASET_A",
            "python_demo_predictions_authorized": ready,
            "ea_consumption_authorized": ready,
            "broker_action_authorized": False,
        },
    )
    _write_json(
        reports / "C03_TRAINING_READINESS_REPORT.json",
        {
            "status": "PASS" if ready else "NO_GO",
            "checks": [
                {"gate": "market_setup_groups", "passed": ready, "observed": "223", "required": ">=300"},
            ],
        },
    )
    _write_json(reports / "A3_ML_TRAINING_STATUS.json", {"status": "TRAINED_SHADOW_ONLY" if ready else "REFUSED_NOT_READY"})
    _write_json(
        reports / "A3_ML_READINESS_GAP_REPORT.json",
        {
            "decision_coverage": {"active_span_weeks": 3.37},
            "backfill_assessment": {"estimated_active_weeks_pass_date_utc": "2026-07-24T10:10:22Z"},
            "gate_gaps": [
                {
                    "gate": "market_setup_groups",
                    "passed": ready,
                    "observed": "223",
                    "required": ">=300",
                    "gap_text": "77",
                },
                {
                    "gate": "slippage_readiness",
                    "passed": ready,
                    "observed": "INSUFFICIENT",
                    "required": "ADEQUATE",
                    "gap_text": "needs different category/state",
                },
            ],
            "slippage_gap": {
                "accounts": [
                    _slippage_account("A1", "ADEQUATE", 0, 0, 0, 0),
                    _slippage_account("A2", "INSUFFICIENT", 188, 92, 46, 188),
                    _slippage_account("A3", "INSUFFICIENT", 125, 46, 29, 176),
                ]
            },
        },
    )
    _write_json(
        reports / "A3_ML_DEMO_PYTHON_LAUNCH_CONTROLLER_STATUS.json",
        {
            "status": "READY_FOR_DEMO_PYTHON_PREDICTIONS" if ready else "WAITING_FOR_DATA",
            "authorization": {
                "python_demo_predictions_authorized": ready,
                "ea_consumption_authorized": ready,
                "broker_action_authorized": False,
            },
        },
    )
    _write_json(
        reports / "A3_ML_DEMO_SHADOW_COLLECTION_HEALTH_STATUS.json",
        {
            "status": "COLLECTING_LIVE_WAITING_FOR_DATA" if all_accounts_collecting else "STALE_OR_PARTIAL_COLLECTION",
            "collection_health": {
                "all_accounts_collecting": all_accounts_collecting,
                "handoff_dataset_current_all_accounts": all_accounts_collecting,
                "observer_prediction_fresh_all_accounts": all_accounts_collecting,
                "broker_shadow_tap_present_all_accounts": all_accounts_collecting,
            },
        },
    )
    _write_json(
        reports / "A3_ML_LABEL_TRAINABILITY_BLOCKER_STATUS.json",
        {"status": "PASS" if ready else "LABEL_PROMOTION_REVIEW_REQUIRED_SLIPPAGE_BLOCKED"},
    )
    _write_json(
        reports / "A3_ML_HISTORICAL_DECISION_COVERAGE_STATUS.json",
        {
            "status": "NO_OLDER_COMPATIBLE_DECISIONS_FOUND",
            "summary": {"older_compatible_current_scope_would_signal_rows": 0},
        },
    )
    return root


def _slippage_account(label: str, status: str, entry: int, sl: int, tp: int, request: int) -> dict:
    return {
        "account_label": label,
        "slippage_status": status,
        "entry_fills": 200 - entry,
        "sl_exits": 100 - sl,
        "tp_exits": 50 - tp,
        "request_price_resolved": 200 - request,
        "deficits_if_per_account": {
            "entry_fills": entry,
            "sl_exits": sl,
            "tp_exits": tp,
            "request_price_resolved": request,
        },
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
