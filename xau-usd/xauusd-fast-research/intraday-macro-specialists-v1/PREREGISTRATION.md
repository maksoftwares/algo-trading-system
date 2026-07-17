# XAUUSD Intraday Macro Specialists V1 Preregistration

Date: `2026-07-17`

## Question

Can native intraday US dollar-index and Treasury total-return pressure define
cost-surviving XAUUSD specialists that are economically distinct from the
rejected XAU-only and slow daily-macro families?

## Frozen Families

1. `M15_DXY_LEAD_CONTINUATION_V1`: a standardized one-hour dollar-index impulse
   predicts the opposite XAU direction. Treasury pressure must be quiet rather
   than strongly confirming or opposing. XAU must confirm with a directional M15
   candle and a controlled one-hour move. Stop `1.50 ATR(14)`, target `2R`, and
   maximum hold eight hours.
2. `M15_BOND_LEAD_CONTINUATION_V1`: a standardized one-hour US Treasury
   total-return impulse predicts the same XAU direction. Dollar pressure must be
   quiet. XAU must confirm with the same controlled continuation geometry. Stop
   `1.50 ATR(14)`, target `2R`, and maximum hold eight hours.
3. `M15_MACRO_DISLOCATION_REVERSAL_V1`: dollar and Treasury pressure must agree
   on the expected XAU direction while XAU's preceding one-hour move has lagged
   or moved against that pressure. A completed M15 rejection candle must turn in
   the macro direction. Stop `1.25 ATR(14)`, target `1.75R`, and maximum hold six
   hours.

Dollar and bond impulses are standardized by the standard deviation of prior
one-hour returns over 192 completed M15 bars. The current impulse is excluded
from its own scale. Dollar pressure maps inversely to gold; Treasury total-return
pressure maps directly to gold.

## Causality And Execution

- Macro M5 rows are aggregated only when all three constituent M5 bars exist.
- A gold M15 signal can use only the macro M15 bar ending at exactly the same
  timestamp. No forward or backward fill is allowed.
- Entry is the next contiguous XAU M5 open, long at Ask and short at Bid.
- Long exits use Bid and short exits use Ask. Native spread is embedded.
- Stop/target collisions are stop-first.
- Stress subtracts `$0.30` execution cost, `$0.35` per 24 hours held, and `0.05R`.
- One position per family, two-hour cooldown, and at most two family entries per
  UTC day.

## Chronological Firewall

- Train: 2020-01-01 through 2021-06-30.
- Validation: 2021-07-01 through 2023-06-30.
- Internal test: 2023-07-01 through 2024-06-30.
- Exam: 2024-07-01 through 2026-06-30.
- Recent tail: fixed exam subset from 2025-07-01 through 2026-06-30.

Later periods become decision-ineligible after the first failed stage. No period
is described as untouched because the repository has inspected retrospective
market history.

## Gates

Every family must pass frozen sample size, minimum `0.10` trades per source day,
stressed PF, average stressed R, active-month stability, drawdown, and
winner-removal gates in sequence. The exam requires at least 100 trades, PF
`1.25`, average `0.05R`, and drawdown no greater than `20R`.

A combined portfolio requires at least two survivors, at least `0.80` trades per
source day, PF `1.30`, average `0.05R`, drawdown no greater than `25R`, no more
than two concurrent positions, no more than four entries per day, controlled
same-opportunity overlap, and daily P&L correlation no greater than `0.60` in
absolute value.

## Anti-Overfit And Authorization

There is one fixed definition per family and no parameter grid. V1 will be
committed before any historical outcome is calculated. Same-version repair is
forbidden. A retrospective survivor still requires independent reproduction,
cost sensitivity, exact-tick parity, and prospective shadow evidence. Research
only; no Python prediction, EA, demo, or live authorization is granted.
