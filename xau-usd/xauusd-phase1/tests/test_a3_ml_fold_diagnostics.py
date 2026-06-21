from __future__ import annotations

from phase2x_test_helpers import ROOT


def test_data_contract_contains_per_fold_purge_and_budget_counts() -> None:
    text = (ROOT / "docs" / "A3_ML_DATA_CONTRACT_V1.md").read_text(encoding="utf-8")
    assert "feature-budget contract owns the exact per-fold" in text
    assert "must not maintain a second copy of the field list" in text


def test_feature_budget_contract_contains_per_fold_purge_and_budget_counts() -> None:
    text = (ROOT / "docs" / "A3_ML_FEATURE_BUDGET_CONTRACT_V1.md").read_text(encoding="utf-8")
    for token in (
        "fold_id",
        "purged_overlap_groups",
        "purge_loss_pct",
        "embargo_excluded_groups",
        "calibration_positive",
        "calibration_negative",
        "model_fit_positive",
        "model_fit_negative",
        "minority_events_fit_fold",
        "feature_budget_fold",
        "budget_binding_fold_id",
    ):
        assert token in text


def test_validation_protocol_requires_fold_diagnostics() -> None:
    text = (ROOT / "docs" / "A3_ML_VALIDATION_PROTOCOL_V1.md").read_text(encoding="utf-8")
    assert "per-fold purge, embargo, calibration, class-count, and feature-budget diagnostics" in text
    assert "A3_ML_FEATURE_BUDGET_CONTRACT_V1.md" in text


def test_feature_budget_contract_names_binding_fold() -> None:
    text = (ROOT / "docs" / "A3_ML_FEATURE_BUDGET_CONTRACT_V1.md").read_text(encoding="utf-8")
    assert "budget_binding_fold_id" in text
    assert "Report:" in text
    assert "which fold binds the budget" in text
    assert "288-active-bar horizon contributes to overlap" in text
