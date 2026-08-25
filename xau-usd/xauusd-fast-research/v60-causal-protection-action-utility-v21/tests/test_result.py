from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def result() -> dict:
    return json.loads((ROOT / "outputs" / "RESULT.json").read_text())


def config() -> dict:
    return json.loads((ROOT / "config" / "diagnostic.json").read_text())


def test_config_matches_preregistered_model_and_gates() -> None:
    value = config()
    assert value["model"] == {
        "estimator": "Ridge",
        "alpha": 10.0,
        "fit_intercept": True,
        "prediction_threshold_exclusive": 0.0,
    }
    assert value["folds"] == [
        {"fold": "F1", "train_year_end": 2022, "evaluation_year": 2023},
        {"fold": "F2", "train_year_end": 2023, "evaluation_year": 2024},
        {"fold": "F3", "train_year_end": 2024, "evaluation_year": 2025},
        {"fold": "F4", "train_year_end": 2025, "evaluation_year": 2026},
    ]
    assert value["acceptance"]["bootstrap_seed"] == 20260825
    assert value["acceptance"]["bootstrap_resamples"] == 10000
    assert value["acceptance"]["bootstrap_percentile"] == 10.0


def test_result_is_read_only_and_exact_v6_parity() -> None:
    value = result()
    assert value["deployment_authorized"] is False
    assert value["broker_action_authorized"] is False
    assert not any(value["authorization"].values())
    assert value["gates"]["exact_dynamic_v6_behavioral_parity"] is True
    assert value["parity"]["full_event_rows_exact"] is True
    assert value["parity"]["close_path_exact"] is True
    assert value["parity"]["veto_audit_exact"] is True


def test_fixed_folds_and_snapshot_identity() -> None:
    value = result()
    assert [row["evaluation_year"] for row in value["folds"]] == [
        2023,
        2024,
        2025,
        2026,
    ]
    assert (
        value["snapshot_audit"]["rows"]
        == value["snapshot_audit"]["giveback_close_rows"]
    )
    assert value["snapshot_audit"]["rows"] > 0


def test_recorded_implementation_hashes_match_files() -> None:
    value = result()
    assert (
        value["implementation_sha256"]["runner"]
        == hashlib.sha256((ROOT / "run_diagnostic.py").read_bytes()).hexdigest()
    )
    assert (
        value["implementation_sha256"]["scenario"]
        == hashlib.sha256((ROOT / "src" / "scenario.py").read_bytes()).hexdigest()
    )


def test_decision_matches_all_gates() -> None:
    value = result()
    expected = (
        "DIAGNOSTIC_NOMINATES_PATH_DEPENDENT_V22"
        if all(value["gates"].values())
        else "NO_STABLE_PROTECTION_UTILITY_KEEP_V6"
    )
    assert value["decision"] == expected
