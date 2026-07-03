# Claude Review Prompt - A1 XAU M5 Momentum Daily Reliability Candidate

Please independently review the new A1 XAU M5 momentum daily-reliability package. The owner explicitly rejected sparse strategies, including any strategy that only produces a couple trades in a month. The business goal is a frequent intraday engine: multiple trades on active days, preferably 3-5, with WR above 50%, positive expectancy, and better daily consistency.

Boundary: offline/repo review only unless separately authorized. Do not touch MT5 runtime. Do not attach charts, change presets, place orders, or modify open positions.

Files to inspect:

- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAY_STATE_SEARCH_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAY_STATE_SEARCH_2026_07_02.json`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAY_STATE_SEARCH_2026_07_02.csv`
- `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_RELIABILITY_FORWARD_DRAFT_2026_07_02.md`
- `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_RELIABILITY_FORWARD_DRAFT_2026_07_02.md.sha256.json`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_RELIABILITY_READINESS_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_RELIABILITY_READINESS_2026_07_02.json`
- `xau-usd/xauusd-phase1/mt5/Experts/A1XauM5MomentumContinuationExecutor.mq5`
- `xau-usd/xauusd-phase1/scripts/attach_a1_xau_m5_momentum_continuation.py`
- `xau-usd/xauusd-phase1/tests/test_a1_xau_m5_momentum_continuation.py`
- `status_summary.md`

Candidate to review:

- Name: `owner_target_50_max6_cooldown_after_loss_15`
- Package shape: +50 USD daily package target, max 6 package trades/day, no daily loss stop, 15-minute cooldown after any closed losing package trade.
- Planned magics: `932294` and `932295`
- Status: `PASS_READY_FOR_REVIEW_NOT_ATTACHED`
- Runtime touched: no

Reported metrics:

| Metric | Value |
|---|---:|
| Trades | 1894 |
| Win rate | 68.74% |
| Profit factor | 1.49 |
| Net USD | 1817.95 |
| Active days | 594 |
| Trades / active day | 3.19 |
| 3+ trade active days | 51.01% |
| Positive active days | 60.44% |
| Positive / negative months | 41 / 7 |
| Older split net / PF | 500.79 / 1.39 |
| Newer split net / PF | 1317.16 / 1.54 |
| Top 100 winners removed | 784.20 |
| Max closed DD | 79.45 |

Please verify:

1. Recompute the row from the source CSV/JSON if possible. Confirm the metrics and whether the cooldown logic is causal.
2. Compare it against the plain +50/max6 baseline:
   - baseline: 1959 trades, WR 66.31%, PF 1.35, net 1431.19, 3.30 trades/active day, 53.54% 3+ trade days, 58.59% positive days, top100 removed 395.04, DD 105.72.
   - cooldown candidate: 1894 trades, WR 68.74%, PF 1.49, net 1817.95, 3.19 trades/active day, 51.01% 3+ trade days, 60.44% positive days, top100 removed 784.20, DD 79.45.
3. Challenge whether the 15-minute cooldown is a real reliability improvement or an overfit day-state parameter.
4. Decide whether 51.01% 3+ trade days is acceptable given the owner goal, because trades/active day remains above 3 and total trades remain high.
5. Verify MQL5 implementation safety:
   - `InpPortfolioCooldownAfterLossMinutes` defaults to `0`.
   - Existing runtime behavior does not change unless a future preset explicitly enables the input.
   - The guard checks closed losing package trades only for the configured magic CSV.
   - The guard logs `portfolio_cooldown_after_loss_active`.
6. Verify attach script safety:
   - planned variants are separate from existing daily-income magics.
   - magics are `932294/932295`.
   - package guard CSV is `932294,932295`.
   - cooldown is `15`.
   - no A2/A3 or 920101 chart is touched by the readiness work.
7. Give a clear verdict:
   - APPROVE_FOR_SMALL_FORWARD_DEMO
   - REVISE
   - REJECT

If you approve, provide the exact forward-test acceptance and kill rules. If you reject or revise, explain what specific evidence would make it acceptable while preserving the owner's core requirement: frequent intraday trades, not sparse monthly trading.
