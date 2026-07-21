# V90 SPDR GLD Flow-Routed Intraday Preregistration

Date: 2026-07-21

## Purpose

V90 tests whether lagged SPDR Gold Shares (`GLD`) trust creation/redemption flow
contains additive directional information for intraday XAUUSD trades. The frozen
V59/V60 portfolio already exceeds one trade per weekday in every modern
out-of-time window. V90 cannot alter, remove, retune, or replace any V59/V60
trade. It is a separate research sleeve toward the later two-trades/day target.

## Source And Causality

- The official SPDR historical archive is hash-bound as an external local input.
- The archive itself is not committed or redistributed.
- A holdings observation dated `D` becomes usable only at `00:00 UTC` on `D+1`.
- Same-date holdings use is forbidden, including after the stated New York update.
- Flow is the percentage change in trust ounces over 1, 3, or 5 valid observations.
- Flow z-scores compare the current, already available 1-day flow only with prior
  available flows; the current value is excluded from the rolling baseline.
- All XAU features use completed H1 bars. Entries use the next M5 ask for longs
  and next M5 bid for shorts. Exits remain side-correct.
- The archive covers 2004-11-18 through 2026-07-17; the XAU research source
  remains the frozen 2016-07-01 through 2026-07-01 Dukascopy cache.

## Registered Mechanics

1. `FLOW_ALIGNED_BREAKOUT`: prior-day GLD flow direction must agree with a
   completed H1 channel breakout.
2. `FLOW_ALIGNED_PULLBACK`: flow direction, an established H1 impulse, a
   completed counter-direction pullback bar, and a completed resumption bar must
   agree.
3. `FLOW_DIVERGENCE_REVERSAL`: price first extends against GLD flow, then a
   completed H1 bar turns back toward the flow direction.
4. `PERSISTENT_FLOW_TREND`: 3- or 5-observation holdings flow must agree with a
   completed H1 trend and confirmation bar.
5. `FLOW_SHOCK_MOMENTUM`: an abnormal 1-day holdings change must agree with a
   completed London or New York momentum bar.

## Registered Search

Exactly 200 deterministic policies per mechanic are admitted by outcome-blind
signal coverage and direction balance, for attempts `121001` through `122000`.
Coverage selection may inspect lagged GLD inputs and completed pre-entry XAU bars.
It may not inspect post-entry quotes, trade returns, profit factor, or labels.

Policy dimensions are mechanic-appropriate subsets of:

- 1-, 3-, or 5-observation flow horizon;
- absolute flow threshold;
- causal 20-, 60-, or 120-observation flow z-score;
- London, New York, or both session routes;
- completed channel, trend, pullback, divergence, or body confirmation;
- `0.6-1.25 ATR` stop, `1.0-2.0 R` target, and `2-8h` hold.

No outcome-exposed policy may be mirrored, retuned, repaired, or quota-rescued
inside V90.

## Sequential Windows

1. Discovery: 2016-07-01 to 2019-01-01.
2. Replication: 2019-01-01 to 2022-07-01.
3. Development 2: 2022-07-01 to 2024-07-01.
4. Confirmation: 2024-07-01 to 2025-07-01.
5. Final: 2025-07-01 to 2026-07-01.

Only unchanged policies that pass the current stage can enter the next stage.
At most one policy per mechanic advances. A zero-advancer stage seals every later
window. The final window is never used for repair.

## Economic Gates

Every stage requires all registered checks: minimum trade count and frequency,
stress profit factor, positive mean stress R, positive-month share, closed-trade
drawdown cap, profitability after removing top winners, segment stability, and
Benjamini-Hochberg `q <= 0.10` across the exposed family.

Confirmation and final each require at least `0.50` trades per source weekday.
Final also requires stress `PF >= 1.25`, average stress return `>= 0.05 R`, both
half-year segments profitable with worst-segment `PF >= 1.0`, and closed drawdown
`<= 18 R`.

## Execution And Authority

- Maximum two entries per policy per UTC day and one per London/New York slot.
- A policy cannot overlap itself; one-hour post-exit cooldown applies.
- Spread, extra execution cost, holding cost, and `0.05 R` stress slippage apply.
- Research only: no model training, prediction publication, EA consumption,
  demo/live order, broker action, payment, or Databento authority is granted.
- Passing standalone gates still requires the separately locked shared-portfolio
  audit beside byte-identical V59/V60.
