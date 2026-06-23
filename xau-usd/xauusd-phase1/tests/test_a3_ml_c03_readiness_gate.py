from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c03_readiness_gate_blocks_when_slippage_and_groups_are_insufficient(tmp_path: Path) -> None:
    from ml.a3_meta_v1.readiness_gate import generate_c03_training_readiness_report

    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    _write_json(
        reports / "C02_DATASET_POINTER.json",
        {
            "dataset_version": "TEST",
            "label_audit_report": str(reports / "labels.json"),
            "slippage_readiness_report": str(reports / "slippage.json"),
            "signal_grouping_audit_report": str(reports / "grouping.json"),
        },
    )
    _write_json(
        reports / "C02_C01_DATA_AUDIT.json",
        {
            "status": "PIPELINE_ONLY",
            "class_balance": {"positive": 100, "negative": 120},
            "direction_balance": {"LONG": 100, "SHORT": 120},
            "regime_balance": {"FALLING": 220},
            "global_feature_budget": 0,
            "leakage_violations": [],
            "fold_diagnostics": [{"train_start_utc": "2026-06-01T00:00:00Z", "test_end_utc": "2026-06-10T00:00:00Z"}],
        },
    )
    _write_json(reports / "labels.json", {"counts": {"positive": 100, "negative": 120}})
    _write_json(reports / "slippage.json", {"status": "INSUFFICIENT"})
    _write_json(reports / "grouping.json", {"counts": {"market_setup_groups": 121}})

    output = generate_c03_training_readiness_report(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "NO_GO"
    assert payload["authorization"]["training_authorized"] is False
    assert any(check["gate"] == "slippage_readiness" and not check["passed"] for check in payload["checks"])


def test_c03_readiness_gate_uses_live_only_counts_when_replay_rows_exist(tmp_path: Path) -> None:
    from ml.a3_meta_v1.readiness_gate import generate_c03_training_readiness_report

    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    _write_json(
        reports / "C02_DATASET_POINTER.json",
        {
            "dataset_version": "TEST_REPLAY",
            "label_audit_report": str(reports / "labels.json"),
            "slippage_readiness_report": str(reports / "slippage.json"),
            "signal_grouping_audit_report": str(reports / "grouping.json"),
        },
    )
    _write_json(
        reports / "C02_C01_DATA_AUDIT.json",
        {
            "status": "EXPLORATORY_MODEL",
            "live_only_status": "EXPLORATORY_MODEL",
            "source_type_counts": {"live": 120, "strategy_tester_replay": 900},
            "class_balance": {"positive": 500, "negative": 500},
            "live_only_class_balance": {"positive": 80, "negative": 70},
            "direction_balance": {"LONG": 600, "SHORT": 400},
            "live_only_direction_balance": {"LONG": 70, "SHORT": 80},
            "regime_balance": {"FALLING": 500, "RISING": 500},
            "live_only_regime_balance": {"FALLING": 150},
            "global_feature_budget": 10,
            "live_only_global_feature_budget": 4,
            "leakage_violations": [],
            "live_only_leakage_violations": [],
            "fold_diagnostics": [{"train_start_utc": "2026-01-01T00:00:00Z", "test_end_utc": "2026-06-01T00:00:00Z"}],
            "live_only_fold_diagnostics": [{"train_start_utc": "2026-06-01T00:00:00Z", "test_end_utc": "2026-06-14T00:00:00Z"}],
        },
    )
    _write_json(
        reports / "labels.json",
        {
            "counts": {"positive": 500, "negative": 500},
            "live_only_counts": {"positive": 80, "negative": 70},
            "source_type_counts": {"live": 150, "strategy_tester_replay": 900},
        },
    )
    _write_json(
        reports / "slippage.json",
        {
            "status": "ADEQUATE",
            "live_only_status": "INSUFFICIENT",
            "source_type_counts": {"live": 150, "strategy_tester_replay": 900},
        },
    )
    _write_json(
        reports / "grouping.json",
        {
            "counts": {"market_setup_groups": 999},
            "live_only_counts": {"market_setup_groups": 121},
            "source_type_counts": {"live": 121, "strategy_tester_replay": 878},
        },
    )

    output = generate_c03_training_readiness_report(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    checks = {check["gate"]: check for check in payload["checks"]}

    assert payload["status"] == "NO_GO"
    assert payload["source_scope"]["gate_counts_source"] == "live_only"
    assert checks["market_setup_groups"]["observed"] == "121"
    assert checks["active_weeks"]["observed"] == "1.86"
    assert checks["minority_labels"]["observed"] == "70"
    assert checks["feature_budget"]["observed"] == "4"
    assert checks["slippage_readiness"]["observed"] == "INSUFFICIENT"
    assert payload["authorization"]["training_authorized"] is False


def test_c03_readiness_script_loads() -> None:
    module = load_script("c03_training_readiness")

    assert hasattr(module, "main")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
