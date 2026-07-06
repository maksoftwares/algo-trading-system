# Forex MT5 Frequency Portability Review - 2026-07-04

Status: PORTABILITY_FAILS_NO_NEW_FOREX_CANDIDATE

## Scope

The tuned EURUSD watchlist rule was replayed unchanged on GBPUSD and USDJPY in actual MT5 Strategy Tester: M15 RSI extreme fade, long-only, RR 0.80, fixed 0.01 lots, blocked entry hours `1,7,21`. No new symbol-specific tuning was applied.

## Results

### Full 2022-07-01 to 2026-07-02

| Symbol | Trades | PF | MT5 PF | Net | Avg/trade | Status |
|---|---:|---:|---:|---:|---:|---|
| GBPUSD | 1380 | 0.9597 | 0.96 | $-38.75 | $-0.0281 | `FREQUENT_BUT_NEGATIVE_SKIP_TUNING` |
| USDJPY | 1465 | 0.8838 | 0.89 | $-122.40 | $-0.0835 | `FREQUENT_BUT_NEGATIVE_SKIP_TUNING` |

### Older Split 2022-07-01 to 2024-06-30

| Symbol | Trades | PF | MT5 PF | Net | Avg/trade | Status |
|---|---:|---:|---:|---:|---:|---|
| GBPUSD | 676 | 1.0188 | 1.01 | $9.40 | $0.0139 | `FREQUENT_BUT_THIN_EDGE_WATCH` |
| USDJPY | 707 | 0.9602 | 0.97 | $-20.17 | $-0.0285 | `FREQUENT_BUT_NEGATIVE_SKIP_TUNING` |

### Current Split 2024-07-01 to 2026-07-02

| Symbol | Trades | PF | MT5 PF | Net | Avg/trade | Status |
|---|---:|---:|---:|---:|---:|---|
| GBPUSD | 704 | 0.8959 | 0.89 | $-48.15 | $-0.0684 | `FREQUENT_BUT_NEGATIVE_SKIP_TUNING` |
| USDJPY | 758 | 0.8128 | 0.82 | $-102.23 | $-0.1349 | `FREQUENT_BUT_NEGATIVE_SKIP_TUNING` |

## Interpretation

Portability fails. GBPUSD is near-flat in the older split but negative in the full and current windows. USDJPY is negative in every window, and the current split is materially weak. This means the tuned EURUSD lead should be treated as a single-symbol watchlist clue, not a broad Forex mean-reversion substrate.

This does not invalidate the EURUSD watchlist result, but it lowers confidence and blocks any attempt to call the rule portfolio-diversifying. The lane still needs either fresh forward evidence on EURUSD, broker/account provenance refresh, or a separate Forex family that works outside EURUSD.

## Source Reports

- full: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\forex-research\outputs\reports\mt5_backtests\mean_reversion_scout\FOREX_MT5_FREQUENCY_SCOUT_PORTABILITY_FULL_2022_2026_M15_RSI_EXTREME_LONG_BLOCKH1_7_21_RR0P8.md`
- oos_2022_2024: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\forex-research\outputs\reports\mt5_backtests\mean_reversion_scout\FOREX_MT5_FREQUENCY_SCOUT_PORTABILITY_OOS_2022_2024_M15_RSI_EXTREME_LONG_BLOCKH1_7_21_RR0P8.md`
- current_2024_2026: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\forex-research\outputs\reports\mt5_backtests\mean_reversion_scout\FOREX_MT5_FREQUENCY_SCOUT_PORTABILITY_CURRENT_2024_2026_M15_RSI_EXTREME_LONG_BLOCKH1_7_21_RR0P8.md`

## Next Gate

No symbol-specific tuning is allowed from this portability failure. Next work should either freeze the EURUSD rule for a genuinely fresh validation window, or return to frequency-first discovery with a different Forex-native family.
