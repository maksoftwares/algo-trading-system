# USDJPY H4 Carry-Regime Diagnostic - 2026-07-03

Status: DIAGNOSTIC_ONLY_NOT_A_SURVIVOR

Boundary: offline research only. No MT5 runtime, demo terminal, chart, preset, EA, order, position, or XAU lane was touched.

## Why This Exists

The first USDJPY H4 trend-pullback v0 screen failed overall after cross-venue expansion:

- 917 trades
- PF 1.0159
- +7.77R total net
- 48.56R max drawdown
- Pepperstone 2019-2021 negative

The long-only and session split showed a structured pocket worth recording as a clue for a new hypothesis, not as a tuned survivor.

## Long-Only Asia/NY-Morning Diagnostic

Filter applied after the v0 diagnostic read:

- Direction: LONG only
- Sessions: Asia and NY morning only
- Source: `forex-research/outputs/tables/usdjpy_h4_trend_continuation_pullback_v0_TRADES_2026_07_03.csv`

| Scope | Trades | Net R | Expectancy R | PF | Max DD R | Positive months |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Overall | 366 | +48.81 | +0.1333 | 1.2844 | 12.01 | 37/74 |
| Capital.com | 225 | +36.84 | +0.1637 | 1.3607 | 7.74 | 45/73 |
| Dukascopy | 91 | +18.31 | +0.2012 | 1.4767 | 4.56 | 17/28 |
| Pepperstone | 50 | -6.34 | -0.1269 | 0.7956 | 11.17 | 8/18 |

## Read

Reject as an immediate candidate. The positive result depends on excluding shorts and weak sessions after the first screen, and it fails the 2019-2021 Pepperstone window. The plausible explanation is a USDJPY carry/rate-divergence regime effect that strengthened after 2022, not a stable all-regime price-pattern edge.

Next valid step is a new pre-registered hypothesis with explicit regime input or refreshed data. Do not attach a demo EA from this diagnostic.
