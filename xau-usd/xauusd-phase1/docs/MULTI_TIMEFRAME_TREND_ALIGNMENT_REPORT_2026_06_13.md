# Multi-Timeframe Trend Alignment Report - 2026-06-13

Status: **TREND_ALIGNMENT_READY**

## Boundary

Research report only. Reads broker-history and exported OHLC bars; does not modify MT5 terminals, EAs, presets, orders, positions, or Phase 2 canonical status.

## Trend Definition

For each H1/H4 timeframe, use the latest completed bar at entry time. Trend is UP when that close is above its 20-bar simple moving average, DOWN when below, and FLAT when equal. BUY/LONG aligned with UP and SELL/SHORT aligned with DOWN are tagged WITH_TREND; the opposite side is AGAINST_TREND.

T12 exported M5/H1/H4/D1 bars. This T16 analysis scores H1 and H4, per the requested with-trend vs against-trend split; D1 coverage is recorded as context and is not used for a trading rule.

## Sources

- Actual broker trades: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv`
- H1/H4 bars: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\m5_replay_bars`

## Row Counts

| Field | Value |
|---|---:|
| actual_trade_rows | 1510 |
| closed_duplicate_hidden_rows | 792 |
| trend_tags | 1584 |
| resolved_trend_tags | 1458 |
| unresolved_trend_tags | 126 |

## Bar Coverage

### H1

| Symbol | Rows | First Bar End UTC | Last Bar End UTC |
|---|---:|---|---|
| EURUSD | 237 | 2026-06-01 01:00:00 | 2026-06-12 21:00:00 |
| GBPUSD | 237 | 2026-06-01 01:00:00 | 2026-06-12 21:00:00 |
| USDJPY | 237 | 2026-06-01 01:00:00 | 2026-06-12 21:00:00 |
| XAUUSD | 228 | 2026-06-01 01:00:00 | 2026-06-12 21:00:00 |

### H4

| Symbol | Rows | First Bar End UTC | Last Bar End UTC |
|---|---:|---|---|
| EURUSD | 61 | 2026-06-01 04:00:00 | 2026-06-13 00:00:00 |
| GBPUSD | 61 | 2026-06-01 04:00:00 | 2026-06-13 00:00:00 |
| USDJPY | 61 | 2026-06-01 04:00:00 | 2026-06-13 00:00:00 |
| XAUUSD | 61 | 2026-06-01 04:00:00 | 2026-06-13 00:00:00 |

### D1 Context

| Symbol | Rows | First Bar End UTC | Last Bar End UTC |
|---|---:|---|---|
| EURUSD | 11 | 2026-06-02 00:00:00 | 2026-06-13 00:00:00 |
| GBPUSD | 11 | 2026-06-02 00:00:00 | 2026-06-13 00:00:00 |
| USDJPY | 11 | 2026-06-02 00:00:00 | 2026-06-13 00:00:00 |
| XAUUSD | 11 | 2026-06-02 00:00:00 | 2026-06-13 00:00:00 |

## Overall Alignment

| timeframe | trend_alignment | Closed | Wins | Losses | WR | PnL AED | PF |
|---|---|---:|---:|---:|---:|---:|---:|
| H1 | AGAINST_TREND | 351 | 89 | 253 | 25.36 | -3084.27 | 0.53 |
| H1 | WITH_TREND | 431 | 178 | 246 | 41.30 | 973.55 | 1.16 |
| H4 | AGAINST_TREND | 294 | 95 | 196 | 32.31 | -1680.89 | 0.69 |
| H4 | WITH_TREND | 382 | 133 | 236 | 34.82 | -362.15 | 0.94 |

## Family Alignment

| family | timeframe | trend_alignment | Closed | Wins | Losses | WR | PnL AED | PF |
|---|---|---|---:|---:|---:|---:|---:|---:|
| breakout_retest_family | H4 | AGAINST_TREND | 70 | 24 | 46 | 34.29 | -204.84 | 0.75 |
| breakout_retest_family | H1 | AGAINST_TREND | 98 | 33 | 65 | 33.67 | -93.77 | 0.91 |
| breakout_retest_family | H4 | WITH_TREND | 133 | 44 | 85 | 33.08 | -76.02 | 0.96 |
| breakout_retest_family | H1 | WITH_TREND | 144 | 52 | 88 | 36.11 | 65.19 | 1.04 |
| round_retest_family | H1 | AGAINST_TREND | 215 | 51 | 160 | 23.72 | -2609.50 | 0.48 |
| round_retest_family | H4 | AGAINST_TREND | 197 | 64 | 131 | 32.49 | -1301.30 | 0.70 |
| round_retest_family | H4 | WITH_TREND | 211 | 80 | 127 | 37.91 | -153.41 | 0.96 |
| round_retest_family | H1 | WITH_TREND | 231 | 107 | 122 | 46.32 | 950.20 | 1.26 |
| session_extreme_family | H1 | AGAINST_TREND | 36 | 5 | 26 | 13.89 | -307.00 | 0.33 |
| session_extreme_family | H4 | WITH_TREND | 38 | 9 | 24 | 23.68 | -132.72 | 0.67 |
| session_extreme_family | H4 | AGAINST_TREND | 25 | 7 | 17 | 28.00 | -100.75 | 0.70 |
| session_extreme_family | H1 | WITH_TREND | 56 | 19 | 36 | 33.93 | -41.84 | 0.92 |
| wr50_family | H1 | AGAINST_TREND | 2 | 0 | 2 | 0.00 | -74.00 | 0.00 |
| wr50_family | H4 | AGAINST_TREND | 2 | 0 | 2 | 0.00 | -74.00 | 0.00 |

