# A3 ML Dukascopy M15 Range Expansion V1 Result

Date: `2026-07-16`

Classification: `DUKASCOPY_M15_RANGE_EXPANSION_TRAIN_REJECTED`

## Decision

Reject the raw M15 range-expansion specialist. It improved materially over the inverse range-fade hypothesis but remained too negative to open validation under the frozen gate.

## Reproduction Lock

- Pre-outcome commit: `c786f3fa`.
- Base causal feature SHA-256: `74ca74f2f6f5b3eaa8bca687fc2cced8dc20140a54506f3a25cb22920b53031b`.
- Train trades: `504`.
- Baseline PF: `0.700`.
- Stressed PF: `0.576`.
- Average stressed result: `-0.2762R`.
- Stressed net: `-139.23R`.
- Maximum closed stressed drawdown: `142.49R`.

The continuation direction was better than the rejected fade direction (`0.700` versus `0.537` baseline PF), but the gap to break-even remains too large for deterministic promotion.

## Next Bounded Diagnostic

The new microstructure and cross-market features have not yet been allowed to fit this transition family because the raw gate stopped the campaign. Run one development-only chronological diagnostic:

- fit on 2018-07 through 2019-06 expansion candidates;
- evaluate on 2019-07 through 2020-06 expansion candidates;
- use the already-frozen model and feature set;
- test only frozen train-score retention fractions;
- require meaningful AUC/rank correlation and positive stressed economics;
- do not open any outcome after 2020-06.

This diagnostic can reject the feature/family combination. It cannot promote a strategy or authorize trading.

No Python prediction, EA consumption, demo, live, or broker action is authorized.
