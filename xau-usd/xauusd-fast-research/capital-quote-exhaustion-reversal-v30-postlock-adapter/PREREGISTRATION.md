# V30 MT5 Timestamp Adapter Preregistration

The adapter is permitted to correct only one pre-outcome transport mismatch:
`time_utc` has second precision and `time_msc` has millisecond precision.

Acceptance requires all of the following:

1. Every V30 source and strategy byte still matches contract
   `456b4ae5ddca695c2e5b37a79ab297c859d133b39e5197c4a78a80cf8a687d95`.
2. Every development row has exact same-second agreement between the two time
   fields.
3. `time_msc` is used unchanged as the causal timestamp.
4. Identity, bid/ask, spread, duplicate, full-day, event, execution, cost, and
   economic checks remain the locked V30 checks.
5. No strategy threshold or output is changed in response to development P&L.

A same-second mismatch fails closed. A strategy-gate failure is terminal for
V30. This adapter grants no execution or model authority.
