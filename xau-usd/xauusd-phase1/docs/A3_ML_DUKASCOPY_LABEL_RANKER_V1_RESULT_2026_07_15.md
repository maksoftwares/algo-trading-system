# A3 ML Dukascopy Label Ranker V1 Result

Date: `2026-07-15`

Classification: `DUKASCOPY_LABEL_RANKER_NO_SURVIVOR`

## Decision

Reject the V1 ranker. It did not identify a positive or statistically credible subset inside the failed symmetric H1 pullback family.

Do not invert the probabilities, change the validation coverage, add calendar masks, or tune features against this result. Any materially different experiment requires a new preregistration and should prioritize a different candidate family.

## Frozen Population

- Train: `1,488` resolved labels.
- Validation: `1,206` resolved labels.
- Test: `567` resolved labels.
- Upstream label SHA-256: `500b0e5d5fd5f5b1b2f245754dcf409a361e9b3512192b6551a64b8961613485`.
- All input rows came from the verified Dukascopy label factory.

## Model Quality

- Validation AUC: `0.457698`.
- Test AUC: `0.503956`.
- Validation Brier score did not beat the constant train-prior predictor.
- Test Brier score did not beat the constant train-prior predictor.

The validation result is below random ranking and the test result is effectively random. This is not evidence of a useful signal-quality model.

## Frozen Selection Result

The fixed validation top-quartile rule selected `302` validation rows and froze the probability cutoff at `0.36999987`. Applying that unchanged cutoff selected `205` test rows.

| Split | Selected | Coverage | Stress PF | Average stress R | Stress net USD | Max closed DD R | Positive months |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Validation | 302 | 25.04% | 0.6834 | -0.2213 | -625.36 | 78.31 | 6/24 |
| Test | 205 | 36.16% | 0.9749 | -0.0528 | -31.50 | 26.01 | 5/12 |

Selected test directions:

- Long: `144`.
- Short: `61`.

The fixed-seed test month-block bootstrap 95% interval for average stress R was `-0.3707` through `0.3018`. It crosses zero widely.

## Gates

Only row-count, direction-count, and coverage mechanics passed. Every predictive-quality, profitability, drawdown, stability, bootstrap, and calibration gate failed.

No strategy, ranker, prediction, EA, broker, or deployment authorization is granted.

## Next Research Direction

The correct response is to test a genuinely different mechanical candidate family on the same verified label infrastructure. The next family should have a different market premise, such as compression breakout or exhaustion mean reversion, rather than a threshold variation of this H1 EMA pullback rule.
