from __future__ import annotations

from phase2x_test_helpers import ROOT


def _feature_budget_text() -> str:
    return (ROOT / "docs" / "A3_ML_FEATURE_BUDGET_CONTRACT_V1.md").read_text(encoding="utf-8")


def test_budget_uses_post_calibration_fit_segment() -> None:
    text = _feature_budget_text()
    ordered_steps = (
        "Create chronological outer-training block",
        "Remove fuzzy setup groups assigned to outer test",
        "Purge event intervals overlapping outer test",
        "Apply the locked embargo",
        "Remove unresolved or non-trainable labels",
        "Reserve the pre-registered chronological calibration tail",
        "Remaining rows form the model-fit segment",
        "Count positive and negative labels in the model-fit segment",
    )
    last = -1
    for step in ordered_steps:
        position = text.index(step)
        assert position > last
        last = position
    assert "Do not calculate the feature budget from the pre-calibration training block." in text


def test_budget_below_five_blocks_training() -> None:
    text = _feature_budget_text()
    assert "global_feature_budget < 5" in text
    assert "dataset_status = PIPELINE_ONLY" in text
    assert "supervised model training = prohibited" in text


def test_same_feature_prefix_used_across_folds() -> None:
    text = _feature_budget_text()
    assert "Use one global feature prefix across all folds." in text
    assert "Do not use a larger feature prefix in later folds." in text
    assert "Do not drop the earliest fold solely to increase model capacity." in text


def test_interaction_counts_against_budget_and_replaces_last_feature() -> None:
    text = _feature_budget_text()
    assert "The interaction may be evaluated only when ASYMMETRY_DEMONSTRATED" in text
    assert "It must not exceed global_feature_budget." in text
    assert "replace feature N with h1_slope_direction_interaction" in text
    assert "last feature in the ordered prefix" in text


def test_holding_horizon_cannot_expand_feature_budget() -> None:
    text = _feature_budget_text()
    assert "may not be changed to enlarge global_feature_budget" in text
    assert "A3_ML_EXECUTION_LABEL_CONTRACT_V1.md" in text
