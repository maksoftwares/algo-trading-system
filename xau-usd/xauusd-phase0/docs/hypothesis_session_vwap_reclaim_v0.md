# Session VWAP Reclaim v0 Hypothesis

Hypothesis date: 2026-05-22
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 40-220
Expected cost-adjusted PF: 1.10-1.45
Expected losing-month percentage: 35%-60%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 2
Expected R-multiple distribution: Many failed reclaims near -1R, fewer 1.5R session-mean reclaim wins, and no dependence on one outsized winner.

## Mechanical Definition

This candidate is a bidirectional XAUUSD session VWAP reclaim expert. It tests whether a large intraday deviation away from the anchored 07:00-17:00 UTC session VWAP/proxy that closes back through VWAP has enough mean-reversion edge to survive Phase 0 costs and concentration gates.

The mechanical setup is:

1. Market and timeframe: XAUUSD with M5 entries.
2. Session window: use completed M5 bars whose bar-start time is from 07:00 UTC inclusive to 17:00 UTC exclusive.
3. VWAP/proxy: compute a cumulative session VWAP from typical price `(high + low + close) / 3`. If tick volume, real volume, or volume is present and positive, use it as the weight; otherwise use equal weights as a deterministic session typical-price average proxy.
4. Trigger window: only completed M5 bars from 08:00 UTC inclusive to 17:00 UTC exclusive can trigger, so at least one hour of session VWAP history exists.
5. Long reclaim: the trigger candle must trade at least 1.00 times current M5 ATR(14) below the current session VWAP and close at least 0.10 times current M5 ATR(14) above the session VWAP.
6. Long reclaim candle: the trigger candle must close bullish, close in the upper 40% of its high-low range, and have body at least 30% of its high-low range.
7. Short reclaim: the trigger candle must trade at least 1.00 times current M5 ATR(14) above the current session VWAP and close at least 0.10 times current M5 ATR(14) below the session VWAP.
8. Short reclaim candle: the trigger candle must close bearish, close in the lower 40% of its high-low range, and have body at least 30% of its high-low range.
9. Entry: enter at the next eligible M5 open after the reclaim candle, using the existing Phase 0 cost model and one-position-at-a-time rule.
10. Stop: for longs, stop below the sweep low by 0.25 times current M5 ATR(14); for shorts, stop above the sweep high by 0.25 times current M5 ATR(14).
11. Target: use a fixed 1.5R target.
12. Daily duplicate rule: allow at most one long and one short setup per UTC date.
13. Invalidation: no setup if session VWAP/proxy, ATR, or reclaim candle requirements are unavailable.

Implementation status:

The matching disabled research strategy is `src/phase0/strategies/session_vwap_reclaim_v0.py`. It is not part of the active Phase 0 `all` registry and is not an approved EA.

## Expected Behavior

Expected behavior is moderate frequency. The candidate should cluster around sharp intraday excursions away from the session mean that reclaim VWAP quickly. It should lose when the deviation is the beginning of a true trend day.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell, or a clear rejection if frequency is too low.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- EURUSD and USDJPY transfer may be weaker than XAUUSD, but should not collapse below the multisymbol PF threshold without a written XAU-specific defense.

## Why This Hypothesis Should Exist

Session VWAP is a common intraday reference for flow and inventory. A sharp deviation that quickly reclaims VWAP may indicate failed directional acceptance and a return to session mean. This candidate tests that behavior with a deterministic VWAP/proxy and completed-candle reclaim rules.

This candidate is intentionally different from session range breakouts. It references an anchored session mean rather than a discrete high/low level.

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

- Session VWAP/proxy construction: `src/phase0/strategies/session_vwap_reclaim_v0.py::prepare_features`
- VWAP reclaim trigger: `src/phase0/strategies/session_vwap_reclaim_v0.py::_setup_at_position`
- Stop/target construction: `src/phase0/strategies/session_vwap_reclaim_v0.py::build_trade_plan`
