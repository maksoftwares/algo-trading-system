# Claude Review Prompt - A1 XAU M5 Momentum Residual Reliability Candidate

Please independently review the new residual-reliability candidate. The owner has rejected sparse strategies; the target remains a frequent intraday engine with multiple trades on active days, not a two-trades-per-month system.

Boundary: offline/repo review only unless separately authorized. Do not touch MT5 runtime. Do not attach charts, change presets, place orders, or modify open positions.

Files to inspect:

- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RELIABILITY_RESIDUAL_SEARCH_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RELIABILITY_RESIDUAL_SEARCH_2026_07_02.json`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RELIABILITY_RESIDUAL_SEARCH_2026_07_02.csv`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_STRESS_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_STRESS_2026_07_02.json`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_STRESS_2026_07_02.csv`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PACKAGE_OPTIMIZER_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PACKAGE_OPTIMIZER_2026_07_02.json`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PACKAGE_OPTIMIZER_2026_07_02.csv`
- `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_FORWARD_DRAFT_2026_07_02.md`
- `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_FORWARD_DRAFT_2026_07_02.md.sha256.json`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_READINESS_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS50_COOLDOWN10_READINESS_2026_07_02.json`
- `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_FORWARD_DRAFT_2026_07_02.md`
- `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_FORWARD_DRAFT_2026_07_02.md.sha256.json`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_READINESS_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PLUS75_HIGH_NET_READINESS_2026_07_02.json`
- `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_FORWARD_DRAFT_2026_07_02.md`
- `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_FORWARD_DRAFT_2026_07_02.md.sha256.json`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_READINESS_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_READINESS_2026_07_02.json`
- `xau-usd/xauusd-phase1/scripts/analyze_a1_momentum_feature_band_reliability_residual_search.py`
- `xau-usd/xauusd-phase1/mt5/Experts/A1XauM5MomentumContinuationExecutor.mq5`
- `xau-usd/xauusd-phase1/scripts/attach_a1_xau_m5_momentum_continuation.py`
- `xau-usd/xauusd-phase1/tests/test_a1_xau_m5_momentum_continuation.py`
- `status_summary.md`

Candidate:

- Name: `combo__block_ANY_entry_hour_18__block_SHORT_close_to_recent_extreme_>=_-0.92`
- Package: +50 USD target, max 6 package trades/day, 15-minute package cooldown after any losing package trade.
- Residual blocks:
  - Block LONG entries at server hour 18.
  - Tighten SHORT close-to-recent-extreme min block from `>= -0.75` to `>= -0.92`.
- Planned magics: `932296` and `932297`
- Status: `PASS_READY_FOR_REVIEW_NOT_ATTACHED`
- Runtime touched: no
- Sparse-strategy veto: fail any candidate that wins by dropping below the owner's useful cadence. Hard minimum is 2 trades per active day; preferred cadence is 3-5 trades per active day with at least 50% 3+ trade active days.
- Preferred owner-target package for review: `+50 USD` target, max `6` package trades/day, `10` minute cooldown after loss, planned magics `932298/932299`, draft SHA256 `1339a7b154bdd04dcd45f5946f91c336f3db9e47c897bc2e81aeba51d7b8ee71`.
- Higher-net alternative for review: `+75 USD` target, no shared max-trade cap, `10` minute cooldown after loss, planned magics `932300/932301`, draft SHA256 `de637fb4be82b0328ea98e8725936a1bf307810a28ab3dc58fcddfe932c4c39a`. This has more trades and higher net, but a lower positive-day rate and larger drawdown, so do not approve it just because the headline net is larger.

Reported comparison:

| Metric | Daily reliability baseline | Residual candidate |
|---|---:|---:|
| Trades | 1894 | 1822 |
| Win rate | 68.74% | 69.10% |
| Profit factor | 1.49 | 1.52 |
| Net USD | 1817.95 | 1837.34 |
| Active days | 594 | 572 |
| Trades / active day | 3.19 | 3.19 |
| 3+ trade active days | 51.01% | 50.87% |
| Positive active days | 60.44% | 62.59% |
| Top 100 winners removed | 784.20 | 806.20 |
| Max closed DD | 79.45 | 84.11 |
| Older split net / PF | 500.79 / 1.39 | 520.77 / 1.43 |
| Newer split net / PF | 1317.16 / 1.54 | 1316.57 / 1.56 |

Stress result:

| Metric | Residual candidate |
|---|---:|
| Stress status | `RESIDUAL_RELIABILITY_STRESS_PASS_REVIEW_READY` |
| Trades | 1822 |
| Trades / active day | 3.19 |
| 2+ trade active days | 66.08% |
| 3+ trade active days | 50.87% |
| Positive active days | 62.59% |
| Top 100 winners removed | +806.20 |
| Top 200 winners removed | +36.55 |
| Negative half-year buckets | 0 |
| Negative rolling 250-trade windows | 0 |

Package optimizer result:

The optimizer searched 4540 package-control rows on the same residual-filtered signal base. It did not touch MT5 runtime.

| Role | Package | Trades | WR | Net | PF | T/active | 3+ days | Pos days | Top100 | Top200 | DD |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Current residual draft | +50 target, max 6, 15m cooldown after loss | 1822 | 69.10% | +1837.34 | 1.52 | 3.19 | 50.87% | 62.59% | +806.20 | +36.55 | 84.11 |
| Best +50 target row | +50 target, max 6, 10m cooldown after loss | 1823 | 69.17% | +1863.81 | 1.53 | 3.19 | 51.05% | 62.94% | +829.08 | +57.55 | 84.11 |
| Best positive-day row | no target, max 6, 10m cooldown after loss | 1824 | 69.19% | +1875.96 | 1.53 | 3.19 | 51.05% | 62.94% | +837.88 | +64.42 | 84.11 |
| Best net row | +75 target, no max-trade cap, 10m cooldown after loss | 2231 | 69.48% | +2400.90 | 1.54 | 3.90 | 51.05% | 60.66% | +1324.53 | +489.31 | 91.59 |

Please decide whether the forward demo should use the already stress-tested +50/15m draft, the slightly improved +50/10m row, the no-target positive-day row, or the higher-net +75/no-cap row. Be strict about whether changing the package from +50/15m to +50/10m requires a new forward draft/hash before attachment.

Please verify:

1. Recompute the candidate from the source CSV/JSON if possible.
2. Confirm whether the residual blocks are causal and implementable from the logged MT5 features.
3. Challenge whether the two added blocks are overfit, especially the server-hour-18 block.
4. Decide whether the trade-off is worth it:
   - Positive active days improve by +2.15 percentage points.
   - PF and net improve slightly.
   - Active days drop by 22.
   - Drawdown rises by 4.66 USD.
5. Verify MQL/attach readiness:
   - `InpPortfolioCooldownAfterLossMinutes` defaults to `0`.
   - planned magics are separate: `932296/932297`.
   - package guard CSV is `932296,932297`.
   - LONG hour 18 is blocked in the long lane.
   - V13 long hour 18 is blocked.
   - V13 short `close_to_recent_extreme` min is `-0.92` and max remains `-2.51`.
6. Give a clear verdict:
   - APPROVE_FOR_SMALL_FORWARD_DEMO
   - APPROVE_DAILY_RELIABILITY_BASELINE_INSTEAD
   - APPROVE_OPTIMIZED_PLUS_50_COOLDOWN_10_INSTEAD
   - APPROVE_HIGHER_NET_PLUS_75_PACKAGE_INSTEAD
   - REVISE
   - REJECT

If you approve, provide exact forward-test acceptance and kill rules. If you reject, explain whether we should use the simpler daily-reliability baseline (`932294/932295`) instead or keep searching for a different entry family. Please specifically challenge whether the cadence is genuinely enough for the owner's daily-profit vision, because a two-trades-per-month strategy is not acceptable regardless of PF.
