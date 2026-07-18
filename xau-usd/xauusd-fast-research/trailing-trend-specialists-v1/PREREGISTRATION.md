# XAUUSD Trailing Trend Specialists V1 Preregistration

## New Mechanism

Earlier screens mostly used fixed profit targets or fixed holding horizons. A
medium-horizon trend strategy has a different payoff mechanism: many contained
losses and a small number of open-ended winners. V1 tests six conventional,
unchanged H4/D1 definitions with ATR trailing stops and opposite-channel exits.

## Fixed Policies

1. `H4_DONCHIAN_20_10_TRAIL`: 20-bar entry channel, 10-bar exit channel,
   2.5 ATR initial stop, 3.0 ATR trailing stop.
2. `H4_DONCHIAN_55_20_TRAIL`: 55/20 channels, 3.0 ATR initial stop, 3.5 ATR trail.
3. `H4_TSMOM_60_TRAIL`: direction of the completed 60-H4-bar return, 2.5 ATR
   initial stop, 3.0 ATR trail.
4. `H4_TSMOM_120_TRAIL`: direction of the completed 120-H4-bar return, 3.0 ATR
   initial stop, 3.5 ATR trail.
5. `D1_DONCHIAN_20_10_TRAIL`: 20/10 daily channels, 2.0 ATR initial stop,
   3.0 ATR trail.
6. `D1_DONCHIAN_55_20_TRAIL`: 55/20 daily channels, 2.5 ATR initial stop,
   3.5 ATR trail.

These are attempts 11,094 through 11,099. Parameter search count is zero.

## Causality And Execution

- Signals, channel exits, ATR, and trail updates use completed H4 or D1 bars.
- Entries and signal exits use the next contiguous M5 Ask/Bid open.
- Stops remain active on native M5 Bid for longs and Ask for shorts.
- Gap-through stops receive the worse executable open.
- Native spread, `$0.30` ticket cost, `$0.35` per 24 hours held, and `0.05R`
  stress slippage are charged.
- A stop and a new signal cannot produce a same-decision immediate re-entry.
- After any exit, the policy skips its configured number of subsequent completed
  signal decisions before another entry is allowed.
- Each policy holds at most one position.

## Firewall

- Discovery: 2016-07-01 through 2020-12-31.
- Confirmation: 2021-01-01 through 2026-06-30.

Discovery evaluates all six and applies Holm correction. Confirmation receives
only unchanged discovery passers and applies Holm again. Positive expectancy must
survive winner removal, chronological segments, drawdown, and realistic costs.

Research only. No model training, Python serving, EA use, demo/live orders, broker
action, Databento use, or paid acquisition is authorized.
