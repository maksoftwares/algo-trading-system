# A1 XAU H4 Box2 Health Gate + Negative Stack Guard Exact-MT5 Preregistration

Date: 2026-07-08

## Objective

Test whether the box2 engine can keep profitable trend pyramiding while blocking only the dangerous part of stacking: adding more entries when the existing H4/D1 box2 basket is floating negative.

Prior exact result:

- Hard cap 2 improved worst week from `-878.18` to `-283.11`.
- Hard cap 2 broke the core: net dropped to `10064.02`, W/L dropped to `1.7101`.

This means open exposure is the correct failure surface, but a hard cap is too blunt. This test allows stacking when the open basket is healthy and blocks new box2 entries only when the basket is already underwater.

## Boundary

- Exact-MT5 H4/D1 box2 component rerun only.
- Broad H4/D1 remains quarantined.
- Frequency and V2 short ledgers are unchanged.
- No live/demo runtime.
- No chart, preset, order, position, or broker-state change.
- One fixed rule only; no threshold sweep.

## Fixed MT5 Inputs

Base component:

- Previous-month health-gated H4/D1 box2.
- Supportive D1 state guard enabled.
- Broad H4/D1 excluded from the recomposed portfolio.

Additional fixed guard:

- `InpH4D1NegativeStackGuardEnabled = true`
- `InpH4D1NegativeStackMaxOpenPositions = 2`
- `InpH4D1NegativeStackMinFloatingUsd = 0.00`
- `InpMaxOpenPositionsPerMagic = 32`
- `InpOnePositionPerMagic = false`

Interpretation: if there are already at least 2 own open box2 positions, block the next box2 entry unless current own floating PnL is at least zero.

## Pass / Fail

Compare against `prevhealth_box2_broad_quarantined`.

A result is a review candidate only if all hold:

- Positive months >= 31.
- Net >= 19000 USD.
- Win rate >= 48%.
- W/L >= 2.0.
- W/L after -0.30 USD/ticket stress >= 1.90.
- Active weekdays >= 84%.
- Max closed drawdown <= the baseline candidate.
- Worst week improves by at least 20%.
- Worst month is not worse than the baseline candidate.

If the tail improves but net or W/L breaks, the guard is too restrictive. If net/WL survive but the tail does not improve, the weekly damage is not caused by underwater stacking.

