# Research Candidate Smoke Report

Status: PASS
Generated at UTC: 2026-05-23T13:31:38+00:00
Expert: `liquidity_sweep_reversal_v0`
Hypothesis SHA256: `fc05b534f2157af427b652eaaa4b67e2461dba324b480a900e55697f56d7875d`

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
| synthetic_trade_plan | PASS | Plan direction=SHORT, entry_type=MARKET, risk_reward=1.5. |

## Latest Synthetic Signal

| Timestamp | Direction | Reason |
| --- | --- | --- |
| 2024-04-02T08:35:00+00:00 | SHORT | LIQUIDITY_SWEEP_REVERSAL_V0_SHORT |

## Latest Synthetic Plan

| Direction | Entry Type | Entry | Stop | Target | R |
| --- | --- | --- | --- | --- | --- |
| SHORT | MARKET |  | 102.12500 | 98.18750 | 1.50 |
