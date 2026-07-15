# A3 ML Dukascopy Feature Comparison

Classification: `DUKASCOPY_FEATURES_NO_RESEARCH_SURVIVOR`

Population: 346 training / 290 validation trades.

| Metric | Baseline | Dukascopy enhanced |
| --- | ---: | ---: |
| ROC AUC | 0.615027 | 0.626103 |
| Brier score | 0.240718 | 0.239352 |
| Log loss | 0.675629 | 0.673110 |

AUC improvement: `0.011076`.
Month-block 95% interval: `-0.008864` to `0.036337`.

## Gates

- `PASS` exact_same_population: baseline and enhanced rows and labels must match
- `FAIL` minimum_training_rows: 346 >= 350
- `PASS` minimum_validation_rows: 290 >= 290
- `PASS` minimum_enhanced_auc: 0.626103 >= 0.55
- `FAIL` minimum_auc_improvement: 0.011076 >= 0.02
- `FAIL` auc_delta_ci_lower_above_zero: -0.008864 > 0
- `PASS` brier_no_regression: 0.239352 <= 0.240718
- `PASS` log_loss_no_regression: 0.67311 <= 0.675629
- `PASS` long_auc_no_material_regression: 0.671518 >= 0.617859
- `PASS` short_auc_no_material_regression: 0.599522 >= 0.580032
- `PASS` causal_complete_dukascopy_features: missing=0 future=0
- `PASS` execution_boundary_closed: all authorization fields remain false

## Boundary

Research only. Python demo predictions, EA consumption, and broker action remain unauthorized.
