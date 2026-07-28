# EURUSD Neutral Kraken/Binance multivenue-flow preregistration

Frozen before the first EURUSD outcome pass for this exact rule on
2026-07-28.

## Hypothesis

Venue-specific executed flow was too noisy on Binance alone. Kraken's actual
EUR/USD reported-side imbalance is nearly uncorrelated with Binance EURUSDT
taker imbalance. Equal-weighting the two bounded observations may preserve
common EUR demand while cancelling venue-specific noise.

Only this equal-weight multivenue rule will be tested. Kraken-only,
agreement-only, weighted, fitted, thresholded, and reversed variants are not
parallel candidates.

## Frozen direction rule

- Regime 1 Neutral dates only.
- Entries at 00:00, 00:15, 00:30, and 00:45 UTC.
- At each venue and entry, require exactly the three immediately preceding,
  consecutive, fully completed M5 bars with positive aggregate quote volume.
- Kraken score:
  `(reported buy quote volume - reported sell quote volume) / total quote volume`.
- Binance score:
  `(2 * taker-buy quote volume - total quote volume) / total quote volume`.
- Multivenue score: the unweighted mean of the two venue scores.
- Enter LONG when the multivenue score is nonnegative; otherwise SHORT.
- Never abstain; an exact zero maps to LONG.
- Exclude the entire date before outcomes if any clock is invalid at either
  venue.
- Do not change venue weights, side mappings, horizon, clock, sign,
  agreement requirement, or threshold after outcomes.

## Outcome-blind census

| Window | Eligible Neutral dates | Forced trades |
|---|---:|---:|
| 2020-2021 development | 133 | 532 |
| 2022-2023 validation | 140 | 560 |
| 2024 validation | 62 | 248 |
| 2025 pseudo-OOS | 79 | 316 |
| 2026 H1 pseudo-OOS | 39 | 156 |
| Total | 453 | 1,812 |

Every retained date has exactly four decisions. The census read timestamps
and decision-time source fields only.

## Frozen execution and admission

Execution remains the locked EURUSD label contract:

- executable bid/ask entry;
- 4-pip stop and 6-pip target;
- 12-hour maximum hold;
- 0.7-pip minimum spread;
- 0.1 pip adverse slippage per execution side;
- stop first when stop and target share one M5 bar;
- overlapping positions retained;
- 0.25 portfolio R per ticket.

Every chronological window must have at least 120 trades, 45%-55% win rate,
1.35-1.75 realized payoff, PF at least 1.10, positive expectancy, at least
70% conditional side accuracy, daily PF at least 1.10, and exactly four
trades per eligible date.

Overall gates remain PF 1.30, exact oracle precision 40%, same-side
15-minute precision 45%, stressed PF 1.15 with positive net, positive net
after removing the best 5% of winners, and daily portfolio drawdown no more
than 20R.

## Evidence status

The Kraken flow archive is new, but earlier EURUSD outcomes and the rejected
Binance rule were already inspected. This is therefore adaptive historical
research with a fully frozen mechanics test, not pristine out-of-sample
evidence. A historical pass cannot authorize broker action and would still
require at least 400 new observations and six post-lock months beginning
2026-07-29.
