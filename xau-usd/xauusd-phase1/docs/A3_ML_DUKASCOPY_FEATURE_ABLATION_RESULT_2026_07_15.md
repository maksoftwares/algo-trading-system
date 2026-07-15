# A3 ML Dukascopy Feature Ablation V1 Result

## Verdict

Classification: `DUKASCOPY_FEATURES_NO_RESEARCH_SURVIVOR`

The eight frozen Dukascopy features produced a small, directionally consistent improvement, but the improvement was below the preregistered minimum and was not statistically stable across calendar months. The feature set is closed without promotion.

## Population

- Pre-availability population: 357 training / 297 validation trades.
- Causally feature-complete population: 346 training / 290 validation trades.
- Excluded before fitting: 18 trades with incomplete prior-60-minute Dukascopy history.
- Baseline and enhanced rows, labels, directions, and strategy families matched exactly.
- Validation period: 2022-01-01 through 2024-06-30.

## Results

| Metric | Baseline | Dukascopy enhanced | Change |
| --- | ---: | ---: | ---: |
| ROC AUC | 0.615027 | 0.626103 | +0.011076 |
| Brier score | 0.240718 | 0.239352 | -0.001366 |
| Log loss | 0.675629 | 0.673110 | -0.002519 |
| Threshold-selected win rate | 52.94% | 56.16% | +3.22 pp |
| Threshold coverage | 23.45% | 25.17% | +1.72 pp |

The fixed-seed 2,000-sample calendar-month block-bootstrap 95% interval for AUC improvement was `-0.008864` to `+0.036337`. Because the interval crosses zero, the measured lift is not reliable enough to authorize use.

Direction diagnostics:

| Direction | Baseline AUC | Enhanced AUC |
| --- | ---: | ---: |
| LONG / R1 | 0.627859 | 0.671518 |
| SHORT / R2 | 0.590032 | 0.599522 |

The long subgroup is encouraging but contains only 63 validation trades. It is not a standalone promotion result.

## Gate Audit

- PASS: exact same baseline and enhanced population.
- FAIL: 346 training rows remained versus the required 350.
- PASS: 290 validation rows met the required 290.
- PASS: enhanced AUC exceeded 0.55.
- FAIL: AUC improvement was 0.011076 versus the required 0.02.
- FAIL: bootstrap lower bound was -0.008864 rather than above zero.
- PASS: Brier score did not regress.
- PASS: log loss did not regress.
- PASS: neither direction regressed materially.
- PASS: no missing feature values or future ticks were used among retained rows.
- PASS: all execution authorization fields remained false.

## Data Integrity

- Source: official Dukascopy `XAU-USD` bid/ask tick responses.
- Raw source hours used: 1,226.
- Included tick count per 60-minute window: minimum 853, median 7,119, maximum 31,523.
- Source-hour composite SHA-256: `8f16de12522d9bff150a30699fda9dc079d83b0c8db70ceba41930d8cc3be185`.
- Feature-row SHA-256: `2597574f1fce54a44d1ca71b4ad6c517f04f5193263765b27089e81bd82a3645`.
- A full rerun reproduced the classification, metrics, bootstrap bounds, feature hash, source hash, and gate audit.

## Decision

Do not publish this feature set to Python demo prediction, an EA consumer, or broker execution. Preserve it as evidence that Dukascopy liquidity and microstructure data may add a small amount of information, especially for R1 longs, but the current sample does not prove a stable incremental edge.
