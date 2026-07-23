# EURUSD regime specialists V2 preregistration

Status: frozen before opening any result dated on or after 2020-07-01.

V2 is a repair of the V1 architecture, not a continuation of the 1,000-candidate
search. V1 archetypes mixed market conditions. V2 assigns each frozen specialist
to one mutually exclusive H4 regime and routes no trade in unsafe, transition, or
unknown states.

## Information boundary

- 2016-07-01 through 2020-07-01 was already opened by V1 and is `train`.
- `validation`, `internal`, and `exam` are opened sequentially and only when the
  immediately preceding gate passes for that specialist.
- A failed stage seals all later stages for that specialist.
- No thresholds or candidates may be changed after a later window is opened.
- The 2024-10-09 23:00 through 2024-10-10 01:00 UTC official-source defect is
  quarantined. Signals and positions touching it are rejected.

## Classifier and routing

The classifier is calculated from completed H4 bars only and becomes available at
the next H4 boundary. The states are `unsafe`, `trend_up`, `trend_down`,
`compression`, `chop`, and `transition`. Rules and thresholds are fully specified
in the config. Rules resolve in that order, making the state mutually exclusive.

Each specialist must qualify independently. A combined router is evaluated only
from independently qualified specialists and must contain at least two regimes.
No portfolio result can rescue a failed specialist.

## Execution

Signals use completed H1 bars. Entry is the next contiguous H1 ask open for longs
or bid open for shorts. Exits use executable bid prices for longs and ask prices
for shorts. Stop wins an ambiguous same-bar collision. Native spread, 0.2 pip
slippage on each entry/exit, and an additional 0.5 pip round-trip stress are
included. This is a conservative Stage-A screen; any qualifier requires M5 and
MT5 replication before demo rehearsal.

## Decision

`DEMO_REHEARSAL_READY` requires every specialist and portfolio gate plus exact M5
and MT5 parity evidence. Otherwise the result is a sealed research result and is
not an authorization to place orders.
