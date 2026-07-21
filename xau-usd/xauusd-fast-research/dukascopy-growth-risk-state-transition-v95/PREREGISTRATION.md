# V95 Dukascopy Growth-Risk State Transition Preregistration

## Conditional Status And Target

V95 is preregistered before any V93 or V94 XAU outcome is opened. It may run
only after V94 fails terminally. V60 already owns the `>=1/day` result; V95 must
help the byte-identical shared account reach at least `2.0/day` separately in
Development-2, Confirmation, and Final while all edge and drawdown gates pass.

V93 tests source-score levels and H1 dislocations. V94 tests immediate M5
lead-lag. V95 asks a different question: whether a change in the cross-asset
state carries information after the previous state has already been observed.

## Registered Mechanics

Exactly five source-state mechanics are registered:

1. `RISK_SIGN_REVERSAL`: the mapped equity/copper/CNH risk score changes sign.
2. `GROWTH_SIGN_REVERSAL`: the copper/CNH growth score changes sign.
3. `RISK_GROWTH_CONVERGENCE`: previously opposed risk and growth scores become
   directionally aligned.
4. `RISK_GROWTH_DIVERGENCE`: previously aligned scores split; the risk score
   defines direction and XAU must confirm with a completed H1 channel break.
5. `RISK_STATE_ACCELERATION`: a persistent risk state strengthens by a locked
   ratio while retaining its sign.

Transitions use only contiguous completed H1 states. Source freshness is
measured from the last actual tick and cannot exceed 15 minutes. Entry is the
next executable XAU M5 quote after the completed H1 decision.

## Attempts And Firewall

Exactly `1,000` policies, attempts `126001-127000`, are locked: `200` per
mechanic. Source-only density and long/short balance determine manifest
admission without XAU bars, labels, trades, or P&L. Stops, targets, holding
periods, sessions, transition lags, thresholds, and XAU response conditions are
fixed before Discovery. At most one policy per mechanic may advance.

Later stages remain sealed after a failure. No exposed outcome may change a
direction, threshold, transition lag, session, exit, or risk rule. The shared
router cannot remove V59/V60 trades and preserves the locked correlation,
cost-stress, and buffered floating-drawdown gates.

This campaign authorizes no training, Python prediction, EA consumption,
demo/live execution, paid data, Databento, or broker action. The program stops
at V100 if the two-trades-per-day target remains unmet.
