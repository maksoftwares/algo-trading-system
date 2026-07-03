# A1 XAU M5 Momentum Frequency-First V11 EMA-Trend Verdict

Generated: 2026-07-02  
Scope: analysis/backtest only; no demo runtime changes; no MT5 chart or preset changes.

## Why this test exists

The owner clarified that sparse strategies do not satisfy the project objective. V11 tested a broader intraday continuation family designed to produce more active-day trades:

```text
SIGNAL_M5_EMA_TREND_CONTINUATION
```

Unlike V4, this mode does not require a fresh break of a recent high/low. It requires M5 EMA trend structure, candle continuation quality, cost discipline, and optional H1/H4 trend alignment.

## Test window and method

```text
Symbol: XAUUSD
Timeframe: M5
Model: MT5 Strategy Tester exact run from project runner
Window: 2024-07-01 through 2026-06-30
Deposit: 1000 USD
Runtime touched: no
Current default signal mode changed: no
```

Artifacts:

```text
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V11_EMA_TREND_TWO_YEAR_2024_07_2026_06.md
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V11_EMA_TREND_TWO_YEAR_2024_07_2026_06.json
xau-usd/xauusd-phase1/outputs/reports/mt5_backtests/a1_momentum_variants_freq_first_v11_ema_trend_two_year_2024_07_2026_06_20260701/
```

## Result table

| Variant | Trades | WR % | Net | PF | Active days | Trades / active day | +months | -months | Top 10 removed | Top 25 removed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| V4 control: `freq_h1_h4_long_rr0p7_v4_combo_rank1` | 612 | 66.67 | +732.83 | 1.47 | 204 | 3.00 | 19 | 5 | +604.50 | +430.71 |
| V11 H1+H4 long 0.6R | 1226 | 63.87 | +175.98 | 1.05 | 247 | 4.96 | 11 | 13 | +61.76 | -93.53 |
| V11 H1+H4 both 0.6R | 1648 | 63.90 | +305.58 | 1.06 | 353 | 4.67 | 14 | 10 | +190.85 | +31.28 |
| V11 H1 long 0.6R | 1532 | 63.19 | -94.42 | 0.98 | 313 | 4.89 | 14 | 10 | -212.38 | -369.98 |
| V11 H1+H4 long 0.5R | 1353 | 67.48 | +183.95 | 1.05 | 248 | 5.46 | 10 | 14 | +82.20 | -48.31 |
| V11 H1+H4 long 0.7R | 1119 | 61.22 | +316.06 | 1.09 | 247 | 4.53 | 13 | 11 | +183.98 | +3.50 |
| V11 H1+H4 long 0.6R, V4 hour mask | 840 | 64.88 | +230.63 | 1.09 | 232 | 3.62 | 12 | 12 | +117.09 | -34.95 |
| V11 H1+H4 long strict | 933 | 63.34 | +112.77 | 1.04 | 238 | 3.92 | 12 | 12 | +6.51 | -144.11 |
| V11 no-HTF long 0.6R | 3047 | 61.90 | -572.22 | 0.94 | 535 | 5.70 | 12 | 12 | -756.41 | -917.70 |

## Verdict

```text
V11 EMA-trend continuation: REJECT_RAW_FOR_PROMOTION
```

Reason:

```text
The family creates the kind of active-day frequency the owner wants,
but the raw edge is too thin.
Best V11 PF is 1.09 versus V4 control PF 1.47.
The no-HTF version proves that frequency without enough structure becomes churn.
```

## Useful finding

V11 is not useless. It proves a broader M5 continuation engine can generate:

```text
800-1600 trades over two years
roughly 3.6-5.5 trades per active day
win rates above 60%
```

The weakness is payoff/quality, not signal count. That makes V11 suitable for a follow-up hour/session-mask diagnostic, but not for demo attachment.

## Next step

Run a V12 hour-mask diagnostic on the best V11 raw families. The goal is to test whether V11's high frequency can be kept while removing the hours that turn it into low-PF churn.

No V11 demo attachment is authorized.

