# EURUSD Neutral prospective inventory portfolio risk validation

Recorded before the first 00:05/06:05/12:05 portfolio observation and with zero
source records, decisions, trade paths, oracle labels, or P&L.

## Purpose

Closed-trade profit factor is not enough for a controlled demo decision. This
read-only validator reconstructs portfolio floating equity from every immutable
bid/ask tick used by the component path manifests, then applies the account,
delay, margin, and sequence-risk rules below. It cannot create evidence, load
historical EURUSD P&L, request data, or contact a broker.

## Frozen account and path rules

- Research balance: USD 1,000.
- Position size: fixed 0.01 lot, at most one concurrent EURUSD position.
- Pip value: USD 0.10 per pip at 0.01 EURUSD lot.
- Margin assumption: 30:1 leverage; margin utilization must stay at or below
  10% of the declared balance.
- Long liquidation marks use bid; short marks use ask. Adverse exit slippage is
  charged at every tick-level liquidation mark.
- Every closed portfolio trade must link to one verified immutable path
  manifest and its raw snapshots. Duplicates, missing paths, or overlap fail.
- Base floating-equity drawdown must stay at or below 5%; the additional
  0.5-pip round-trip-cost curve must stay at or below 10%.

## Frozen execution and sequence stresses

- All trades are re-executed with five-second and 30-second delayed decisions
  against the same immutable tick paths.
- Five seconds is an admission stress: at least 95% must remain executable,
  profit factor must be at least 1.00, and the delayed intervals must not
  overlap. Thirty seconds is reported but cannot be selected after outcomes.
- Sequence risk uses 20,000 circular moving-block bootstrap paths, five trades
  per block, fixed seed `20260729`, the observed prospective trade count, and
  the extra-cost-stressed returns.
- Risk of exhausting the USD 1,000 balance must be below 1%. The probability of
  a 10% drawdown and the 50th/95th/99th drawdown quantiles are also reported.

Risk gates open only after at least 12 calendar months and 90 closed trades, and
only if the already frozen three-clock portfolio passes every one of its own
gates. Passing this validator permits independent research review only. Exact
MT5 parity, broker rejection telemetry, demo-only account/server guards, and
daily/rolling loss protection remain separate blockers.
