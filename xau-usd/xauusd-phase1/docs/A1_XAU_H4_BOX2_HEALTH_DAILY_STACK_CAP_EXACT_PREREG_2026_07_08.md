# A1 XAU H4 Box2 Health Gate + Daily Stack Cap Exact-MT5 Preregistration

Date: 2026-07-08

## Objective

Test whether the remaining worst-week loss is caused by same-day burst stacking rather than total open exposure.

Observed failure:

- Worst week remains `-878.18`.
- Box2 contributes `-866.37` of that week.
- The damaging box2 cluster includes three entries on 2025-12-22 and three more on 2025-12-23, all closing into the same loss window.
- Hard open cap 2 repairs the tail but destroys the core by cutting box2 from 208 portfolio trades to 68.
- Negative-stack guard fires only once and does not touch the worst week.

This test targets the burst-entry shape directly while preserving longer-duration trend pyramiding.

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

- `InpMaxTradesPerDay = 2`
- `InpOnePositionPerMagic = false`
- `InpMaxOpenPositionsPerMagic = 32`
- `InpH4D1NegativeStackGuardEnabled = false`
- `InpH4D1WeeklyLossGovernorEnabled = false`

Interpretation: allow pyramiding across the trend, but block the third and later same-day box2 entry.

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

If the tail improves but net or W/L breaks, the daily cap is too restrictive. If net/WL survive but the tail does not improve, the worst week is not primarily a same-day burst problem.

