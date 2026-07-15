# A3 ML Dukascopy Microstructure Regime V1 Result

Date: `2026-07-16`

Classification: `DUKASCOPY_MICROSTRUCTURE_REGIME_NO_TRAIN_FAMILY_SURVIVOR`

## Decision

Reject the frozen M5 specialist definitions before ML. None passed the train-only raw-quality gate, so validation filtering, internal test, and the two-year exam remained closed.

## Reproduction Lock

- Pre-outcome commit: `d791e7cb`.
- Consumed Parquet files: `504`.
- Consumed bytes: `2,976,149,641`.
- Source manifest SHA-256: `d7cedcf3eebc4fba32120636f63e8ced0b61ef72626c0e535edb5bac9d8a51db`.
- Causal feature cache rows: `424,942`.
- Causal feature cache SHA-256: `74ca74f2f6f5b3eaa8bca687fc2cced8dc20140a54506f3a25cb22920b53031b`.

## Train Evidence

| Specialist | Trades | Baseline PF | Baseline average R | Stress PF | Stress average R |
| --- | ---: | ---: | ---: | ---: | ---: |
| Range fade | 31 | 0.963 | -0.0212 | 0.811 | -0.1212 |
| Shock continuation | 3,675 | 0.631 | -0.2477 | 0.531 | -0.3477 |
| Shock reversal | 3,675 | 0.695 | -0.1965 | 0.583 | -0.2965 |
| Trend breakout | 336 | 0.623 | -0.2562 | 0.524 | -0.3562 |
| Trend pullback | 1,401 | 0.647 | -0.2313 | 0.542 | -0.3313 |

The model was intentionally not trained. Training a ranker on these admitted families would violate the preregistered requirement that ML not be used to rescue a deeply negative raw stream.

## Learned Constraint

The main M5 failure was economic, not computational. In the train period, the median next-bar Dukascopy spread for otherwise eligible range excursions was about `0.61` of the frozen one-ATR risk unit. The `0.25R` spread gate therefore left only 31 completed range trades.

An outcome-blind opportunity census found that M15 aggregation improves the cost/frequency geometry: approximately `1.16` raw range excursions per source day, with approximately `0.78/day` surviving a `0.33R` spread gate. This census used no trade outcomes.

## Next Locked Hypothesis

Test one M15 range-rotation specialist with:

- a causal M15 range regime;
- a new 1.25-standard-deviation excursion crossing;
- executable next-bar bid/ask entry;
- a target at the causal range midpoint;
- a range-specific structural stop and fixed time expiry;
- microstructure ranking only if the raw train stream is near break-even;
- the same conditional validation, internal-test, and exam firewall.

No Python prediction, EA consumption, demo, live, or broker action is authorized.
