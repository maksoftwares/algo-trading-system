# A3 ML Dukascopy M5 Nonlinear Ranker V1 Result

Date: `2026-07-15`

Classification: `DUKASCOPY_M5_NONLINEAR_RANKER_NO_VALIDATION_SURVIVOR`

## Decision

Reject the shallow histogram gradient-boosting ranker. Stop tuning the current six candle-based candidate families and current causal feature set.

## Reproduction Lock

- Pre-outcome commit: `64b33090`.
- Validation AUC: `0.5087`.
- Model SHA-256: `9aa33014ab1c27172dea362524d248efc65aee23790035f5ec889c0dd2059d72`.
- Prediction SHA-256: `5ba336d4c7a62457083ecb4d5d1e9df78a90cfb33247a02ee195d0de563f8840`.

An immediate rerun reproduced both artifact hashes exactly.

## Validation Evidence

No retention fraction passed:

| Top fraction | Trades | Trades/source day | PF | Average R | Net USD |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 50% | 1,523 | 5.880 | 0.844 | -0.1146 | -801.27 |
| 40% | 1,260 | 4.865 | 0.809 | -0.1509 | -837.55 |
| 30% | 990 | 3.822 | 0.852 | -0.1376 | -513.64 |
| 20% | 685 | 2.645 | 0.794 | -0.1741 | -520.25 |

The model had worse discrimination than the rejected logistic rankers and did not create positive expectancy at any frozen frequency level. Internal test and every post-2021 reserved outcome remained closed.

## Architecture Decision

The current architecture has enough candidate frequency but insufficient predictive information:

- deterministic trend profiles: all negative;
- deterministic mean-reversion profiles: all negative;
- linear ranker: validation AUC about `0.516`, all selected streams negative;
- shallow nonlinear ranker: validation AUC `0.5087`, all selected streams negative.

Further threshold, model-depth, or retention tuning on these rows would be strategy-development contamination.

## Next Research Direction

Preserve the verified raw-tick label and replay foundation. Build new causal information before training again:

- pre-entry tick direction and quote-intensity imbalance;
- spread level, spread change, and liquidity-shock features;
- short-horizon realized volatility and acceleration;
- XAGUSD and major-FX cross-asset state;
- session and event-distance context;
- regime-specific specialists whose raw expectancy is at least near break-even before ML.

No Python prediction, EA consumption, demo, live, or broker action is authorized.
