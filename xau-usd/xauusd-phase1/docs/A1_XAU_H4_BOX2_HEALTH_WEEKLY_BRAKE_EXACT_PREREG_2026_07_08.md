# A1 XAU H4 Box2 Health Gate + Weekly Brake Exact-MT5 Preregistration

Date: 2026-07-08

## Objective

Test one source-local weekly brake on the current best composition:

- Previous-month health-gated H4/D1 box2.
- Broad H4/D1 quarantined.
- Frequency engine unchanged.
- V2 short hedge unchanged.

The previous composition repaired monthly consistency from 29/19 to 31/17 and avoided the broad-H4 drawdown regression, but the worst week remained `-878.18`. This pass tests whether the existing H4/D1 weekly loss governor can reduce that weekly tail without destroying the core.

## Boundary

- One exact-MT5 component rerun only: H4/D1 box2 with supportive guard + previous-month health gate + weekly loss governor.
- No threshold sweep.
- No live/demo runtime.
- No chart, preset, order, position, or broker-state change.
- Broad H4/D1 remains quarantined.

## Fixed MT5 Inputs

Base H4/D1 box2 inputs remain unchanged from the prior exact H4 component run.

Additional fixed guards:

- `InpH4D1SupportiveStateGuardEnabled = true`
- `InpH4D1SupportiveEmaPeriod = 20`
- `InpH4D1SupportiveSlopeLagBars = 5`
- `InpH4D1PrevMonthHealthGateEnabled = true`
- `InpH4D1PrevMonthNetMinUsd = -50.00`
- `InpH4D1WeeklyLossGovernorEnabled = true`
- `InpH4D1WeeklyLossLimitUsd = 150.00`

## Pass / Fail

Compare against `prevhealth_box2_broad_quarantined`.

A result is a review candidate only if all hold:

- Positive months >= 31.
- Net >= 19000 USD.
- Win rate >= 48%.
- W/L >= 2.0.
- W/L after -0.30 USD/ticket stress >= 1.90.
- Active weekdays >= 84%.
- Max closed drawdown <= the box2-health broad-quarantined candidate.
- Worst week improves by at least 20%.
- Worst month is not worse than the candidate.

If the weekly brake reduces trades but leaves the worst week unchanged, it fails; the losses are closing too late for this brake to help.

