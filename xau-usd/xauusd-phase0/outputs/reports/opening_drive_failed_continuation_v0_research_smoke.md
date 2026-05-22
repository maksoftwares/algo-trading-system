# Research Candidate Smoke Report

Status: PASS
Generated at UTC: 2026-05-22T13:08:59+00:00
Expert: `opening_drive_failed_continuation_v0`
Hypothesis SHA256: `63673ecb407415a1397d465fff9c18e9d66b4490c38dd82e9a3624a196b76eaf`

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
| 2024-10-01T14:25:00+00:00 | SHORT | OPENING_DRIVE_FAILED_CONTINUATION_V0_SHORT |

## Latest Synthetic Plan

| Direction | Entry Type | Entry | Stop | Target | R |
| --- | --- | --- | --- | --- | --- |
| SHORT | MARKET |  | 101.74500 | 99.75750 | 1.50 |
