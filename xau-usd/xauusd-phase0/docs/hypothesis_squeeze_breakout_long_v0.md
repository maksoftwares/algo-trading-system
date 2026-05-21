# Squeeze Breakout Long v0 Hypothesis

Hypothesis date: 2026-05-22
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 35-140
Expected cost-adjusted PF: 1.10-1.45
Expected losing-month percentage: 35%-55%
Expected worst single month: -8R to -16R
Expected max consecutive zero months: 2
Expected R-multiple distribution: Many small losses near -1R, a smaller set of +1.5R winners, and limited tail contribution from any single trade.

## Mechanical Definition

This candidate is a long-only XAUUSD compression-expansion expert intended to test whether quiet M15 ranges release into continuation moves often enough to survive Phase 0 costs and concentration gates.

The mechanical setup is:

1. Market and timeframe: XAUUSD with M5 entries, M15 compression context, and H1 trend/activity context.
2. Compression range: use the most recent completed 16 M15 candles. The range high is the maximum high, and the range low is the minimum low across those completed candles.
3. Compression qualification: the 16-candle M15 range width must be below the 35th percentile of the previous 120 completed M15 range widths, and M5 ATR(14) must be below the 40th percentile of the previous 288 completed M5 ATR values.
4. H1 context: the latest completed H1 close must be above H1 EMA(50), and H1 EMA(50) must not be sloping down over the previous 12 completed H1 candles.
5. Breakout trigger: a completed M5 candle must close above the M15 compression range high by at least 0.20 times current M5 ATR(14).
6. Breakout candle quality: the breakout candle close must be in the upper 35% of its high-low range, and candle body must be at least 45% of the high-low range.
7. Entry: enter long at the next eligible M5 open after the breakout candle, using the existing Phase 0 cost model and one-position-at-a-time rule.
8. Stop: place the stop below the compression range low or 1.0 times M5 ATR(14) below entry, whichever creates the wider protective distance.
9. Target: use a fixed 1.5R target.
10. Expiration: if entry cannot be taken on the next eligible M5 bar, cancel the setup.
11. Invalidation: no setup if the compression range is older than 6 hours, the breakout candle range exceeds 2.5 times M5 ATR(14), spread is above the active cost model allowance, or the signal occurs in a blocked session window.

Implementation status:

No strategy class is enabled for this candidate yet. The hypothesis is registered first so any future implementation and result-producing run can be reviewed against this fixed definition.

## Expected Behavior

Expected behavior is moderate frequency with clustered opportunities around London and New York activity transitions. The strategy should not trade every day. It should earn through asymmetric continuation after volatility compression, while accepting frequent failed breaks as normal losses.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- EURUSD and USDJPY transfer may be weaker than XAUUSD, but should not collapse below the multisymbol PF threshold without a written XAU-specific defense.

## Why This Hypothesis Should Exist

Gold often alternates between low-volatility balance and fast repricing when session liquidity expands or macro positioning becomes one-sided. A completed-candle compression range gives the strategy an objective reference point. A long-only first version keeps the behavioral thesis narrow: it tests whether upside continuation after compression is persistent enough without mixing it with short-side exhaustion behavior.

This candidate is intentionally different from `breakout_retest`. `breakout_retest` waits for a level break and retest. `squeeze_breakout_long_v0` tests immediate expansion from compression with no retest requirement. If both eventually pass independently, they would diversify the portfolio across different market mechanics.

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

Code mapping after implementation:

- Compression feature construction: pending future strategy implementation.
- H1 context gate: pending future strategy implementation.
- M5 breakout trigger: pending future strategy implementation.
- Stop/target construction: pending future strategy implementation.

The mapping above is intentionally marked as future implementation work; it is not evidence and does not authorize a result-producing run.
