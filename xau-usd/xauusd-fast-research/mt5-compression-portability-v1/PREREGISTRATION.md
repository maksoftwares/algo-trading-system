# MT5 Compression Breakout Dukascopy Portability V1

Date: `2026-07-17`

## Question

Does the fixed MT5 `long_box2_atr80_range150_body035` mechanism retain positive
after-cost expectancy on the independent Dukascopy XAUUSD Bid/Ask source?

This is a replication study. The MT5 outcome is already known, so no MT5 period is
described as untouched. The Dukascopy result is scored only after this rule and its
execution policies are frozen.

## Fixed Signal

- Chart features use completed Bid bars on UTC calendar D1 and H4 boundaries.
- The prior two completed D1 bars define the box.
- D1 ATR(14) must be at or below its 80th percentile over 252 completed D1 bars.
- Half the two-day box width must be no more than 1.50 times the median D1 range of
  the prior 20 completed D1 bars.
- The completed H4 candle body must be at least 35% of its range.
- Long only: completed H4 close above the box high and above its open.
- Stop distance is the greater of H4 close minus box low, H4 ATR(14), and $3.50.
- Target is 2R.

Scheduled daily maintenance gaps remain inside their UTC D1/H4 buckets. A bucket
needs at least twelve M5 bars. A signal enters only at a Dukascopy M5 bar starting
within ten minutes of the completed H4 boundary.

## Fixed Execution Views

1. `MT5_STACKING_DIAGNOSTIC`: up to 32 concurrent positions and six entries per UTC
   day. This diagnoses how much the historical headline depends on stacking and
   cannot qualify for shared-account use.
2. `PORTFOLIO_CONSTRAINED_PRIMARY`: at most two concurrent positions and one new
   entry per UTC day. Only this view is eligible for the portability decision.

Long entries use Ask. Long exits use Bid. Same-M5 stop/target collisions are
stop-first. Stress includes native spread, `$0.30` per 0.01-lot trade, `$0.35` per
24 hours held, and `0.05R` adverse slippage.

## Chronological Stages

- Replication fit: 2017-07-01 through 2021-06-30.
- Development: 2021-07-01 through 2024-06-30.
- Exam: 2024-07-01 through 2026-06-30.
- Prospective holdout begins 2026-07-01.

The full retrospective source has been inspected by prior campaigns. These stages
are stability partitions, not untouched claims.

## Decision

The constrained view must pass every eligible stage for stress PF, average stress
R, drawdown, active-year stability, sample size, and winner removal. Failure is a
portability rejection. No failed threshold may be repaired inside V1.

Research only. No model training, EA consumption, demo order, or live order is
authorized by this study.
