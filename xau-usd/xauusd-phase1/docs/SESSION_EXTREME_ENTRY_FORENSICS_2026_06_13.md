# Session Extreme Entry Forensics - 2026-06-13

Status: **FORENSICS_READY**

## Boundary

Research report only. No EA-T3 code, no presets, no chart changes, no orders, and no canonical Phase 2 or live-readiness change. Magic band 933200-933299 remains reserved but unused.

## Sources

- Actual broker trades: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv`
- Impulse rows: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_IMPULSE_VETO_SHADOW_ROWS.csv`
- M5 bars: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\m5_replay_bars`

## Row Counts

| Field | Value |
|---|---:|
| actual_trade_rows | 1510 |
| session_extreme_exact_rows | 127 |
| session_extreme_exact_duplicate_hidden_rows | 94 |
| same_duplicate_key_clone_rows | 94 |
| clone_inclusive_rows | 221 |
| clone_inclusive_duplicate_hidden_rows | 127 |

## Summary

| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| session_extreme_exact_raw | 127 | 127 | 0 | 39 | 79 | 30.71 | -43.43 | 0.97 | 35.51 | -18.08 |
| session_extreme_exact_duplicate_hidden | 94 | 94 | 0 | 26 | 62 | 27.66 | -299.94 | 0.70 | 27.52 | -16.38 |
| same_duplicate_key_clones | 94 | 94 | 0 | 38 | 49 | 40.43 | 925.54 | 1.77 | 55.95 | -24.50 |
| clone_inclusive_raw | 221 | 221 | 0 | 77 | 128 | 34.84 | 882.11 | 1.34 | 45.60 | -20.54 |
| clone_inclusive_duplicate_hidden | 127 | 127 | 0 | 38 | 80 | 29.92 | -89.99 | 0.94 | 35.82 | -18.14 |

## Breakdowns

### time_bucket

| time_bucket | Closed | Wins | Losses | WR | PnL AED | PF |
|---|---:|---:|---:|---:|---:|---:|
| Night 20:00-05:59 | 37 | 11 | 25 | 29.73 | -138.47 | 0.68 |
| Afternoon 12:00-15:59 | 29 | 8 | 21 | 27.59 | -128.49 | 0.59 |
| Evening 16:00-19:59 | 28 | 7 | 16 | 25.00 | -32.98 | 0.88 |

### symbol_direction

| symbol | direction | Closed | Wins | Losses | WR | PnL AED | PF |
|---|---|---:|---:|---:|---:|---:|---:|
| EURUSD | BUY | 18 | 3 | 14 | 16.67 | -190.24 | 0.24 |
| XAUUSD | BUY | 14 | 3 | 11 | 21.43 | -52.30 | 0.71 |
| XAUUSD | SELL | 20 | 7 | 13 | 35.00 | -33.42 | 0.87 |
| USDJPY | BUY | 4 | 0 | 4 | 0.00 | -12.02 | 0.00 |
| GBPUSD | BUY | 12 | 4 | 7 | 33.33 | -11.50 | 0.92 |
| USDJPY | SELL | 4 | 1 | 3 | 25.00 | -6.67 | 0.21 |
| EURUSD | SELL | 17 | 6 | 7 | 35.29 | 2.39 | 1.02 |
| GBPUSD | SELL | 5 | 2 | 3 | 40.00 | 3.82 | 1.06 |

### session_extreme_level_type

| session_extreme_level_type | Closed | Wins | Losses | WR | PnL AED | PF |
|---|---:|---:|---:|---:|---:|---:|
| session_high_retest | 48 | 10 | 36 | 20.83 | -266.06 | 0.55 |
| session_low_retest | 46 | 16 | 26 | 34.78 | -33.88 | 0.92 |

### session_level_availability

| session_level_availability | Closed | Wins | Losses | WR | PnL AED | PF |
|---|---:|---:|---:|---:|---:|---:|
| asia_and_london_levels_available | 64 | 18 | 41 | 28.12 | -173.06 | 0.73 |
| asia_level_only_available | 14 | 3 | 11 | 21.43 | -77.29 | 0.53 |
| pre_07_00_no_session_level_expected_by_source | 16 | 5 | 10 | 31.25 | -49.59 | 0.76 |

### impulse_bucket

| impulse_bucket | Closed | Wins | Losses | WR | PnL AED | PF |
|---|---:|---:|---:|---:|---:|---:|
| hard_against_lt_-1_5 | 30 | 7 | 19 | 23.33 | -114.42 | 0.63 |
| extended_with_gt_1_5 | 11 | 1 | 9 | 9.09 | -110.72 | 0.20 |
| fresh_flat_abs_lt_0_5 | 21 | 7 | 14 | 33.33 | -72.44 | 0.70 |
| mild_against_-1_5_to_-0_5 | 10 | 4 | 6 | 40.00 | -6.01 | 0.92 |
| mild_with_0_5_to_1_5 | 22 | 7 | 14 | 31.82 | 3.65 | 1.01 |

### impulse_threshold_neg_1_5

| lt_neg_1_5_shadow_action | Closed | Wins | Losses | WR | PnL AED | PF |
|---|---:|---:|---:|---:|---:|---:|
| KEEP | 64 | 19 | 43 | 29.69 | -185.52 | 0.74 |
| BLOCK | 30 | 7 | 19 | 23.33 | -114.42 | 0.63 |

### distance_from_session_open_r_bucket

| distance_from_session_open_r_bucket | Closed | Wins | Losses | WR | PnL AED | PF |
|---|---:|---:|---:|---:|---:|---:|
| 0_5_to_1R_from_session_open | 23 | 4 | 18 | 17.39 | -212.95 | 0.35 |
| gte_2R_from_session_open | 35 | 10 | 22 | 28.57 | -87.46 | 0.77 |
| 1_to_2R_from_session_open | 24 | 6 | 17 | 25.00 | -81.70 | 0.64 |
| lt_0_5R_from_session_open | 12 | 6 | 5 | 50.00 | 82.17 | 2.02 |

### clone_candidates

| candidate | Closed | Wins | Losses | WR | PnL AED | PF |
|---|---:|---:|---:|---:|---:|---:|
| breakout_retest | 15 | 4 | 10 | 26.67 | -72.61 | 0.61 |
| swing_breakout_retest_v0 | 15 | 4 | 10 | 26.67 | -27.10 | 0.84 |
| symbol_normalized_round_retest_v0_repair_v1 | 9 | 5 | 3 | 55.56 | 203.01 | 2.40 |
| symbol_normalized_round_retest_v0 | 17 | 7 | 8 | 41.18 | 216.36 | 1.85 |
| round_number_retest_v0 | 18 | 7 | 10 | 38.89 | 220.55 | 1.90 |
| session_extreme_retest_v0_repair_v1 | 20 | 11 | 8 | 55.00 | 385.33 | 2.95 |

## Worst Duplicate-Hidden Clusters

| symbol | direction | time_bucket | impulse_bucket | distance_from_session_open_r_bucket | Closed | Wins | Losses | WR | PnL AED | PF |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| EURUSD | BUY | Night 20:00-05:59 | hard_against_lt_-1_5 | 0_5_to_1R_from_session_open | 3 | 0 | 3 | 0.00 | -58.47 | 0.00 |
| EURUSD | SELL | Evening 16:00-19:59 | hard_against_lt_-1_5 | gte_2R_from_session_open | 3 | 0 | 0 | 0.00 | 0.00 | n/a |
| XAUUSD | BUY | Evening 16:00-19:59 | mild_with_0_5_to_1_5 | gte_2R_from_session_open | 3 | 1 | 2 | 33.33 | 2.99 | 1.06 |
| XAUUSD | SELL | Night 20:00-05:59 | hard_against_lt_-1_5 | 0_5_to_1R_from_session_open | 3 | 1 | 2 | 33.33 | 15.28 | 1.44 |
| XAUUSD | SELL | Afternoon 12:00-15:59 | fresh_flat_abs_lt_0_5 | gte_2R_from_session_open | 4 | 2 | 2 | 50.00 | 23.03 | 1.66 |

## Observability Gaps

- Broker-history rows do not carry the exact session-extreme label that fired; BUY implies a session-high retest and SELL implies a session-low retest, but `asia_high`, `asia_low`, `london_high`, or `london_low` is not recoverable per row.
- Distance from session open is reconstructed from exported M5 bar opens using the bar timestamp convention in the replay export; it is not an MT5 runtime field.

## Candidate Fix Hypothesis

Status: **DESIGN_INPUT_ONLY_NO_EA_T3_CODE**

Do not build EA-T3 yet. The data supports continued quarantine and a pre-registered observer rebuild that logs exact session level label plus impulse and session-open distance fields. A deployable filter is not supported until those level labels are captured and re-scored.

This is design input only. Magic band 933200-933299 remains reserved but unused.
