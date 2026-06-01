# Hypothesis: H4 HYG/IEF Credit-Risk Rotation Reversal v0

Hypothesis date: 2026-06-01
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H4 credit-risk-versus-Treasury rotation overreaction reversal
Entry / decision timeframe: H4 completed-candle decisions with M5 execution bars in the Phase 0 simulator
Expected median hold bars M5-equivalent: 96-336
Expected median hold hours: 16-56
Expected decisions per week: 0-4
Timeframe diversification qualifies: yes
Hypothesis status: REGISTERED_RESEARCH_CANDIDATE
Expert id: `h4_hyg_ief_credit_risk_rotation_reversal_v0`
Primary symbol: XAUUSD
Decision timeframe: H4
Execution timeframe: H4 market entry simulated through Phase 0 execution engine
Reference data: public Yahoo daily HYG/IEF OHLCV proxy, shifted one completed daily observation before use

## Mechanical Definition

This candidate tests whether completed daily credit-risk rotation between high-yield credit (`HYG`) and intermediate Treasuries (`IEF`) identifies H4 XAUUSD overreaction/reversal opportunities.

The strategy computes shifted HYG/IEF daily features:

- `hyg_return_5d = log(hyg_close / hyg_close.shift(5))`
- `ief_return_5d = log(ief_close / ief_close.shift(5))`
- `credit_stress_5d = ief_return_5d - hyg_return_5d`
- `credit_stress_z126`
- `credit_stress_abs_percentile252`

The daily reference features are shifted one row before being merged into H4 XAUUSD bars with backward as-of matching. No same-day future HYG/IEF close may be used.

An H4 reversal setup is eligible only when:

- `abs(credit_stress_5d) >= 0.0060`
- `abs(credit_stress_z126) >= 0.35`
- `credit_stress_abs_percentile252 >= 0.55`
- `h4_atr14 > 0`

LONG setup:

- `credit_stress_5d >= 0.0060`
- XAU has fallen over the last 12 H4 bars: `h4_return_12 <= -0.0045`
- the decline is not a crash extension: `h4_return_24 >= -0.0450`
- short-term H4 return has not already recovered strongly: `h4_return_6 <= 0.0010`
- completed H4 candle closes above open
- completed H4 candle close-location is at least 0.60
- close is no more than 2.50 ATR below EMA40

SHORT setup:

- `credit_stress_5d <= -0.0060`
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

Expected trade count per year: 25 to 95 trades.
Expected cost-adjusted PF: 1.30 to 1.65 if the credit-stress reversal mechanism is real.
Expected losing-month percentage: 40% to 55%.
Expected worst single month: -6R to -12R.
Expected max consecutive zero months: 2.
Expected R-multiple distribution: many small full-risk losses, a thinner set of 1.55R wins, and limited same-week repeat clustering due to the weekly direction cap.

The expected edge is not a breakout, retest, or level edge. It should appear when credit markets rotate abruptly into or out of risk-off posture and XAU initially overshoots in the opposite direction before mean-reverting on H4.

## Why This Hypothesis Should Exist

HYG/IEF is a traded proxy for credit-risk appetite versus Treasury safety demand. When `IEF` outperforms `HYG`, credit stress is rising. Gold can behave as a safety asset, but spot XAU may initially move the wrong way because of dollar/liquidity pressure or forced deleveraging. The hypothesis is that a completed H4 rejection candle after that mismatch captures the point where gold starts to reprice the credit-risk state.

The inverse applies when HYG outperforms IEF: credit relief can reduce safe-haven demand for gold after an overextended XAU rally.

## What Would Falsify It

Reject this candidate without tuning if any of the following occurs in first pass:

- fewer than 7 of 9 matrix cells reach PF >= 1.30
- fewer than 7 of 9 cells reach the minimum trade-count gate
- performance is isolated to one broker or one cost model
- P95-cost cells erase the edge
- concentration/activity gates fail materially
- the setup behaves like another high-frequency level/retest variant rather than a credit-risk reversal mechanism

## Code Mapping

- Strategy class: `src/phase0/strategies/h4_hyg_ief_credit_risk_rotation_reversal_v0.py`
- HYG/IEF data contract: `src/phase0/hyg_ief_credit_risk_rotation_data.py`
- HYG/IEF shifted feature builder reused from: `src/phase0/strategies/h1_hyg_ief_credit_risk_rotation_followthrough_v0.py`
- Synthetic smoke context: `src/phase0/synthetic.py::_h4_hyg_ief_credit_risk_rotation_reversal_context`

## Safety Boundary

This is Phase 0 research code only. It must not contain live trading calls, MT5 order placement, `OrderSend`, `CTrade`, `trade.Buy`, `trade.Sell`, position modification, martingale, grid, recovery mode, or averaging down.
