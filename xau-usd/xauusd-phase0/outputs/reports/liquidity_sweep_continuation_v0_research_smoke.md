# Research Candidate Smoke Report

Status: PASS
Generated at UTC: 2026-05-23T15:52:11+00:00
Expert: `liquidity_sweep_continuation_v0`
Hypothesis SHA256: `b279d49b88a4ef24e993906cf3b24aeec1df7b4a4816df73ab3e4ac9cb09858f`

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
| 2024-04-02T08:35:00+00:00 | LONG | LIQUIDITY_SWEEP_CONTINUATION_V0_LONG |

## Latest Synthetic Plan

| Direction | Entry Type | Entry | Stop | Target | R |
| --- | --- | --- | --- | --- | --- |
| LONG | MARKET |  | 100.72500 | 102.53750 | 1.50 |
