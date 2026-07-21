# V96 Dukascopy Growth-Risk State Transition Preregistration

## Conditional Status And Target

V96 is preregistered before any V96 XAU outcome is opened. It may run only after
the artifact-bound V94 terminal failure and the committed V95 source-only lock
failure are verified. V60 already owns the `>=1/day` result; V96 must help the
byte-identical shared account reach at least `2.0/day` separately in
Development-2, Confirmation, and Final while all edge and drawdown gates pass.

V93 source-score levels and H1 dislocations failed terminally. V94 immediate M5
lead-lag failed terminally. V95 never opened XAU outcomes because convergence
had no source-eligible policy. V96 asks the narrower remaining question: whether
source-dense sign changes or state acceleration carry information after the
previous state has already been observed.

## Registered Mechanics

Exactly four source-state mechanics are registered:

1. `RISK_SIGN_REVERSAL`: the mapped equity/copper/CNH risk score changes sign.
2. `GROWTH_SIGN_REVERSAL`: the copper/CNH growth score changes sign.
3. `RISK_STATE_ACCELERATION`: a persistent risk state strengthens by a locked
   ratio while retaining its sign.
4. `GROWTH_STATE_ACCELERATION`: a persistent growth state strengthens by a
   locked ratio while retaining its sign.

The pre-outcome source census found 17,664 eligible risk-reversal variants,
24,320 growth-reversal variants, 29,376 risk-acceleration variants, and 1,332
eligible unique growth-acceleration source rules. Convergence and divergence
remain excluded: their maximum raw Discovery counts were only 12 and 8.

Transitions use only contiguous completed H1 states. Source freshness is
measured from the last actual tick and cannot exceed 15 minutes. Entry is the
next executable XAU M5 quote after the completed H1 decision.

## Attempts And Firewall

Exactly `1,000` policies, attempts `127001-128000`, are locked: `250` per
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
