# Research Candidate Smoke Report

Status: PASS
Generated at UTC: 2026-05-23T15:17:34+00:00
Expert: `symbol_round_sweep_reversal_v0`
Hypothesis SHA256: `420149e4e02059fcd677b0d249d979f3d3f91dc06fa47fa87f6449ec552b5019`

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
| 2024-12-03T11:35:00+00:00 | LONG | SYMBOL_ROUND_SWEEP_REVERSAL_V0_LONG |

## Latest Synthetic Plan

| Direction | Entry Type | Entry | Stop | Target | R |
| --- | --- | --- | --- | --- | --- |
| LONG | MARKET |  | 99.45000 | 101.45000 | 1.50 |
