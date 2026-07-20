# COMEX Size-Segment Flow V33 Preregistration

## Reason For New Version

V32 terminated during outcome-blind calibration. Across 20 eligible full
weekdays and 144 registered policies, its maximum density was 43 candidates, or
2.15/day, below the prelocked 2.3869731801/day minimum. The best-density row was
direction-balanced and active on 90% of days. V32 opened no future spot price,
label, fill, return, or P/L. Its calibration audit SHA-256 is
`b84d951eb9e935581552029dc7e09f15e3acef8919ebf53c5b05442e6a61d090`.

V33 is one outcome-blind density repair of the same registered family claim. It
does not change the hypothesis, session, five-minute completed clock, trade-size
segmentation, direction rule, one-hour economic hold, stop, target, execution,
costs, chronological partitions, or economic gates. It registers 96 additional
frequency-only policies by widening candidate activity thresholds and allowing
a 45- or 60-minute signal cooldown. This repair is frozen before any V33 spot
outcome is opened.

## Hypothesis And Rule

Directional disagreement between large-lot and small-lot aggressive COMEX flow
may identify a latent institutional metaorder whose impact has not fully reached
XAUUSD spot. V33 follows the large-lot direction.

- Signal source: existing Databento `GLBX.MDP3` `GC.v.0` trades files.
- Execution source, once locked: verified Dukascopy XAUUSD bid/ask ticks.
- Session: 08:20-13:30 `America/New_York`.
- Features: fixed completed five-minute half-open intervals.
- Small trades: no more than two contracts.
- Large trades: at least 8 or 10 contracts.
- Small and large signed-flow imbalances must oppose one another.
- The signal cooldown is a non-overlap control, never a quota.
- Multiple instrument IDs remain separate; future volume cannot select a
  dominant contract.

## Calibration Firewall

The same July 2022 packet may expose only source quality, candidate count,
candidate frequency, active-day share, and direction balance. The selector must
find 2.3869731801-3.3869731801 candidates per eligible full weekday, at least 80%
active days, and at least 30% minority direction. It minimizes distance from
2.8869731801/day and then prefers stricter size, volume, imbalance, small-volume,
and cooldown settings.

No P/L-bearing source is imported by the calibration runner. If no row qualifies,
the family fails before economics. If a row qualifies, it is locked and cannot
be changed after outcomes.

## Economic And Statistical Contract

V33 inherits V32's economic and statistical contract byte-for-byte from the
hashed V32 configuration:

- first verified quote strictly after the decision, within two seconds;
- executable ask/bid entry and opposite-side exit;
- stop at max(0.50 completed-M5 ATR, four spreads, USD 1.00);
- 1.50R target, 60-minute timeout, one ounce;
- USD 0.30 ticket cost, prorated holding cost, and extra 0.05R stress slippage;
- development 2022-08 to 2024-07, validation 2024-07 to 2025-07, and exam
  2025-07 to 2026-07, opened sequentially;
- 2.3869731801-3.3869731801 resolved trades/full weekday;
- base PF >=1.20, stress PF >=1.10, positive net and mean;
- >=50% profitable days and positive months, >=20% each direction;
- both half-stage stress PFs >=1.00, top-five-winners-removed net positive;
- stress drawdown <=USD 250; and
- centered-null circular five-weekday block-bootstrap p <=0.01.

Development requires 500 resolved trades; validation and exam require 200 each.
The runner stops at the first failed stage. A historical pass is still
development evidence because the broader period has informed prior research; an
unchanged post-2026-07-20 forward shadow remains mandatory.

## Authority

No network request, Databento payment, model training, Python prediction, EA
consumption, demo, live, terminal change, account change, or broker action is
authorized.

