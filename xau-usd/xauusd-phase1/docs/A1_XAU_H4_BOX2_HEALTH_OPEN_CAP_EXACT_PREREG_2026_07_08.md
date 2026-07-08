# A1 XAU H4 Box2 Health Gate + Open Exposure Cap Exact-MT5 Preregistration

Date: 2026-07-08

## Objective

Test whether the remaining weekly tail in the current best candidate is caused by stacked H4/D1 box2 exposure.

Current best candidate:

- Previous-month health-gated H4/D1 box2.
- Broad H4/D1 quarantined.
- Frequency engine unchanged.
- V2 short hedge unchanged.

The candidate repaired monthly consistency from 29/19 to 31/17 without worsening max closed drawdown, but the worst week remained `-878.18`. The prior weekly closed-PnL brake fired zero times, so the next structural hypothesis is open exposure, not closed-loss sequencing.

## Boundary

- Exact-MT5 H4/D1 box2 component rerun only.
- Broad H4/D1 remains quarantined.
- Frequency and V2 short ledgers are unchanged.
- No live/demo runtime.
- No chart, preset, order, position, or broker-state change.
- No threshold sweep.

## Fixed Primary Test

`open_cap_2`:

- `InpOnePositionPerMagic = false`
- `InpMaxOpenPositionsPerMagic = 2`

Other fixed guards:

- `InpH4D1SupportiveStateGuardEnabled = true`
- `InpH4D1SupportiveEmaPeriod = 20`
- `InpH4D1SupportiveSlopeLagBars = 5`
- `InpH4D1PrevMonthHealthGateEnabled = true`
- `InpH4D1PrevMonthNetMinUsd = -50.00`
- `InpH4D1WeeklyLossGovernorEnabled = false`

## Contingency

If cap 2 does not improve the worst week, run exactly one contingency:

`open_cap_1`:

- `InpOnePositionPerMagic = false`
- `InpMaxOpenPositionsPerMagic = 1`

This is not a parameter search; it is a predeclared diagnostic to determine whether only a hard single-position cap touches the stacked-exposure tail.

## Pass / Fail

Compare each result against `prevhealth_box2_broad_quarantined`.

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

If the open cap preserves the core but fails to improve the worst week, this path is diagnostic only.

