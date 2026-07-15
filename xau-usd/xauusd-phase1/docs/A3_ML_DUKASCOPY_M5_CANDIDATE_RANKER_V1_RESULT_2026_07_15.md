# A3 ML Dukascopy M5 Candidate Ranker V1 Result

Date: `2026-07-15`

Classification: `DUKASCOPY_M5_CANDIDATE_RANKER_NO_VALIDATION_SURVIVOR`

## Decision

Reject both L2 logistic rankers and all four retention fractions. Do not open the frozen 2021 internal test for this model family.

## Reproduction Lock

- Pre-outcome commit: `1a1cfe09`.
- Train rows: `5,357`.
- Validation rows: `4,267`.
- Suppressed internal-test rows: `2,268`.
- Train positive-label share: `36.74%`.
- Model artifact SHA-256: `eadf3dcca8401527f396b9bbbf3a192f065bd572e6412a4d29e55264af3278a3`.
- Prediction artifact SHA-256: `5ba336d4c7a62457083ecb4d5d1e9df78a90cfb33247a02ee195d0de563f8840`.

An immediate rerun reproduced both artifact hashes exactly.

## Validation Evidence

Both models had near-random validation discrimination:

- L2 `0.01`: AUC `0.5161`;
- L2 `0.10`: AUC `0.5156`.

All eight model/fraction streams retained high frequency but remained unprofitable. The best selected PF was `0.843` at the L2 `0.01`, top-30% configuration:

- trades: `919`;
- trades per source day: `3.548`;
- average stress return: `-0.0882R`;
- stress net: `-$583.61` at fixed `0.01` lot.

No validation configuration passed. The internal 2021 test and every post-2021 reserved outcome remained closed.

## Next Research Direction

One bounded nonlinear interaction test is justified because a linear ranker cannot represent conditional feature combinations. Use a single shallow histogram gradient-boosting model with frozen complexity and the same features, inputs, portfolio controls, splits, retention fractions, and gates. Do not conduct a broad hyperparameter search.

No Python prediction, EA consumption, demo, live, or broker action is authorized.
