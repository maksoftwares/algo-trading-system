# A1 XAU M5 Momentum Frequency-First V10 Opening-Range Verdict

Generated: 2026-07-02  
Scope: analysis/backtest only; no demo runtime changes; no MT5 chart or preset changes.

## Why this test exists

The owner clarified that a strategy with only a handful of trades in a month does not satisfy the project goal. The goal is not just a high profit factor from rare setups; the system needs enough intraday opportunities to realistically produce daily/near-daily profit attempts.

V10 therefore tested a new default-off signal family:

```text
SIGNAL_OPENING_RANGE_CONTINUATION
```

The idea was to use London/New York/Asia opening-range breaks as a higher-frequency continuation family.

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
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V10_OPENING_RANGE_TWO_YEAR_2024_07_2026_06.md
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V10_OPENING_RANGE_TWO_YEAR_2024_07_2026_06.json
xau-usd/xauusd-phase1/outputs/reports/mt5_backtests/a1_momentum_variants_freq_first_v10_opening_range_two_year_2024_07_2026_06_20260701/
```

## Result table

| Variant | Trades | WR % | Net | PF | Active days | Trades / active day | +months | -months | Top 10 winners removed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| V4 control: `freq_h1_h4_long_rr0p7_v4_combo_rank1` | 612 | 66.67 | +732.83 | 1.47 | 204 | 3.00 | 19 | 5 | +604.50 |
| V10 London H1+H4 long 0.6R | 373 | 59.79 | -68.28 | 0.94 | 124 | 3.01 | 9 | 12 | -164.19 |
| V10 London H1+H4 both 0.6R | 534 | 62.73 | +164.41 | 1.10 | 181 | 2.95 | 12 | 12 | +58.46 |
| V10 London H1 long 0.6R | 484 | 59.71 | -132.74 | 0.91 | 163 | 2.97 | 9 | 15 | -234.38 |
| V10 London H1+H4 long 0.5R | 408 | 62.99 | -99.91 | 0.91 | 124 | 3.29 | 11 | 10 | -181.00 |
| V10 NY H1+H4 long 0.6R | 176 | 63.64 | +39.83 | 1.07 | 95 | 1.85 | 13 | 8 | -74.56 |
| V10 NY H1+H4 both 0.6R | 245 | 60.41 | -41.81 | 0.95 | 130 | 1.88 | 13 | 11 | -156.95 |
| V10 Asia H1+H4 long 0.6R | 355 | 64.79 | +98.86 | 1.11 | 120 | 2.96 | 14 | 9 | -0.92 |

## Verdict

```text
V10 opening-range continuation: REJECT_FOR_PROMOTION
```

Reason:

```text
The family creates a usable number of trades on active days, but the edge is too weak.
No V10 variant beats the V4 control.
Best V10 PF is 1.11 versus V4 PF 1.47.
Several V10 variants become negative after removing top winners.
```

This is important because it separates two problems:

```text
Sparse candidates are rejected for low frequency.
Opening-range V10 is rejected for weak profitability.
```

## Frequency assessment

V10 does not suffer from the "two trades in a month" problem. The London variants produced hundreds of trades and around three trades per active day. However, the active-day coverage is still not enough to claim "multiple trades every day", and the profitability does not justify promotion.

The current best candidate remains V4-style break-and-run momentum:

```text
freq_h1_h4_long_rr0p7_v4_combo_rank1
```

But even V4 should not be described as fully satisfying the owner's long-term goal yet. It produces about three trades per active day, not guaranteed daily trading.

## Next research implication

The next family should not be another rare setup, and it should not be another opening-range clone. The project now needs one of:

```text
1. A higher-frequency V4-compatible companion signal that keeps PF >= 1.25.
2. A portfolio of independent intraday modules whose combined daily coverage is high.
3. A separate instrument/timeframe with structurally higher signal frequency and lower cost drag.
```

No demo attachment is authorized from V10.

