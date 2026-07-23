# Forex MT5 Frequency-First Scout

Generated at UTC: `2026-07-23T10:12:34Z`
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
| `1` | `EURUSD` | `rsi_bb_close_fade_m30_long_all_hours_rr0p80` | `FREQUENT_RAW_EDGE_TUNING_CANDIDATE` | `1145` | `57.55%` | `90.57` | `1.1301` | `1145` | `1.11` | `27.56 (2.68%)` |

## Next Step

- Status: `TUNE_TOP_FREQUENT_RAW_EDGE_NEXT`
- Candidate: `EURUSD rsi_bb_close_fade_m30_long_all_hours_rr0p80`
- Reason: Highest trade-count raw-edge candidate cleared the frequency-first screen.

## Artifacts

- `EURUSD rsi_bb_close_fade_m30_long_all_hours_rr0p80`: report `eur-usd\eurusd-phase0\unmasked-audit-v1\outputs\mt5\ForexFreqScout_EURUSD_V1_UNMASKED_AUDIT_2026_07_23_EURUSD_M5_rsi_bb_close_fade_m30_long_all_hours_rr0p80\ForexFreqScout_EURUSD_V1_UNMASKED_AUDIT_2026_07_23_EURUSD_M5_rsi_bb_close_fade_m30_long_all_hours_rr0p80.htm`, summary `eur-usd\eurusd-phase0\unmasked-audit-v1\outputs\mt5\ForexFreqScout_EURUSD_V1_UNMASKED_AUDIT_2026_07_23_EURUSD_M5_rsi_bb_close_fade_m30_long_all_hours_rr0p80\ForexFreqScout_EURUSD_V1_UNMASKED_AUDIT_2026_07_23_EURUSD_M5_rsi_bb_close_fade_m30_long_all_hours_rr0p80_summary.json`
