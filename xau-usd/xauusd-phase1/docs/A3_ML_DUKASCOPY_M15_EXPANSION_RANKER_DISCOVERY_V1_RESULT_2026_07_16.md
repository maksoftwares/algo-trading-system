# A3 ML Dukascopy M15 Expansion Ranker Discovery V1 Result

Date: `2026-07-16`

Classification: `DUKASCOPY_M15_EXPANSION_RANKER_NO_DEVELOPMENT_SURVIVOR`

## Decision

Reject the current microstructure/cross-market feature set for the frozen M15 range-expansion family. Stop tuning this combination.

## Reproduction Lock

- Preregistration commit: `c7528d2b`.
- Reporting-only field fix: `5878a7a4`.
- Fit candidates: `203`.
- Chronological development-evaluation candidates: `301`.
- Outcomes on or after `2020-07-01` opened: `false`.
- Model SHA-256: `52233556423174ba9c64c0e0e603ac1d0d9acec4e88ccd34fd26631c51abd787`.
- Evaluation SHA-256: `8c9f58e030685088cc658c71b0096c10bbd9b08b614e302b12572ef4d6b3808a`.
- Empty prediction SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- Immediate rerun reproduced all three hashes exactly.
- Targeted test suite: `59 passed`.

## Predictive Evidence

- Development-evaluation AUC: `0.4243`.
- Spearman rank correlation: `-0.1205`.

The model ranked outcomes in the wrong direction out of time. This is stronger negative evidence than a merely random AUC near 0.50.

## Selected-Trade Evidence

| Retention | Trades | Trades/source day | Stress PF | Average stress R | Stress net R |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 60% | 164 | 0.524 | 0.463 | -0.3705 | -60.76 |
| 45% | 129 | 0.412 | 0.391 | -0.4299 | -55.45 |
| 30% | 81 | 0.259 | 0.402 | -0.4362 | -35.33 |
| 20% | 45 | 0.144 | 0.201 | -0.6414 | -28.86 |

Higher model scores selected worse trades. Every economic, stability, concentration, and predictive promotion path failed.

## Phase Conclusion

The phase achieved a verified six-year causal research foundation:

- 504 hash-inventoried Dukascopy inputs;
- 424,942 synchronized M5 feature rows;
- causal tick pressure, quote intensity, spread, top-of-book volume, microprice, realized volatility, XAGUSD, EURUSD, and USDJPY features;
- M15 complete-bar aggregation and exact bid/ask execution;
- train-first and conditional holdout firewalls;
- deterministic reproducibility.

It did not find a profitable new high-frequency specialist. Trend, shock, range rotation, range expansion, and the ML ranker all failed before any later holdout was consumed.

## Next Research Direction

Do not add another candle threshold, model depth, or retention fraction to this dataset. Preserve the existing profitable low-frequency R1/R2 specialists as the current strategy base.

The next alpha campaign must add materially different information, such as causal US real-yield/rate changes, dollar-index state, gold futures volume/order-flow, and actual macro surprise values. These inputs are not present in the current Dukascopy spot quote set and directly address gold repricing mechanisms that the present features cannot observe.

No Python prediction, EA consumption, demo, live, or broker action is authorized by this result.
