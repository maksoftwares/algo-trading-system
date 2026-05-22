# Research Candidate Smoke Report

Status: PASS
Generated at UTC: 2026-05-22T05:27:36+00:00
Expert: `squeeze_breakout_long_v0`
Hypothesis SHA256: `8afa7c87ae1ee1915a8fd5845e5babb673937084f5a38de98076cac45c252553`

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
| 2024-01-02T10:15:00+00:00 | LONG | SQUEEZE_BREAKOUT_LONG_V0 |

## Latest Synthetic Plan

| Direction | Entry Type | Entry | Stop | Target | R |
| --- | --- | --- | --- | --- | --- |
| LONG | MARKET |  | 99.90000 | 101.52500 | 1.50 |
