# EMR Inactivity Long v0 Hypothesis

Hypothesis date: 2026-05-22
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 25-120
Expected cost-adjusted PF: 1.10-1.50
Expected losing-month percentage: 35%-60%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 2
Expected R-multiple distribution: Many failed reversal attempts near -1R, fewer +1.5R mean-reversion wins, and no dependence on one outsized winner.

## Mechanical Definition

This candidate is a long-only XAUUSD extreme mean-reversion expert after inactivity. It tests whether downside sweeps after documented inactivity revert often enough to survive costs and the Phase 0 concentration gates.

The mechanical setup is:

1. Market and timeframe: XAUUSD with M5 entries, M15 inactivity context, and H1 trend/activity context.
2. M5 inactivity: current M5 ATR(14) must be below the 35th percentile of the previous 288 completed M5 ATR values.
3. M15 inactivity: the most recent 16 completed M15 candle range width must be below the 35th percentile of the previous 120 completed 16-candle M15 range widths.
4. Downside sweep window: use the three completed M5 candles immediately before the rejection candle.
5. Downside sweep qualification: the three-candle low must be at least 0.40 times current M5 ATR(14) below the prior 96 completed M5 lows.
6. Drop qualification: the open of the first candle in the three-candle sweep window must be at least 1.50 times current M5 ATR(14) above the three-candle low.
7. H1 context: the latest completed H1 close must not be more than 4.0 current M5 ATR(14) below H1 EMA(50), and H1 EMA(50) slope over 12 H1 candles must not be strongly negative.
8. Rejection candle: the completed M5 rejection candle must trade at or below the sweep low area, close bullish, close in the upper 40% of its high-low range, have body at least 40% of its high-low range, and close back above the prior 96-low reference by at least 0.10 times current M5 ATR(14).
9. Entry: enter long at the next eligible M5 open after the rejection candle, using the existing Phase 0 cost model and one-position-at-a-time rule.
10. Stop: place the stop below the sweep low by 0.25 times current M5 ATR(14).
11. Target: use a fixed 1.5R target.
12. Expiration: if entry cannot be taken on the next eligible M5 bar, cancel the setup.
13. Invalidation: no setup if inactivity, sweep, rejection, or H1 context features are unavailable or fail their thresholds.

Implementation status:

The matching disabled research strategy is `src/phase0/strategies/emr_inactivity_long_v0.py`. It is not part of the active Phase 0 `all` registry and is not an approved EA.

## Expected Behavior

Expected behavior is moderate-to-low frequency. The candidate should cluster after quiet ranges that break down and quickly reclaim the breakdown area. It should lose when the sweep becomes a real downside continuation.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell, or a clear rejection if frequency is too low.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- EURUSD and USDJPY transfer may be weaker than XAUUSD, but should not collapse below the multisymbol PF threshold without a written XAU-specific defense.

## Why This Hypothesis Should Exist

Gold often compresses before liquidity-driven sweeps. Some downside sweeps after inactivity fail quickly when they are stop runs rather than sustained bearish repricing. This candidate isolates that behavior with objective inactivity, sweep, and reclaim rules.

This candidate is intentionally different from `breakout_retest`, `squeeze_breakout_long_v0`, and `post_spike_short_v0`. It tests long-side mean reversion after inactivity, not continuation or short-side exhaustion.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Manual adversarial review finds logic gaps above the allowed threshold.
- The strategy only passes after adding discretionary time, news, volatility, or price-action filters after results are known.

Code mapping:

- Inactivity and sweep feature construction: `src/phase0/strategies/emr_inactivity_long_v0.py::prepare_features`
- H1 context gate: `src/phase0/strategies/emr_inactivity_long_v0.py::_h1_context_ok`
- M5 sweep/rejection trigger: `src/phase0/strategies/emr_inactivity_long_v0.py::_setup_at_position`
- Stop/target construction: `src/phase0/strategies/emr_inactivity_long_v0.py::build_trade_plan`
