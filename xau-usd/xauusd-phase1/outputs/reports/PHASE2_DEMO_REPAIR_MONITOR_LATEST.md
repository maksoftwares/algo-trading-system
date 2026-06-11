# Phase 2 Demo Repair Monitor

Overall status: SHADOW_REPAIR_POLICY_WOULD_BLOCK_EVENTS_OBSERVED

Monitor/report only. No MT5 runtime is modified.

Generated at UTC: `2026-06-11T04:06:50.382108Z`
Policy ID: `phase2_demo_repair_policy_2026_06_09_v1`
Policy enforced: `false`
Policy effective at Dubai: `None`
Since: `2026-06-09 00:00:00`
Rows checked: `176`

## Counters

| Counter | Value |
|---|---:|
| weak_variant_order_attempts | `79` |
| blocked_by_repair_policy | `83` |
| orders_after_quarantine_by_candidate | `{'symbol_normalized_round_retest_v0': 62, 'session_extreme_retest_v0': 17}` |
| symbol_normalized_new_orders_after_suspend | `62` |
| session_extreme_new_orders_after_suspend | `17` |
| usdjpy_new_orders_after_disable | `0` |

## Findings

| Severity | Type | Candidate | Symbol | Ticket | Detail |
|---|---|---|---|---|---|
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3910118 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3909950 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3908428 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3908013 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3907422 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3907222 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3907032 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | EURUSD | 3907034 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | EURUSD | 3906726 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3906723 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | session_extreme_retest_v0 | EURUSD | 3906638 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | session_extreme_retest_v0 | EURUSD | 3906501 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | EURUSD | 3906466 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3906384 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | EURUSD | 3906329 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | session_extreme_retest_v0 | EURUSD | 3905897 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | EURUSD | 3905898 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | session_extreme_retest_v0 | EURUSD | 3905712 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | EURUSD | 3905527 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3905384 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | EURUSD | 3904871 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | session_extreme_retest_v0 | EURUSD | 3904466 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | session_extreme_retest_v0 | EURUSD | 3903525 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | EURUSD | 3902871 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3902058 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3901716 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3901510 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | session_extreme_retest_v0 | GBPUSD | 3901316 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3901317 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3901083 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3900805 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | session_extreme_retest_v0 | EURUSD | 3900807 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3898834 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3897374 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3896907 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3896547 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | session_extreme_retest_v0 | EURUSD | 3896405 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3896406 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3895619 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | GBPUSD | 3895243 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | GBPUSD | 3895064 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | session_extreme_retest_v0 | GBPUSD | 3894701 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | GBPUSD | 3894451 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3894313 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | GBPUSD | 3894056 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3893121 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | session_extreme_retest_v0 | XAUUSD | 3893122 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3892904 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | session_extreme_retest_v0 | XAUUSD | 3892906 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3892671 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | GBPUSD | 3892382 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | session_extreme_retest_v0 | GBPUSD | 3891612 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | session_extreme_retest_v0 | EURUSD | 3891613 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | GBPUSD | 3891615 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3890849 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | GBPUSD | 3890850 |  |
| SHADOW | P2WEAKNESS_WRONG_MAGIC |  |  | 3890853 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3889726 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | GBPUSD | 3888804 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3887787 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3886758 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | GBPUSD | 3886761 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | GBPUSD | 3886704 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3886705 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3884809 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3883721 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3883316 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | session_extreme_retest_v0 | EURUSD | 3883188 |  |
| SHADOW | P2WEAKNESS_WRONG_MAGIC |  |  | 3881817 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3880437 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3880080 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3879909 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3879584 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3879390 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3878718 |  |
| SHADOW | P2WEAKNESS_WRONG_MAGIC |  |  | 3878351 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3877792 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3877538 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3877349 |  |
| SHADOW | P2WEAKNESS_WRONG_MAGIC |  |  | 3877302 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | session_extreme_retest_v0 | XAUUSD | 3877018 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | symbol_normalized_round_retest_v0 | XAUUSD | 3876902 |  |
| SHADOW | SUSPENDED_CANDIDATE_ORDER | session_extreme_retest_v0 | XAUUSD | 3876817 |  |