## Candidate Alignment

| candidate | timeframe | trend_alignment | Closed | Wins | Losses | WR | PnL AED | PF |
|---|---|---|---:|---:|---:|---:|---:|---:|
| WR50_BreakoutEvening_v0 | H1 | AGAINST_TREND | 2 | 0 | 2 | 0.00 | -74.00 | 0.00 |
| WR50_BreakoutEvening_v0 | H4 | AGAINST_TREND | 2 | 0 | 2 | 0.00 | -74.00 | 0.00 |
| breakout_retest | H4 | AGAINST_TREND | 67 | 23 | 44 | 34.33 | -202.57 | 0.75 |
| breakout_retest | H1 | AGAINST_TREND | 91 | 32 | 59 | 35.16 | -76.18 | 0.92 |
| breakout_retest | H4 | WITH_TREND | 122 | 41 | 77 | 33.61 | -44.88 | 0.97 |
| breakout_retest | H1 | WITH_TREND | 135 | 48 | 83 | 35.56 | 19.06 | 1.01 |
| p2weakness_br_v1 | H1 | AGAINST_TREND | 1 | 0 | 1 | 0.00 | -14.44 | 0.00 |
| p2weakness_br_v1 | H4 | WITH_TREND | 1 | 0 | 1 | 0.00 | -14.44 | 0.00 |
| round_number_retest_v0 | H1 | WITH_TREND | 3 | 1 | 2 | 33.33 | 11.76 | 1.38 |
| round_number_retest_v0 | H4 | WITH_TREND | 3 | 1 | 2 | 33.33 | 11.76 | 1.38 |
| session_extreme_retest_v0 | H1 | AGAINST_TREND | 36 | 5 | 26 | 13.89 | -307.00 | 0.33 |
| session_extreme_retest_v0 | H4 | WITH_TREND | 38 | 9 | 24 | 23.68 | -132.72 | 0.67 |
| session_extreme_retest_v0 | H4 | AGAINST_TREND | 25 | 7 | 17 | 28.00 | -100.75 | 0.70 |
| session_extreme_retest_v0 | H1 | WITH_TREND | 56 | 19 | 36 | 33.93 | -41.84 | 0.92 |
| swing_breakout_retest_v0 | H4 | WITH_TREND | 10 | 3 | 7 | 30.00 | -16.70 | 0.68 |
| swing_breakout_retest_v0 | H1 | AGAINST_TREND | 6 | 1 | 5 | 16.67 | -3.15 | 0.90 |
| swing_breakout_retest_v0 | H4 | AGAINST_TREND | 3 | 1 | 2 | 33.33 | -2.27 | 0.71 |
| swing_breakout_retest_v0 | H1 | WITH_TREND | 9 | 4 | 5 | 44.44 | 46.13 | 2.53 |
| symbol_normalized_round_retest_v0 | H1 | AGAINST_TREND | 215 | 51 | 160 | 23.72 | -2609.50 | 0.48 |
| symbol_normalized_round_retest_v0 | H4 | AGAINST_TREND | 197 | 64 | 131 | 32.49 | -1301.30 | 0.70 |
| symbol_normalized_round_retest_v0 | H4 | WITH_TREND | 207 | 79 | 124 | 38.16 | -142.94 | 0.96 |
| symbol_normalized_round_retest_v0 | H1 | WITH_TREND | 227 | 106 | 119 | 46.70 | 960.67 | 1.27 |
| symbol_normalized_round_retest_v0_repair_v1 | H1 | WITH_TREND | 1 | 0 | 1 | 0.00 | -22.23 | 0.00 |
| symbol_normalized_round_retest_v0_repair_v1 | H4 | WITH_TREND | 1 | 0 | 1 | 0.00 | -22.23 | 0.00 |

## Unresolved Context

| timeframe | trend_status | Closed | Wins | Losses | WR | PnL AED | PF |
|---|---|---:|---:|---:|---:|---:|---:|
| H1 | UNRESOLVED_NO_BAR_CONTEXT | 10 | 5 | 5 | 50.00 | -45.86 | 0.69 |
| H4 | UNRESOLVED_NO_BAR_CONTEXT | 116 | 44 | 72 | 37.93 | -113.54 | 0.91 |

## Findings

- H1: WITH_TREND minus AGAINST_TREND closed PnL delta = 4057.82 AED (431 with-trend tags vs 351 against-trend tags).
- H4: WITH_TREND minus AGAINST_TREND closed PnL delta = 1318.74 AED (382 with-trend tags vs 294 against-trend tags).
- No EA code change is implied by this report; any shared trend-context guard needs a separate pre-registered hypothesis and forward test.
