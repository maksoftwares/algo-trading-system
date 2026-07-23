# Forex MT5 Frequency-First Scout

Generated at UTC: `2026-07-23T08:49:57Z`
Status: `MT5_FREQUENCY_SCOUT_COMPLETE_RESEARCH_ONLY`

## Boundary

- Actual MT5 Strategy Tester was used for each row.
- Tuning attempted in this run: `true`.
- No survivor/demo spec is created by this runner.
- Python only compiled/launched MT5 and parsed completed MT5 reports.
- No live/demo chart, preset, order, or position was touched outside Strategy Tester.
- Isolated tester root: `C:\MT5A1M5MomentumBacktest`.

## Scope

- Window: `2022.07.01 -> 2026.07.02`.
- Symbols: `EURUSD`.
- Period: `M5`.
- Tester model: `MT5 Strategy Tester Model=0 every tick`.
- Tuning attempted: `true`.

## Frequency Ranking

| Rank | Symbol | Variant | Status | Trades | Win Rate | Net USD | PF | MT5 Trades | MT5 PF | Equity DD Max |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| `1` | `EURUSD` | `rsi_bb_close_fade_m30_long_blockh6_7_10_13_rr0p80` | `FREQUENT_RAW_EDGE_TUNING_CANDIDATE` | `831` | `59.33%` | `114.8` | `1.2325` | `831` | `1.20` | `30.85 (2.95%)` |

## Next Step

- Status: `TUNE_TOP_FREQUENT_RAW_EDGE_NEXT`
- Candidate: `EURUSD rsi_bb_close_fade_m30_long_blockh6_7_10_13_rr0p80`
- Reason: Highest trade-count raw-edge candidate cleared the frequency-first screen.

## Artifacts

- `EURUSD rsi_bb_close_fade_m30_long_blockh6_7_10_13_rr0p80`: report `eur-usd\eurusd-phase0\outputs\mt5_parity\ForexFreqScout_EURUSD_PHASE0_PARITY_V1_EURUSD_M5_rsi_bb_close_fade_m30_long_blockh6_7_10_13_rr0p80\ForexFreqScout_EURUSD_PHASE0_PARITY_V1_EURUSD_M5_rsi_bb_close_fade_m30_long_blockh6_7_10_13_rr0p80.htm`, summary `eur-usd\eurusd-phase0\outputs\mt5_parity\ForexFreqScout_EURUSD_PHASE0_PARITY_V1_EURUSD_M5_rsi_bb_close_fade_m30_long_blockh6_7_10_13_rr0p80\ForexFreqScout_EURUSD_PHASE0_PARITY_V1_EURUSD_M5_rsi_bb_close_fade_m30_long_blockh6_7_10_13_rr0p80_summary.json`
