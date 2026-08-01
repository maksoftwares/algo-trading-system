# Frequency Hunt Result

Date: 2026-08-01
Status: **`FREQUENCY_ACHIEVED_EDGE_DOES_NOT_EXIST`**

## Target vs achieved

| | Required | Achieved |
|---|---:|---:|
| Trades per active day | ≥ 1.00 | **7.60** |

The frequency requirement is comfortably met by portfolio breadth — 12 diverse
members drawn from 830 configurations that independently cleared design and
validation. No entry rule was loosened to get there.

## But the edge was never there to maintain

| Window | Portfolio | Buy & hold | |
|---|---:|---:|---|
| design 2016–2019 | +21.73% | **+59.77%** | loses |
| validation 2020–2021 | +18.18% | **+47.57%** | loses |
| **holdout 2022–2023** | **−14.95%** | −0.31% | loses |
| broker 2025-08→2026-07 | +9.39% | **+25.16%** | loses |

**The portfolio loses to simply holding the index in all four windows**,
including the two it was selected on.

## The cause, in one number

Of the 830 configurations that cleared both the design and validation gates,
**828 are long-only — 99.8%**.

The gates were PF ≥ 1.10 on 2016–2019 and PF ≥ 1.05 on 2020–2021. Both windows
rose hard (+59.77% and +47.57%). Any rule with a long bias therefore cleared
them, regardless of whether it had predictive content. The filter was not
selecting for edge; it was selecting for **long exposure to a rising market** —
and a strictly worse version of it, because it captures a fraction of the move
while paying spread on 7.6 trades a day.

The holdout contains 2022. Long bias stops paying, and the portfolio drops to
PF 0.886.

## Consistency with the mega-search

This is the same finding, reached independently. All 28 three-stage survivors of
the 14,400-attempt search were also long-only, and the null run produced 29
survivors with a *higher* median holdout profit factor. Two different assembly
methods, one conclusion.

## What this closes

Chasing frequency was worth doing and the mechanism works — breadth reaches
7.6 trades/day cleanly. The obstacle is not frequency and never was. There is no
edge in this search space to spread across more trades, so raising frequency
raises cost and drawdown against a return that was market beta all along.

Adding members, loosening gates, or re-tuning stops cannot fix a pool that is
99.8% long-only in bull-market windows. The fix would be a qualification window
containing a bear market — but 2022 is the holdout, and spending it on selection
would leave nothing to test against.

**Recommendation: do not deploy.** Anyone wanting this exposure can buy the index
and keep the spread.
