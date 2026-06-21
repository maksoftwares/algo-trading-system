from __future__ import annotations

from phase2x_test_helpers import ROOT


def _direction_text() -> str:
    return (ROOT / "docs" / "A3_ML_DIRECTION_ASYMMETRY_PROTOCOL_V1.md").read_text(encoding="utf-8")


def _model_text() -> str:
    return (ROOT / "docs" / "A3_ML_MODEL_SELECTION_PROTOCOL_V1.md").read_text(encoding="utf-8")


def test_direction_metrics_are_computed_separately() -> None:
    text = _direction_text()
    assert "report separately for LONG and SHORT" in text
    for token in ("Brier score", "calibration intercept", "PF under P95-stress labels", "BAD_SIGNAL share"):
        assert token in text


def test_asymmetry_gate_requires_inner_oof_predictions() -> None:
    text = _direction_text()
    assert "inner OOF predictions" in text
    assert "Outer-test diagnostics are reporting only" in text
    assert "may not retroactively select the model" in text


def test_asymmetry_gate_sample_minimums_and_fold_consistency() -> None:
    text = _direction_text()
    for token in (
        "LONG labeled setup groups >= 100",
        "SHORT labeled setup groups >= 100",
        "LONG minority class >= 30",
        "SHORT minority class >= 30",
        "consistent in at least 2 of the 3 inner expanding folds",
        "90 percent confidence interval",
    ):
        assert token in text


def test_interaction_term_exact_formula_and_singleton() -> None:
    text = _direction_text()
    assert "h1_slope_direction_interaction =" in text
    assert "direction_sign * h1_ema20_slope_aligned_atr" in text
    assert "Exactly one additional feature" in text
    assert "Do not add a second interaction" in text


def test_direction_interaction_does_not_change_final_gates() -> None:
    text = _model_text()
    assert "It does not lower, waive, or substitute for any final candidate gate." in text
    assert "point PF >= 1.30" in text
    assert "PF fifth percentile > 1.00" in text
    assert "point expectancy improvement >= +0.03R" in text
    assert "point PF improvement >= +0.10" in text
