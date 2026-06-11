from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from phase0.constants import BROKERS, COST_MODELS, SECOND_EA_CAMPAIGN_CANDIDATES


REQUIRED_READINESS_FIELDS = {
    "broker",
    "symbol",
    "timeframe",
    "start_utc",
    "end_utc",
    "bar_count",
    "missing_bar_count",
    "duplicate_bar_count",
    "largest_gap_minutes",
    "true_holdout_excluded",
    "history_asymmetry_note",
    "data_status",
}


def test_second_ea_data_readiness_json_has_required_fields_and_allows_owner_accepted_partial_runs(project_root: Path):
    payload = _read_payload(project_root)

    assert payload["overall_status"] == "PARTIAL"
    assert payload["matrix_runs_allowed"] is True
    assert payload["owner_accepted_partial_data"] is True
    assert payload["partial_data_decision_status"] == "OWNER_ACCEPTED_PARTIAL"
    assert payload["true_holdout_cutoff_utc"] == "2025-06-30T23:59:59+00:00"
    assert len(payload["rows"]) == 15

    for row in payload["rows"]:
        assert REQUIRED_READINESS_FIELDS <= set(row)
        assert row["symbol"] == "XAUUSD"
        assert row["timeframe"] in {"M5", "M15", "H1", "H4", "D1"}
        assert row["bar_count"] > 0
        assert row["duplicate_bar_count"] >= 0
        assert row["largest_gap_minutes"] >= 0
        assert row["true_holdout_excluded"] is True
        assert row["data_status"] in {"PASS", "PARTIAL", "FAIL"}


def test_second_ea_data_readiness_records_broker_window_asymmetry(project_root: Path):
    payload = _read_payload(project_root)
    statuses = {(row["broker"], row["data_status"]) for row in payload["rows"]}

    assert ("capital_com", "PASS") in statuses
    assert ("pepperstone", "PARTIAL") in statuses
    assert ("dukascopy", "PASS") in statuses
    assert all(row["data_status"] == "PASS" for row in payload["rows"] if row["broker"] == "dukascopy")
    assert all(
        "actual" in row["history_asymmetry_note"]
        for row in payload["rows"]
        if row["data_status"] == "PARTIAL"
    )
    assert {row["broker"] for row in payload["rows"] if row["data_status"] == "PARTIAL"} == {
        "pepperstone"
    }


def test_second_ea_data_readiness_content_hash_is_stable(project_root: Path):
    payload = _read_payload(project_root)
    stable_payload = {
        "overall_status": payload["overall_status"],
        "true_holdout_cutoff_utc": payload["true_holdout_cutoff_utc"],
        "rows": payload["rows"],
    }
    expected_hash = hashlib.sha256(
        json.dumps(stable_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    assert payload["readiness_content_sha256"] == expected_hash


def test_second_ea_matrix_manifest_records_candidate_9_cell_asymmetry(project_root: Path):
    manifest = project_root / "outputs" / "reports" / "SECOND_EA_MATRIX_MANIFEST.csv"
    rows = list(csv.DictReader(manifest.open(newline="", encoding="utf-8")))

    assert len(rows) == len(SECOND_EA_CAMPAIGN_CANDIDATES) * 9
    for candidate in SECOND_EA_CAMPAIGN_CANDIDATES:
        candidate_rows = [row for row in rows if row["candidate_id"] == candidate]
        assert {int(row["cell_id"]) for row in candidate_rows} == set(range(1, 10))
        assert {row["broker"] for row in candidate_rows} == set(BROKERS)
        assert {row["cost_model"] for row in candidate_rows} == set(COST_MODELS)
        assert {row["matrix_cell_status"] for row in candidate_rows} == {"BLOCKED_PREFLIGHT"}
        assert {row["run_permission"] for row in candidate_rows} == {"false"}

    partial_rows = [row for row in rows if row["data_status"] == "PARTIAL"]
    assert partial_rows
    assert all("actual" in row["history_asymmetry_note"] for row in partial_rows)
    assert {row["true_holdout_excluded"] for row in rows} == {"true"}


def _read_payload(project_root: Path) -> dict:
    path = project_root / "outputs" / "reports" / "SECOND_EA_DATA_EXTENSION_READINESS.json"
    return json.loads(path.read_text(encoding="utf-8"))
