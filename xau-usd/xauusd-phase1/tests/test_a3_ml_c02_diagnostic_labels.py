from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c02_diagnostic_label_builder_writes_tp_without_authorizing_training(tmp_path: Path) -> None:
    root = tmp_path / "phase1"
    dataset = root / "data" / "ml" / "a3_meta_v1" / "c02" / "TEST"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    decisions = reports / "C02_NORMALIZED_DECISIONS.csv"
    signal_instances = dataset / "normalized" / "signals" / "signal_instances.csv"
    ticks = dataset / "raw" / "A1" / "ticks" / "XAUUSD_ticks_20260601.csv"
    deals = dataset / "raw" / "A1" / "history" / "deals.csv"
    for account in ("A2", "A3"):
        _write_csv(dataset / "raw" / account / "history" / "deals.csv", ["entry", "comment"], [])
    _write_csv(
        decisions,
        [
            "signal_id",
            "candidate_id",
            "decision_time",
            "opened",
            "reason",
            "session_bucket",
            "cost_R",
            "final_r_if_raw",
            "source_logical_source_name",
            "source_file_sha256",
            "source_row_number",
            "schema_mapping_status",
        ],
        [
            {
                "signal_id": "1025742|XAUUSD|breakout_retest|LONG|2026-06-01 00:00:00Z|2026-06-01 00:05:00Z|2026-06-01 00:10:00Z|100.00",
                "candidate_id": "B0_RAW_ALL_SESSION",
                "decision_time": "2026-06-01 00:14:00Z",
                "opened": "false",
                "reason": "TEST",
                "session_bucket": "Night 20:00-05:59",
                "cost_R": "",
                "final_r_if_raw": "",
                "source_logical_source_name": "test_signal",
                "source_file_sha256": "abc",
                "source_row_number": "1",
                "schema_mapping_status": "TEST",
            }
        ],
    )
    _write_csv(
        signal_instances,
        [
            "account_label",
            "account_scope",
            "source_file_sha256",
            "source_row_number",
            "logical_source_name",
            "entry_price",
            "stop_loss",
            "take_profit",
            "stop_distance_points",
            "spread_points",
        ],
        [
            {
                "account_label": "A1",
                "account_scope": "1025742",
                "source_file_sha256": "abc",
                "source_row_number": "1",
                "logical_source_name": "test_signal",
                "entry_price": "100",
                "stop_loss": "97",
                "take_profit": "104.5",
                "stop_distance_points": "300",
                "spread_points": "50",
            }
        ],
    )
    _write_csv(
        ticks,
        ["time_utc", "bid", "ask"],
        [
            {"time_utc": "2026-06-01T00:14:01Z", "bid": "100.00", "ask": "100.50"},
            {"time_utc": "2026-06-01T00:15:00Z", "bid": "105.10", "ask": "105.60"},
        ],
    )
    _write_csv(deals, ["entry", "comment"], [{"entry": "0", "comment": "entry"}])
    (reports / "C02_DATASET_POINTER.json").write_text(
        json.dumps(
            {
                "dataset_version": "TEST",
                "output_root": str(dataset),
                "c02_decisions_csv": str(decisions),
                "snapshot_cutoff_utc": "2026-06-02T00:00:00Z",
                "training_authorized": False,
            }
        ),
        encoding="utf-8",
    )
    from ml.a3_meta_v1.diagnostic_labels import generate_diagnostic_labels

    output = generate_diagnostic_labels(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    labels = list(csv.DictReader((dataset / "normalized" / "labels" / "diagnostic_tick_labels.csv").open(encoding="utf-8")))

    assert payload["boundary"]["model_training_authorized"] is False
    assert labels[0]["label_status"] == "TP"
    assert labels[0]["model_training_authorized"] == "false"


def test_c02_diagnostic_label_script_loads() -> None:
    module = load_script("c02_build_diagnostic_labels")

    assert hasattr(module, "main")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
