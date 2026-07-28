# EURUSD Neutral Coinbase stablecoin-flow preregistration

This contract will be hash-locked before the first EURUSD outcome or oracle
pass for this exact Coinbase rule.

## Hypothesis

Coinbase's `USDC-EUR` and `USDT-EUR` order books reflect euro demand against
two independently funded dollar stablecoins. A short, volume-weighted
candle-direction consensus may capture euro buying or selling pressure that
is not present in price-only EURUSD bars or in the previously tested Kraken
and Binance sources.

The prices of the two products are strongly related, but their
volume-weighted pressure correlation is only 0.374. This campaign tests one
agreement rule without a magnitude threshold, product weighting, model,
clock selection, or subgroup.

## Frozen decision rule

- Start from the existing four first-hour Neutral decision opportunities from
  2022 through June 2026.
- At each Coinbase product and decision, require the three immediately
  preceding consecutive completed M5 candles.
- Require positive aggregate base volume at both products.
- For each product calculate
  `-sum(sign(close-open) * base_volume) / sum(base_volume)`.
- The minus sign converts stablecoin/EUR price direction to EURUSD direction:
  a falling stablecoin/EUR candle indicates a strengthening euro.
- If both pressures are nonnegative, enter LONG EURUSD.
- If both are negative, enter SHORT EURUSD.
- If the signs disagree or either source is invalid, remain in CASH.
- Use no magnitude threshold, product weight, daily quota, or model.

The source is allowed to produce zero through four trades on a Neutral date.
Missing candles are never filled.

## Outcome-blind census

| Window | Source dates | Both-product valid points | Agreement trades | Traded dates | Trades/source date |
|---|---:|---:|---:|---:|---:|
| 2022-2023 development | 149 | 279 | 166 | 83 | 1.114 |
| 2024 validation | 66 | 264 | 169 | 65 | 2.561 |
| 2025 pseudo-OOS | 80 | 295 | 194 | 76 | 2.425 |
| 2026 H1 pseudo-OOS | 39 | 125 | 85 | 36 | 2.179 |
| Overall | 334 | 963 | 614 | 260 | 1.838 |

There are 373 invalid/missing product decisions and 349 valid sign
disagreements. The 614 selected candidates are 49.35% LONG. The daily
candidate distribution across all 334 source dates is 74 dates with zero, 48
with one, 99 with two, 84 with three, and 29 with four. No EURUSD outcome or
oracle field was loaded for this census.

## Execution and admission

Execution remains the locked executable bid/ask contract: 4-pip stop, 6-pip
target, 12-hour maximum hold, 0.7-pip spread floor, 0.1 pip adverse slippage
per execution side, stop-first same-bar handling, overlapping positions, and
0.25 portfolio R per ticket.

Every chronological window requires at least 50 trades, 1.35-1.75 realized
payoff, positive expectancy, ticket and daily PF strictly above 1.00, and
conditional direction accuracy strictly above 50%.

Overall PF must reach 1.15, exact oracle precision 25%, and same-side
15-minute precision 45%. The strategy must remain positive with PF above
1.00 after an extra half pip, remain positive after removing the best 5% of
winners, and keep daily portfolio drawdown at or below 20R.

The last six months require at least 50 trades, positive net R, and ticket and
daily PF above 1.00. No exact daily-frequency gate exists.

## Evidence status

The Coinbase source is new and was acquired without EURUSD outcomes. Existing
EURUSD history has nevertheless been inspected by earlier campaigns, so a
historical pass remains adaptive research and would require 200 new
observations and six post-lock months beginning 2026-07-29.
