# A1 XAU Short Downside Impulse Retest Preregistration

Generated: 2026-07-08

## Purpose

Test the TradingView-observed short idea as an exact-MT5 standalone short specialist: after a large downside impulse, wait for a failed retest of broken support, then enter short at fixed 2R. The intent is to improve short-side win rate without lowering the payoff target.

This is research-only. It does not authorize demo/live trading.

## Execution Boundary

- Exact MT5 Strategy Tester only.
- Sandbox terminal root: `C:\MT5A1M5MomentumBacktest`.
- EA: `A1XauM5MomentumContinuationExecutor`.
- Symbol/timeframe: `XAUUSD` / `M5`.
- Window: `2022.07.01 -> 2026.06.30`.
- Tester model: MT5 every tick using local terminal history quality.
- Deposit/currency: `1000 USD`.
- No live/demo runtime, chart, profile, preset, open order, or broker-state change.
- Python only orchestrates MT5 and recomputes metrics from exported MT5 trades.

## New Signal Mode

`SIGNAL_BEAR_DOWNSIDE_IMPULSE_RETEST = 19`

The mode extends the already-audited `SIGNAL_BEAR_BREAKDOWN_RETEST = 15` rule with one extra prerequisite: the support break must be preceded by a minimum ATR-sized downside impulse.

Fixed rule:

1. Short-only.
2. A completed M5 break bar must close below the prior support low by at least `0.10 * ATR14(M5)`.
3. The break must be bearish and its body must be at least `0.45` of its range.
4. From three completed M5 bars before the break to the break close, price must move down at least `1.20 * ATR14(M5)`.
5. Price must retest near broken support without closing back above support plus the reclaim buffer.
6. Current completed M5 confirmation bar must be bearish, close in the lower 35% of its range, and remain below the broken support reclaim zone.
7. Stop is above the retest high plus `0.25 * ATR14(M5)`.
8. Target is fixed `2.00R`.

## Frozen Inputs

Common inputs for every variant:

```text
InpDirectionMode = 2
InpSignalMode = 19
InpRiskReward = 2.00
InpMaxSpreadPoints = 75
InpMaxEstimatedCostR = 0.05
InpMaxTradesPerDay = 24
InpCooldownMinutes = 0
InpBlockedEntryHoursCsv =
InpBlockedEntryDayHoursCsv =
InpBlockedLongEntryHoursCsv =
InpBlockedShortEntryHoursCsv =
InpBearRetestLookbackBars = 10
InpBearRetestSupportLookbackBars = 12
InpBearRetestBreakAtr = 0.10
InpBearRetestTouchAtr = 0.05
InpBearRetestReclaimAtr = 0.05
InpBearRetestStopBufferAtr = 0.25
InpBearRetestMinBodyFraction = 0.35
InpShortCloseLocation = 0.35
InpBearImpulseRetestImpulseBars = 3
InpBearImpulseRetestMinImpulseAtr = 1.20
InpBearImpulseRetestBreakMinBodyFraction = 0.45
InpStopFloorPoints = 350
InpStopCeilingPoints = 2200
```

## Structural Variants

Run exactly three variants. These are regime definitions, not parameter tuning.

| Variant | Rule |
| --- | --- |
| `short_v4_impulse_retest_d1_nonup_h1h4` | D1 EMA20 non-up plus H1/H4 EMA20/50 downtrend filters |
| `short_v4_impulse_retest_d1_structural_h1h4` | D1 close below EMA50 and EMA50 not rising, plus H1/H4 downtrend filters |
| `short_v4_impulse_retest_d1_nonup_h1_only` | D1 EMA20 non-up plus H1 downtrend filter only |

Selection is not by highest net. A variant must pass the standalone gates before it can be discussed.

## Standalone Gates

The user's target is a standalone short expert with about/above 50% win rate and about 2R payoff. Pass requires:

- WR `>= 50%`.
- Raw average win/loss `>= 1.90`.
- At least `75` trades.
- Full-window net `> 0`.
- Stress net after `-$0.30` per trade `> 0`.
- Stress PF after `-$0.30` per trade `>= 1.15`.
- Q2-2026 net `> 0`.
- Recent three months net `> 0`.
- 2023 plus 2024 combined net `>= 0`.
- At least three positive yearly buckets across 2022 partial, 2023, 2024, 2025, 2026 partial.
- Net after removing top 10 winning trades remains `> 0`.
- Net excluding top 3 entry days remains `> 0`.

## Forbidden

- No hour/session/day/month masking.
- No RR reduction below 2R.
- No post-result parameter grid.
- No mixing into the long strategy to hide standalone weakness.
- No demo spec without a separate reviewer-approved promotion path.

## Decision

If a variant passes all standalone gates:

- Status: `SHORT_IMPULSE_RETEST_WR50_RR2_REVIEW_CANDIDATE`.
- Keep research-only pending review.

If no variant reaches WR50/RR2:

- Keep the result as a diagnostic.
- Do not tune hours or months from this ledger.
- Decide whether to retire standalone short search or request a new reviewer-signed short objective.
