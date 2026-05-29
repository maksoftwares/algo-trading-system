# H1 GC/XAU Basis Reversion v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: Futures-spot relative-value convergence
Entry / decision timeframe: H1 completed-candle decision with M5 market-entry simulation
Expected median hold bars M5-equivalent: 36-216
Expected median hold hours: 3-18
Expected decisions per week: 0-12
Timeframe diversification qualifies: yes
Expected trade count per year: 80-600
Expected cost-adjusted PF: 1.00-1.45
Expected losing-month percentage: 40%-80%
Expected worst single month: -10R to -24R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many 1R losses and time stops, with occasional 1.50R convergence moves when XAU catches up to or fades excess movement versus shifted GC continuous futures. Reject if results require changing basis thresholds, H1 confirmation rules, stop, target, or time stop after first-pass evidence.

## Status

Research-only candidate. Disabled until explicitly run through the research-candidate command path.

Important audit note: this is not a breakout, retest, round-number, or support/resistance strategy. It tests a futures-versus-spot relative-value mechanism using the existing non-authoritative Yahoo `GC=F` continuous futures daily proxy. This is not primary CME order-flow data and must be labelled as proxy evidence only.

## Mechanical Definition

`h1_gc_xau_basis_reversion_v0` tests whether prior-day divergence between GC continuous futures and broker XAUUSD spot bars produces short-term H1 convergence pressure.

Data source:

- Yahoo `GC=F` daily OHLCV proxy already stored as `data/reference/futures/gc_continuous_daily_yahoo_2015_2025.csv`.
- XAUUSD D1 and H1 broker bars.
- GC and XAU daily features are shifted one observation before being merged into XAUUSD H1 bars.

Feature rules:

1. Compute prior-day GC log return.
2. Compute prior-day XAU D1 log return.
3. Compute prior-day divergence as `gc_return_1d - xau_return_1d`.
4. Compute daily GC/XAU log basis as `log(gc_close / xau_d1_close)`.
5. Compute 252-observation z-score of the shifted GC/XAU basis.

Signal rules:

1. Use completed XAUUSD H1 bars only.
2. Evaluate only H1 bars ending at 07:00, 11:00, 15:00, or 19:00 UTC.
3. Long setup:
   - prior-day GC minus XAU return >= 0.0020
   - shifted GC/XAU basis z-score >= 0.35
   - H1 candle closes bullish
   - H1 close location within candle range >= 0.56
   - H1 close is not more than 0.80 x H1 ATR14 below EMA40
4. Short setup:
   - prior-day GC minus XAU return <= -0.0020
   - shifted GC/XAU basis z-score <= -0.35
   - H1 candle closes bearish
   - H1 close location within candle range <= 0.44
   - H1 close is not more than 0.80 x H1 ATR14 above EMA40
5. Entry is simulated at market from the H1 signal close.
6. Stop is 1.10 x H1 ATR14 from entry.
7. Target is 1.50R.
8. Time stop is 18 H1 bars.
9. Maximum one signal per UTC day per direction.

## Expected Behavior

Expected trade count: moderate H1 frequency, likely 80-600 trades per year if futures-spot divergences are frequent enough.
Expected PF: at least 1.30 in 7 of 9 matrix cells if GC/XAU convergence contains usable independent signal.
Expected losing-month percentage: below 55%.
Expected worst month: no worse than -12R on fixed-notional reporting.
Expected zero-trade months: no more than 3 consecutive months.

## Why This Hypothesis Should Exist

GC futures and XAU spot should broadly track the same underlying gold price but can diverge across sessions because of futures roll, exchange-session flow, broker spot construction, funding, and liquidity timing. If the prior-day GC proxy meaningfully outpaces XAU, XAU may catch up after an H1 bullish confirmation; if XAU outpaces GC, XAU may revert after an H1 bearish confirmation. This is a relative-value convergence thesis, not a price-level retest thesis.

## What Would Falsify It

Reject v0 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gates fail
- cost-sensitivity gate fails
- max zero-trade months exceeds 3
- the GC proxy cannot cover the matrix windows
- the edge appears only in one broker window

Do not tune v0 thresholds after first-pass results. Any revisit must use a new versioned hypothesis and fresh SHA256 registration.
