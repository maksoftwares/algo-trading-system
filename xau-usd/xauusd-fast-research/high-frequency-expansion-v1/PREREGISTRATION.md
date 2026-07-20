# XAUUSD High-Frequency Expansion V1 Preregistration

Locked before candidate outcomes from this campaign are inspected.

## Objective

Test whether a separate Expansion layer can raise the combined XAUUSD portfolio
toward 3-4 executed trades per weekday without changing, filtering, delaying, or
replacing any frozen Core trade.

The frequency target is an average including zero-trade weekdays. It is not a
daily quota. The system must abstain when no candidate clears the locked policy.

## Architectural lock

1. Frozen Core signals bypass every Expansion model and retain first priority.
2. Expansion begins with mechanically generated, causal candidate events.
3. ML may rank an event and choose one of three frozen risk/holding actions. It
   may not invent an entry.
4. Unsafe/shock observations remain abstain states.
5. Expansion is rejected unless it passes its own cost-stressed expectancy,
   frequency, stability, and drawdown gates before any Core combination study.
6. No EA, terminal, account, runtime, or broker setting may be changed by V1.

## Frozen candidate sources

The exact six source files and SHA-256 values are in
`config/high_frequency_expansion_v1.json`. They contain every M5 decision from
three mechanical families over 2016-2021 and 2022-2026:

- opening-range reversal;
- downside impulse/retest;
- break-and-run momentum.

Only rows whose stage is `WOULD_SIGNAL` are candidates. Saturday and Sunday UTC
signals are excluded. Rows sharing the same signal timestamp and direction are
one event with mechanism flags; no outcome is used in event construction.

## Independent market source

The verified Dukascopy bid/ask M5 feature cache is hash locked in the config.
An MT5 signal logged at time `T` describes the completed M5 bar ending at
`floor(T, 5 minutes)`. Features therefore join to that exact closed Dukascopy bar,
and entry occurs at the first side-specific bar open at or after the unrounded
decision time `T`.

Pre-outcome implementation clarification: 30,714 of 30,733 source candidate rows
are exactly on a five-minute boundary. Nineteen occur 1-120 seconds/minutes into a
new bar because the tester evaluated on the first available tick. Those timestamps
remain unrounded for entry, so V1 delays them to the next M5 open rather than
rounding backward and receiving a price from before the decision.

All joins are backward or exact-to-closed-bar. Forward prices are used only for
labels.

## Frozen actions

Each event receives three hypothetical labels:

| Action | Stop | Target | Maximum hold |
|---|---:|---:|---:|
| FAST | 1.00 ATR, minimum $2.50 | 1.00R | 4h |
| INTRADAY | 1.50 ATR, minimum $3.00 | 1.50R | 12h |
| SWING | 2.25 ATR, minimum $3.50 | 2.00R | 36h |

Entry and exit use side-specific bid/ask prices. A bar touching stop and target is
scored stop-first. Gap-through-stop is filled at the adverse opening price.
Stress subtracts $0.30 per 0.01-lot equivalent, $0.35 per 24 hours held, and
0.05R slippage in addition to observed spread.

## Frozen time firewall

| Stage | Half-open UTC window | Use |
|---|---|---|
| Fit | 2016-07-01 to 2019-01-01 | Fit model |
| Selection | 2019-01-01 to 2022-01-01 | Rank exactly 1,000 attempts |
| Internal test | 2022-07-01 to 2024-07-01 | Select one finalist from at most 20 |
| Final exam | 2024-07-01 to 2026-07-01 | One final evaluation, no tuning |
| Recent tail | 2025-07-01 to 2026-07-01 | Diagnostic subset of final exam |

All history is development data in the wider program and is not represented as a
pristine market holdout. The firewall only prevents same-campaign outcome tuning.

## Frozen search budget

Exactly 125 deterministic HistGradientBoosting model specifications are crossed
with eight causal selection policies, producing exactly 1,000 strategy attempts.
The policies combine rolling prior-score quantiles of 0.30, 0.40, 0.50, or 0.60
with either no absolute floor or a predicted-stress-R floor of zero.

The rolling threshold uses only the previous 500 event scores and needs 200 prior
events. It uses no realized outcome. Each event keeps only its highest-scored
action.

Selection constraints are fixed:

- maximum four Expansion entries per UTC weekday;
- maximum three concurrent Expansion positions;
- maximum two concurrent positions in one direction;
- 30-minute same-direction opportunity separation;
- 15-minute separation between any two Expansion entries;
- no Expansion entry in `UNSAFE_SHOCK`;
- no Saturday or Sunday entry.

## Gates

Selection-stage attempts must have 2.50-4.10 trades per weekday, stress PF at
least 1.15, average stress result at least 0.02R, positive-month share at least
55%, every calendar-year PF at least 1.02, drawdown no more than 60R, and positive
net result after removing the best 20 trades.

At most 20 passing attempts advance. The deterministic order is: highest worst
calendar-year PF, highest overall PF, highest average R, frequency nearest 3.5,
then attempt ID.

The one internal-test finalist must have 2.75-4.10 trades per weekday, stress PF
at least 1.20, average stress result at least 0.03R, positive-month share at least
55%, every calendar-year PF at least 1.05, drawdown no more than 50R, and positive
net after removing the best 15 trades. The same deterministic ordering chooses one
finalist.

The final exam passes only with 3.00-4.10 trades per weekday, stress PF at least
1.25, average stress result at least 0.04R, positive-month share at least 55%,
every calendar-year PF at least 1.10, drawdown no more than 45R, and positive net
after removing the best 10 trades. The recent tail must independently have at
least 2.50 trades per weekday, PF at least 1.15, and positive average R.

## Decision lock

`EXPANSION_V1_PASSES_REQUIRES_CORE_PORTFOLIO_TEST` is possible only if every final
exam and recent-tail gate passes. Otherwise the result is
`EXPANSION_V1_REJECTED`. A pass is still research-only and must next prove that
Core P&L identity is unchanged in a shared-account simulation.

No threshold, feature, cost, action, split, gate, or model may be altered in V1
after results are produced.
