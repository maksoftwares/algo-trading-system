# EURUSD Neutral selective multivenue-agreement preregistration

Frozen before inspecting any outcomes for the Kraken/Binance sign-agreement
subset on 2026-07-28.

## Why this one test is allowed

The preceding fixed-frequency rule forced a trade at all four clocks and
failed. The user subsequently made four trades per day negotiable, provided
the strategy is profitable. That instruction permits abstention but does not
permit fitting another score to the outcomes.

This campaign therefore tests one mechanically derived selective rule. It was
formulated after aggregate outcomes from the forced-trade parent were known,
so the evidence is adaptive historical research. However, the selected
subgroup's outcomes, oracle matches, clock results, and P&L were not inspected
before this freeze.

## Frozen decision rule

- Use only Regime 1 Neutral dates retained by the locked parent multivenue
  source contract.
- Consider the same 00:00, 00:15, 00:30, and 00:45 UTC decisions.
- Each venue must have exactly the three immediately preceding, consecutive,
  fully completed M5 bars with positive quote volume.
- Treat a nonnegative Kraken EUR/USD reported-side imbalance as LONG and a
  negative value as SHORT.
- Treat a nonnegative Binance EURUSDT taker-side imbalance as LONG and a
  negative value as SHORT.
- Trade only when the two signs agree. Enter the agreed side.
- Stay in CASH when the signs disagree.
- Use no magnitude threshold, venue weight, fitted model, daily quota, clock
  filter, or retrospective subgroup.
- A source-eligible date may produce zero through four trades.

## Outcome-blind census

| Window | Source-complete days | Trades | Traded days | Cash-only days |
|---|---:|---:|---:|---:|
| 2020-2021 development | 133 | 294 | 126 | 7 |
| 2022-2023 validation | 140 | 298 | 133 | 7 |
| 2024 validation | 62 | 114 | 52 | 10 |
| 2025 pseudo-OOS | 79 | 167 | 73 | 6 |
| 2026 H1 pseudo-OOS | 39 | 68 | 35 | 4 |
| Total | 453 | 941 | 419 | 34 |

There are 2.077 candidates per source-complete day and 2.246 per traded day.
The all-window candidate-count distribution is 34 dates with zero, 96 with
one, 168 with two, 111 with three, and 44 with four. The census used only
timestamps and decision-time source fields.

## Execution

Execution remains unchanged:

- executable bid/ask entry;
- 4-pip stop and 6-pip target;
- 12-hour maximum hold;
- 0.7-pip minimum spread;
- 0.1 pip adverse slippage per execution side;
- stop first when stop and target share one M5 bar;
- overlapping positions retained;
- 0.25 portfolio R per ticket.

## Profitability-first admission

Every chronological window must contain at least 50 trades, preserve a
1.35-1.75 realized payoff ratio, have PF strictly above 1.00, positive
expectancy, conditional side accuracy strictly above 50%, and daily PF
strictly above 1.00.

Overall PF must be at least 1.10. Exact oracle precision must be at least 20%
and same-side 15-minute precision at least 40%. The extra-half-pip stress PF
must remain strictly above 1.00 with positive net R. Net R must remain
positive after removing the best 5% of winners. Daily portfolio drawdown may
not exceed 20R.

The 2026 H1 last-six-month block must have at least 50 trades, positive net R,
ticket PF strictly above 1.00, and daily PF strictly above 1.00. No exact
daily-frequency gate exists.

## Forward requirement

Even a complete historical pass remains research-only. Promotion review
cannot begin before 200 new post-lock observations and six calendar months
from 2026-07-29. A failure closes this exact rule without repair.
