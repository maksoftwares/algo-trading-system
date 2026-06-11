# Experiment Guard Re-arm And De-dilution Plan - 2026-06-09

Status: `RUNTIME_ACTION_PENDING_OWNER_CONFIRMATION`

## Boundary

This is a runtime-configuration plan only. It is not a source-code change, strategy change, canonical Phase 2 approval, live-trading approval, or real-capital approval.

No EA should be deleted. No position should be closed or modified. Canonical Phase 2 remains blocked and the breakout-retest family remains `COST_SUSPENDED_CANONICAL`.

This document records the next runtime correction requested by the reviewer note `CODEX_NOTE_REARM_EXPERIMENT_GUARDS_AND_DEDILUTE_2026_06_09.md`. It has not been applied by this repo update.

## Why This Is Needed

The 2026-06-09 execution unblock kept demo orders flowing, but it also disabled cost, spread, exposure, and throttle guards on measurement charts. With those guards off, the net-R-after-measured-cost KPI is diluted by junk-cost bars and duplicate same-family stacking.

The goal is not to reduce valid order flow. The goal is to stop measuring duplicate/re-stacked exposure as if it were independent signal quality.

## Guard Values To Re-arm

| Chart group | Input | Current risk state | Target value |
|---|---|---|---|
| WR50 WST12 / WST15 | `InpMaxCostR` | Disabled if `0` | `0.15` |
| WR50 WST12 / WST15 | `InpMaxSpreadPoints` | Disabled if `0` | `75` |
| WR50 WST12 / WST15 | `InpMaxOpenPositionsForThisEA` | Disabled if `0` | `1` |
| WR50 WST12 / WST15 | `InpMaxOpenWR50PositionsTotal` | Disabled if `0` | `5` |
| WR50 WST12 / WST15 | `InpAllowSharedSymbolExposure` | Keep enabled | `true` |
| WR50 WST12 / WST15 | `InpMaxTradesPerDay` | Keep relaxed | `0` |
| breakout_retest control | `InpMaxEstimatedCostR` | Disabled if `0` | `0.30` |
| breakout_retest control | `InpMaxMeasuredSpreadPoints` | Disabled if `0` | `75` |
| breakout_retest control | `InpMaxOpenPositionsPerInstance` | Disabled if `0` | `1` |
| breakout_retest control | `InpMinSecondsBetweenOrders` | Disabled if `0` | `60` |
| breakout_retest control | `InpMaxOrdersPerDay` | Keep relaxed | `0` |

## De-dilution Decision Required

The reviewer recommends path A, but path A conflicts with the owner's earlier instruction to keep EAs placing demo orders. Owner confirmation is required before runtime action.

| Path | Runtime action | Benefit | Tradeoff |
|---|---|---|---|
| A - Recommended | Set `symbol_normalized_round_retest_v0`, `round_number_retest_v0`, and `session_extreme_retest_v0` to broker-action false / observer-only | Removes known diluters from actual demo PnL and makes the breakout-retest comparison cleaner | Stops those EAs from placing broker orders |
| B - Keep all EAs trading | Leave diluters live, but require the week-1 report to show a breakout_retest-only virtual stream beside the full diluted portfolio | Preserves owner preference for maximum demo order flow | Actual account PnL remains diluted and KPI interpretation must use virtual de-diluted reporting |

Until the owner explicitly chooses A, use B for reporting interpretation and do not disable broker action on the diluters.

## Required Runtime Procedure Before Any Applied Change

1. Back up the MT5 demo profile.
2. Record the backup path.
3. Apply only the listed input edits.
4. Do not recompile unless MT5 requires it.
5. Do not modify EA source.
6. Do not delete charts.
7. Do not close or modify open positions.
8. Confirm server contains `Demo` or `Practice`.
9. Generate reconciliation after the change.

## Acceptance Evidence

The reconciliation report must prove:

- Profile backup exists.
- Only listed input values changed.
- No source files changed.
- No open positions were closed or modified.
- Demo server confirmed.
- Canonical Phase 2 status unchanged.
- Order flow remains active after re-arming cost/spread/exposure guards.

## Current Repo-Side Decision

Dynamic exit partial/breakeven rules are rejected for deployment. Guard re-arm is prepared but not applied. De-dilution path remains pending owner runtime confirmation.
