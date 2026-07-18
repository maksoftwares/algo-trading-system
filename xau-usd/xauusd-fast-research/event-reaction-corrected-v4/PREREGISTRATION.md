# XAUUSD Event Reaction Corrected V4 Preregistration

## Reason For V4

The prior NFP, CPI, FOMC, and PPI event outcomes are invalid. Their shared
execution engine treated `datetime64[ms]` M5 timestamps as nanoseconds and
divided them by one million. Stops and targets were therefore never scanned;
all 382 audited outcomes exited through `MAX_HOLD`.

V4 changes only that execution defect and the audit guards needed to detect it.
It does not rescue, filter, or tune any prior result. The corrected engine:

1. converts every datetime storage resolution explicitly to epoch milliseconds;
2. rejects candidate timestamps outside the M5 range;
3. tests stop and target paths against raw Dukascopy ticks; and
4. reports stop, target, and timeout counts in the execution audit.

## Registered Family

V4 registers eight policies as attempts 11,103 through 11,110:

- NFP impulse and fade;
- CPI impulse and fade;
- FOMC impulse and fade; and
- PPI impulse and fade.

Every signal parameter is the unchanged pre-defect rule: completed event range,
0.1 ATR break and stop buffers, minimum 0.35 body fraction, and 2R target. There
is no policy grid, regime filter, direction filter, or parameter search.

## Data And Execution

- NFP/CPI dates are from the official BLS archive and FOMC dates are from the
  official Federal Reserve statement archive.
- PPI dates are from the official BLS PPI archive index frozen in PPI V1.
- Signal construction uses causal M5 bars and the causal H4 regime label.
- Entry is the first verified quote strictly after the completed signal, within
  ten seconds.
- Stops and targets are ordered on verified raw Dukascopy ticks with stop-first
  same-tick priority.
- Native spread, $0.30 ticket cost, $0.35 per 24 hours held, and 0.05R stress
  slippage are included. Maximum hold is 72 hours; a weekend-safe 72-hour quote
  grace finds the first available timeout quote without changing the deadline.
- No MT5 bar is used as execution truth. No paid data or Databento is used.

## Firewall And Gates

Historical replication is 2016-07-01 through 2021-12-31. All eight policies
enter together and receive one Holm correction. Every historical gate must pass:

- at least 18 trades and 20% event participation;
- stress PF at least 1.25 and average stress return at least +0.08R;
- closed drawdown at most 12R;
- positive P&L after removing the three largest winners;
- at least 50% positive active months and 50% positive active years;
- at least 80% current-account feasibility; and
- Holm q-value at most 0.15.

Only unchanged full-gate passers may enter the related 2022-01-01 through
2026-06-30 confirmation. The confirmation is not a pristine blind exam. It
requires at least 12 trades, 20% participation, PF 1.20, +0.05R average,
drawdown at most 10R, positive top-three-winners-removed P&L, 50% positive
active months and years, 80% feasibility, and Holm q-value at most 0.15.

A pass is only a near-survivor. It still requires independent-era replication,
portfolio-independence testing, and prospective shadow evidence. Research only:
no model training, Python serving, EA, demo/live order, broker, paid-data, or
Databento authority is granted.
