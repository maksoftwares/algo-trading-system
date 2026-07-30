# EURUSD V1R immediate next-bar reclaim contract

Status: `FROZEN_IMPLEMENTED_NOT_RUN`

Candidate: `EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1R_IMMEDIATE_NEXT_BAR_RECLAIM_V1`

This package implements the sole alpha intervention authorized by the binding independent review in the parent V1R package. It must be committed before any candidate compile or Strategy Tester run.

## Sole change

A completed M30 bar `t` must first satisfy the exact corrected V1R long RSI/Bollinger close-fade setup. The candidate does not enter immediately. It stores one pending setup and examines only the immediate next completed M30 bar `t+1`.

The setup confirms only when `Close(t+1) > LowerBand(t+1)`. Equality fails. No RSI, candle-color, body-fraction, distance, buffer, or additional filter is evaluated on the confirmation bar. A pass enters on the first executable tick of `t+2`.

All stop, target, size, direction, spread, session, cooldown, daily-cap, and ownership rules are inherited unchanged. Stop ATR and the six-bar swing are evaluated through completed bar `t+1`. Requested target remains quote-anchored at 0.8R.

## State invariants

- Maximum one pending setup and one confirmation bar.
- Stored setup must be series shift 2 on the confirmation decision tick.
- Reinitialization discards pending state; it is never reconstructed.
- A pass, operational guard failure, open-position block, or failed request consumes the setup.
- On a failed confirmation, the just-completed bar may become the sole fresh raw setup.
- No queue, retry, multi-bar wait, parameter sweep, or post-outcome filter is allowed.
- Strategy Tester only. No chart, demo, shadow, or live action is authorized.

## Binding gates

Stage 1 is conjunctive and fatal. Core minimums include full PF >= 1.2100021357, at least 400 trades, +0.5-pip stressed PF >= 1.15, +1.0-pip stressed PF >= 1.00 with positive net, last-12 PF >= 1.22, last-6 PF >= 1.20, positive 2023/2024/2025, at least two of those years PF >= 1.15, and the previously frozen concentration, rolling-window, bootstrap, regime-coverage, drawdown, and evidence gates.

Any Stage 1 failure ends this RSI/Bollinger close-fade family. Stage 2 historical admission additionally requires full PF >= 1.30, payoff ratio >= 0.90, defensible DSR >= 0.95, and complete evidence. A historical pass would still require new prospective real-tick validation before demo trading.

