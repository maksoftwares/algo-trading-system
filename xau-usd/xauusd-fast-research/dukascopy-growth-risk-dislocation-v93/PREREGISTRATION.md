# V93 Dukascopy Growth-Risk Dislocation Preregistration

## Target

V60 already achieved at least one combined trade per weekday in Development-2,
Confirmation, and Final. V93 receives no credit for repeating that result. It
must add independent trades to the byte-identical V59/V60 ledger so the routed
shared account reaches at least `2.0` trades per weekday separately in all three
windows while preserving the locked profit-factor, correlation, and drawdown
gates.

## New Information

V93 uses official Dukascopy M5 source bars for `USA500.IDX/USD`,
`COPPER.CMD/USD`, and `USD/CNH`. No V61-V92 campaign tested this three-source
growth/risk state. Collection and source validation contain no XAU outcomes.

## Registered Mechanics

1. `RISK_PULSE_CATCHUP`: US equity weakness, copper weakness, and CNH weakness
   form a signed risk pulse; XAU trades toward a materially incomplete response.
2. `GROWTH_PULSE_CATCHUP`: copper and CNH form a signed reflation/growth pulse;
   XAU trades toward an incomplete response.
3. `CROSSASSET_GATED_BREAKOUT`: a broad source pulse must agree with a completed
   XAU H1 channel break before entry.
4. `ROLLING_BETA_RESIDUAL`: a causal ridge model trained only on earlier
   completed hours estimates the contemporaneous XAU response; the trade follows
   a large unfilled residual.
5. `ROLLING_BETA_CONTINUATION`: the same prior-only model gates a partial XAU
   transmission already moving in the predicted direction.

The rolling model is a deterministic feature constructor, not execution ML. It
is refit from earlier observations only and is not trained on future trade P&L.

## Attempts And Sealing

Exactly `1,000` policies, attempts `124001-125000`, are selected before XAU
outcomes: `200` per mechanic. Admission uses only source-event density and
source-sign balance in Development-2. Discovery opens once; an unsuccessful
mechanic is terminal and cannot be mirrored, re-exited, re-sessioned, or tuned.
Only one policy per mechanic may advance. Confirmation and Final remain sealed
unless every prior gate passes.

## Costs And Controls

Entries use the first executable XAU quote after a completed H1 decision. Longs
enter Ask and exit Bid; shorts enter Bid and exit Ask. Stops use completed H1
ATR, same-bar ambiguity is stop-first, and baseline ticket/holding costs plus
`0.05R` slippage stress are charged. Each policy permits at most two entries per
UTC date and one per session slot.

The shared router keeps the V59/V60 ledger byte-identical, admits no more than two
V93 positions, caps concurrent add-on initial risk at USD `45`, suspends at USD
`225` closed drawdown, and requires the buffered floating drawdown to remain at
or below USD `449.7675`.

This is retrospective research only. It authorizes no model training, Python
prediction, EA consumption, demo/live execution, paid data, Databento, or broker
action.

The surrounding program stops at V100 if the `>=2/day` target is still unmet;
the next step would be a brainstorming decision review, not an automatic V101.
