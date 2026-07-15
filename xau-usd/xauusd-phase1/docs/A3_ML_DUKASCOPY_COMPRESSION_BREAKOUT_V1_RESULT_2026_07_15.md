# A3 ML Dukascopy Compression Breakout V1 Result

Date: `2026-07-15`

Classification: `DUKASCOPY_COMPRESSION_BREAKOUT_INVALID`

## Decision

Reject the V1 D1-compression/H4-breakout strategy. The frozen definition produced too few candidates for a valid experiment and the resolved trades did not show positive expectancy.

Do not loosen the compression threshold, shorten the box, remove the trend condition, change the stop or target, split the directions, or add calendar masks against this result. Any new experiment requires a separate preregistration and a genuinely different candidate premise.

## Verified Population

- Source: `72` verified Dukascopy XAUUSD raw bid/ask tick months from July 2018 through June 2024.
- Aggregated bars: `35,459` H1, `9,252` H4, and `1,548` D1.
- Candidates: `31`.
- Eligible and resolved candidates: `31` (`100.00%`).
- Long candidates: `13`.
- Short candidates: `18`.

Only `14` train, `14` validation, and `3` test trades were available. This fails the preregistered minimum of `250` total candidates and `40` resolved rows per split.

## Frozen Result

| Split | Trades | Win rate | Stress net USD | Stress PF | Average stress R | Max closed DD R | Positive months |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Train | 14 | 35.71% | -18.10 | 0.9129 | -0.0633 | 4.94 | 2/7 |
| Validation | 14 | 35.71% | 2.00 | 1.0111 | -0.0349 | 4.16 | 2/9 |
| Test | 3 | 33.33% | -6.34 | 0.8590 | -0.0705 | 1.13 | 1/3 |
| All | 31 | 35.48% | -22.44 | 0.9482 | -0.0512 | 8.38 | 5/19 |

The test set was too small for the preregistered calendar-month bootstrap. All profitability, average-R, stability, and minimum-population gates failed. The drawdown gate passed only because the strategy traded very rarely; it does not rescue the experiment.

## Interpretation

This strict two-completed-day compression followed by a first H4 trend-aligned breakout is not a viable strategy on this evidence. It is both too sparse and slightly loss-making after the frozen cost model.

The result does not establish that every breakout strategy fails. It rejects this exact family definition and prevents it from being promoted, selectively repaired, or presented as a profitable backtest.

## Authorization

No strategy promotion, Python demo prediction, EA consumption, broker action, or deployment authorization is granted.

## Next Research Direction

The next preregistered experiment should test a different source of opportunity with naturally higher sample density. A session-anchored intraday specialist is the strongest next candidate because London and New York liquidity windows provide repeated daily opportunities without reusing this failed multi-day compression premise. It must retain causal features, raw Dukascopy bid/ask replay, chronological splits, realistic costs, and untouched acceptance gates.
