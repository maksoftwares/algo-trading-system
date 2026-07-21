# V89 Cboe GVZ-Routed Intraday Preregistration

## Purpose

V89 tests a new causal input: the Cboe Gold ETF Volatility Index (`GVZ`), an
option-implied volatility measure. Previous campaigns tested spot price,
cross-asset direction, COMEX trades, scheduled clocks, and weekly CFTC option
positioning. They did not test the daily gold option-implied volatility index as
an intraday state router.

V89 is additive research beside byte-identical V59/V60. It cannot alter, remove,
resize, reroute, or outcome-select an accepted V59 trade.

## Causality

- A GVZ close dated `D` becomes usable only at `00:00 UTC` on `D + 1`.
- Same-date GVZ use is forbidden even though the index closes before midnight
  UTC. This conservative lag avoids exchange-close and publication ambiguity.
- GVZ z-scores compare the current, already available observation with a rolling
  baseline containing prior observations only.
- Realized volatility, ATR, channels, impulses, and confirmation use completed
  XAUUSD H1 bars only.
- Entry is the first contiguous M5 quote after the completed H1 decision, at Ask
  for long and Bid for short.
- Stop wins same-M5 stop/target ambiguity. Spread, ticket cost, holding cost, and
  additional slippage are charged exactly as locked in the contract.

## Registered Mechanics

1. `GVZ_HIGH_BREAKOUT`: an unusually high prior-day GVZ state routes a completed
   H1 channel break in the break direction.
2. `GVZ_RISING_BREAKOUT`: an unusually large causal GVZ increase routes the same
   completed breakout geometry.
3. `GVZ_LOW_REVERSION`: an unusually low GVZ state routes a completed H1 reversal
   against a multi-hour XAUUSD extension.
4. `GVZ_FALLING_REVERSION`: an unusually large GVZ decrease routes that completed
   reversal geometry.
5. `GVZ_PREMIUM_EXPANSION`: a high option-implied-minus-realized volatility
   premium routes a completed XAUUSD breakout from bounded realized volatility.

Exactly 200 deterministic, coverage-eligible policies per mechanic are admitted
for attempts `120001` through `121000`. Coverage selection may inspect GVZ and
pre-entry XAU structure, candidate timestamps, direction, and density. It may not
inspect an entry, exit, MAE, MFE, P&L, or any post-entry quote.

Each policy may create at most one London and one New York entry per UTC date.
Splitting tickets or counting repeated H1 confirmations inside one session is
forbidden.

## Sequential Windows

1. Discovery: July 2016 through December 2018.
2. Replication: January 2019 through June 2022.
3. Development 2: July 2022 through June 2024.
4. Confirmation: July 2024 through June 2025.
5. Final: July 2025 through June 2026.

Only discovery may open after the contract is locked. A later stage remains
sealed unless the prior stage writes a hash-bound advancement naming an unchanged
policy. Benjamini-Hochberg correction applies to every policy entering a stage,
and zero-trade calendar weeks remain in significance tests.

## Terminal Rule

Failure at any stage is terminal for the exposed V89 policy or family. No mirror,
threshold, session, stop, target, hold, cost, or quota rescue is allowed on opened
outcomes. A final survivor is only a shared-portfolio nominee; it is not execution
authority.

No payment, Databento request, account creation, model training, Python serving,
EA consumption, demo order, live order, or broker action is authorized.
