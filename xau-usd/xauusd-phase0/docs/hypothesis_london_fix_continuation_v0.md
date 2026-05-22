# London Fix Continuation v0 Hypothesis

Hypothesis date: 2026-05-22
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 35-150
Expected cost-adjusted PF: 1.10-1.45
Expected losing-month percentage: 35%-60%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 2
Expected R-multiple distribution: Many failed continuation attempts near -1R, fewer 1.5R imbalance continuations, and no dependence on one outsized winner.

## Mechanical Definition

This candidate is a bidirectional XAUUSD London afternoon-fix continuation expert. It tests whether displacement out of the immediate pre-fix range after the 15:00 Europe/London fix proxy persists enough to survive Phase 0 costs and concentration gates.

The mechanical setup is:

1. Market and timeframe: XAUUSD with M5 entries, M15 range-normalization context, and Europe/London local clock handling.
2. Fix proxy: use the 15:00 Europe/London afternoon fix boundary, with daylight-saving conversion handled by the timezone database.
3. Pre-fix range: use completed M5 bars whose Europe/London bar-start time is from 14:30 inclusive to 15:00 exclusive. The highest high is the pre-fix high and the lowest low is the pre-fix low for that London-local date.
4. Post-fix trigger window: only completed M5 bars whose Europe/London bar-start time is from 15:00 inclusive to 16:00 exclusive can trigger.
5. Range sanity gate: the pre-fix range width must be at least 0.25 times and at most 4.0 times the latest completed M15 ATR(14).
6. Long continuation: the post-fix M5 bar must close at least 0.20 times current M5 ATR(14) above the pre-fix high, close bullish, close in the upper 40% of its high-low range, and have body at least 35% of its high-low range.
7. Short continuation: the post-fix M5 bar must close at least 0.20 times current M5 ATR(14) below the pre-fix low, close bearish, close in the lower 40% of its high-low range, and have body at least 35% of its high-low range.
8. Entry: enter at the next eligible M5 open after the breakout candle, using the existing Phase 0 cost model and one-position-at-a-time rule.
9. Stop: for longs, stop at the lesser of the pre-fix low or one current M5 ATR(14) below entry; for shorts, stop at the greater of the pre-fix high or one current M5 ATR(14) above entry.
10. Target: use a fixed 1.5R target.
11. Daily duplicate rule: allow at most one post-fix continuation setup per London-local date.
12. Invalidation: no setup if pre-fix range values, ATR values, local timestamps, or breakout candle requirements are unavailable.

Implementation status:

The matching disabled research strategy is `src/phase0/strategies/london_fix_continuation_v0.py`. It is not part of the active Phase 0 `all` registry and is not an approved EA.

## Expected Behavior

Expected behavior is moderate frequency. The candidate should cluster around the afternoon gold-fix window and should lose when the post-fix move is only a brief stop run rather than a directional imbalance.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell, or a clear rejection if frequency is too low.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- EURUSD and USDJPY transfer may be weaker than XAUUSD, but should not collapse below the multisymbol PF threshold without a written XAU-specific defense.

## Why This Hypothesis Should Exist

Gold has a structurally important afternoon London fixing process. The period immediately after the fix can express residual flow or inventory imbalance. This candidate tests whether a completed-candle break out of the pre-fix range behaves as continuation, without discretionary news labels or post-result filters.

This candidate is intentionally different from `breakout_retest`. It uses a fixed calendar/session event and immediate range displacement, not a general technical level retest.

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

- Pre-fix range and London-local clock feature construction: `src/phase0/strategies/london_fix_continuation_v0.py::prepare_features`
- Post-fix continuation trigger: `src/phase0/strategies/london_fix_continuation_v0.py::_setup_at_position`
- Stop/target construction: `src/phase0/strategies/london_fix_continuation_v0.py::build_trade_plan`
