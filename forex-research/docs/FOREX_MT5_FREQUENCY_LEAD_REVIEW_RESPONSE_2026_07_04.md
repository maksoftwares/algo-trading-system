# Forex MT5 Frequency Lead Review Response - 2026-07-04

Status: REVIEW_COMPLETE_WATCHLIST_ONLY_CONFIRMED

## Verdict

No blocking issue was found for the current status `WATCHLIST_ONLY_MT5_TUNED_FREQUENCY_EDGE`.

The same evidence does block any demo-forward spec. The tuned EURUSD lead is a real MT5-tested research lead, but it is not yet a strategy to attach, forward on demo, or call profitable.

## Findings

1. Demo-forward blocker: the tuned hour filter is post-hoc with respect to the full raw MT5 sample.

   Blocking hours `1`, `7`, and `21` is a constrained and transparent tune, but those hours were selected from the raw full-window robustness report. That makes the tuned result acceptable as a watchlist hypothesis only. It cannot be treated as clean out-of-sample evidence until a fresh forward window or separately pre-registered validation window confirms it.

2. Demo-forward blocker: the edge is still thin.

   Tuned full-window PF is `1.1705`, average trade is `$0.0831` at 0.01 lots, and the older split is only PF `1.0875` / `+$30.87`. That leaves little room for broker differences, slippage, spread regime drift, and execution changes.

3. Demo-forward blocker: rolling-window weakness remains.

   The worst tuned 250-trade window is still negative: PF `0.8131`, `-$25.78`, from `2025-07-07 06:45:00` to `2026-03-18 20:38:05`. This is improved from the raw result but still too weak for deployment claims.

4. Resolved metadata issue: tuned aggregate report originally marked `scope.tuning_attempted=false`.

   The trade metrics were unaffected, but the metadata was misleading. The runner now accepts a `tuning_attempted` flag, the mean-reversion wrapper passes it through, Markdown renders it explicitly, and the current tuned aggregate JSON/Markdown report has been corrected to `true`.

## Runtime Isolation Review

PASS for watchlist research.

- `ForexMeanReversionScout.mq5` returns `INIT_FAILED` when `MQL_TESTER` is false.
- The Python runner launches `C:\MT5A1M5MomentumBacktest\terminal64.exe` with `/portable`.
- The generated tester config uses `ShutdownTerminal=1`, `UseLocal=1`, `UseRemote=0`, and `UseCloud=0`.
- No live/demo chart, preset, order, position, or running XAU EA is touched by the Forex MT5 runner.

## Evidence Checked

- Raw MT5 report: `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_FREQUENCY_SCOUT_FULL_2022_2026_M15_RSI_EXTREME_LONG_RR0P8.md`
- Raw robustness report: `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_M15_RSI_EXTREME_LONG_RR0P8_ROBUSTNESS_2026_07_04.md`
- Tuned MT5 report: `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_FREQUENCY_SCOUT_TUNE_FULL_2022_2026_M15_RSI_EXTREME_LONG_BLOCKH1_7_21_RR0P8.md`
- Tuned robustness report: `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_M15_RSI_EXTREME_LONG_BLOCKH1_7_21_RR0P8_TUNING_ROBUSTNESS_2026_07_04.md`
- EA source: `forex-research/mt5/Experts/ForexMeanReversionScout.mq5`
- Runner source: `forex-research/scripts/run_forex_mt5_frequency_scout.py`
- Mean-reversion wrapper: `forex-research/scripts/run_forex_mt5_mean_reversion_scout.py`

## Next Gate

Pause further tuning unless a reviewer explicitly accepts the bad-hour filter as a registered watchlist hypothesis. The next evidence should be one of:

1. A fresh, pre-registered forward/recent MT5 window with the tuned rule frozen.
2. A broker-provenance refresh that confirms symbol/account/spread conditions.
3. A second broker or account-type MT5 replay, with no new threshold or hour changes.

Any pass remains watchlist-only until the rolling-window weakness is materially reduced and a separate owner-approved demo-forward spec is drafted.
