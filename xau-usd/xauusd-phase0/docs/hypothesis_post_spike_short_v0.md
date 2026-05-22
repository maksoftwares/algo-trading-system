# Post Spike Short v0 Hypothesis

Hypothesis date: 2026-05-22
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 25-120
Expected cost-adjusted PF: 1.10-1.45
Expected losing-month percentage: 35%-60%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 2
Expected R-multiple distribution: Many failed fade attempts near -1R, fewer +1.5R exhaustion wins, and no dependence on one outsized winner.

## Mechanical Definition

This candidate is a short-only XAUUSD post-spike exhaustion expert. It tests whether fast upside displacement into a fresh short-term high tends to mean-revert enough to survive costs and the Phase 0 concentration gates.

The mechanical setup is:

1. Market and timeframe: XAUUSD with M5 entries, M15 extension context, and H1 trend/activity context.
2. Spike window: use the three completed M5 candles immediately before the rejection candle.
3. Spike qualification: the high of that three-candle window must be at least 2.0 times current M5 ATR(14) above the open of the first candle in the spike window.
4. Fresh-high qualification: the spike-window high must exceed the prior 96 completed M5 highs by at least 0.50 times current M5 ATR(14).
5. M15 extension: the spike-window high must be at or above the prior 32 completed M15 high.
6. H1 context: the latest completed H1 EMA(50) slope over 12 H1 candles must be non-positive, and H1 close must not be extended more than 4.0 current M5 ATR(14) above H1 EMA(50).
7. Rejection candle: the completed M5 rejection candle must trade within 0.25 times current M5 ATR(14) of the spike-window high, close bearish, close in the lower 40% of its high-low range, have body at least 45% of its high-low range, and close at least 0.35 times current M5 ATR(14) below the spike-window high.
8. Entry: enter short at the next eligible M5 open after the rejection candle, using the existing Phase 0 cost model and one-position-at-a-time rule.
9. Stop: place the stop above the spike-window high by 0.25 times current M5 ATR(14).
10. Target: use a fixed 1.5R target.
11. Expiration: if entry cannot be taken on the next eligible M5 bar, cancel the setup.
12. Invalidation: no setup if any required M5, M15, or H1 feature is unavailable, the spike does not create a fresh high, the rejection candle closes bullish, or the H1 context gate fails.

Implementation status:

The matching disabled research strategy is `src/phase0/strategies/post_spike_short_v0.py`. It is not part of the active Phase 0 `all` registry and is not an approved EA.

## Expected Behavior

Expected behavior is moderate-to-low frequency. The candidate should cluster around sharp upside displacements and should lose when a spike becomes a genuine breakout instead of an exhaustion move.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell, or a clear rejection if frequency is too low.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- EURUSD and USDJPY transfer may be weaker than XAUUSD, but should not collapse below the multisymbol PF threshold without a written XAU-specific defense.

## Why This Hypothesis Should Exist

Gold frequently produces fast upside repricing into visible short-term highs, especially around session liquidity changes and stop runs. Some of those spikes fail quickly when the move is driven by liquidity rather than sustained directional demand. This candidate isolates that behavior with a completed-candle spike and rejection definition.

This candidate is intentionally different from `breakout_retest` and `squeeze_breakout_long_v0`. It tests short-side exhaustion after a rapid upside move, not continuation after a level break or compression release.

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

- Spike and fresh-high feature construction: `src/phase0/strategies/post_spike_short_v0.py::prepare_features`
- H1 context gate: `src/phase0/strategies/post_spike_short_v0.py::_h1_context_ok`
- M5 spike/rejection trigger: `src/phase0/strategies/post_spike_short_v0.py::_setup_at_position`
- Stop/target construction: `src/phase0/strategies/post_spike_short_v0.py::build_trade_plan`
