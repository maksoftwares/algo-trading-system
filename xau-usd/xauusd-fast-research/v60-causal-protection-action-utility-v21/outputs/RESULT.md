# V60 Causal Protection-Action Utility V21 Result

Decision: **NO_STABLE_PROTECTION_UTILITY_KEEP_V6**

Read-only exposed diagnostic. No broker or deployment action is authorized.

## Parity

- Reference Dynamic V6 trades: `1377`
- Observed giveback rows: `160`
- Distinct protection actions: `121`
- Exact event path: `PASS`
- Exact close path: `PASS`
- Exact V6 metrics: `PASS`

## Out-of-time diagnostic

- Nominated rows: `45`
- Nominated actions: `37`
- Positive utility folds: `2/4`
- Combined action utility R: `-8.699290`
- Cluster-bootstrap 10th percentile: `-0.533013934560386`

## Gates

- `exact_dynamic_v6_behavioral_parity`: PASS
- `causal_feature_contract`: PASS
- `all_four_fixed_evaluation_years`: PASS
- `minimum_nominated_rows`: PASS
- `minimum_nominated_actions`: PASS
- `minimum_actions_every_fold`: PASS
- `positive_utility_in_three_of_four_folds`: FAIL
- `nonnegative_2025_utility`: PASS
- `nonnegative_2026_utility`: FAIL
- `combined_utility_positive`: FAIL
- `single_action_concentration_below_limit`: PASS
- `cluster_bootstrap_tenth_percentile_positive`: FAIL

A pass only nominates a separately preregistered path-dependent replay. It does not prove portfolio P/L improvement and cannot authorize deployment.
