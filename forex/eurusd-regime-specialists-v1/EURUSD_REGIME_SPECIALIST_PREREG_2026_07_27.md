# EURUSD regime-specialist preregistration

Status: `LOCK_BEFORE_REGIME_OUTCOME_INSPECTION`

## Objective

Advance only the existing raw EURUSD M30 RSI/Bollinger long-fade seed. Do not tune its hours, thresholds, direction, stop, or target. Apply the already-frozen causal USD regime classifier and test whether exclusive regime ownership turns the weak aggregate seed into a robust, sufficiently frequent EURUSD portfolio.

The inherited MT5 seed evidence (2022-07 through 2026-07) is already known: 1,145 trades, parsed PF 1.1301. The regime-level outcomes under this classifier have not been inspected. This is therefore a decomposition experiment, not a claim of a fresh untouched strategy.

## Frozen seed

- completed M30 bid close at or below the 20-period, 2-standard-deviation lower Bollinger band;
- Wilder RSI(14) at or below 35;
- long-only, enter at the first M5 open after signal completion;
- stop below the lower of the most recent six completed M30 lows or 1.4 Wilder ATR(14), with 3-pip floor and 70-pip ceiling;
- target 0.80R;
- one open EURUSD position, maximum 24 entries per UTC day;
- no hour exclusions and no time exit.

## Causal regime ownership

The signal uses only its completed M30 bar. Its regime is the latest fully completed H1 cross-asset state. Ownership is exclusive:

1. any cross-asset shock: cash;
2. non-shock joint DXY/EURUSD compression: `S1_JOINT_COMPRESSION_FADE`;
3. established USD-down state: `S2_SUPPORTIVE_ESTABLISHED`;
4. transitional USD-down state: `S3_SUPPORTIVE_TRANSITION`;
5. neutral/unresolved state: `S4_NEUTRAL_AUCTION`;
6. USD-up state: `S5_OPPOSING_CAPITULATION`.

Compression takes precedence over direction. No regime may be relabelled after P&L inspection.

## Outcome-blind capacity gate

Before any regime signal is joined to an exit or P&L, the raw opportunity census must show:

- at least 1.50 owned signals per active EURUSD day overall;
- at least 60% of active EURUSD days contain one or more owned signals;
- at least 350 owned signals in each chronological window.

Failure stops the experiment before P&L.

## Execution and costs

Use the archived Dukascopy M5 bid/ask bars. For a long entry, use the observed ask or enforce a 0.70-pip minimum retail spread over bid, whichever is worse, then add 0.10 pip adverse entry slippage. Exit from bid with 0.10 pip adverse exit slippage. On a bar touching stop and target, book the stop first. The known EURUSD suspect interval is quarantined.

## Frozen admission

Each specialist requires at least 75 trades, PF at least 1.10, and expectancy above 0.01R in every chronological window; overall drawdown no more than 20R; positive net after removing the top 5% of winners; and positive net after another 0.50 pip round trip.

The portfolio includes only specialists passing those rules, uses one open position and frozen priority, and must achieve PF at least 1.15, positive net in every window, and at least 1.0 actual trade per active EURUSD day.

No threshold, owner, stop, target, cost, or gate changes are permitted after outcome inspection. A failure is reported as a failure.
