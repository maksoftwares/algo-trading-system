# W1/D1 Momentum M5 Continuation - Preliminary Backtest Note

Date: 2026-06-11

EA source: `xau-usd/xauusd-phase1/mt5/Experts/W1D1MomentumM5ContinuationExperimental.mq5`

Python mirror: `xau-usd/xauusd-phase0/src/phase0/strategies/w1_d1_momentum_m5_continuation_experimental.py`

Status: `PRELIMINARY_ONLY_NOT_APPROVED`

## Scope

This is an offline Phase 0-style backtest of the new M5 variant. It does not touch MT5 terminals, broker state, running demo EAs, or live orders.

The local processed Phase 0 OHLC data currently ends at `2025-07-01`, so this is not a June 2026 demo-week replay. It is a bounded historical slice using warmup bars from `2024-10-01` and scoring the period `2025-01-01` through `2025-07-01`.

## Result Summary

The first mirror was still too slow, so an active profile was tested on the same bounded historical slice. The current committed default is now:

```text
pullback trigger only
InpEnableImpulseTrigger=false
InpMaxTradesPerDay=12
InpCooldownMinutes=10
InpOnePositionAtATime=false
InpStopAtrMultiple=4.0
InpStopFloorPoints=250
```

This achieves more activity, but the edge weakens materially.

Current active pullback-only default, P95 cost model:

| Broker | Trades | Win rate | PF | Net PnL on Phase 0 $10k baseline | Return | Max DD | Trades/day |
|---|---:|---:|---:|---:|---:|---:|---:|
| capital_com | 283 | 40.99% | 1.0362 | $278.70 | 2.7870% | 6.9409% | 1.55 |
| pepperstone | 0 | 0.00% | 0.0000 | $0.00 | 0.0000% | 0.0000% | 0.00 |
| dukascopy | 226 | 38.50% | 0.8598 | -$819.70 | -8.1970% | 10.2772% | 1.24 |

Activity variant scan, Capital.com, P95 cost model:

| Variant | Trades | Trades/day | Win rate | PF | Net PnL | Return | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| old_pullback_slow_stop | 114 | 0.63 | 43.86% | 1.1472 | $386.95 | 3.8695% | 3.9073% |
| pullback_fast_stop | 283 | 1.55 | 40.99% | 1.0362 | $278.70 | 2.7870% | 6.9409% |
| pullback_slow_stop_high_cap | 115 | 0.63 | 41.74% | 1.0167 | $46.60 | 0.4660% | 6.0445% |
| impulse_strict_slow_stop | 127 | 0.70 | 41.73% | 1.0565 | $170.70 | 1.7070% | 5.4737% |
| active_current_with_loose_impulse | 254 | 1.40 | 38.98% | 0.9369 | -$432.19 | -4.3219% | 9.8373% |

The loose impulse branch is therefore disabled by default. It remains available as an input for controlled experiments only.

## Prior Slower Profile

P95 cost model:

| Broker | Trades | Win rate | PF | Net PnL on Phase 0 $10k baseline | Return | Max DD | Avg win | Avg loss | Trades/day |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| capital_com | 114 | 43.86% | 1.1472 | $386.95 | 3.8695% | 3.9073% | $60.32 | -$41.08 | 0.63 |
| pepperstone | 0 | 0.00% | 0.0000 | $0.00 | 0.0000% | 0.0000% | $0.00 | $0.00 | 0.00 |
| dukascopy | 92 | 41.30% | 1.0175 | $39.01 | 0.3901% | 4.5511% | $59.57 | -$41.20 | 0.51 |

Capital.com median vs P95 costs for the same slice:

| Broker | Cost model | Trades | Win rate | PF | Return | Max DD | Trades/day |
|---|---|---:|---:|---:|---:|---:|---:|
| capital_com | median | 114 | 43.86% | 1.1518 | 3.9815% | 3.8830% | 0.63 |
| capital_com | p95 | 114 | 43.86% | 1.1472 | 3.8695% | 3.9073% | 0.63 |

## Interpretation

The active M5 conversion can increase activity from roughly 0.5-0.6 trades/day to roughly 1.2-1.6 trades/day in the bounded historical slice. However, the increase comes from accepting lower-quality M5 situations. Capital.com remains slightly positive, but Dukascopy fails under the active pullback-only profile.

The evidence is not strong enough to deploy as a real-money candidate. It is also not strong enough to claim the active M5 conversion is a solved improvement. The correct interpretation is: activity is fixed, edge quality is not fixed.

## Verification Performed

| Check | Result |
|---|---|
| MQL5 isolated compile | PASS: 0 errors, 0 warnings |
| Python strategy unit tests | PASS: 4/4 |
| W1/D1 parent + M5 mirror tests | PASS: 8/8 |
| Research registry import smoke | PASS |

## Output Artifacts

Local CSV artifacts were written under the ignored Phase 0 output directory:

```text
xau-usd/xauusd-phase0/outputs/reports/w1_d1_m5_momentum_experimental_capital_2025h1_backtest_2026_06_11.csv
xau-usd/xauusd-phase0/outputs/reports/w1_d1_m5_momentum_experimental_2025h1_p95_backtest_2026_06_11.csv
xau-usd/xauusd-phase0/outputs/reports/w1_d1_m5_momentum_active_experimental_2025h1_p95_backtest_2026_06_11.csv
xau-usd/xauusd-phase0/outputs/reports/w1_d1_m5_momentum_activity_variant_scan_capital_2025h1_2026_06_11.csv
xau-usd/xauusd-phase0/outputs/reports/w1_d1_m5_momentum_activity_variant_scan_xbroker_2025h1_2026_06_11.csv
```

These output files are ignored by git under the current policy. This Markdown note preserves the reviewable numbers.

## Next Work

1. Run a longer matrix-style evaluation if the owner wants this candidate to enter the formal research queue.
2. Register and hash-lock a dedicated hypothesis before any full result-producing Phase 0 campaign.
3. Compare against June 2026 demo trades only after matching current broker/export data exists locally.
4. Do not attach this EA to demo execution until the owner explicitly approves it as a separate experimental lane.
