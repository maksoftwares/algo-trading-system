# H4 VIX Term Structure Inversion Reversal v0 Hypothesis

Hypothesis date: 2026-06-01
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H4 equity-volatility term-structure inversion reversal
Entry / decision timeframe: H4 completed-candle decisions with M5 execution bars in the Phase 0 simulator
Expected median hold bars M5-equivalent: 72-288
Expected median hold hours: 12-48
Expected decisions per week: 0-4
Timeframe diversification qualifies: yes
Hypothesis status: REGISTERED_RESEARCH_CANDIDATE
Expert id: `h4_vix_term_structure_inversion_reversal_v0`
Primary symbol: XAUUSD
Decision timeframe: H4
Execution timeframe: H4 market entry simulated through Phase 0 execution engine
Reference data: public FRED VIXCLS and VXVCLS daily observations, shifted one completed daily observation before use

## Mechanical Definition

This candidate tests whether shifted FRED VIX/VXV term-structure inversion marks equity-risk panic conditions where XAUUSD H4 overextension can reverse after a completed rejection candle.

The strategy computes shifted daily term-structure features:

- `vix_vxv_ratio = vix_close / vxv_close`
- `vix_vxv_ratio_change_5d`
- `vix_vxv_ratio_change_z126`

The daily term-structure features are shifted one row before being merged into H4 XAUUSD bars with backward as-of matching. No same-day future VIX/VXV close may be used.

LONG setup:

- VIX/VXV term structure is in contango-relief state: `vix_vxv_ratio <= 0.92`.
- Five-day term-structure change is negative enough: `vix_vxv_ratio_change_5d <= -0.020` or `vix_vxv_ratio_change_z126 <= -0.65`.
- XAUUSD H4 has declined over 12 bars: `h4_return_12 <= -0.006`.
- The signal candle closes bullish with close location at least `0.60`.
- Close is not more than `0.80 ATR` above H4 EMA40.

SHORT setup:

- VIX/VXV term structure is inverted: `vix_vxv_ratio >= 1.02`.
- Five-day term-structure change is positive enough: `vix_vxv_ratio_change_5d >= 0.025` or `vix_vxv_ratio_change_z126 >= 0.65`.
- XAUUSD H4 has rallied over 12 bars: `h4_return_12 >= 0.006`.
- The signal candle closes bearish with close location at most `0.40`.
- Close is not more than `0.80 ATR` below H4 EMA40.

Only one signal per ISO week and direction is allowed.

Trade plan:

- entry type: market
- stop distance: 1.15 * H4 ATR14
- target: 1.55R
- planned time stop: 6 H4 bars
- max holding bars in Phase 0 engine: 288 M5 bars

## Expected Behavior

Expected trade count per year: 15 to 80 trades.
Expected cost-adjusted PF: 1.30 to 1.65 if equity-volatility inversion/reversal spillover is real.
Expected losing-month percentage: 42% to 62%.
Expected worst single month: -7R to -15R.
Expected max consecutive zero months: 3.
Expected R-multiple distribution: many full-risk losses, occasional 1.55R wins after H4 rejection candles, and reduced same-week clustering due to the weekly direction cap.

The expected edge is not a breakout, retest, or level edge. It should appear when broad equity-volatility stress or relief is extreme and XAU has overextended into a completed H4 reversal candle.

## Why This Hypothesis Should Exist

VIX/VXV inversion is a broad equity-risk stress proxy. Gold can initially overreact to cross-asset risk repricing, especially when equity volatility spikes or relaxes quickly. A completed H4 rejection candle after that stress state may identify exhaustion in XAU's immediate response. This H4 version deliberately uses slower timing than the rejected H1 VIX/VXV variants to reduce cost pressure and avoid reacting to intraday noise.

## What Would Falsify It

Reject this candidate without tuning if any of the following occurs in first pass:

- fewer than 7 of 9 matrix cells reach PF >= 1.30
- fewer than 7 of 9 cells reach the minimum trade-count gate
- performance is isolated to one broker or one cost model
- P95-cost cells erase the edge
- concentration/activity gates fail materially
- the setup behaves like another high-frequency level/retest variant rather than a term-structure reversal mechanism

## Code Mapping

- Strategy class: `src/phase0/strategies/h4_vix_term_structure_inversion_reversal_v0.py`
- Data contract: `src/phase0/vix_term_structure_data.py`
- Shifted feature builder reused from: `src/phase0/strategies/h1_vix_term_structure_inversion_reversal_v0.py`
- Synthetic smoke context: `src/phase0/synthetic.py::_h4_vix_term_structure_inversion_reversal_context`

## Safety Boundary

This is Phase 0 research code only. It must not contain live trading calls, MT5 order placement, `OrderSend`, `CTrade`, `trade.Buy`, `trade.Sell`, position modification, martingale, grid, recovery mode, or averaging down.
