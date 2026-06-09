# Phase 2 Demo Repair Monitor

Overall status: SHADOW_REPAIR_POLICY_WOULD_BLOCK_EVENTS_OBSERVED

Monitor/report only. No MT5 runtime is modified.

Generated at UTC: `2026-06-09T08:07:38.838266Z`
Policy ID: `phase2_demo_repair_policy_2026_06_09_v1`
Policy enforced: `false`
Policy effective at Dubai: `None`
Since: `2026-06-09 00:00:00`
Rows checked: `32`

## Counters

| Counter | Value |
|---|---:|
| weak_variant_order_attempts | `12` |
| blocked_by_repair_policy | `15` |
| orders_after_quarantine_by_candidate | `{'symbol_normalized_round_retest_v0': 10, 'session_extreme_retest_v0': 2}` |
| symbol_normalized_new_orders_after_suspend | `10` |
| session_extreme_new_orders_after_suspend | `2` |
| usdjpy_new_orders_after_disable | `0` |

## Findings

| Severity | Type | Candidate | Symbol | Ticket | Detail |
|---|---|---|---|---|---|
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
