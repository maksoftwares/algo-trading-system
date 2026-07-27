# EURUSD confirmed-reversal preregistration

Status: `LOCKED_BEFORE_CONFIRMATION_OUTCOME_INSPECTION`

## Hypothesis

The prior 1.50R experiment demonstrated acceptable payoff but insufficient entry accuracy. Immediate RSI/Bollinger fades enter while adverse momentum is still active. A distinct two-stage mechanism should improve accuracy: first identify completed M15 exhaustion, then require a completed M5 break of local structure before entry.

This is not another hour mask or exit retune. The 1.50R target and 12-hour lifecycle remain frozen.

## Causal entry

An arm occurs on the first completed M15 bar of an episode:

- long arm: RSI(14) at or below 35 and close at or below the 20-period, 2-standard-deviation lower Bollinger band;
- short arm: RSI(14) at or above 65 and close at or above the upper band.

For at most 60 minutes after the arm:

- long confirms when a completed bullish M5 bar closes above the highs of the preceding three completed M5 bars;
- short confirms when a completed bearish M5 bar closes below the lows of the preceding three completed M5 bars.

Entry is the next M5 open after confirmation. Unconfirmed arms expire. Identical confirmation timestamps and directions are deduplicated.

## Exclusive regime owners

The latest fully completed causal H1 state assigns each confirmation:

1. shock: cash;
2. joint DXY/EURUSD compression: `C1_COMPRESSION_REVERSAL`;
3. direction aligned with EURUSD (`USD_DOWN`/long or `USD_UP`/short): `C2_USD_ALIGNED_PULLBACK`;
4. neutral/unresolved: `C3_NEUTRAL_REVERSAL`;
5. direction opposing the trade: `C4_COUNTERTREND_EXHAUSTION`.

## Risk and execution

Stop distance is the worse of 1.25 arm-M15 ATR, 3 pips, or the extreme between arm and confirmation; stop ceiling is 70 pips. Target is 1.50R and maximum hold is 12 hours. Longs pay ask and exit bid; shorts mirror. Enforce a 0.70-pip minimum retail spread, 0.10-pip adverse slippage per side, and stop-first same-bar ambiguity.

## Outcome firewall

Before exits or P&L are inspected, the confirmation census must show at least:

- 1.50 owned confirmations per Monday-Friday UTC date;
- 50% weekday coverage;
- 850 confirmations in each chronological window.

Failure stops the campaign before P&L.

## Admission

Each specialist must have at least 75 trades in every window and, in every window, 45–55% wins, realized payoff 1.35–1.75, PF at least 1.30, and expectancy above 0.05R. Overall drawdown must not exceed 20R; top-5%-winner removal and another 0.50-pip round trip must remain positive.

Only admitted specialists enter the portfolio. It must preserve the same accuracy/payoff bands, PF at least 1.30, positive net in every window, and at least one actual trade per weekday.

All history is adaptive development evidence. A pass would still require prospective confirmation. No parameter repair is allowed after outcome inspection.
