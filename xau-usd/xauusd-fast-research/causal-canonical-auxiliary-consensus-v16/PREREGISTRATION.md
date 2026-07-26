# Auxiliary Consensus V16 Preregistration

## Question

Can the three auxiliary models stabilize the locked B1+B2+B3 veto by requiring
cross-domain agreement before a canonical V60 trade is removed?

## Frozen evidence

V14 remains the immutable prospective lane. V15 remains a completed historical
experiment. V16 uses the same overlap-cleaned auxiliary population: 64,319
action labels from 24,835 events in 13,639 structural episodes, including
26,775 winners and 37,544 failures. The 117,534 journey-attempt rows remain
quarantined.

The exact canonical population, folds, B1+B2+B3 predictions, V60 ledger,
post-loss cooldown, and evaluation windows remain frozen.

## Policy

For each outer fold:

1. fit the three V15 auxiliary models only on actions whose decision and label
   end precede the canonical calibration boundary;
2. score canonical calibration and test rows without using canonical outcomes;
3. independently calculate the weighted 10%, 15%, and 20% calibration
   thresholds for each auxiliary score;
4. mark auxiliary weakness only when at least two of the three scores are in
   the selected bottom tail;
5. veto only candidates that are both rejected by the locked B1+B2+B3 policy
   and marked weak by the auxiliary consensus;
6. choose among the three fixed tail sizes using canonical calibration
   economics only;
7. retain all candidates when no choice improves calibration P&L over raw
   candidates while retaining at least 95% of weight and not worsening mean
   Expected-R, profit factor, or drawdown.

The auxiliary scores cannot directly alter the B1+B2+B3 score. A B1+B2+B3
retained candidate is always retained by V16.

## Decision

V16 passes its historical gate only if exact V60 replay:

- improves all-history net P&L versus both raw V60 and locked B1+B2+B3;
- is nonnegative versus raw V60 in the latest three months;
- improves raw V60 over six and twelve months;
- retains at least 95% of raw trades;
- does not worsen all-history profit factor or closed-trade drawdown.

Historical outcomes were exposed before this design. A pass would nominate a
new prospective challenger only; it would not authorize Python serving,
shadowing, EA consumption, demo trading, live trading, sizing, or broker
actions.
