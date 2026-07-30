# EURUSD high-frequency regime stability audit

Status: `REGIME_ROUTER_CANNOT_RESCUE_FREQUENCY_SLEEVE`

This diagnostic asks whether the rejected 635-trade M15 frequency sleeve can be repaired by routing its trades through the already causal five-state regime labels. It cannot. The apparent full-period edge is entirely concentrated in the first chronological year and deteriorates across almost every regime in the second year.

This is retrospective diagnostic evidence, not a new holdout and not a portfolio-selection authorization.

## Normalization

- Source: exact 2024-07-01 through 2026-06-30 Capital.com M15 trade ledger.
- M15 overlay trades are normalized from 0.02 to the executable 0.01-lot core, so H4 overlay sizing cannot masquerade as an independent expert.
- Regime labels use only the already causal, lagged state assigned in `TRADES_WITH_CAUSAL_REGIME.csv`.
- A weekday frequency denominator is used rather than “active dates.”

## Whole M15 sleeve

| Window | Trades | Trades/weekday | Net at 0.01 lot | PF | Best 5% removed PF |
|---|---:|---:|---:|---:|---:|
| Full two years | 635 | 1.216 | $73.00 | 1.2533 | 1.0121 |
| First 12 months | 269 | 1.031 | $92.90 | 1.9044 | 1.5396 |
| Second 12 months | 364 | 1.395 | -$19.79 | 0.8928 | 0.7334 |

At an additional 0.5 pip round trip, the full normalized sleeve falls to PF 1.1369 and its best-5%-removed PF falls to 0.9115.

The frequency rose in the losing year. This is not a shortage of signals; it is a loss of conditional expectancy.

## Regime stability

| Causal regime | Full trades | Full PF | First-12 PF | Second-12 PF | Second-12 net conclusion |
|---|---:|---:|---:|---:|---|
| Joint Compression | 248 | 1.2132 | 1.4092 | 1.0231 | nearly flat |
| Neutral | 113 | 1.3471 | 2.9216 | 0.7552 | losing |
| Shock | 151 | 1.3144 | 2.9210 | 0.8029 | losing |
| USD Down | 43 | 0.9925 | 1.3759 | 0.7861 | losing |
| USD Up | 80 | 1.2536 | 1.3666 | 1.1856 | modestly positive but sparse |

The strongest full-period regimes—Neutral, Shock, and USD Up—still produce 214 trades, PF 0.8510, and -$17.82 in the second chronological year. Excluding only USD Down preserves 1.303 trades per weekday in that year but still produces PF 0.9020 and -$16.65.

USD Up is the only state that remains positive in the second year. It supplies only 51 trades, about 0.195 per weekday. Adding the low-frequency H4 control cannot lift that to the required portfolio frequency.

## Why a router does not solve the goal

The edge change is broad rather than isolated to one bad state:

1. Neutral and Shock created most of the first-year profit and both became materially negative.
2. Joint Compression degraded to essentially break-even.
3. USD Down remained unusable.
4. Retaining only USD Up sacrifices roughly 84% of M15 trades.

A post-hoc router can make the two-year aggregate look cleaner, but it cannot be justified by chronological stability. A trailing health gate could eventually switch the sleeve off after losses appear, but then it necessarily loses the one-trade-per-day frequency. This is the exact frequency/edge tradeoff blocking the current goal.

## Decision

Do not implement or deploy a regime-filtered version of this M15 sleeve from these outcomes. Continue protecting the admitted H4 short-chop expert and require a genuinely independent high-frequency mechanism or new prospective evidence before adding orders.

