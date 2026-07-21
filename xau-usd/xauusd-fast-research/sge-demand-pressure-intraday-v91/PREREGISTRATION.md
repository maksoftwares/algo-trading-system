# V91 SGE Demand-Pressure Intraday Preregistration

Date: 2026-07-21

## Purpose

V59/V60 is immutable and already exceeds one trade per weekday in each modern
window. V91 tests whether lagged Shanghai Gold Exchange cash, deferred,
open-interest, basis, and physical-delivery states can add enough independent
qualified trades for the combined portfolio to exceed two trades per weekday.
V91 cannot alter, remove, delay, retune, or replace a V59/V60 trade.

## Source And Causality

- The accepted public SGE source is hash-bound from
  `C:/SgeGoldDemandFoundationV1` and remains outside Git.
- An SGE trading-date observation `D` becomes usable only at `00:00 UTC` on
  `D+1`; same-date use is forbidden.
- Missing SGE values are not imputed. A mechanism requiring a missing state
  abstains.
- Return, basis, volume, open-interest, and delivery features use only SGE
  observations available at the decision time. Rolling z-score baselines
  exclude the current observation.
- XAU features use completed H1 bars. Entries use the next M5 ask for longs and
  next M5 bid for shorts; exits remain side-correct.

## Registered Mechanics

1. `CASH_MOMENTUM_BREAKOUT`: lagged Au99.99 return direction must agree with a
   completed H1 channel breakout.
2. `CASH_VOLUME_PRESSURE`: lagged Au99.99 return and abnormal cash-market volume
   must agree with completed H1 impulse and body confirmation.
3. `DEFERRED_BASIS_REVERSION`: an abnormal Au(T+D)-versus-Au99.99 basis
   dislocation must be followed by a completed H1 turn toward normalization.
4. `DEFERRED_OI_EXPANSION`: lagged Au(T+D) return, open-interest expansion, and
   completed H1 trend confirmation must agree.
5. `DELIVERY_DIRECTION_PRESSURE`: lagged Au(T+D) delivery direction and abnormal
   delivery volume must agree with completed H1 trend confirmation.

`Short to Long` delivery direction is registered as positive and `Long to Short`
as negative. That interpretation is fixed before outcomes and may not be
reversed or repaired in V91.

## Registered Search

Exactly 200 deterministic policies per mechanic are admitted by outcome-blind
signal coverage and direction balance, for attempts `122001` through `123000`.
Coverage selection may inspect lagged SGE states and completed pre-entry XAU
bars. It may not inspect post-entry quotes, trade returns, labels, P&L, or profit
factor.

Policy dimensions are mechanic-appropriate subsets of one- to three-observation
returns, 20/60/120-observation causal z-scores, London/New York routing,
completed channel/impulse/body filters, `0.6-1.25 ATR` stops, `1.0-2.0 R`
targets, and `2-8h` holds. No outcome-exposed policy may be mirrored, retuned,
repaired, or quota-rescued inside V91.

## Sequential Windows

1. Discovery: 2016-07-01 to 2019-01-01.
2. Replication: 2019-01-01 to 2022-07-01.
3. Development 2: 2022-07-01 to 2024-07-01.
4. Confirmation: 2024-07-01 to 2025-07-01.
5. Final: 2025-07-01 to 2026-07-01.

Only unchanged policies passing the current stage may enter the next. At most
one policy per mechanic advances. A zero-advancer stage seals every later
window. Final is never used for repair.

## Gates And Authority

Every stage requires the config-locked trade-count, frequency, stress-PF,
average-R, positive-month, drawdown, top-winner-removal, segment-stability, and
Benjamini-Hochberg gates. Confirmation and Final each require at least `0.50`
standalone trades per weekday; passing still does not imply shared admission.

Maximum two entries per policy per UTC date and one per London/New York slot are
allowed. Spread, extra cost, holding cost, and `0.05 R` stress slippage apply.
V91 is research only and grants no model, EA, demo/live, broker, payment, or
Databento authority.
