# A1 XAU H4 Box2 Health Gate + Third-Entry Quality Gate Exact-MT5 Preregistration

Date: 2026-07-08

## Objective

Test a selective repair for the remaining box2 worst-week cluster.

Prior findings:

- Current best candidate: `prevhealth_box2_broad_quarantined`.
- Hard open cap 2 fixed the weekly tail but destroyed the box2 profit engine.
- Daily stack cap 2 improved the weekly tail but dropped net below the 19000 USD gate.
- Negative-stack guard fired only once and did not touch the worst week.

The next structural hypothesis is that same-day burst stacking should not be banned outright; instead, first and second same-day entries should remain normal, while third and later same-day entries must show stronger H4 expansion quality.

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

Third-entry quality rule:

- `InpMaxTradesPerDay = 6`
- `InpH4D1ThirdEntryQualityGateEnabled = true`
- `InpH4D1ThirdEntryQualityNormalEntries = 2`
- `InpH4D1ThirdEntryMinH4BodyFraction = 0.50`
- `InpH4D1ThirdEntryMinBreakDistanceAtr = 0.10`

Interpretation: first two box2 entries per broker day are unchanged. A third or later same-day box2 entry is allowed only if the closed H4 expansion candle has body fraction at least 0.50 and breakout distance at least 0.10 H4 ATR.

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

If the rule improves the tail but misses net, it is a near-miss clue. If it preserves net but leaves the tail unchanged, same-day third-entry signal quality is not the right repair.

