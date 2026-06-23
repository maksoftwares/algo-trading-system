from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c57_analyzes_quarantined_replay_without_authorizing_training(tmp_path: Path) -> None:
    from ml.a3_meta_v1.replay_observer_analysis import analyze_replay_observer_evidence

    root = _root_with_replay_analysis_inputs(tmp_path)

    output = analyze_replay_observer_evidence(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "REPLAY_OBSERVER_ANALYSIS_READY_RESEARCH_ONLY"
    assert payload["usefulness_summary"]["signal_rows"] == 3
    assert payload["usefulness_summary"]["would_signal_rows"] == 2
    assert payload["usefulness_summary"]["research_candidate_rows"] == 2
    assert payload["duplicate_overlap"]["exact_live_setup_overlap_rows"] == 1
    assert payload["duplicate_overlap"]["date_direction_overlap_rows"] == 1
    assert payload["live_data_needed"]["c03_status"] == "NO_GO"
    assert payload["authorization"]["training_authorized"] is False
    assert payload["authorization"]["broker_action_authorized"] is False
    assert pointer["c57_replay_observer_analysis_status"] == "REPLAY_OBSERVER_ANALYSIS_READY_RESEARCH_ONLY"
    assert pointer["python_demo_predictions_authorized"] is False


def test_c57_blocks_when_replay_not_quarantined(tmp_path: Path) -> None:
    from ml.a3_meta_v1.replay_observer_analysis import analyze_replay_observer_evidence

    root = _root_with_replay_analysis_inputs(tmp_path, bad_label_status=True)

    output = analyze_replay_observer_evidence(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    checks = {check["check"]: check for check in payload["safety"]["checks"]}

    assert payload["status"] == "REPLAY_OBSERVER_ANALYSIS_BLOCKED"
    assert checks["label_status_replay_observer_only"]["passed"] is False
    assert payload["authorization"]["training_authorized"] is False


def test_c57_script_loads() -> None:
    module = load_script("c57_analyze_replay_observer")

    assert hasattr(module, "main")


def _root_with_replay_analysis_inputs(tmp_path: Path, *, bad_label_status: bool = False) -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    dataset = root / "data" / "ml" / "a3_meta_v1" / "c02" / "DATASET_C57"
    replay_csv = dataset / "normalized" / "replay_observer" / "A3_lane.csv"
    market_groups = dataset / "normalized" / "signals" / "market_setup_groups.csv"
    labeled = reports / "C02_LABELED_DECISIONS.csv"
    label_status = "BAD_STATUS" if bad_label_status else "REPLAY_OBSERVER_ONLY"
    replay_rows = [
        _replay_row("2026.06.15 05:50:00", "LONG", "4308.82", "true", label_status),
        _replay_row("2026.06.16 10:00:00", "SHORT", "4310.00", "true", label_status),
        _replay_row("2026.06.16 10:05:00", "SHORT", "0.00", "false", label_status),
    ]
    _write_csv(replay_csv, replay_rows)
    _write_csv(
        market_groups,
        [
            {
                "symbol": "XAUUSD",
                "direction": "LONG",
                "retest_bar_time_utc": "2026-06-15 05:50:00Z",
                "normalized_level_price": "4308.82",
            }
        ],
    )
    _write_csv(
        labeled,
        [
            {
                "signal_id": "1033669|XAUUSD|breakout_retest|LONG|2026-06-15 05:45:00Z|2026-06-15 05:50:00Z|2026-06-15 05:55:00Z|4308.82",
                "decision_time": "2026-06-15 05:50:00Z",
            }
        ],
    )
    _write_json(
        reports / "C02_DATASET_POINTER.json",
        {
            "dataset_version": "DATASET_C57",
            "market_setup_groups_csv": str(market_groups),
            "c02_labeled_decisions_csv": str(labeled),
            "c56_replay_quarantined_observer_csv": str(replay_csv),
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
    )
    _write_json(
        reports / "A3_ML_REPLAY_IMPORT_STATUS.json",
        {
            "status": "REPLAY_OBSERVER_IMPORT_QUARANTINED",
            "dataset_version": "DATASET_C57",
            "selected_lane_id": "A3_lane",
            "outputs": {"quarantined_observer_csv": str(replay_csv)},
        },
    )
    _write_json(
        reports / "C03_TRAINING_READINESS_REPORT.json",
        {
            "status": "NO_GO",
            "checks": [
                {"gate": "market_setup_groups", "passed": False, "observed": "223", "required": ">=300"},
                {"gate": "active_weeks", "passed": False, "observed": "3.37", "required": ">=8"},
                {"gate": "slippage_readiness", "passed": False, "observed": "INSUFFICIENT", "required": "ADEQUATE"},
            ],
        },
    )
    _write_json(
        reports / "C02_C01_DATA_AUDIT.json",
        {
            "global_feature_budget": 0,
            "missingness": {"retest_penetration_atr": 349},
            "slippage_adequacy_status": {
                "entry_fills": 0,
                "sl_exits": 0,
                "tp_exits": 0,
                "required_entry_fills": 200,
                "required_sl_exits": 100,
                "required_tp_exits": 50,
            },
        },
    )
    return root


def _replay_row(timestamp: str, direction: str, level: str, would_signal: str, label_status: str) -> dict[str, str]:
    return {
        "timestamp_utc": timestamp,
        "m5_bar_time": timestamp,
        "symbol": "XAUUSD",
        "direction": direction,
        "would_signal": would_signal,
        "reason_code": "BREAKOUT_RETEST_LONG_DRY_RUN" if direction == "LONG" else "BREAKOUT_RETEST_SHORT_DRY_RUN",
        "level_price": level,
        "entry_price": "4310.00",
        "stop_loss": "4300.00",
        "take_profit": "4330.00",
        "stop_distance_points": "100.00",
        "estimated_cost_R": "0.05",
        "dry_run": "true",
        "broker_action_allowed": "false",
        "h1_trend": "UP",
        "h4_trend": "UP",
        "dirstate_regime": "FLAT",
        "dirstate_strength": "0.1",
        "source_type": "strategy_tester_replay",
        "label_status": label_status,
        "candidate_trainable": "false",
        "training_authorized": "false",
        "broker_action_authorized": "false",
    }


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
