# Research Candidate Smoke Report

Status: PASS
Generated at UTC: 2026-05-23T13:46:30+00:00
Expert: `daily_pivot_reclaim_v0`
Hypothesis SHA256: `a2376e560029ba88281e451114d935c1e50328873d457ea3d99640b739456624`

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
| synthetic_trade_plan | PASS | Plan direction=LONG, entry_type=MARKET, risk_reward=1.5. |

## Latest Synthetic Signal

| Timestamp | Direction | Reason |
| --- | --- | --- |
| 2024-04-02T08:35:00+00:00 | LONG | DAILY_PIVOT_RECLAIM_V0_LONG |

## Latest Synthetic Plan

| Direction | Entry Type | Entry | Stop | Target | R |
| --- | --- | --- | --- | --- | --- |
| LONG | MARKET |  | 99.22500 | 101.91250 | 1.50 |
