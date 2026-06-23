from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c37_reports_approval_alone_not_sufficient_when_other_gates_remain(tmp_path: Path) -> None:
    from ml.a3_meta_v1.contract_expansion_impact_estimate import generate_contract_expansion_impact_estimate

    root = _root_with_reports(tmp_path)

    output = generate_contract_expansion_impact_estimate(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))
    gates = {gate["gate"]: gate for gate in payload["gate_projection"]}

    assert payload["status"] == "APPROVAL_ALONE_NOT_SUFFICIENT"
    assert gates["market_setup_groups"]["projected_passed"] is True
    assert gates["market_setup_groups"]["projected_observed"] == "1603"
    assert gates["active_weeks"]["projected_passed"] is False
    assert gates["feature_budget"]["projected_passed"] is False
    assert gates["slippage_readiness"]["projected_passed"] is False
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert payload["authorization"]["broker_action_authorized"] is False
    assert pointer["c37_contract_expansion_impact_estimate_status"] == "APPROVAL_ALONE_NOT_SUFFICIENT"
    assert pointer["python_demo_predictions_authorized"] is False


def test_c37_reports_no_candidates_when_c34_has_no_out_of_scope_rows(tmp_path: Path) -> None:
    from ml.a3_meta_v1.contract_expansion_impact_estimate import generate_contract_expansion_impact_estimate

    root = _root_with_reports(tmp_path, out_of_scope_rows=0, out_of_scope_groups=0)

    output = generate_contract_expansion_impact_estimate(root)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "NO_EXPANSION_CANDIDATES"
    assert payload["authorization"]["training_authorized"] is False


def test_c37_script_loads() -> None:
    module = load_script("c37_estimate_contract_expansion_impact")

    assert hasattr(module, "main")


def _root_with_reports(tmp_path: Path, *, out_of_scope_rows: int = 2747, out_of_scope_groups: int = 1381) -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "DATASET_A"})
    _write_json(
        reports / "C02_C01_DATA_AUDIT.json",
        {
            "status": "PIPELINE_ONLY",
            "labeled_and_trainable_setup_groups": {"candidate_trainable_groups": 0},
            "regime_balance": {"FALLING": 110, "UNKNOWN": 236},
            "global_feature_budget": 0,
        },
    )
    _write_json(
        reports / "C03_TRAINING_READINESS_REPORT.json",
        {
            "status": "NO_GO",
            "dataset_version": "DATASET_A",
            "checks": [
                _check("dataset_status", False, "PIPELINE_ONLY", "EXPLORATORY_MODEL or higher"),
                _check("market_setup_groups", False, "222", ">=300"),
                _check("minority_labels", True, "169", ">=90"),
                _check("active_weeks", False, "3.36", ">=8"),
                _check("both_directions", True, "LONG,SHORT", "LONG and SHORT"),
                _check("at_least_two_regimes", False, "FALLING", ">=2 non-UNKNOWN regimes"),
                _check("feature_budget", False, "0", ">=6"),
                _check("slippage_readiness", False, "INSUFFICIENT", "ADEQUATE"),
                _check("leakage", True, "0", "0"),
            ],
        },
    )
    _write_json(
        reports / "A3_ML_READINESS_GAP_REPORT.json",
        {
            "status": "GAP_REMAINS",
            "decision_coverage": {
                "min_decision_utc": "2026-05-29T09:39:56Z",
                "max_decision_utc": "2026-06-21T22:54:59Z",
            },
        },
    )
    _write_json(
        reports / "A3_ML_DECISION_BACKFILL_AUDIT_STATUS.json",
        {
            "status": "CURRENT_SCOPE_EXHAUSTED_OUT_OF_SCOPE_BACKFILL_FOUND",
            "dataset_version": "DATASET_A",
            "summary": {
                "out_of_scope_files_with_would_signals": 13 if out_of_scope_rows else 0,
                "out_of_scope_would_signal_rows": out_of_scope_rows,
                "out_of_scope_estimated_groups": out_of_scope_groups,
            },
            "out_of_scope_candidates": [
                {
                    "family": "round_number_retest",
                    "min_signal_utc": "2026-05-29T09:34:56Z",
                    "max_signal_utc": "2026-06-19T16:10:00Z",
                }
            ]
            if out_of_scope_rows
            else [],
        },
    )
    _write_json(
        reports / "A3_ML_CONTRACT_EXPANSION_CONFIG_PROPOSAL_STATUS.json",
        {"status": "WAITING_FOR_REVIEW_APPROVAL"},
    )
    return root


def _check(gate: str, passed: bool, observed: str, required: str) -> dict:
    return {"gate": gate, "passed": passed, "observed": observed, "required": required}


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
