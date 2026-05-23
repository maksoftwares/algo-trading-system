# Research Candidate Smoke Report

Status: PASS
Generated at UTC: 2026-05-23T16:07:44+00:00
Expert: `session_extreme_retest_v0`
Hypothesis SHA256: `3c2dc7bfb26462c0b04b86bd035d5e573937195d82ed27b39c7c6213191c84e1`

## Boundary

This is a synthetic smoke check only. It does not authorize matrix, decile, multisymbol, or adversarial result runs.

Phase 0 result run allowed: `false`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| hypothesis_hash_locked | PASS | Research hypothesis is complete and hash-locked. |
| research_strategy_registered | PASS | Strategy is available only in the research registry. |
| active_registry_disabled | PASS | Strategy is not included in the active Phase 0 `all` registry. |
| synthetic_signal | PASS | Generated 1 synthetic signal(s). |
| synthetic_trade_plan | PASS | Plan direction=LONG, entry_type=STOP, risk_reward=1.5. |

## Latest Synthetic Signal

| Timestamp | Direction | Reason |
| --- | --- | --- |
| 2024-04-01T07:30:00+00:00 | LONG | BREAKOUT_RETEST_LONG |

## Latest Synthetic Plan

| Direction | Entry Type | Entry | Stop | Target | R |
| --- | --- | --- | --- | --- | --- |
| LONG | STOP | 100.41000000000001 | 99.85000 | 101.25000 | 1.50 |
