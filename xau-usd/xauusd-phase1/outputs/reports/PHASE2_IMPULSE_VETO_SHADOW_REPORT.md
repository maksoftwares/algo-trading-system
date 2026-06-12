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
| raw_rows | 1372 |
| closed_rows | 1356 |
| resolved_closed_rows | 1356 |
| target_resolved_closed_rows | 949 |
| unresolved_rows | 0 |

## Bar Export Quality

| symbol | status | rows | first_bar_utc | last_bar_utc | gap_count_gt_5m | max_gap_minutes | duplicate_bar_times |
|---|---|---|---|---|---|---|---|
| EURUSD | WARN_GAPS_OR_DUPLICATES | 2696 | 2026-06-01 00:00:00 | 2026-06-12 09:15:00 | 9 | 2885.0000 | 0 |
| GBPUSD | WARN_GAPS_OR_DUPLICATES | 2696 | 2026-06-01 00:00:00 | 2026-06-12 09:15:00 | 9 | 2885.0000 | 0 |
| USDJPY | WARN_GAPS_OR_DUPLICATES | 1611 | 2026-06-01 00:00:00 | 2026-06-08 14:30:00 | 5 | 2885.0000 | 0 |
| XAUUSD | WARN_GAPS_OR_DUPLICATES | 2596 | 2026-06-01 00:00:00 | 2026-06-12 09:15:00 | 9 | 2945.0000 | 0 |

## Dose Response - All Resolved Closed Rows

| bucket | closed | wins | losses | win_rate_pct | closed_pnl_aed | avg_pnl_aed | profit_factor |
|---|---|---|---|---|---|---|---|
| hard_against_lt_-1_5 | 351 | 101 | 236 | 28.77 | -2681.2900 | -7.6390 | 0.6029 |
| mild_against_-1_5_to_-0_5 | 218 | 84 | 134 | 38.53 | 1216.2300 | 5.5790 | 1.3460 |
| fresh_flat_abs_lt_0_5 | 272 | 103 | 162 | 37.87 | -493.9100 | -1.8158 | 0.8833 |
| mild_with_0_5_to_1_5 | 193 | 76 | 113 | 39.38 | 493.7000 | 2.5580 | 1.1728 |
| extended_with_gt_1_5 | 322 | 135 | 179 | 41.93 | 1527.2000 | 4.7429 | 1.3435 |

## Threshold Scoreboard - Target Families

| Threshold | Baseline PnL | Kept PnL | Blocked PnL | Delta | Kept Share | Dedup Baseline | Dedup Kept | Dedup Blocked | Dedup Delta |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| -1.0 | -776.7100 | 2222.2400 | -2998.9500 | 2998.9500 | 66.91 | -1378.7700 | 416.6800 | -1795.4500 | 1795.4500 |
| -1.5 | -776.7100 | 2044.0800 | -2820.7900 | 2820.7900 | 75.03 | -1378.7700 | 45.9900 | -1424.7600 | 1424.7600 |
| -2.0 | -776.7100 | 1189.7000 | -1966.4100 | 1966.4100 | 80.93 | -1378.7700 | -387.6100 | -991.1600 | 991.1600 |

## Threshold Scoreboard By Family

| family | Threshold | Closed | Kept | Blocked | Baseline PnL | Kept PnL | Blocked PnL | Delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| round_retest_family | -1.0 | 811 | 543 | 268 | -1285.0600 | 1862.7800 | -3147.8400 | 3147.8400 |
| round_retest_family | -1.5 | 811 | 611 | 200 | -1285.0600 | 1555.4200 | -2840.4800 | 2840.4800 |
| round_retest_family | -2.0 | 811 | 658 | 153 | -1285.0600 | 671.3900 | -1956.4500 | 1956.4500 |
| session_extreme_family | -1.0 | 138 | 92 | 46 | 508.3500 | 359.4600 | 148.8900 | -148.8900 |
| session_extreme_family | -1.5 | 138 | 101 | 37 | 508.3500 | 488.6600 | 19.6900 | -19.6900 |
| session_extreme_family | -2.0 | 138 | 110 | 28 | 508.3500 | 518.3100 | -9.9600 | 9.9600 |

## Breakout Control

| Metric | Value |
|---|---:|
| closed | 400 |
| wins | 147 |
| losses | 245 |
| win_rate_pct | 36.75 |
| closed_pnl_aed | 869.0000 |
| avg_pnl_aed | 2.1725 |
| profit_factor | 1.1896 |

## Notes

- ret12_atr = (last closed M5 close - close 12 completed M5 bars earlier) / ATR14.
- impulse_alignment = direction_sign * ret12_atr; negative values mean the trade fights the latest impulse.
- Thresholds are pre-registered for weak families only: round_retest_family and session_extreme_family.
- Open trades are enriched in the row CSV but excluded from threshold PnL scoreboards.
- Duplicate rows are retained in the raw row export; scoreboard rows also include duplicate-hidden summaries.
