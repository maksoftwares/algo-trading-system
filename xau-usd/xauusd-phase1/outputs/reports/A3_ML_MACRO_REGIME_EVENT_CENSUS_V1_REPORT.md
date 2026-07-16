# A3 ML Macro Regime Event Census V1 Report

Classification: `MACRO_REGIME_EVENT_CENSUS_NO_TRAIN_SURVIVOR`

## Quality

- H1 rows: `59003`
- Macro coverage: `100.0000%`
- Events: `2824`
- Resolved or ineligible share: `99.7521%`
- dukascopy_hash_and_rows_match: `PASS`
- broker_cost_report_hash_and_values_match: `PASS`
- macro_hashes_and_rows_match: `PASS`
- macro_availability_lag_enforced: `PASS`
- macro_coverage_share_ge_minimum: `PASS`
- resolved_or_ineligible_event_share_ge_minimum: `PASS`
- event_ids_unique: `PASS`
- events_chronological: `PASS`

## Hypotheses

- `macro_aligned_h1_trend_pullback_v1:LONG`: train pass `false`, events `269`, PF `0.6753096978512058`, average R `-0.2372`
- `macro_aligned_h1_trend_pullback_v1:SHORT`: train pass `false`, events `218`, PF `0.44617852730266294`, average R `-0.4752`
- `macro_aligned_h1_range_break_v1:LONG`: train pass `false`, events `135`, PF `0.8698609043939466`, average R `-0.0763`
- `macro_aligned_h1_range_break_v1:SHORT`: train pass `false`, events `111`, PF `0.47691023590896575`, average R `-0.3571`
- `macro_shock_h1_continuation_v1:LONG`: train pass `false`, events `82`, PF `1.0535182098374656`, average R `0.0275`
- `macro_shock_h1_continuation_v1:SHORT`: train pass `false`, events `103`, PF `0.8780349780801778`, average R `-0.0705`
- `macro_divergence_h1_reclaim_v1:LONG`: train pass `false`, events `27`, PF `0.5682833410839755`, average R `-0.3090`
- `macro_divergence_h1_reclaim_v1:SHORT`: train pass `false`, events `38`, PF `1.1793126724892253`, average R `0.0794`

## Decision Boundary

- Exam hypothesis candidates: `[]`
- Model training authorization: `false`
- Demo or live authorization: `false`
