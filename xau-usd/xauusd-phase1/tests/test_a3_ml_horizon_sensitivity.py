from __future__ import annotations

from phase2x_test_helpers import ROOT


def _data_text() -> str:
    return (ROOT / "docs" / "A3_ML_DATA_CONTRACT_V1.md").read_text(encoding="utf-8")


def _execution_text() -> str:
    return (ROOT / "docs" / "A3_ML_EXECUTION_LABEL_CONTRACT_V1.md").read_text(encoding="utf-8")


def test_horizon_sensitivity_is_mechanics_only() -> None:
    text = _data_text()
    assert "During inventory only" in text
    assert "96 active M5 bars" in text
    assert "144 active M5 bars" in text
    assert "288 active M5 bars primary" in text
    assert "Allowed mechanics" in text
    for token in ("resolved label count", "unresolved label count", "purge loss by fold", "implied feature budget"):
        assert token in text


def test_horizon_sensitivity_contains_no_outcome_metrics_as_allowed_metrics() -> None:
    text = _data_text()
    allowed = text.split("Allowed mechanics:", 1)[1].split("Prohibited outcome metrics:", 1)[0]
    for forbidden in ("PF", "expectancy", "win rate", "model score", "threshold"):
        assert forbidden not in allowed


def test_horizon_change_cannot_reference_feature_budget_as_rationale() -> None:
    text = _execution_text()
    assert "not a model-capacity parameter" in text
    assert "does not cite implied feature budget, feature count, or model capacity" in text
    assert "A larger implied feature budget is never" in text


def test_horizon_change_requires_new_contract_version() -> None:
    text = _execution_text()
    assert "new versioned label contract" in text
    assert "new review" in text
    assert "new SHA256 lock" in text
