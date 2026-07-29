# V60 Portable Mature Top-Up Prospective V3

Decision: **PASS_PROSPECTIVE_DEMO_INTEGRATION_NOMINATED**

No July outcome labels were used.

## Metrics

- `common_completed_bars`: `4896`
- `context_rows`: `19584`
- `score_spearman`: `0.9825260333908673`
- `rank_spearman`: `0.9825076969868741`
- `mean_absolute_rank_difference`: `0.03097717122350134`
- `top_quintile_jaccard`: `0.8892105263157895`
- `capital_precision`: `0.9547894885560892`
- `capital_recall`: `0.9282967032967033`
- `dukascopy_topups`: `7280`
- `capital_topups`: `7078`
- `agreed_topups`: `6758`

## Gates

- PASS: `stored_scores_reproduce`
- PASS: `stored_ranks_reproduce`
- PASS: `enough_common_bars`
- PASS: `enough_context_rows`
- PASS: `score_spearman`
- PASS: `rank_spearman`
- PASS: `mean_rank_difference`
- PASS: `top_quintile_jaccard`
- PASS: `capital_precision`
- PASS: `capital_recall`
- PASS: `all_scored_values_finite`

This result grants no live authority. Demo integration remains
fail-closed to the deterministic baseline unless separately deployed.
