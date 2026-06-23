from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c35_requests_contract_expansion_without_authorizing_predictions(tmp_path: Path) -> None:
    from ml.a3_meta_v1.contract_expansion_packet import generate_contract_expansion_packet

    root = _root_with_reports(tmp_path)
    _write_json(
        root / "outputs" / "reports" / "A3_ML_DECISION_BACKFILL_AUDIT_STATUS.json",
        _c34_payload(uncataloged_current_scope_files=0, out_of_scope_would_signal_rows=2455),
    )

    output = generate_contract_expansion_packet(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "CONTRACT_EXPANSION_REVIEW_REQUIRED"
    assert payload["summary"]["out_of_scope_would_signal_rows"] == 2455
    assert payload["summary"]["all_accounts_collecting"] is True
    assert payload["candidate_families"][0]["family"] == "round_number_retest"
    assert "versioned contract expansion" in payload["reviewer_prompt"]
    assert payload["authorization"]["contract_expansion_authorized"] is False
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert payload["authorization"]["broker_action_authorized"] is False
    assert pointer["c35_contract_expansion_packet_status"] == "CONTRACT_EXPANSION_REVIEW_REQUIRED"
    assert pointer["python_demo_predictions_authorized"] is False


def test_c35_prioritizes_current_scope_import_review(tmp_path: Path) -> None:
    from ml.a3_meta_v1.contract_expansion_packet import generate_contract_expansion_packet

    root = _root_with_reports(tmp_path)
    _write_json(
        root / "outputs" / "reports" / "A3_ML_DECISION_BACKFILL_AUDIT_STATUS.json",
        _c34_payload(uncataloged_current_scope_files=1, out_of_scope_would_signal_rows=2455),
    )

    output = generate_contract_expansion_packet(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "CURRENT_SCOPE_IMPORT_REVIEW_REQUIRED"
    assert "Review uncataloged current-scope files" in payload["next_allowed_stage"]
    assert payload["boundary"]["data_export_attempted"] is False


def test_c35_handles_c03_pass_without_expansion(tmp_path: Path) -> None:
    from ml.a3_meta_v1.contract_expansion_packet import generate_contract_expansion_packet

    root = _root_with_reports(tmp_path, c03_status="PASS")
    _write_json(
        root / "outputs" / "reports" / "A3_ML_DECISION_BACKFILL_AUDIT_STATUS.json",
        _c34_payload(uncataloged_current_scope_files=0, out_of_scope_would_signal_rows=2455),
    )

    output = generate_contract_expansion_packet(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "NO_EXPANSION_REQUIRED_C03_PASS"
    assert payload["authorization"]["training_authorized"] is False
    assert payload["next_allowed_stage"] == "C03 already passes; continue through C05/C04/C06/C23 using the locked contract."


def test_c35_script_loads() -> None:
    module = load_script("c35_generate_contract_expansion_packet")

    assert hasattr(module, "main")


def _root_with_reports(tmp_path: Path, *, c03_status: str = "NO_GO") -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    docs = root / "docs"
    reports.mkdir(parents=True)
    docs.mkdir(parents=True)
    (docs / "A3_ML_DATA_CONTRACT_V1.md").write_text("# Contract\n", encoding="utf-8")
    (docs / "A3_ML_SHADOW_GOVERNANCE_V1.md").write_text("# Governance\n", encoding="utf-8")
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "DATASET_A"})
    _write_json(reports / "C03_TRAINING_READINESS_REPORT.json", _c03_payload(c03_status))
    _write_json(
        reports / "A3_ML_READINESS_GAP_REPORT.json",
        {
            "status": "GAP_REMAINS",
            "backfill_assessment": {"remaining_active_weeks": 4.64},
        },
    )
    _write_json(
        reports / "A3_ML_DEMO_SHADOW_COLLECTION_HEALTH_STATUS.json",
        {
            "status": "COLLECTING_LIVE_WAITING_FOR_DATA",
            "collection_health": {
                "all_accounts_collecting": True,
                "total_observer_prediction_rows": 817,
                "total_broker_shadow_tap_rows": 63,
            },
        },
    )
    _write_json(reports / "A3_ML_DECISION_BACKFILL_AUDIT_STATUS.json", _c34_payload())
    return root


def _c03_payload(status: str) -> dict:
    return {
        "status": status,
        "checks": [
            {"gate": "market_setup_groups", "observed": "222"},
            {"gate": "active_weeks", "observed": "3.36"},
            {"gate": "feature_budget", "observed": "0"},
            {"gate": "slippage_readiness", "observed": "INSUFFICIENT"},
        ],
    }


def _c34_payload(*, uncataloged_current_scope_files: int = 0, out_of_scope_would_signal_rows: int = 0) -> dict:
    return {
        "status": "CURRENT_SCOPE_EXHAUSTED_OUT_OF_SCOPE_BACKFILL_FOUND",
        "summary": {
            "current_scope_would_signal_rows": 569,
            "uncataloged_current_scope_files": uncataloged_current_scope_files,
            "out_of_scope_would_signal_rows": out_of_scope_would_signal_rows,
            "out_of_scope_estimated_groups": 1127,
        },
        "family_summary": [
            {
                "family": "round_number_retest",
                "would_signal_rows": out_of_scope_would_signal_rows,
                "estimated_groups": 1127,
                "files": 7,
                "min_signal_utc": "2026-05-29T09:34:56Z",
                "max_signal_utc": "2026-06-19T16:10:00Z",
            }
        ],
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
