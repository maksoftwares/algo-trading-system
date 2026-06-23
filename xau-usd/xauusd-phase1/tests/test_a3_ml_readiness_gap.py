from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c11_reports_active_week_and_setup_group_gaps(tmp_path: Path) -> None:
    from ml.a3_meta_v1.readiness_gap import generate_readiness_gap_report

    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    decisions = reports / "C02_LABELED_DECISIONS.csv"
    _write_decisions(decisions)
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "TEST", "c02_labeled_decisions_csv": str(decisions)})
    _write_json(
        reports / "C03_TRAINING_READINESS_REPORT.json",
        {
            "status": "NO_GO",
            "checks": [
                {"gate": "market_setup_groups", "passed": False, "observed": "121", "required": ">=300"},
                {"gate": "active_weeks", "passed": False, "observed": "1.53", "required": ">=8"},
                {"gate": "minority_labels", "passed": True, "observed": "121", "required": ">=90"},
            ],
        },
    )
    _write_json(reports / "C02_C01_DATA_AUDIT.json", {"status": "PIPELINE_ONLY", "raw_source_row_counts": {"snapshot_rows": 2}, "selected_features": []})
    _write_json(reports / "C02_SLIPPAGE_READINESS.json", _slippage())
    _write_json(reports / "C02_BAR_TICK_EXPORT_REPORT.json", _export())

    output = generate_readiness_gap_report(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "WAITING_FOR_DECISION_HISTORY"
    active_gap = next(item for item in payload["gate_gaps"] if item["gate"] == "active_weeks")
    setup_gap = next(item for item in payload["gate_gaps"] if item["gate"] == "market_setup_groups")
    assert active_gap["gap_text"] == "6.47 weeks"
    assert setup_gap["gap_text"] == "179"
    assert payload["backfill_assessment"]["older_market_history_before_first_decision"] is True


def test_c11_render_mentions_no_authorization() -> None:
    from ml.a3_meta_v1.readiness_gap import render_readiness_gap_report_md

    report = render_readiness_gap_report_md(
        {
            "status": "GAP_REMAINS",
            "dataset_version": "TEST",
            "c03_status": "NO_GO",
            "decision_coverage": {"rows": 2, "min_decision_utc": "2026-06-09T00:00:00Z", "max_decision_utc": "2026-06-19T00:00:00Z", "active_span_weeks": 1.43},
            "gate_gaps": [{"gate": "active_weeks", "passed": False, "observed": "1.53", "required": ">=8", "gap_text": "6.47 weeks"}],
            "slippage_gap": {"status": "INSUFFICIENT", "accounts": []},
            "export_coverage": {"accounts": []},
            "backfill_assessment": {"verdict": "NEEDS_MORE_ACTIVE_DECISION_TIME", "detail": "Collect more.", "estimated_active_weeks_pass_date_utc": "2026-08-03T00:00:00Z"},
            "next_actions": ["Collect more data."],
        }
    )

    assert "Overall status: GAP_REMAINS" in report
    assert "Model training authorized: false." in report
    assert "Python demo predictions authorized: false." in report
    assert "Broker action authorized: false." in report


def test_c11_script_loads() -> None:
    module = load_script("c11_analyze_ml_readiness_gap")

    assert hasattr(module, "main")


def _write_decisions(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["decision_time"])
        writer.writeheader()
        writer.writerow({"decision_time": "2026-06-09 00:00:00Z"})
        writer.writerow({"decision_time": "2026-06-19 00:00:00Z"})


def _slippage() -> dict:
    return {
        "status": "INSUFFICIENT",
        "requirements": {"entry_fills": 200, "sl_exits": 100, "tp_exits": 50, "request_price_resolved": 200},
        "accounts": [{"account_label": "A1", "entry_fills": 10, "sl_exits": 5, "tp_exits": 2, "request_price_resolved": 1, "slippage_status": "INSUFFICIENT"}],
    }


def _export() -> dict:
    return {
        "status": "PASS",
        "requested_start_utc": "2026-06-01T00:00:00Z",
        "snapshot_cutoff_utc": "2026-06-21T00:00:00Z",
        "account_records": [
            {
                "account_label": "A1",
                "status": "PASS",
                "coverage": {
                    "bars": {"M5": {"row_count": 10, "min_time_utc": "2026-06-01T00:00:00Z", "max_time_utc": "2026-06-19T00:00:00Z"}},
                    "ticks": {"chunks": [{"row_count": 5}, {"row_count": 0}]},
                },
            }
        ],
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
