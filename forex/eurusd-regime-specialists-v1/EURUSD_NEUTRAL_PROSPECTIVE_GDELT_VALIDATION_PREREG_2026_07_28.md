# EURUSD Neutral prospective GDELT validation preregistration

This validation contract was frozen at `2026-07-28T20:09:34Z`, before the
prospective start, first source capture, first decision, first signal, first
path outcome, and first prospective oracle row.

## Purpose

The GDELT relative-tone expert is evaluated only from immutable prospective
decisions, raw Dukascopy ticks, path manifests, and oracle labels that become
safe after the traded date. Historical EURUSD P&L is prohibited. The validator
may measure the strategy but may never change, filter, reverse, or retrain it.

Trade frequency is descriptive only. There is no minimum trades-per-day or
active-day gate. A cash decision is preferred to a weak or incomplete signal.

## Evidence integrity

Every decision, path manifest, raw tick archive, and metadata record must match
its SHA-256. Each signal may have at most one path manifest. Every closed path
must be replayed from the immutable raw ticks using the frozen entry, spread,
slippage, stop, target, and time-exit semantics; the replayed execution must
match the recorded execution exactly. Evidence observed after the evaluation
timestamp is excluded, and future-dated evidence is an error.

The validator reports the full cash/no-trade reason census. Only a path whose
execution status is `CLOSED` enters economic metrics.

## Economic and robustness review

Review is prohibited until both 12 calendar months and 30 closed trades have
elapsed. At least eight LONG and eight SHORT trades are required.

The frozen economic gates are:

- win rate from 45% through 55%;
- realized payoff ratio from 1.35 through 1.75;
- profit factor at least 1.15 and positive expectancy;
- LONG and SHORT profit factor each at least 1.0;
- profit factor at least 1.0 after another 0.5 pip round trip;
- closed-trade maximum drawdown no more than 15R;
- profit factor at least 1.0 after removing the largest 5% of winners;
- at least 60% of active months profitable; and
- no single month contributing more than 35% of total positive monthly profit.

The stressed R sequence also receives a frozen 10,000-simulation circular
moving-block bootstrap with seed `20260729`, block length five trades, and a
30-trade horizon. The probability of a 15R drawdown must be at most 10%.
This is an additional independent robustness gate frozen before outcomes.

## Oracle resemblance

Oracle evidence cannot route or filter the expert. Same-day Neutral,
same-side precision must reach 50%. Temporal resemblance uses optimal
one-to-one matching within UTC date and side at 15, 60, and 240 minutes. The
primary 60-minute precision must reach 25%, exceed the exact uniform
time-and-side null, and have a Poisson-binomial upper-tail p-value no greater
than 0.10. Recall is diagnostic only.

Profitability, same-day regime resemblance, and full temporal oracle imitation
are separate claims. A profitable result may proceed to independent research
review without proving temporal imitation. No passing result automatically
authorizes demo, live, broker, or account action.

## Frozen failure policy

Insufficient evidence remains `ACCUMULATING_PROSPECTIVE_EVIDENCE`. After
maturity, a failed economic or robustness gate rejects the exact rule without
retuning on its prospective record. Any later strategy is a new hypothesis
with a new prospective clock.
