# H4 XLU/XLK Defensive Rotation Reversal v0 Hypothesis

Hypothesis date: 2026-06-01
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H4 defensive-sector-versus-technology rotation overreaction reversal
Entry / decision timeframe: H4 completed-candle decisions with M5 execution bars in the Phase 0 simulator
Expected median hold bars M5-equivalent: 96-336
Expected median hold hours: 16-56
Expected decisions per week: 0-4
Timeframe diversification qualifies: yes
Hypothesis status: REGISTERED_RESEARCH_CANDIDATE
Expert id: `h4_xlu_xlk_defensive_rotation_reversal_v0`
Primary symbol: XAUUSD
Decision timeframe: H4
Execution timeframe: H4 market entry simulated through Phase 0 execution engine
Reference data: public Yahoo daily XLU/XLK OHLCV proxy, shifted one completed daily observation before use

## Mechanical Definition

This candidate tests whether completed daily defensive-sector rotation between utilities (`XLU`) and technology (`XLK`) identifies H4 XAUUSD overreaction/reversal opportunities.

The strategy computes shifted XLU/XLK daily features:

- `xlu_return_5d = log(xlu_close / xlu_close.shift(5))`
- `xlk_return_5d = log(xlk_close / xlk_close.shift(5))`
- `defensive_rotation_5d = xlu_return_5d - xlk_return_5d`
- `defensive_rotation_z126`
- `defensive_rotation_abs_percentile252`

The daily reference features are shifted one row before being merged into H4 XAUUSD bars with backward as-of matching. No same-day future XLU/XLK close may be used.

An H4 reversal setup is eligible only when:

- `abs(defensive_rotation_5d) >= 0.0100`
- `abs(defensive_rotation_z126) >= 0.35`
- `defensive_rotation_abs_percentile252 >= 0.55`
- `h4_atr14 > 0`

LONG setup:

- `defensive_rotation_5d >= 0.0100`
- XAU has fallen over the last 12 H4 bars: `h4_return_12 <= -0.0045`
- the decline is not a crash extension: `h4_return_24 >= -0.0450`
- short-term H4 return has not already recovered strongly: `h4_return_6 <= 0.0010`
- completed H4 candle closes above open
- completed H4 candle close-location is at least 0.60
- close is no more than 2.50 ATR below EMA40

SHORT setup:

- `defensive_rotation_5d <= -0.0100`
- XAU has risen over the last 12 H4 bars: `h4_return_12 >= 0.0045`
- the rally is not a blow-off extension: `h4_return_24 <= 0.0450`
- short-term H4 return has not already rolled over strongly: `h4_return_6 >= -0.0010`
- completed H4 candle closes below open
- completed H4 candle close-location is no more than 0.40
- close is no more than 2.50 ATR above EMA40

Only one signal per ISO week and direction is allowed.

Trade plan:

- entry type: market
- stop distance: 1.15 * H4 ATR14
- target: 1.55R
- planned time stop: 7 H4 bars
- max holding bars in Phase 0 engine: 336 M5 bars

## Expected Behavior

Expected trade count per year: 25 to 110 trades.
Expected cost-adjusted PF: 1.30 to 1.65 if the defensive-sector reversal mechanism is real.
Expected losing-month percentage: 40% to 58%.
Expected worst single month: -7R to -14R.
Expected max consecutive zero months: 3.
Expected R-multiple distribution: many full-risk losses, occasional 1.55R wins after H4 overreaction candles, and limited same-week clustering due to the weekly direction cap.

The expected edge is not a breakout, retest, or level edge. It should appear when sector rotation into defensive utilities or into technology/risk appetite leads or conflicts with XAU risk/safe-haven repricing.

## Why This Hypothesis Should Exist

XLU/XLK is a traded sector proxy for defensive equity demand versus technology-led risk appetite. When utilities outperform technology, the market may be rotating defensive before gold fully prices safe-haven demand. When technology outperforms utilities, gold may lose safe-haven premium after an overextended rally.

The candidate deliberately waits for XAU to move against the shifted sector-rotation pressure and then print a completed H4 rejection candle. The thesis is that H4 reversal timing can reduce cost pressure while still reacting quickly enough to a broad risk-state shift.

## What Would Falsify It

Reject this candidate without tuning if any of the following occurs in first pass:

- fewer than 7 of 9 matrix cells reach PF >= 1.30
- fewer than 7 of 9 cells reach the minimum trade-count gate
- performance is isolated to one broker or one cost model
- P95-cost cells erase the edge
- concentration/activity gates fail materially
- the setup behaves like another high-frequency level/retest variant rather than a defensive-sector reversal mechanism

## Code Mapping

- Strategy class: `src/phase0/strategies/h4_xlu_xlk_defensive_rotation_reversal_v0.py`
- XLU/XLK data contract: `src/phase0/xlu_xlk_defensive_rotation_data.py`
- Shifted feature builder reused from: `src/phase0/strategies/h1_xlu_xlk_defensive_rotation_followthrough_v0.py`
- Synthetic smoke context: `src/phase0/synthetic.py::_h4_xlu_xlk_defensive_rotation_reversal_context`

## Safety Boundary

This is Phase 0 research code only. It must not contain live trading calls, MT5 order placement, `OrderSend`, `CTrade`, `trade.Buy`, `trade.Sell`, position modification, martingale, grid, recovery mode, or averaging down.
