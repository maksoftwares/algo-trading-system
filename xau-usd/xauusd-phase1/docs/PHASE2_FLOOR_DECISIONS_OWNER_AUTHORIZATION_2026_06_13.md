# Phase 2 Floor Decisions Owner Authorization - 2026-06-13

Status: `OWNER_DECISIONS_RECORDED_APPROVED_SELECTED_ITEMS`

This packet prepares Block A from `CODEX_INSTRUCTIONS_FLOOR_AND_ANALYSIS_2026_06_12.md`. It does not execute any runtime change. It does not authorize canonical Phase 2, live trading, real capital, or any change to the `breakout_retest` entry/stop/TP logic.

Block A may be executed only as one recorded maintenance window after the owner approves or declines each item below. Declines must be recorded; they are not skipped silently.

## Global Boundaries

- Demo account only.
- No live trading and no real capital.
- Canonical Phase 2 status remains unchanged.
- `breakout_retest` entry, stop, and take-profit logic remains untouched.
- Profile backup required before any terminal change.
- Consolidated applied report required after any approved maintenance window: `PHASE2_FLOOR_DECISIONS_APPLIED_2026_06_13.md`.
- This packet alone does not change MT5 terminals, charts, presets, orders, positions, profiles, or running EAs.

## Owner Decision Summary

| Item | Runtime action | Owner decision |
| --- | --- | --- |
| A1 | Quarantine round family and `session_extreme_retest_v0` to observer-only | DECLINE |
| A2 | Turn repair executors broker-action OFF | DECLINE |
| A3 | Add family duplicate mutex to `Phase2ExperimentalDemoExecutor.mq5` | APPROVE |
| A4 | Re-arm quantitative guards | DECLINE |
| A5 | Revert EURUSD/GBPUSD lot to 0.01 and source defaults to 0.01 | DECLINE |
| A6 | Turn USDJPY broker action OFF | APPROVE |
| A7 | Attach `AccountEquityGuardianShadow` Stage A observer | APPROVE |

## A1 - Quarantine Weak Families To Observer-Only

Runtime action: set all `symbol_normalized_round_retest_v0`, `round_number_retest_v0`, and `session_extreme_retest_v0` charts on all symbols to `InpBrokerActionAllowed=false` and `InpDryRunOnly=true`, while keeping signal/would-trade logging enabled.

Evidence basis: cumulative unique-view losses across review windows, the June 11 XAUUSD shorting-defect finding, and broker-joined observer scoreboards showing weak-family loss clusters.

Rollback step: restore the pre-window profile backup or re-enable broker action only from a new owner-signed packet.

```text
Owner decision for A1: DECLINE
Owner notes: Keep these EAs trading for now.
Owner name: Muhammad Ali Khan
Owner signature: Recorded from owner instruction in Codex chat
Decision timestamp UTC: 2026-06-12T10:52:58Z
```

## A2 - Repair Executors Broker Action OFF

Runtime action: set every `Phase2ExperimentalDemoRepairExecutor` chart for `*_repair_v1` lanes to `InpBrokerActionAllowed=false`.

Evidence basis: repair lanes were supposed to be `NONE_SHADOW_ONLY`; later broker-action use diluted the audit chain and should be restored to shadow-only before further decisions.

Rollback step: keep repair executors off unless a future approved packet re-arms a specific repaired candidate with fresh evidence.

```text
Owner decision for A2: DECLINE
Owner notes: Keep repair executors trading for now.
Owner name: Muhammad Ali Khan
Owner signature: Recorded from owner instruction in Codex chat
Decision timestamp UTC: 2026-06-12T10:52:58Z
```

## A3 - Family Duplicate Mutex

Runtime action: add a family duplicate mutex inside `Phase2ExperimentalDemoExecutor.mq5` before order send: if an open position already exists for the same symbol, same direction, same family magic band, and current M5 bar, block with guard reason `WOULD_DUPLICATE_FAMILY_EVENT`.

Evidence basis: duplicate same-family stacking amplified losses; broker and observer views must be closer to one family event rather than multiple clone trades.

Rollback step: restore the pre-change source/profile backup or disable the guard only through a new owner-signed packet.

```text
Owner decision for A3: APPROVE
Owner notes: Add family duplicate mutex.
Owner name: Muhammad Ali Khan
Owner signature: Recorded from owner instruction in Codex chat
Decision timestamp UTC: 2026-06-12T10:52:58Z
```

