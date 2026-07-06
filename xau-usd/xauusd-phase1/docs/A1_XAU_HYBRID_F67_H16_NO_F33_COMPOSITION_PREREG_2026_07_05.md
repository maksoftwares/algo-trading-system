# A1 XAU Hybrid F67-H16 No-F33 Composition Preregistration

Date: 2026-07-05

## Purpose

Package one exact-ledger composition follow-up after the f67 hour-16 exact repair.

The f67 hour-16 exact replay produced:

- `3861` signals
- WR `49.96%`
- W/L `1.9999`
- Active weekdays `86.39%`
- PF `2.0114`

The source contribution table showed the f33 high-payout source had become a small, marginal final-book contributor after the f67 hour-16 repair:

- `step1_f33_r30_be_never`: `115` kept signals, net `448.07 USD`

## Frozen Composition Change

Remove `step1_f33_r30_be_never` from the final hybrid composition and rerun the same 5-minute same-direction dedupe from the raw exact-ledger composition.

No MT5 launch is needed for this step because no component entry logic is changed:

- The changed f67 components already have exact MT5 replay evidence.
- The unchanged v8, opening-range reversal, and H4/D1 components are reused from exact MT5 ledgers.
- This step only changes the Step3-style portfolio membership.

## Decision Rule

- `EXACT_LEDGER_OWNER_GOAL_HIT_REVIEW_REQUIRED`: WR >= 50%, W/L >= 2.0, active weekdays >= 90%, net > 0.
- `EXACT_LEDGER_CORE_FRONTIER_ACTIVITY_GAP_NO_REVIEW`: WR >= 50%, W/L >= 2.0, active weekdays >= 85%, net > 0, but active weekdays below 90%.
- Anything weaker remains near-frontier context only.

No demo spec, runtime attach, or live action is allowed from this composition alone.
