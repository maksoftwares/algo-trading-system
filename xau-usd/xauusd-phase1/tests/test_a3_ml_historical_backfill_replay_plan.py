from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import load_script


def test_c50_generates_safe_historical_backfill_plan(tmp_path: Path) -> None:
    from ml.a3_meta_v1.historical_backfill_replay_plan import generate_historical_backfill_replay_plan

    root = _root_with_reports(tmp_path)

    output = generate_historical_backfill_replay_plan(root, lookback_days=120, max_tick_days=10)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "HISTORICAL_BACKFILL_REPLAY_PLAN_READY"
    assert payload["window"]["historical_start_utc"] == "2026-02-22T02:19:00Z"
    assert payload["window"]["max_tick_days"] == 10
    assert "--requested-start-utc 2026-02-22T02:19:00Z" in payload["commands"]["historical_readonly_export"]
    assert "--accounts A1,A2,A3" in payload["commands"]["historical_readonly_export"]
    assert payload["authorization"]["training_authorized"] is False
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert payload["authorization"]["ea_consumption_authorized"] is False
    assert payload["authorization"]["broker_action_authorized"] is False
    assert payload["boundary"]["mt5_connection_attempted"] is False
    assert payload["boundary"]["data_export_attempted"] is False
    assert pointer["c50_historical_backfill_replay_plan_status"] == "HISTORICAL_BACKFILL_REPLAY_PLAN_READY"
    assert pointer["broker_action_authorized"] is False


def test_c50_marks_replay_as_reviewer_gated_evidence(tmp_path: Path) -> None:
    from ml.a3_meta_v1.historical_backfill_replay_plan import generate_historical_backfill_replay_plan

    output = generate_historical_backfill_replay_plan(_root_with_reports(tmp_path))
    payload = json.loads(output.read_text(encoding="utf-8"))
    rules = {item["evidence"]: item for item in payload["evidence_rules"]}

    assert "reviewer" in rules["EA Strategy Tester/replay logs"]["allowed_use"].lower()
    assert "Cannot close live slippage readiness" in rules["EA Strategy Tester/replay logs"]["cannot_do"]
    assert "reviewer-gated evidence" in payload["next_allowed_stage"]


def test_c50_script_loads() -> None:
    module = load_script("c50_generate_historical_backfill_replay_plan")

    assert hasattr(module, "main")


def _root_with_reports(tmp_path: Path) -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    _write_json(
        reports / "C02_DATASET_POINTER.json",
        {
            "dataset_version": "DATASET_A",
            "snapshot_cutoff_utc": "2026-06-22T02:19:00Z",
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
                {"gate": "dataset_status", "passed": False},
                {"gate": "market_setup_groups", "passed": False},
                {"gate": "active_weeks", "passed": False},
                {"gate": "at_least_two_regimes", "passed": False},
                {"gate": "feature_budget", "passed": False},
                {"gate": "slippage_readiness", "passed": False},
            ],
        },
    )
    _write_json(
        reports / "A3_ML_DEMO_SHADOW_COLLECTION_HEALTH_STATUS.json",
        {"status": "COLLECTING_LIVE_WAITING_FOR_DATA", "collection_health": {"all_accounts_collecting": True}},
    )
    _write_json(
        reports / "A3_ML_READINESS_PROGRESS_TRACKER_STATUS.json",
        {"status": "COLLECTING_LIVE_PROGRESS_TRACKED"},
    )
    return root


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
