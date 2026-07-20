# V68 COMEX Liquidity-Provision Anti-Signal Preregistration

## Hypothesis Origin

V44 flow-transition continuation and V45 sequence-ignition continuation were
selected without spot outcomes and then failed development decisively. Their
stress PF values were 0.4333 and 0.4224 across 1,615 and 1,939 resolved trades,
with both chronological halves below 0.46. V68 treats that evidence only as
hypothesis generation. It makes no claim that reversing a losing strategy must
be profitable.

The exact V44/V45 validation and exam stage artifacts were absent when V68 was
locked. Those periods are the only mechanism-specific historical holdouts used
for an evidence claim.

## Fixed Candidate Construction

1. Reproduce the exact V44 and V45 candidates from their locked policies.
2. Change V44 `LONG` to `SHORT` and `SHORT` to `LONG`.
3. Apply the same inversion to V45.
4. Sort by completed decision time and fixed source priority V44 then V45.
5. Retain only the first candidate per UTC date.
6. Do not inspect source score, price outcome, P&L, regime, or later price while
   routing.

The one-per-day router is an account-risk and dependence control. It is not a
quota: a date with no mechanical candidate remains an abstain date.

## Execution

- Session and source-quality rules remain byte-equivalent to V44/V45.
- Entry is the first verified Dukascopy quote strictly after the decision and
  no more than two seconds later.
- Long enters ask and exits bid; short enters bid and exits ask.
- Stop is max(0.50 completed-M5 ATR, four entry spreads, USD 1.00).
- Target is 1.50R.
- V44-origin holds at most 30 minutes; V45-origin at most 20 minutes.
- One XAU ounce, USD 0.30 ticket cost, prorated USD 0.35/day holding cost, and
  an additional 0.05R stress charge are fixed.

## Sequential Evidence

1. Development: 2022-08-01 through 2024-06-30. This is contaminated
   hypothesis-generation evidence and cannot support admission.
2. Validation: 2024-07-01 through 2025-06-30. It opens only after unchanged
   development passage.
3. Exam: 2025-07-01 through 2026-06-30. It opens only after unchanged
   validation passage.

Every stage requires 0.60-1.00 resolved trades per eligible weekday, both
directions at least 20%, positive base/stress net and mean, base PF at least
1.20, stress PF at least 1.10, at least 40% profitable full weekdays, at least
60% positive months, both half-stage stress PF values at least 1.00, positive
stress net after removing the five largest winners, closed stress drawdown no
more than USD 150, and a centered-null five-weekday block-bootstrap one-sided
p-value no more than 0.01. Development requires 350 resolved trades;
validation and exam require 180 each.

## Firewall

No parameter, direction, source membership, priority, daily cap, hold, stop,
target, cost, split, or gate may change after the contract lock. Failure is
terminal and later stages remain sealed. V68 cannot change the frozen V59/V60
portfolio or authorize training, prediction, EA, demo/live, paid-data, or
broker operations.
