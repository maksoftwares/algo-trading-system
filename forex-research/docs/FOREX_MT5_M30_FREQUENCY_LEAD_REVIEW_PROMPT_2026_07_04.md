# Independent Review Prompt - Forex MT5 M30 Frequency Lead

Please independently review the new M30 MT5 frequency packet and give a direct verdict.

Question: is `EURUSD rsi_bb_close_fade_m30_long_blockh6_7_10_13_rr0p80` a valid `WATCHLIST_ONLY` Forex research lead, and is it correctly blocked from demo-forward status?

Scope to verify:

1. Actual MT5 evidence: confirm the reports came from MT5 Strategy Tester output, not a Python price simulator. Python only compiled/launched MT5 and parsed completed MT5 reports.
2. Runtime isolation: confirm the runner used isolated tester root `C:\MT5A1M5MomentumBacktest` and did not touch live/demo charts, presets, profiles, orders, positions, or XAU runtime terminals.
3. Frequency-first sequencing: confirm the raw M30 rule was preserved before tuning:
   - Raw design 2022-2024: 585 trades, CSV PF 1.0804, +$30.29.
   - Raw current 2024-2026: 560 trades, CSV PF 1.1889, +$60.28.
   - Raw full 2022-2026: 1145 trades, CSV PF 1.1301, +$90.57.
4. Tuning discipline: the only tuning change was blocking entry hours `6,7,10,13`, selected from the older 2022-2024 raw split, then checked on 2024-2026 validation. No indicator threshold, stop, symbol, direction, or RR was changed.
5. Tuned result:
   - Design 2022-2024: 405 trades, CSV PF 1.1585, MT5 PF about 1.13, +$40.57.
   - Current 2024-2026: 426 trades, CSV PF 1.3123, MT5 PF about 1.29, +$74.23.
   - Full 2022-2026: 831 trades, CSV PF 1.2325, MT5 PF about 1.20, +$114.80.
6. Robustness:
   - Positive: 36/49 active months positive; worst 250-trade rolling window PF 0.9765 / -$3.62; worst 500-trade window PF 1.1557 / +$47.36; top-10-winner removal PF 1.1641 / +$80.99.
   - Negative: worst 100-trade rolling window PF 0.7357 / -$20.81; worst 150-trade window PF 0.8399 / -$17.26; top-50-winner removal PF 0.9735 / -$13.10.
7. Portability: frozen rule failed on GBPUSD and USDJPY:
   - GBPUSD full PF 0.9470 / -$37.36; current PF 0.8537 / -$52.84.
   - USDJPY full PF 0.8367 / -$125.30; current PF 0.8128 / -$78.50.
8. Overclaim audit: status should be `WATCHLIST_ONLY_MT5_TUNED_FREQUENCY_EDGE`, no demo-forward spec, no survivor claim.

Please answer with:

- Verdict: methodology sound or not.
- Whether watchlist-only status is justified.
- Whether demo-forward status must remain blocked.
- Any blocker, caveat, or exact next test you require before further tuning.

Evidence files:

- Status: `forex-research/docs/FOREX_MT5_FREQUENCY_STATUS_2026_07_04.md`
- Robustness report: `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_M30_RSI_BB_LONG_BLOCKH6_7_10_13_RR0P8_TUNING_ROBUSTNESS_2026_07_04.md`
- Robustness JSON: `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_M30_RSI_BB_LONG_BLOCKH6_7_10_13_RR0P8_TUNING_ROBUSTNESS_2026_07_04.json`
