# Review Prompt - A1 XAU Regime Router / R4 Chop Next Direction

Please review the current repo state after the 2026-07-09 regime-router and R4/chop work. Return your response as a markdown file.

## Goal

We are trying to build an exact-MT5 XAUUSD regime-specialist portfolio that is practical for eventual demo review. Current target shape:

- defend recent non-uptrend markets better than the long-only edge,
- preserve profitable full-window behavior,
- avoid fake activity/filler,
- keep the result interpretable by regime,
- do not overfit hours/months after seeing failures,
- use exact MT5 Strategy Tester evidence, not Python-only backtests, for candidate promotion.

## Current Best Book

Current best defensible portfolio is still:

`A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10_KEPT.csv`

Summary:

- 678 trades
- WR 51.03%
- realized W/L 2.6082
- PF 2.7182
- net +$9,640.05
- stressed net after -$0.30/ticket +$9,436.65
- recent 3 months: 59 trades, +$764.92
- max closed DD $889.69

This is R1 long plus R2 pullback short plus R2 continuation short.

## New Work To Review

### 1. Ten-year regime map

Files:

- `xau-usd/xauusd-phase1/scripts/analyze_xau_10y_regime_map.py`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_10Y_REGIME_MAP_20260709.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_10Y_REGIME_MAP_20260709_DAYS.csv`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_10Y_REGIME_MAP_20260709_MONTHS.csv`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_10Y_REGIME_MAP_20260709_SEGMENTS.csv`

Key conclusion:

- 2016-2026 XAU regimes are not one thing. We saw uptrend, downtrend, chop, compression, transition, shock.
- March-June 2026 was mainly chop/downtrend/transition, not the regime where the R1 long edge should be expected to fire.
- This supports the router/specialist approach, but not naive daily filtering.

### 2. Current candidate regime attribution

Files:

- `xau-usd/xauusd-phase1/scripts/analyze_a1_current_candidate_regime_attribution.py`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_CURRENT_CANDIDATE_REGIME_ATTRIBUTION_20260709.md`

Key conclusion:

- R1 long remains strongest in uptrend but loses too much if filtered by a coarse previous-D1 uptrend-only rule.
- R2 continuation short is genuinely useful in recent downtrend/transition.
- R3 compression long is historically powerful but not active enough recently, and its May 2026 loss occurred in chop.
- R4 prior-day reclaim does not earn its keep, even inside chop.
- Best overlay remains R1+R2 current best; naive regime overlay did not improve it.

### 3. R4 prior-day reclaim exact-MT5

Files:

- `xau-usd/xauusd-phase1/docs/A1_XAU_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_PREREG_2026_07_09.md`
- `xau-usd/xauusd-phase1/scripts/run_a1_r4_chop_prior_day_reclaim_v1_exact.py`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_PRIOR_DAY_RECLAIM_V1_EXACT_20260709.md`

Result:

- No deployable survivor.
- Both-direction prior-day reclaim: 526 trades, WR 33.84%, W/L 2.0740, PF 1.0608, net +$95.06.
- Recent 3 months: 24 trades, -$26.73.
- Inside previous-D1 chop it was still negative.

### 4. R4 opening-range reversal exact-MT5

Files:

- `xau-usd/xauusd-phase1/docs/A1_XAU_R4_CHOP_OPENING_RANGE_REVERSAL_V1_EXACT_PREREG_2026_07_09.md`
- `xau-usd/xauusd-phase1/scripts/run_a1_r4_chop_opening_range_reversal_v1_exact.py`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R4_CHOP_OPENING_RANGE_REVERSAL_V1_EXACT_20260709.md`

Result:

- Status: `R4_CHOP_ORREV_V1_SHADOW_ONLY`
- It adds activity and a little profit, but not cleanly enough.

Standalone R4 OR both:

- 578 trades
- WR 33.22%
- W/L 2.1668
- PF 1.0778
- net +$125.16
- stressed net -$48.24
- recent 3 months: 46 trades, +$43.08
- top-10-trades-removed net -$111.15

Combined R1+R2+R4 OR both:

- 1,256 trades
- WR 42.83%
- W/L 3.1398
- PF 2.3527
- net +$9,765.21
- stressed net +$9,388.41
- recent 3 months: 105 trades, +$808.00
- max DD $846.66

This improves net, activity, recent net, and drawdown versus R1+R2, but win rate collapses below the desired shape. We treated it as shadow-only/diagnostic.

## Questions For Reviewer

1. Is the ten-year regime taxonomy methodologically acceptable as a diagnostic tool, given it is not used as a same-day deployable filter?
2. Is our conclusion correct that naive previous-D1 regime filtering is too coarse for production routing?
3. Should R4/chop continue from opening-range reversal, or should we retire this branch because the standalone source is low-WR and top-trade fragile?
4. If continuing R4, what source class is most defensible next?
   - intraday VWAP/mean-reversion bands,
   - Asian range fade,
   - liquidity sweep around session highs/lows,
   - compression breakout-failure with stricter close-location,
   - time-boxed no-trade/chop-defense governor instead of a trade source,
   - something else?
5. Is the current best book, R1+R2, still the only defensible forward candidate while R4 remains shadow-only?
6. Is it acceptable to carry R4 OR as a shadow telemetry layer because it improves recent net/activity, or does the low standalone WR make that misleading?
7. What exact preregistered next test would you run in one iteration, with no parameter grid?
8. What would be the most important kill rule to prevent us from wasting more time on weak chop fillers?
9. Are we missing a better way to define the router state intraday from MT5-native data rather than relying on the daily regime audit?
10. Please identify any code, data, or reporting gaps that would block a serious review.

## Requested Output

Please return a markdown review file with:

- strict verdict,
- methodology issues,
- overfitting risks,
- interpretation of R4 OR shadow-only result,
- whether to continue R4 or move elsewhere,
- one best next work order,
- exact pass/fail criteria for that work order,
- files you inspected.