## A4 - Re-Arm Quantitative Guards

Runtime action: set remaining broker-action charts to `InpMaxEstimatedCostR=0.30`, `InpMaxMeasuredSpreadPoints=75`, `InpMaxOpenPositionsPerInstance=1`, `InpMinSecondsBetweenOrders=60`, and leave `InpMaxOrdersPerDay=0`.

Evidence basis: the June 9 guard re-arm plan was not applied; current evidence shows noisy trade bursts and duplicate family stacks need basic quantitative guardrails.

Rollback step: restore pre-window inputs from the profile backup or owner-sign a narrower guard update.

```text
Owner decision for A4: DECLINE
Owner notes: Do not re-arm quantitative guards now.
Owner name: Muhammad Ali Khan
Owner signature: Recorded from owner instruction in Codex chat
Decision timestamp UTC: 2026-06-12T10:52:58Z
```

## A5 - Lot Normalization

Runtime action: revert every EURUSD and GBPUSD chart to fixed lot `0.01`; change committed source defaults `InpEURUSDFixedLot` and `InpGBPUSDFixedLot` from `0.05` to `0.01` so a later recompile does not resurrect the larger lot.

Evidence basis: lot increases were useful as an experiment but now obscure EA quality and cross-symbol comparison; review needs normalized sizing.

Rollback step: future lot increases require a separate owner-signed lot authorization with symbol, lot size, account, and expiry.

```text
Owner decision for A5: DECLINE
Owner notes: Do not revert EURUSD/GBPUSD lots or source defaults now.
Owner name: Muhammad Ali Khan
Owner signature: Recorded from owner instruction in Codex chat
Decision timestamp UTC: 2026-06-12T10:52:58Z
```

## A6 - USDJPY Broker Action OFF

Runtime action: set all USDJPY charts to `InpBrokerActionAllowed=false`, observer-only.

Evidence basis: USDJPY is the weakest instrumented symbol in the current evidence: poor PF, small average win versus spread, and incomplete replay support.

Rollback step: re-enable USDJPY only after a new USDJPY-specific evidence packet and owner approval.

```text
Owner decision for A6: APPROVE
Owner notes: Turn USDJPY broker action off and keep it observer-only.
Owner name: Muhammad Ali Khan
Owner signature: Recorded from owner instruction in Codex chat
Decision timestamp UTC: 2026-06-12T10:52:58Z
```

## A7 - AccountEquityGuardianShadow Stage A

Runtime action: attach one `AccountEquityGuardianShadow` observer-only chart to the standard demo terminal so it can see account equity and open exposure. It must contain no broker-action calls and must pass forbidden-term scan before attachment.

Evidence basis: account-level drawdown, peak-giveback, and circuit-breaker logic should be observed before any future Stage B arming decision.

Rollback step: detach the Stage A observer chart or restore the pre-window profile backup; no flatten/halt behavior may be armed without a separate Stage B owner packet.

```text
Owner decision for A7: APPROVE
Owner notes: Attach AccountEquityGuardianShadow Stage A observer.
Owner name: Muhammad Ali Khan
Owner signature: Recorded from owner instruction in Codex chat
Decision timestamp UTC: 2026-06-12T10:52:58Z
```

## Maintenance-Window Acceptance Checklist

If any item is approved, the maintenance-window report must include:

- Before/after chart inventory with candidate, symbol, magic, broker-action state, dry-run state, lot, and guard values.
- Profile backup path.
- Compile logs with 0 errors / 0 warnings for any changed source.
- Startup-log proof after restart.
- Kill-switch or safety proof for any new observer that can see account state.
- Explicit list of declined A-items.
- Next-trading-day checks: duplicate rate `<= 2%`, max same-direction family stack `<= 2`, and expected `8-9` broker-action charts remaining.

## Owner Signature

```text
Overall Block A maintenance window decision: APPROVE_SELECTED_ITEMS
Approved item IDs: A3, A6, A7
Declined item IDs: A1, A2, A4, A5
Owner name: Muhammad Ali Khan
Owner signature: Recorded from owner instruction in Codex chat
Decision timestamp UTC: 2026-06-12T10:52:58Z
Operator: Codex
Reviewer: PENDING_REVIEW
```
