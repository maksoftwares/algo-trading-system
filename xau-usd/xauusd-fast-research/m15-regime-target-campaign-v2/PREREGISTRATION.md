# XAUUSD M15 Regime Target Campaign V2 Preregistration

## Scope

V1 is invalidated and permits no quantitative inference because mixed datetime units rejected every candidate before execution. V2 reruns the exact same 1,000 parameter definitions and economic gates under new attempt numbers after one isolated clock correction.

## Locked correction

`bar_start_utc`, `bar_end_utc`, and `timestamp_utc` are each explicitly converted to `datetime64[ns, UTC]` before integer array conversion. The runner asserts that every signal timestamp equals its completed bar end. A regression test constructs millisecond bar starts and microsecond signal times representing the same instant, then requires a zero-minute next-bar entry gap and an executable trade.

No strategy parameter, feature, target, stop, holding horizon, cost, regime definition, era, or gate changes from V1.

## Attempts

- New attempts: 18120 through 19119 inclusive.
- V1 definitions are regenerated from the hash-pinned V1 source and config.
- Historical outcomes remain discovery-only.
- Same-version post-outcome tuning is forbidden.

## Gates and next step

The V1 economic gates remain mandatory: 120 total trades, 15 per era, PF at least 1.10 and average at least 0.02R in every era, total PF at least 1.25, drawdown no more than 30R, and positive net after removing five winners.

Any survivor still requires separately locked raw-tick replay and prospective shadow evidence. No result authorizes training or execution.
