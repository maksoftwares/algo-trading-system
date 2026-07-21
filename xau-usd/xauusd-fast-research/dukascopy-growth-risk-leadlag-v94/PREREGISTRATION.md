# V94 Dukascopy Growth-Risk M5 Lead-Lag Preregistration

## Conditional Status And Target

V94 is preregistered before any V93 XAU outcome is opened. It may run only if
V93 fails. V93 tests completed-H1 dislocations; V94 asks a distinct question:
whether synchronized completed-M5 source pulses lead the next executable XAU
move. V60 already owns the `>=1/day` result. V94 must help the unchanged shared
account reach at least `2.0/day` separately in Development-2, Confirmation, and
Final while all edge and drawdown gates pass.

## Frozen Source And Mechanics

V94 uses official Dukascopy M5 source bars for `USA500.IDX/USD`,
`COPPER.CMD/USD`, and `USD/CNH`. Exactly five mechanics are registered:

1. `M5_RISK_PULSE_CATCHUP`: broad risk-off/risk-on movement leads an incomplete
   XAU response.
2. `M5_GROWTH_PULSE_CATCHUP`: copper/CNH growth pressure leads an incomplete XAU
   response.
3. `M5_BREADTH_CONTINUATION`: all three mapped source legs agree and the
   completed XAU M5 bar has begun moving in the same direction.
4. `M5_PULSE_EXHAUSTION_FADE`: a source pulse is followed by an outsized
   opposite XAU response, which is faded only after the bar completes.
5. `M5_SEQUENCE_BREAKOUT`: the source pulse keeps the same sign across two
   completed horizons and agrees with a completed XAU M5 channel break.

Every feature is available at the signal-bar close. Entry is the immediately
following contiguous XAU M5 open. Missing bars reject entry; no partially formed
bar is used.

## Attempts And Firewall

Exactly `1,000` policies, attempts `125001-126000`, are locked: `200` per
mechanic. Manifest admission uses only source-event density and source-sign
balance. It cannot inspect XAU bars, labels, trade outcomes, or P&L. Discovery is
the V59/V60 Development-2 window. At most one policy per mechanic may advance,
and later stages remain sealed after any failure.

Stops use completed M5 ATR; target/hold profiles are fixed in the policy
registry. Longs enter Ask and exit Bid, shorts enter Bid and exit Ask, same-bar
ambiguity is stop-first, and ticket, holding, spread, and `0.05R` slippage stress
are charged. Each policy permits at most two trades per UTC date and one per
session slot.

The shared router and floating-equity caps are unchanged from V93 and do not
remove any V59/V60 trade. Failure is terminal: no direction, session, threshold,
exit, or risk rescue may be selected from exposed outcomes.

This is retrospective research only. It authorizes no training, Python
prediction, EA consumption, demo/live execution, paid data, Databento, or broker
action. The overall research program still stops at V100 if `>=2/day` is unmet.
