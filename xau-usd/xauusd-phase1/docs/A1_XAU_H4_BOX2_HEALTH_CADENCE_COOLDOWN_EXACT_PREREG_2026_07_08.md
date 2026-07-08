# A1 XAU H4 Box2 Health Gate + Cadence Cooldown Exact-MT5 Preregistration

Date: 2026-07-08

## Objective

Test whether the remaining box2 worst-week cluster is caused by entries arriving too close together on the H4 cadence.

Prior findings:

- Current best candidate: `prevhealth_box2_broad_quarantined`.
- Hard open cap 2 repaired the worst week but destroyed net and W/L.
- Daily stack cap 2 improved worst week and drawdown, but net fell below the 19000 USD gate.
- Third-entry H4 quality gate preserved net but did not touch the worst week.

The next structural hypothesis is cadence, not signal quality: allow box2 to pyramid, but require time spacing between accepted box2 entries.

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

Cadence rule:

- `InpCooldownMinutes = 480`
- `InpMaxTradesPerDay = 6`
- `InpOnePositionPerMagic = false`
- `InpMaxOpenPositionsPerMagic = 32`
- `InpH4D1WeeklyLossGovernorEnabled = false`
- `InpH4D1NegativeStackGuardEnabled = false`
- `InpH4D1ThirdEntryQualityGateEnabled = false`

Interpretation: keep pyramiding available, but prevent back-to-back H4 entries closer than 8 hours.

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

If cooldown improves the tail but misses net, it is a near-miss clue. If it preserves net but leaves the tail unchanged, simple H4 cadence spacing is not enough.

