# H4 MOVE/VIX Bond-Vol Shock Reversal v0 Hypothesis

Hypothesis date: 2026-06-01
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H4 rates-volatility shock exhaustion reversal
Entry / decision timeframe: H4 completed-candle decisions with M5 execution bars in the Phase 0 simulator
Expected median hold bars M5-equivalent: 96-336
Expected median hold hours: 16-56
Expected decisions per week: 0-4
Timeframe diversification qualifies: yes
Hypothesis status: REGISTERED_RESEARCH_CANDIDATE
Expert id: `h4_move_vix_bond_vol_shock_reversal_v0`
Primary symbol: XAUUSD
Decision timeframe: H4
Execution timeframe: H4 market entry simulated through Phase 0 execution engine
Reference data: public Yahoo MOVE daily proxy and public FRED VIXCLS observations, shifted one completed daily observation before use

## Mechanical Definition

This candidate tests whether rates-volatility shocks that are larger than equity-volatility shocks mark H4 XAUUSD exhaustion once a completed H4 reversal candle appears.

The strategy computes shifted daily shock features:

- `move_return_5d = log(move_close / move_close.shift(5))`
- `vix_return_5d = log(vix_close / vix_close.shift(5))`
- `move_vix_ratio = log(move_close / vix_close)`
- `move_vix_ratio_z252`
- `move_vix_ratio_change_5d`
- `move_vix_ratio_change_z126`

The daily MOVE/VIX features are shifted one row before being merged into H4 XAUUSD bars with backward as-of matching. No same-day future MOVE or VIX close may be used.

An H4 reversal setup is eligible only when:

- `move_return_5d >= 0.060`
- `move_return_5d > vix_return_5d + 0.015`
- `move_vix_ratio_z252 >= 0.35`
- `move_vix_ratio_change_5d >= 0.035` or `move_vix_ratio_change_z126 >= 0.40`
- `h4_atr14 > 0`

LONG setup:

- XAU has fallen over the last 6 H4 bars: `h4_return_6 <= -0.0045`
- the decline is not a crash extension: `h4_return_12 >= -0.0500`
- completed H4 candle closes above open
- completed H4 candle close-location is at least 0.60
- close is no more than 0.80 ATR above EMA40

SHORT setup:

- XAU has risen over the last 6 H4 bars: `h4_return_6 >= 0.0045`
- the rally is not a blow-off extension: `h4_return_12 <= 0.0500`
- completed H4 candle closes below open
- completed H4 candle close-location is no more than 0.40
- close is no more than 0.80 ATR below EMA40

Only one signal per ISO week and direction is allowed.

Trade plan:

- entry type: market
- stop distance: 1.15 * H4 ATR14
- target: 1.55R
- planned time stop: 7 H4 bars
- max holding bars in Phase 0 engine: 336 M5 bars

## Expected Behavior

Expected trade count per year: 15 to 80 trades.
Expected cost-adjusted PF: 1.30 to 1.65 if rates-volatility shock exhaustion has independent XAU value.
Expected losing-month percentage: 42% to 62%.
Expected worst single month: -7R to -15R.
Expected max consecutive zero months: 3.
Expected R-multiple distribution: many full-risk losses, occasional 1.55R wins after H4 exhaustion candles, and limited same-week clustering due to the weekly direction cap.

The expected edge is not a breakout, retest, or level edge. It should appear when rates-market volatility is rising materially faster than equity volatility and XAU initially overreacts before reversing on H4.

## Why This Hypothesis Should Exist

Gold often reacts to rates volatility through real-yield, duration, dollar-liquidity, and forced-positioning channels. A MOVE expansion that materially outpaces VIX can represent rates-specific stress rather than broad equity-risk fear. The rejected H1 MOVE/VIX variants may have been too noisy and cost-sensitive; this H4 version tests whether the same macro mechanism only becomes tradable after a slower completed-candle rejection.

## What Would Falsify It

Reject this candidate without tuning if any of the following occurs in first pass:

- fewer than 7 of 9 matrix cells reach PF >= 1.30
- fewer than 7 of 9 cells reach the minimum trade-count gate
- performance is isolated to one broker or one cost model
- P95-cost cells erase the edge
- concentration/activity gates fail materially
- the setup behaves like another high-frequency level/retest variant rather than a rates-volatility shock reversal mechanism

## Code Mapping

- Strategy class: `src/phase0/strategies/h4_move_vix_bond_vol_shock_reversal_v0.py`
- MOVE data contract: `src/phase0/move_bond_vol_data.py`
- VIX data contract: `src/phase0/vix_risk_data.py`
- Shifted feature builder reused from: `src/phase0/strategies/h1_move_vix_bond_vol_shock_reversal_v0.py`
- Synthetic smoke context: `src/phase0/synthetic.py::_h4_move_vix_bond_vol_shock_reversal_context`

## Safety Boundary

This is Phase 0 research code only. It must not contain live trading calls, MT5 order placement, `OrderSend`, `CTrade`, `trade.Buy`, `trade.Sell`, position modification, martingale, grid, recovery mode, or averaging down.
