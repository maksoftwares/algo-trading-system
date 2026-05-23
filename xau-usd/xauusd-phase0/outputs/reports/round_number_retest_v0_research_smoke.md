# Research Candidate Smoke Report

Status: PASS
Generated at UTC: 2026-05-23T14:47:56+00:00
Expert: `round_number_retest_v0`
Hypothesis SHA256: `03b34ddfeb155a915d980ba6c960a567a918fe14280c1c10a21eb9b2d6dd13ab`

## Boundary

This is a synthetic smoke check only. It does not authorize matrix, decile, multisymbol, or adversarial result runs.

Phase 0 result run allowed: `false`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| hypothesis_hash_locked | PASS | Research hypothesis is complete and hash-locked. |
| research_strategy_registered | PASS | Strategy is available only in the research registry. |
| active_registry_disabled | PASS | Strategy is not included in the active Phase 0 `all` registry. |
| synthetic_signal | PASS | Generated 2 synthetic signal(s). |
| synthetic_trade_plan | PASS | Plan direction=LONG, entry_type=STOP, risk_reward=1.5. |

## Latest Synthetic Signal

| Timestamp | Direction | Reason |
| --- | --- | --- |
| 2016-01-05T11:55:00+00:00 | LONG | BREAKOUT_RETEST_LONG |

## Latest Synthetic Plan

| Direction | Entry Type | Entry | Stop | Target | R |
| --- | --- | --- | --- | --- | --- |
| LONG | STOP | 100.51 | 99.90000 | 101.42500 | 1.50 |
