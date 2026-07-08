# A1 XAU Short HTF Resistance Sweep/Reclaim Final Test

Generated: 2026-07-08

## Purpose

This is the final falsification test for the standalone XAUUSD short goal:

- around/above 50% win rate,
- fixed nominal RR around 2.0,
- meaningful trade frequency,
- exact MT5 only.

The preceding exact-MT5 short tests converged around 33-36% WR. This pass tests the only remaining materially different archetype recommended by both reviewers: a higher-timeframe resistance sweep and reclaim failure.

If this fixed test also lands below roughly 45% WR, the standalone WR50/RR2 short search is closed. Shorts may remain useful as combined-portfolio hedges, but not as a standalone WR50 expert.

## Execution Contract

- Terminal: `C:\MT5A1M5MomentumBacktest`
- Symbol/timeframe: `XAUUSD` / `M5` tester, with signal evaluated once per completed M15 bar
- Direction: short only
- Window: `2022.07.01 -> 2026.06.30`
- Deposit/currency: `1000 USD`
- Lot: fixed `0.01`
- Nominal RR: `InpRiskReward=2.00`
- Max spread: `75`
- Max estimated cost R: `0.05`
- No hour/session/day/month masks
- No breakeven, trailing, partial exits, or RR reduction

## Signal

Candidate: `short_htf_resistance_sweep_reclaim_rr2`

EA signal mode: `SIGNAL_BEAR_HTF_RESISTANCE_SWEEP = 18`

Regime gate:

```text
D1 close[1] <= D1 EMA20[1]
OR
D1 EMA20[1] < D1 EMA20[6]
```

Implementation uses existing `InpD1SupportStateGateMode=4` with period `20` and slope lag `5`.

Resistance level:

```text
Collect:
  previous D1 high
  previous W1 high
  latest confirmed H4 swing high in the last 30 completed H4 bars

A confirmed H4 swing high is greater than the two completed H4 highs before it
and the two completed H4 highs after it.

Select the nearest candidate above the M15 reclaim close.
```

Sweep/reclaim:

```text
1. A completed M15 bar within the last 1 to 6 M15 bars trades above selected resistance by >= 0.10 x H4 ATR14.
2. The current completed M15 bar closes back below selected resistance.
3. Current completed M15 bar is bearish: close < open.
4. Current completed M15 body/range >= 0.35.
5. Current completed M15 close location <= 0.35.
6. No completed M15 bar after the sweep and before the reclaim closes above resistance + 0.10 x H4 ATR14.
```

Entry limitation:

```text
The reviewer suggested a sell stop below the reclaim candle low with 3-M15-bar expiry.
The current EA harness supports market-at-signal execution, so this final test enters short
at the reclaim close. This limitation must be considered in review.
```

Stop and target:

```text
SL = highest M15 high from sweep through reclaim + 0.10 x H4 ATR14
TP = 2.0 x stop distance
```

Fixed inputs:

```text
InpSignalMode                         = 18
InpD1SupportStateGateMode             = 4
InpD1SupportStateEmaPeriod            = 20
InpD1SupportStateSlopeLagBars         = 5
InpBearHtfResistanceH4LookbackBars    = 30
InpBearHtfResistanceReclaimBars       = 6
InpBearHtfResistanceH4AtrPeriod       = 14
InpBearHtfResistanceSweepH4Atr        = 0.10
InpBearHtfResistanceStopH4Atr         = 0.10
InpBearHtfResistanceMinBodyFraction   = 0.35
InpBearHtfResistanceCloseLocation     = 0.35
```

## Gates

True WR50/RR2 pass:

- WR >= 50.00%.
- Realized W/L >= 1.90.
- Trades >= 100.
- PF >= 1.20.
- Stress PF after `-0.30` per trade >= 1.15.
- Stress net > 0.
- 2023+2024 combined net >= 0.
- At least 3 yearly buckets positive.
- Net after removing top 10 winning trades > 0.
- Net after removing top 3 entry days > 0.

Watchlist-only clue:

- WR >= 45.00%.
- All non-WR pass checks above pass.

Closeout:

- If WR < 45.00%, close the standalone WR50/RR2 short search.
- If WR is 45-50% but the stability/cost/concentration gates fail, close the standalone WR50/RR2 short search unless a reviewer explicitly signs a new work order.

## Forbidden

- No parameter sweep.
- No extra variants after seeing the result.
- No hour/session/day/month masks.
- No lowering RR.
- No demo, forward-watchlist, or standalone promotion without reviewer sign-off.
