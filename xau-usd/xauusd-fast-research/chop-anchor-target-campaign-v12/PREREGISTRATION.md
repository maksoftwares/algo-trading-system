# Chop Anchor-Target Campaign V12 Preregistration

## Decision question

Can target-aware balance rotation produce an economically robust XAUUSD specialist
while the frozen H4 owner regime is `CHOP`?

Prior chop campaigns entered around session, range, or VWAP structure but exited on
a fixed clock. V12 tests a changed economic mechanism: every trade has a causal
price anchor known at the completed M15 signal, and that frozen anchor is the profit
exit. `UNSAFE_SHOCK` is never eligible.

## Data and causality

Only the free verified Dukascopy bid/ask M5 foundation from 2016-07-01 through
2026-07-01 is used. M15 signals use a regime attached from the latest completed H4
bar. Previous-day values are shifted by one completed UTC trading day. Asian range
values are unavailable before 06:00 UTC. Day VWAP is cumulative through the signal
bar. Weekly open is known from the first completed bar of the week. Rolling balance
levels exclude the current bar.

Entry is the next complete M15 opening quote. Stops and targets use the executable
bid or ask side. If both are touched in one bar, the stop wins. Costs and stress
slippage are deducted. No anchor moves after entry.

## Locked search

Exactly 1,000 definitions, attempts 27239 through 28238:

- 200 previous-day extreme reclaims.
- 200 completed-Asia extreme reclaims.
- 200 intraday anchored-VWAP rotations.
- 200 weekly-open rotations.
- 200 rolling-balance reentries.

Manifest membership is determined before outcomes by SHA-256 ordering and minimum
signal coverage only. It cannot use forward returns, trade outcomes, PF, or P&L.
All 1,000 rows are included in false-discovery adjustment.

## Economic gates

- At least 100 trades and 15 trades in every era.
- Stress PF at least 1.10 and average stress R at least 0.02 in every era.
- Total stress PF at least 1.25.
- Closed-trade drawdown no more than 25 R.
- Positive net after removing the five largest winners.

Any historical survivor requires separately locked raw-tick replay, independent
replication, and prospective shadow evidence. No result authorizes training or
execution.
