# XAUUSD Round-Family Quarantine Owner Decision - 2026-06-17

Status: `OWNER_APPROVED_BOTH_ITEMS_APPLIED`

Boundary: demo only. This document does not authorize live trading, real capital, canonical Phase 2 approval, or any runtime change by itself.

## Reviewer Sign-Off

Reviewer sign-off file:

```text
XAUUSD_REVIEWER_SIGNOFF_ROUND_QUARANTINE_2026_06_17.md
```

Reviewer conclusion:

```text
Proceed to the Owner Decision Step.
Round-family quarantine/restriction is the first, best-evidenced runtime-change candidate.
Do not broad-ban XAUUSD afternoon.
Do not change breakout-core evening/night behavior.
No EA/runtime change before owner approval.
```

## Evidence Basis

| Evidence View | Rows | Win Rate | PnL AED | PF |
| --- | ---: | ---: | ---: | ---: |
| All deduped XAUUSD selected signals | 586 | 37.80% | -554.52 | 0.95 |
| Round-family selected signals | 432 | 36.60% | -1359.41 | 0.84 |
| Breakout-core selected signals | 112 | 47.75% | 1059.34 | 1.82 |
| Afternoon XAUUSD selected signals | 82 | 28.05% | -523.03 | 0.62 |
| Round-family afternoon | 55 | 27.27% | -452.13 | 0.58 |
| Non-round afternoon residual | 27 | 29.63% | -70.90 | 0.77 |
| Protected breakout evening/night | 79 | 52.56% | 1027.32 | 2.17 |

Round-family explains `86.44%` of afternoon loss and does not overlap the protected breakout evening/night cluster.

## Exact Candidates In Scope

Only these two candidates are in scope:

```text
symbol_normalized_round_retest_v0
round_number_retest_v0
```

## Explicitly Out Of Scope

The following are not approved by this packet:

```text
broad XAUUSD afternoon ban
evening/night-only routing
direction-only long/short rule
cost threshold runtime rule
breakout_retest change
swing_breakout_retest_v0 change
A2/A3 changes unless separately listed in a maintenance report
live trading
real capital
canonical Phase 2 PASS
```

## Owner Decision Item 1

Decision item:

```text
Restrict/quarantine symbol_normalized_round_retest_v0 on XAUUSD demo runtime.
```

Evidence:

```text
410 duplicate-hidden selected rows, 36.61% win rate, -1270.55 AED.
```

Preferred reversible implementation:

```text
Turn broker-action off or convert to observer-only for XAUUSD in the affected demo runtime lane.
Do not delete source code, logs, history, or chart evidence.
```

Rollback:

```text
Restore pre-change profile backup and original chart inputs.
```

Owner decision:

```text
APPROVE
```

Owner name:

```text
Muhammad Ali Khan
```

Decision timestamp Dubai:

```text
2026-06-17 15:22:56 +04:00
```

## Owner Decision Item 2

Decision item:

```text
Restrict/quarantine round_number_retest_v0 on XAUUSD demo runtime.
```

Evidence:

```text
22 duplicate-hidden selected rows, 36.36% win rate, -88.86 AED.
Part of the same round-family loss cluster; reviewer confirmed it should be scoped with symbol_normalized_round_retest_v0.
```

Preferred reversible implementation:

```text
Turn broker-action off or convert to observer-only for XAUUSD in the affected demo runtime lane.
Do not delete source code, logs, history, or chart evidence.
```

Rollback:

```text
Restore pre-change profile backup and original chart inputs.
```

Owner decision:

```text
APPROVE
```

Owner name:

```text
Muhammad Ali Khan
```

Decision timestamp Dubai:

```text
2026-06-17 15:22:56 +04:00
```

## If Approved

Apply only in a controlled maintenance window:

1. Capture profile backup.
2. Record before chart list and inputs.
3. Apply only the approved candidate restrictions.
4. Relaunch/reload as needed.
5. Record after chart list and inputs.
6. Verify startup/order logs.
7. Generate an applied report.
8. Score one fresh week against protected breakout-core impact.

## Required Applied Report

If either item is approved and applied, produce:

```text
xau-usd/xauusd-phase1/outputs/reports/XAUUSD_ROUND_FAMILY_QUARANTINE_APPLIED_2026_06_17.md
```

Applied report:

```text
xau-usd/xauusd-phase1/outputs/reports/XAUUSD_ROUND_FAMILY_QUARANTINE_APPLIED_2026_06_17.md
```

The report must include:

```text
owner decisions
profile backup path
before/after chart inventory
before/after chart inputs for affected candidates
startup/order-log verification
protected breakout evening/night unchanged proof
rollback path
```

## Source Evidence

| Source | Path |
| --- | --- |
| Evidence step | `xau-usd/xauusd-phase1/outputs/reports/XAUUSD_AFTERNOON_ROUND_FAMILY_EVIDENCE_STEP_2026_06_17.md` |
| Canonical report | `xau-usd/xauusd-phase1/outputs/reports/XAUUSD_CANONICAL_LOSS_AVOIDANCE_2026_06_17.md` |
| Canonical rows | `xau-usd/xauusd-phase1/outputs/reports/XAUUSD_CANONICAL_LOSS_AVOIDANCE_2026_06_17_ROWS.csv` |
| Reviewer sign-off | `XAUUSD_REVIEWER_SIGNOFF_ROUND_QUARANTINE_2026_06_17.md` |
