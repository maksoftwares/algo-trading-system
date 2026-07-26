# Causal Candidate Quality ML V1 - Step 2 Result

Decision: `STEP_2_METADATA_AUDIT_COMPLETE_REPAIR_REQUIRED`

Step 2 completed the metadata-only source and candidate audit. It did not read economic outcomes, build labels or features, fit a model, change thresholds, simulate a portfolio, or alter the demo runtime.

- Canonical candidate rows: `3752`
- Unique candidate IDs: `3752`
- Candidates with a decision-time proxy: `3194`
- Candidates with all pre-label causal clocks: `0`
- Provisional conservative episodes: `853`
- Failed readiness checks: `['all_prelabel_causal_clocks_complete', 'all_canonical_sources_are_pre_policy_candidate_ledgers', 'all_action_geometry_complete', 'episode_weights_ready_to_lock', 'features_ready_to_build']`

## Decision

The source inventory and candidate counts reconcile, but the training dataset is not ready. The immediate successor must build metadata adapters for missing candidate clocks, complete action geometry, complete pre-policy candidate lineage, and source-availability rules. Counterfactual labels remain unauthorized until that repair is locked and re-audited.

ML remains offline and detached from MT5.
