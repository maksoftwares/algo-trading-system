from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c47_classifies_reviewer_and_market_data_actions(tmp_path: Path) -> None:
    from ml.a3_meta_v1.gate_closure_plan import generate_gate_closure_plan

    root = _root_with_reports(tmp_path)

    output = generate_gate_closure_plan(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))
    by_gate = {item["gate"]: item for item in payload["gate_actions"]}

    assert payload["status"] == "WAITING_FOR_REVIEWER_AND_MARKET_DATA"
    assert by_gate["dataset_status"]["primary_owner"] == "reviewer_then_pipeline"
    assert by_gate["market_setup_groups"]["primary_owner"] == "reviewer_or_market_data"
    assert by_gate["active_weeks"]["can_move_today"] == "no_without_external_history"
    assert by_gate["slippage_readiness"]["primary_owner"] == "live_fill_collection"
    assert "Send C45 reviewer submission bundle" in payload["today_possible"][0]
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert payload["authorization"]["broker_action_authorized"] is False
    assert pointer["c47_gate_closure_plan_status"] == "WAITING_FOR_REVIEWER_AND_MARKET_DATA"


def test_c47_reports_ready_when_c03_passes_but_still_does_not_authorize_broker(tmp_path: Path) -> None:
    from ml.a3_meta_v1.gate_closure_plan import generate_gate_closure_plan

    root = _root_with_reports(tmp_path, c03_pass=True)

    output = generate_gate_closure_plan(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "READY_FOR_DEMO_PYTHON_PREDICTIONS"
    assert payload["gate_actions"] == []
    assert payload["authorization"]["broker_action_authorized"] is False


def test_c47_script_loads() -> None:
    module = load_script("c47_generate_gate_closure_plan")

    assert hasattr(module, "main")


def _root_with_reports(tmp_path: Path, *, c03_pass: bool = False) -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    _write_json(
        reports / "C02_DATASET_POINTER.json",
        {
            "dataset_version": "DATASET_A",
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
    )
    checks = [] if c03_pass else [
        {"gate": "dataset_status", "passed": False, "observed": "PIPELINE_ONLY", "required": "EXPLORATORY_MODEL or higher"},
        {"gate": "market_setup_groups", "passed": False, "observed": "223", "required": ">=300"},
        {"gate": "active_weeks", "passed": False, "observed": "3.37", "required": ">=8"},
        {"gate": "slippage_readiness", "passed": False, "observed": "INSUFFICIENT", "required": "ADEQUATE"},
    ]
    _write_json(reports / "C03_TRAINING_READINESS_REPORT.json", {"status": "PASS" if c03_pass else "NO_GO", "checks": checks})
    _write_json(reports / "A3_ML_TRAINING_STATUS.json", {"status": "REFUSED_NOT_READY"})
    _write_json(reports / "A3_ML_DEMO_PYTHON_LAUNCH_CONTROLLER_STATUS.json", {"status": "WAITING_FOR_DATA"})
    _write_json(
        reports / "A3_ML_DEMO_SHADOW_COLLECTION_HEALTH_STATUS.json",
        {"status": "COLLECTING_LIVE_WAITING_FOR_DATA", "collection_health": {"all_accounts_collecting": True}},
    )
    _write_json(
        reports / "A3_ML_DEMO_READINESS_WORK_ORDER.json",
        {
            "per_account_slippage_deficits": [
                {"account_label": "A2", "slippage_status": "INSUFFICIENT", "entry_fills_deficit": 188, "sl_exits_deficit": 92, "tp_exits_deficit": 46, "request_price_resolved_deficit": 188}
            ]
        },
    )
    _write_json(reports / "A3_ML_REVIEWER_SUBMISSION_BUNDLE_STATUS.json", {"status": "READY_TO_SEND_TO_REVIEWER"})
    _write_json(
        reports / "A3_ML_READINESS_PROGRESS_TRACKER_STATUS.json",
        {
            "status": "COLLECTING_LIVE_PROGRESS_TRACKED",
            "latest_dataset": {"dataset_version": "DATASET_A"},
            "delta_from_previous": {"market_setup_groups": 0, "signal_instances": 24, "labels": 0, "mature_labels": 0, "fill_rows": 0},
        },
    )
    return root


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
