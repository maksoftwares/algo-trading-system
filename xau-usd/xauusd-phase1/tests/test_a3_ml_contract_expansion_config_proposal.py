from __future__ import annotations

import json
import sys
from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_c36_default_proposes_nothing_and_keeps_config_locked(tmp_path: Path) -> None:
    from ml.a3_meta_v1.contract_expansion_config_proposal import generate_contract_expansion_config_proposal

    root = _root_with_c34(tmp_path)

    output = generate_contract_expansion_config_proposal(root)
    payload = json.loads(output.read_text(encoding="utf-8"))
    pointer = json.loads((root / "outputs" / "reports" / "C02_DATASET_POINTER.json").read_text(encoding="utf-8"))

    assert payload["status"] == "WAITING_FOR_REVIEW_APPROVAL"
    assert payload["candidate_summary"]["candidate_files"] == 2
    assert payload["candidate_summary"]["selected_files"] == 0
    assert payload["selected_entries"] == []
    assert payload["proposed_config_if_approved"]["contract_expansion_authorized"] is False
    assert payload["authorization"]["python_demo_predictions_authorized"] is False
    assert payload["authorization"]["broker_action_authorized"] is False
    assert pointer["c36_contract_expansion_config_proposal_status"] == "WAITING_FOR_REVIEW_APPROVAL"
    assert pointer["python_demo_predictions_authorized"] is False


def test_c36_refuses_authorize_without_review_reference(tmp_path: Path) -> None:
    from ml.a3_meta_v1.contract_expansion_config_proposal import generate_contract_expansion_config_proposal

    root = _root_with_c34(tmp_path)

    try:
        generate_contract_expansion_config_proposal(
            root,
            allowed_families=("round_number_retest",),
            authorize=True,
        )
    except ValueError as exc:
        assert "review_reference" in str(exc)
    else:
        raise AssertionError("C36 accepted authorization without review_reference")


def test_c36_writes_approved_config_only_with_explicit_authorization(tmp_path: Path) -> None:
    from ml.a3_meta_v1.contract_expansion_config_proposal import generate_contract_expansion_config_proposal
    from ml.a3_meta_v1.contract_scope import load_contract_scope

    root = _root_with_c34(tmp_path)
    config_path = root / "config" / "ml" / "a3_ml_contract_expansion.json"

    output = generate_contract_expansion_config_proposal(
        root,
        allowed_families=("round_number_retest",),
        review_reference="Reviewer approved round_number_retest for C36 test",
        authorize=True,
        write_config=True,
        config_json=config_path,
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    config = json.loads(config_path.read_text(encoding="utf-8"))
    scope = load_contract_scope(root)

    assert payload["status"] == "APPROVED_CONFIG_WRITTEN"
    assert payload["candidate_summary"]["selected_files"] == 1
    assert config["contract_expansion_authorized"] is True
    assert config["allowed_families"] == ["round_number_retest"]
    assert list(config["accounts"]) == ["A1"]
    assert scope.active_families == ("breakout_retest", "round_number_retest")
    assert len(scope.accounts["A1"]) == 1
    assert payload["authorization"]["training_authorized"] is False
    assert payload["authorization"]["broker_action_authorized"] is False


def test_c36_script_loads() -> None:
    module = load_script("c36_generate_contract_expansion_config_proposal")

    assert hasattr(module, "main")


def _root_with_c34(tmp_path: Path) -> Path:
    root = tmp_path / "phase1"
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True)
    _write_json(reports / "C02_DATASET_POINTER.json", {"dataset_version": "DATASET_A"})
    _write_json(
        reports / "A3_ML_DECISION_BACKFILL_AUDIT_STATUS.json",
        {
            "status": "CURRENT_SCOPE_EXHAUSTED_OUT_OF_SCOPE_BACKFILL_FOUND",
            "dataset_version": "DATASET_A",
            "out_of_scope_candidates": [
                {
                    "account_label": "A1",
                    "account_scope": "1025742",
                    "filename": "experimental_demo_executor_signal_log_round_number_retest_v0_xauusd.csv",
                    "family": "round_number_retest",
                    "would_signal_rows": 100,
                    "min_signal_utc": "2026-06-01T00:00:00Z",
                    "max_signal_utc": "2026-06-02T00:00:00Z",
                },
                {
                    "account_label": "A2",
                    "account_scope": "1033030",
                    "filename": "experimental_demo_attachment_log_session_extreme_retest_v0_xauusd.csv",
                    "family": "session_extreme_retest",
                    "would_signal_rows": 20,
                    "min_signal_utc": "2026-06-01T00:00:00Z",
                    "max_signal_utc": "2026-06-02T00:00:00Z",
                },
            ],
        },
    )
    _write_json(
        reports / "A3_ML_CONTRACT_EXPANSION_PACKET_STATUS.json",
        {"status": "CONTRACT_EXPANSION_REVIEW_REQUIRED", "dataset_version": "DATASET_A"},
    )
    return root


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
