# A1 XAU Short V2 Robustness Preregistration

Generated: 2026-07-08

## Purpose

This pass tests whether `short_hedge_v2_breakdown_retest` is a durable standalone XAUUSD short edge or only a 2025-2026 regime artifact. It uses exact MT5 Strategy Tester only on the isolated backtest terminal `C:\MT5A1M5MomentumBacktest`. It does not touch live/demo runtime, charts, profiles, presets, broker state, orders, or positions.

The target is not to raise standalone win rate. The target is year/block stability under fixed rules.

## Frozen Execution Contract

- Symbol: `XAUUSD`
- Timeframe: `M5`
- Direction: short only
- Signal mode: `InpSignalMode = 15`
- Window: `2022.07.01 -> 2026.06.30`
- Tester model: MT5 Every Tick using the terminal's local history/report quality
- Deposit/currency: `1000 USD`
- Lot: fixed `0.01`
- Risk reward: `2.00`, except optional T3 robustness
- Max spread: `75`
- Max estimated cost R: `0.05`
- Max trades per day: `24`
- Cooldown: `0`
- Session/hour/day/month filters: none

Frozen V2 breakdown-retest inputs:

```text
InpBearRetestLookbackBars        = 10
InpBearRetestSupportLookbackBars = 12
InpBearRetestBreakAtr            = 0.10
InpBearRetestTouchAtr            = 0.05
InpBearRetestReclaimAtr          = 0.05
InpBearRetestStopBufferAtr       = 0.25
InpBearRetestMinBodyFraction     = 0.30
InpUseH1TrendFilter              = true
InpUseH4TrendFilter              = true
InpH1TrendMinSlopePoints         = 0
InpH4TrendMinSlopePoints         = 0
InpShortCloseLocation            = 0.42
```

## T1 Regime-Definition Robustness

Run exactly three variants. The only intended difference is the D1 regime gate.

| Variant | Rule | EA settings |
| --- | --- | --- |
| R1 baseline/parity | D1 EMA20 bearish, current V2 | `InpD1SupportStateGateMode=3`, `InpD1SupportStateEmaPeriod=20`, `InpD1SupportStateSlopeLagBars=5` |
| R2 non-up | D1 non-up | `InpD1SupportStateGateMode=4`, `InpD1SupportStateEmaPeriod=20`, `InpD1SupportStateSlopeLagBars=5` |
| R3 structural down | D1 close below EMA50 and EMA50 not rising over 5 completed D1 bars | `InpD1StructuralDownGateEnabled=true`, `InpD1StructuralDownEmaPeriod=50`, `InpD1StructuralDownSlopeLagBars=5` |

R3 exact rule, completed D1 bars only:

```text
D1 close[1] < D1 EMA50[1]
AND
D1 EMA50[1] <= D1 EMA50[6]
```

When `InpD1StructuralDownGateEnabled=true`, the structural gate replaces the normal `InpD1SupportStateGateMode` gate for that run.

T1 pass gate, per variant:

- Positive yearly net in at least 3 yearly buckets across 2022 partial, 2023, 2024, 2025, and 2026 partial.
- 2023 plus 2024 combined net is at least `0.00`.
- Full-window net is greater than `0.00`.
- Cost-stress PF after subtracting `0.30` per trade is at least `1.20`.
- Trade count is at least `200`.

Selection rule: among T1 passers, choose the simplest passing definition in order `R1`, then `R2`, then `R3`. Do not pick by highest net.

## T2 Walk-Forward Stability

Apply only to the T1 winner, if one exists.

Fixed blocks:

- B1: `2022-07-01 -> 2022-12-31`
- B2: `2023-01-01 -> 2023-06-30`
- B3: `2023-07-01 -> 2023-12-31`
- B4: `2024-01-01 -> 2024-06-30`
- B5: `2024-07-01 -> 2024-12-31`
- B6: `2025-01-01 -> 2025-06-30`
- B7: `2025-07-01 -> 2025-12-31`
- B8: `2026-01-01 -> 2026-06-30`

T2 pass gate:

- At least 6 of 8 blocks have net greater than or equal to `0.00`.
- No single block contributes more than 50% of full-window net.
- At least one of B1 through B6 is positive, so the result does not depend only on B7/B8.

## T3 RR Robustness

Run only if a T1 winner also passes T2 and the concentration guard.

Run the winner at `RR=1.5`, `RR=2.0`, and `RR=2.5`. Report all three. Pass if every RR has net greater than `0.00` and cost-stress PF at least `1.15`.

## Metrics

Compute for every variant:

- Trades, wins, losses, WR, average win/loss, PF, net.
- Cost stress after subtracting `0.30` per trade, recomputing net, average win/loss, and PF.
- By-year table for 2022 through 2026.
- Fixed six-month walk-forward table B1 through B8.
- Concentration: net after removing top 1, top 5, and top 10 winning trades; best-day share; net excluding top 3 entry days.
- Positive weeks and worst week using exit-time weekly buckets.

Concentration guard before any candidate can advance:

- Net after removing top 10 winning trades remains greater than `0.00`.
- Net excluding top 3 entry days remains greater than `0.00`.

## Decision Tree

If a T1 variant passes T1, T2, and concentration:

- Verdict: `VALIDATED_STANDALONE_SHORT_BASE_REVIEW_REQUIRED`.
- Next step is a separate reviewer-signed forward-watchlist spec.
- No demo spec.

If a T1 variant passes T1 but fails T2 or concentration:

- Verdict: `RECENT_REGIME_ARTIFACT_NOT_PROMOTED`.
- Keep V2 frozen as reference.
- No watchlist.

If no T1 variant passes:

- Verdict: `NO_DURABLE_STANDALONE_SHORT_EDGE`.
- Downgrade the short to combined-portfolio hedge only.
- Stop standalone short iteration rather than forcing it with post-hoc filters.

## Forbidden

- No hour, session, day, or month masking.
- No parameter grid.
- No post-result quality filters.
- No RR selection by best result.
- No break-even, trailing, or partial exit changes.
- No forward-watchlist or demo claim without reviewer sign-off.
