# Out-Of-Era Breakout Economics And Independence V2

## Purpose

Three fixed long-breakout rules were positive in multiple 2016-2026 slices, but
none is authorized: R1 lacked one development trade, strict-compression R1B was
under-sampled and winner-concentrated under the primary portfolio policy, and the
broader compression rule failed earlier chronological gates. This study asks
whether their unchanged definitions survive the independently collected 2010-2016
Dukascopy period and whether more than one is genuinely distinct.

## Fixed Candidates

1. `R1_UPTREND_PORTABILITY_EXACT`: unchanged two-day R1 regime-owned breakout
   and `PORTFOLIO_CONSTRAINED_PRIMARY` policy.
2. `R1B_STRICT_COMPRESSION_EXACT`: unchanged three-day, lower-volatility strict
   R1 reclassification and the same primary portfolio policy.
3. `COMPRESSION_LONG_PORTABILITY_EXACT`: unchanged two-day compression breakout
   without R1 regime ownership and its primary portfolio policy.

There is no parameter search. Every source configuration and implementation is
hashed before the 2010-2016 outcomes are opened.

## Execution And Data

- Source: all 78 normalized Dukascopy months from 2010-01 through 2016-06.
- The final V1 out-of-era data contract must validate before this study locks.
- Decisions use completed D1 and H4 bars and enter the next contiguous M5 Ask.
- Long exits use Bid; gap-through stops receive the worse open; same-M5 ambiguity
  is stop-first.
- Native spread, ticket cost, holding cost, and 0.05R stress slippage are charged.
- Each primary policy permits two concurrent positions and one new entry per UTC
  day, exactly as in its source study.

## Economic Gates

Each candidate must pass its registered minimum trade count, stressed PF, average
R, closed drawdown, positive-active-year share, top-five-winners-removed net, and
Holm-adjusted one-sided daily p-value. A candidate that fails any gate is rejected.

## Independence Gates

For each economically surviving pair:

- same-direction entries within 60 minutes must be at most 20% of the smaller
  trade set;
- absolute daily stressed-P&L correlation over all source trading days must be at
  most 0.60.

The fixed selection order is R1, then R1B, then broader compression. A later rule
counts as a distinct specialist only if it passes both independence checks against
every earlier selected survivor. Economic survival without independence is not a
new specialist.

Research only. No model training, EA consumption, broker action, demo/live orders,
Databento use, or paid acquisition is authorized.
