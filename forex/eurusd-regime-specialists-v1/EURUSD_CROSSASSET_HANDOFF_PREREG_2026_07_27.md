# EURUSD cross-asset session-handoff preregistration

Status: `LOCKED_BEFORE_CROSSASSET_HANDOFF_OUTCOME_INSPECTION`

## Hypothesis

The local-price fade and confirmation families failed because they did not identify when a move had independent macro participation. EURUSD session range resolution should have higher precision when a completed Dollar Index impulse and the causal multi-asset USD regime agree with the EURUSD break.

This is a new entry mechanism. RSI and Bollinger signals are not used.

## Specialists

`X1_LONDON_CROSSASSET_HANDOFF`:

- reference range: completed M15 bars from 00:00 through 05:59 UTC;
- decision bars: 06:00 through 09:59 UTC.

`X2_NEWYORK_CROSSASSET_HANDOFF`:

- reference range: completed M15 bars from 06:00 through 11:59 UTC;
- decision bars: 12:00 through 15:59 UTC.

Only the first qualifying signal per specialist and UTC date is eligible.

## Causal direction confirmation

At the completed M15 decision:

- long: EURUSD closes more than 0.05 M15 ATR above the reference high, the latest completed H1 regime is non-shock `USD_DOWN`, and completed DXY closes below its prior six-H1 low;
- short: EURUSD closes more than 0.05 M15 ATR below the reference low, the latest completed H1 regime is non-shock `USD_UP`, and completed DXY closes above its prior six-H1 high.

Entry is the next M5 open. No transition/established outcome split and no post-outcome session mask are allowed.

## Risk and costs

Stop is 1.25 M15 ATR with a 4-pip floor and 70-pip ceiling. Target is 1.50R; maximum hold is 12 hours. Use archived bid/ask, a 0.70-pip minimum retail spread, 0.10-pip adverse slippage per side, and stop-first ambiguity.

## Capacity firewall

Because this is intended as a quality sleeve rather than the whole frequency portfolio, P&L opens only if the combined census has:

- at least 0.15 signals per weekday;
- at least 10% weekday coverage;
- at least 75 signals in every chronological window.

## Admission

Each specialist needs at least 40 trades in every window. Every window must show 45–55% wins, realized payoff 1.35–1.75, PF at least 1.30, and expectancy above 0.05R. Overall drawdown must not exceed 15R; top-5%-winner removal and another 0.50-pip round trip must remain positive.

Any admitted portfolio must have PF at least 1.30 and positive net in every window. All history is adaptive development evidence, and a pass would still require prospective confirmation.
