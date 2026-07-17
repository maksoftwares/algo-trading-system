# MT5 R1 Uptrend Specialist Dukascopy Portability V1

Date: `2026-07-17`

## Question

Does the fixed MT5 `r1_box_clean_strict_uptrend` specialist retain positive
after-cost expectancy on independent Dukascopy XAUUSD Bid/Ask data?

The MT5 results are known. This is an exact-mechanism replication and no historical
window is described as untouched.

## Fixed Candidate Mechanism

The entry is the already frozen two-day D1 compression / completed-H4 bullish
breakout:

- D1 ATR(14) percentile over 252 bars at or below 80.
- Half of the prior two-day box width no more than 1.50 times median D1 range(20).
- Completed H4 bullish body at least 35% of range and close above the box high.
- Stop distance is max(H4 close minus box low, H4 ATR(14), $3.50); target is 2R.

R1 ownership additionally requires:

- Two consecutive completed D1 bars with close > EMA20 > EMA50.
- On both bars, EMA20 and EMA50 are nondecreasing versus five D1 bars earlier.
- The completed H4 bar has close > EMA20 > EMA50 and both EMAs nondecreasing
  versus five H4 bars earlier.
- Shock veto when completed H1 range is at least 3.0 H1 ATR(14), or completed D1
  ATR(14) is at or above its 95th percentile over 60 D1 bars.
- The completed D1 close remains above EMA20 with nondecreasing EMA20.

All price features use completed Bid bars. Long entry uses next contiguous M5 Ask;
exits use Bid. Same-M5 collisions are stop-first.

## Fixed Execution Views

1. `MT5_STACKING_DIAGNOSTIC`: 32 concurrent positions, six entries per UTC day.
   It cannot qualify for shared-account use.
2. `PORTFOLIO_CONSTRAINED_PRIMARY`: two concurrent positions and one new entry per
   UTC day. Only this view is eligible for the decision.

Stress includes native spread, `$0.30` per 0.01-lot trade, `$0.35` per 24 hours
held, and `0.05R` adverse slippage.

## Stages And Decision

- Replication fit: 2017-07-01 through 2021-06-30.
- Development: 2021-07-01 through 2024-06-30.
- Exam: 2024-07-01 through 2026-06-30.
- Prospective holdout begins 2026-07-01.

The constrained view must pass every frozen stage gate. No failed filter, threshold,
session, direction, or execution rule may be repaired inside V1.

Research only. No model training, EA consumption, demo order, or live order is
authorized by this study.
