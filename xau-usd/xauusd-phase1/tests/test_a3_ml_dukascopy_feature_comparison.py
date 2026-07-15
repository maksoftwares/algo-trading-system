from __future__ import annotations

from ml.a3_meta_v1.dukascopy_feature_comparison import (
    _block_bootstrap_auc_delta,
    _paired_population,
    _score_logistic,
)


def test_population_pairing_detects_label_change() -> None:
    baseline = [
        {
            "split": "validation",
            "strategy_family": "r1",
            "direction": "LONG",
            "entry_time": "2024-01-01T00:00:00Z",
            "source_summary": "source",
            "profit_aed": "1.0",
            "y_win": "1",
        }
    ]
    enhanced = [dict(baseline[0])]
    assert _paired_population(baseline, enhanced) == (True, "exact")
    enhanced[0]["y_win"] = "0"
    assert _paired_population(baseline, enhanced)[0] is False


def test_logistic_scorer_uses_numeric_and_category_features() -> None:
    model = {
        "model_family": "LOGISTIC_REGRESSION_V1",
        "numeric_features": ["feature"],
        "model_parameters": {
            "intercept": 0.0,
            "coefficients": [1.0, 1.0],
            "feature_names": ["feature", "direction=LONG"],
            "numeric_means": [0.0],
            "numeric_scales": [1.0],
        },
    }
    probabilities = _score_logistic(model, [{"feature": "1.0", "direction": "LONG"}])
    assert 0.88 < probabilities[0] < 0.89


def test_month_block_bootstrap_reports_positive_auc_delta() -> None:
    rows = []
    labels = []
    baseline = []
    enhanced = []
    for month in range(1, 13):
        for label in (0, 1):
            rows.append({"entry_time": f"2023-{month:02d}-01T00:00:00Z"})
            labels.append(label)
            baseline.append(0.5)
            enhanced.append(0.8 if label else 0.2)
    result = _block_bootstrap_auc_delta(rows, labels, baseline, enhanced, samples=200, seed=7)
    assert result["auc_delta_p025"] > 0.0
