# EURUSD Neutral session OCO preregistration

Date: 2026-07-28

Status: `FROZEN_BEFORE_THIS_CAMPAIGN_OUTCOME_PASS`

## Motivation

The full-calendar oracle knows whether a long or short path wins and then
deletes the other side. Without authenticated strike-surface or CVOL
history, trying to predict that direction from another tuned indicator
would repeat the exhausted directional research.

This campaign instead makes direction causal. At four standard six-hour
UTC session anchors, it places a two-sided one-cancels-other breakout
around the fully completed prior-hour range. The first executable side to
trade becomes the position and cancels the other order.

## Fixed rule

1. Consider 00:00, 06:00, 12:00, and 18:00 UTC on weekdays.
2. Use the latest completed cross-market state no later than anchor hour
   minus one hour.
3. Trade only non-shock, non-compressed `NEUTRAL` states.
4. Form a range from the previous twelve completed EURUSD M5 bars.
5. Place the buy stop 0.2 pip above the bid range high and the sell stop
   0.2 pip below the bid range low.
6. Cancel both orders if neither triggers in 90 minutes.
7. If both sides trigger within the same M5 bar, record an ambiguous
   no-trade; do not infer intrabar ordering.
8. Apply a 0.7-pip minimum retail spread and 0.1-pip adverse slippage per
   side.
9. Use fixed 4-pip risk, 1.50R target, 12-hour maximum hold, and stop-first
   handling for ambiguous exit bars.
10. Allow one open position and no more than four entries per UTC date.

There is one strategy and no parameter or subgroup selection.

## Chronology and evidence limits

The fixed rule is measured separately on 2019-2020, 2021-2022,
2023-2024, and 2025-2026 H1. The archive has already been inspected by
earlier campaigns, so even the later windows are pseudo-out-of-sample,
not pristine evidence. Oracle rows are opened only after the fixed trade
ledger exists and are used solely for behavioral comparison.

## Admission

Every window must have at least 50 trades, 45-55% wins, 1.35-1.75
realized payoff, and PF at least 1.10. Overall maximum drawdown must not
exceed 30R. Results must remain positive after removing the largest 5% of
winners and after an additional half-pip round-trip cost.

Failure closes this exact OCO rule. It does not authorize repairs.
