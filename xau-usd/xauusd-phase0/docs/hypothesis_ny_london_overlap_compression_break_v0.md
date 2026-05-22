# NY London Overlap Compression Break v0 Hypothesis

Hypothesis date: 2026-05-22
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 35-160
Expected cost-adjusted PF: 1.10-1.45
Expected losing-month percentage: 35%-60%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 2
Expected R-multiple distribution: Frequent -1R failed expansion losses, fewer +1.5R continuation winners, and no dependence on one outsized trade.

## Mechanical Definition

This candidate is a bidirectional XAUUSD overlap-session compression-break expert intended to test whether the London/New York liquidity handoff releases compressed price action into continuation often enough to survive Phase 0 costs and concentration gates.

The mechanical setup is:

1. Market and timeframe: XAUUSD with M5 entries, M15 compression context, and H1 directional context.
2. Session window: only completed M5 bars whose bar start time is from 13:00 UTC through 15:55 UTC are eligible. This fixed UTC window is used for v0 to avoid discretionary daylight-saving adjustments.
3. Compression range: use the most recent completed 12 M15 candles. The range high is the maximum high, and the range low is the minimum low across those completed candles.
4. Compression qualification: the 12-candle M15 range width must be below the 35th percentile of the previous 96 completed M15 range widths, and current M5 ATR(14) must be below the 45th percentile of the previous 288 completed M5 ATR values.
5. Directional context: long setups require the latest completed H1 close to be at or above H1 EMA(50) with non-negative EMA(50) slope over 12 completed H1 candles. Short setups require the latest completed H1 close to be at or below H1 EMA(50) with non-positive EMA(50) slope over 12 completed H1 candles.
6. Long trigger: a completed M5 candle must close above the M15 compression range high by at least 0.25 times current M5 ATR(14).
7. Short trigger: a completed M5 candle must close below the M15 compression range low by at least 0.25 times current M5 ATR(14).
8. Breakout candle quality: candle body must be at least 40% of the high-low range. Long breakouts must close in the upper 35% of the candle range. Short breakouts must close in the lower 35% of the candle range. The breakout candle range must not exceed 2.5 times current M5 ATR(14).
9. Entry: enter at the next eligible M5 open after the breakout candle, using the existing Phase 0 cost model and one-position-at-a-time rule.
10. Stop: for long setups, place the stop below the compression low or 1.0 times M5 ATR(14) below entry, whichever creates the wider protective distance. For short setups, place the stop above the compression high or 1.0 times M5 ATR(14) above entry, whichever creates the wider protective distance.
11. Target: use a fixed 1.5R target.
12. Frequency control: take at most one setup per UTC session day.
13. Invalidation: no setup if any required timeframe is missing, compression thresholds are unavailable, the breakout occurs outside the fixed overlap window, the candle fails the quality rule, or the stop/target construction creates non-positive risk.

Implementation status:

The research-only strategy implementation is mapped below. The candidate is disabled from the active Phase 0 registry and can only be run through explicit research commands.

## Expected Behavior

Expected behavior is moderate frequency, clustered around the London/New York overlap when liquidity expands and directional flows can leave a compressed intraday balance. The strategy should not trade every day because it requires both M15 compression and M5 ATR compression.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- EURUSD and USDJPY transfer should remain directionally coherent because the mechanism is session-liquidity expansion rather than XAU-only level behavior.

## Why This Hypothesis Should Exist

The London/New York overlap is one of the most liquid and information-rich intraday windows. When XAUUSD enters that window after measurable M15 and M5 compression, new flow can force a clean repricing. This candidate tests immediate expansion from compressed balance, not a level break and retest, and it allows both long and short continuation depending on the H1 context.

The candidate is intentionally independent from `breakout_retest` and `swing_breakout_retest_v0`. Those candidates require a break and retest of prior levels. This candidate requires compression before the overlap and immediate breakout candle quality, with no retest requirement.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Manual adversarial review finds logic gaps above the allowed threshold.
- The strategy only passes after adding discretionary time, news, volatility, or candle filters after results are known.

Code mapping after implementation:

- Compression feature construction: `src/phase0/strategies/ny_london_overlap_compression_break_v0.py::NyLondonOverlapCompressionBreakV0Strategy.prepare_features`
- M5 overlap and breakout trigger: `src/phase0/strategies/ny_london_overlap_compression_break_v0.py::NyLondonOverlapCompressionBreakV0Strategy._setup_at_position`
- H1 directional context gate: `src/phase0/strategies/ny_london_overlap_compression_break_v0.py::NyLondonOverlapCompressionBreakV0Strategy._setup_at_position`
- Stop/target construction: `src/phase0/strategies/ny_london_overlap_compression_break_v0.py::NyLondonOverlapCompressionBreakV0Strategy.build_trade_plan`
