# Independent Review Prompt - Forex MT5 Frequency Lead

Please review the new Forex MT5 frequency-first evidence in this repo. The prior Forex review concluded methodology sound but no survivor because earlier screens were Python/offline or proxy-data based. The new work intentionally uses actual MT5 Strategy Tester, not the Python simulator.

## Scope To Review

Review these files:

- `forex-research/docs/FOREX_MT5_FREQUENCY_STATUS_2026_07_04.md`
- `forex-research/mt5/Experts/ForexMeanReversionScout.mq5`
- `forex-research/scripts/run_forex_mt5_frequency_scout.py`
- `forex-research/scripts/run_forex_mt5_mean_reversion_scout.py`
- `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_FREQUENCY_SCOUT_FULL_2022_2026_M15_RSI_EXTREME_LONG_RR0P8.md`
- `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_M15_RSI_EXTREME_LONG_RR0P8_ROBUSTNESS_2026_07_04.md`
- `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_M15_RSI_EXTREME_LONG_RR0P8_ROBUSTNESS_2026_07_04.json`
- `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_FREQUENCY_SCOUT_TUNE_FULL_2022_2026_M15_RSI_EXTREME_LONG_BLOCKH1_7_21_RR0P8.md`
- `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_M15_RSI_EXTREME_LONG_BLOCKH1_7_21_RR0P8_TUNING_ROBUSTNESS_2026_07_04.md`
- `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_M15_RSI_EXTREME_LONG_BLOCKH1_7_21_RR0P8_TUNING_ROBUSTNESS_2026_07_04.json`

## Facts To Verify

- The EA is tester-only and cannot place live/demo orders outside MT5 Strategy Tester.
- The runner uses an isolated MT5 tester root and does not modify the existing demo/live XAU terminals.
- The reported lead is `EURUSD rsi_extreme_fade_m15_long_rr0p80`.
- Combined actual-MT5 result for 2022-07-01 through 2026-07-02 is 1524 trades, CSV PF 1.1336, MT5 report PF about 1.12, net +$97.94 at fixed 0.01 lots.
- Chronological split is positive in both halves: 2022-2024 has 785 trades, PF 1.0839, +$33.28; 2024-2026 has 739 trades, PF 1.1924, +$64.66.
- Robustness does not rely on one big trade: top 10 winner removal leaves PF 1.0925 and +$67.76.
- Weakness remains: only 28/49 active months positive, full PF only 1.1336, average trade only $0.0643, and the worst 250-trade rolling window is PF 0.7305 / -$38.20.
- A constrained tuning pass blocked only entry hours 1, 7, and 21, selected from the raw robustness report.
- Tuned actual-MT5 result for 2022-07-01 through 2026-07-02 is 1309 trades, CSV PF 1.1705, MT5 report PF about 1.15, net +$108.84.
- Tuned chronological split is positive but uneven: 2022-2024 has 674 trades, PF 1.0875, +$30.87; 2024-2026 has 635 trades, PF 1.2733, +$77.97.
- Tuned robustness improves but still has weakness: top 10 winner removal leaves PF 1.1232 and +$78.66, but only 27/49 active months are positive and the worst 250-trade rolling window is PF 0.8131 / -$25.78.

## Questions For Reviewer

1. Is `WATCHLIST_ONLY_MT5_TUNED_FREQUENCY_EDGE` the correct status, or should this be rejected outright because the edge is too small?
2. Are the MT5 runner and EA truly isolated from runtime/demo execution?
3. Is the combined MT5 evidence sufficient to justify a constrained first tuning pass?
4. Is blocking hours 1, 7, and 21 acceptable as a constrained tune, or is it too post-hoc?
5. What exact evidence should be required before any Forex demo-forward spec is even drafted?

Please lead with blocking issues or overclaims. If there are no blockers, say that clearly and list the residual risks.
