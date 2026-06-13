# Phase 2 Impulse Veto Shadow Report

Status: `SHADOW_READY`

Shadow-only impulse-veto evidence. Reads broker-trade CSV and exported M5 bars only; does not read or modify terminals, charts, presets, orders, positions, or running EAs.

## Boundary

- Shadow-only analysis.
- No terminal, chart, preset, order, position, or running-EA changes.
- Applies only to weak families: `round_retest_family` and `session_extreme_family`.
- `breakout_retest_family` is scored as a control and is not blocked by this rule.

## Sources

- Actual trades CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv`
- M5 bars dir: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\m5_replay_bars`
- Hypothesis doc: `docs/FORWARD_WEEK_IMPULSE_VETO_HYPOTHESIS_2026_06_15.md`

## Row Counts

| Metric | Value |
|---|---:|
| raw_rows | 1510 |
| closed_rows | 1502 |
| resolved_closed_rows | 1502 |
| target_resolved_closed_rows | 1065 |
| unresolved_rows | 0 |

## Bar Export Quality

| symbol | status | rows | first_bar_utc | last_bar_utc | gap_count_gt_5m | max_gap_minutes | duplicate_bar_times |
|---|---|---|---|---|---|---|---|
| EURUSD | WARN_GAPS_OR_DUPLICATES | 2836 | 2026-06-01 00:00:00 | 2026-06-12 20:55:00 | 9 | 2885.0000 | 0 |
| GBPUSD | WARN_GAPS_OR_DUPLICATES | 2836 | 2026-06-01 00:00:00 | 2026-06-12 20:55:00 | 9 | 2885.0000 | 0 |
| USDJPY | WARN_GAPS_OR_DUPLICATES | 2702 | 2026-06-01 00:00:00 | 2026-06-12 09:45:00 | 9 | 2885.0000 | 0 |
| XAUUSD | WARN_GAPS_OR_DUPLICATES | 2736 | 2026-06-01 00:00:00 | 2026-06-12 20:55:00 | 9 | 2945.0000 | 0 |

## Dose Response - All Resolved Closed Rows

| bucket | closed | wins | losses | win_rate_pct | closed_pnl_aed | avg_pnl_aed | profit_factor |
|---|---|---|---|---|---|---|---|
| hard_against_lt_-1_5 | 387 | 110 | 263 | 28.42 | -3254.0200 | -8.4083 | 0.5711 |
| mild_against_-1_5_to_-0_5 | 246 | 86 | 160 | 34.96 | 410.8400 | 1.6701 | 1.0939 |
| fresh_flat_abs_lt_0_5 | 309 | 109 | 193 | 35.28 | -1348.0700 | -4.3627 | 0.7458 |
| mild_with_0_5_to_1_5 | 215 | 91 | 120 | 42.33 | 832.1600 | 3.8705 | 1.2734 |
| extended_with_gt_1_5 | 345 | 140 | 197 | 40.58 | 1395.2200 | 4.0441 | 1.2835 |

## Threshold Scoreboard - Target Families

| Threshold | Baseline PnL | Kept PnL | Blocked PnL | Delta | Kept Share | Dedup Baseline | Dedup Kept | Dedup Blocked | Dedup Delta |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| -1.0 | -2392.7300 | 1400.2000 | -3792.9300 | 3792.9300 | 66.85 | -2059.5100 | 73.1500 | -2132.6600 | 2132.6600 |
| -1.5 | -2392.7300 | 744.5500 | -3137.2800 | 3137.2800 | 75.12 | -2059.5100 | -545.6700 | -1513.8400 | 1513.8400 |
| -2.0 | -2392.7300 | -487.5200 | -1905.2100 | 1905.2100 | 81.69 | -2059.5100 | -1080.0000 | -979.5100 | 979.5100 |

## Threshold Scoreboard By Family

| family | Threshold | Closed | Kept | Blocked | Baseline PnL | Kept PnL | Blocked PnL | Delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| round_retest_family | -1.0 | 918 | 616 | 302 | -2734.6300 | 1115.3300 | -3849.9600 | 3849.9600 |
| round_retest_family | -1.5 | 918 | 695 | 223 | -2734.6300 | 330.4800 | -3065.1100 | 3065.1100 |
| round_retest_family | -2.0 | 918 | 756 | 162 | -2734.6300 | -931.2400 | -1803.3900 | 1803.3900 |
| session_extreme_family | -1.0 | 147 | 96 | 51 | 341.9000 | 284.8700 | 57.0300 | -57.0300 |
| session_extreme_family | -1.5 | 147 | 105 | 42 | 341.9000 | 414.0700 | -72.1700 | 72.1700 |
| session_extreme_family | -2.0 | 147 | 114 | 33 | 341.9000 | 443.7200 | -101.8200 | 101.8200 |

## Breakout Control

| Metric | Value |
|---|---:|
| closed | 430 |
| wins | 153 |
| losses | 269 |
| win_rate_pct | 35.58 |
| closed_pnl_aed | 459.2200 |
| avg_pnl_aed | 1.0680 |
| profit_factor | 1.0896 |

## Notes

- ret12_atr = (last closed M5 close - close 12 completed M5 bars earlier) / ATR14.
- impulse_alignment = direction_sign * ret12_atr; negative values mean the trade fights the latest impulse.
- Thresholds are pre-registered for weak families only: round_retest_family and session_extreme_family.
- Open trades are enriched in the row CSV but excluded from threshold PnL scoreboards.
- Duplicate rows are retained in the raw row export; scoreboard rows also include duplicate-hidden summaries.
