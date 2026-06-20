# Hypothesis: EURUSD H4 Swing Trend Continuation Pullback V0

Expert candidate ID: `eurusd_h4_swing_trend_continuation_pullback_v0`
Version: `v0`
Status: LOCKED
Mechanic family: `eurusd_h4_swing_trend_continuation_pullback`
Entry / decision timeframe: `H4`
Reference timeframe: `D1`, `H4`
Expected median hold bars M5-equivalent: `288-1440`
Expected median hold hours: `24-120`
Expected decisions per week: `1-4`
Expected trades per year: `50-150`
Timeframe diversification qualifies: `YES`
Same-family as breakout_retest: `NO`
Expected median stop distance points: `H4 ATR-relative; expected near 3 x H4 ATR14, approximately 600-1300 EURUSD points`
Expected median cost_R under measured P95 spread: `<= 0.04 including spread, slippage, and measured Capital.com overnight financing`
Expected PF after measured cost: `>= 1.25 discovery, >= 1.30 promotion`
Expected average net R: `>= +0.10R discovery, >= +0.15R promotion`
Expected win rate range: `38%-55%`
Expected worst month R: `>= -8R`
Expected losing-month percentage: `<= 45%`
Expected max zero-trade months: `2`
Why this behavior should exist on XAUUSD: `It should not be treated as an XAUUSD behavior. This is a deliberate reallocation away from XAUUSD after XAU intraday entries were falsified net-of-cost. The testable behavior is EURUSD H4 trend continuation in low-cost swing geometry.`
What would falsify this hypothesis: `Any failure of the raw deduped net-of-cost acceptance bar defined below falsifies V0.`
Forbidden changes after lock: `No threshold tuning, no symbol switch, no timeframe switch, no stop multiplier changes, no session filter, no adding macro filters, no removing swap/financing cost, and no interpreting gross or cost-filter survivor slices as approval evidence.`
Allowed bug fixes after lock: `Timestamp alignment, indicator calculation bugs, broker point/digit normalization, swap normalization bugs, and reporting-only fixes that do not alter candidate decisions.`

## Status And Boundary

This hypothesis is locked after owner selection and Claude Round 11 pre-lock approval. The owner selected the `Capital.com / EURUSD / H4 / swing_atr_3x` cost-geometry cell on 2026-06-19.

It is authorized for offline Phase 0R screening only. It is not authorized for MT5 runtime, observer attachment, paper trading, or demo execution.

The target deployment broker for the research cell is `Capital.ComMena-Demo` / Capital.com data. Pepperstone XAU H4 from the cost map remains comparison-only evidence and is not selectable for this hypothesis.

## Why This Behavior Should Exist On EURUSD

The XAU intraday effort failed because spread and slippage consumed too much of the stop distance, and because short-horizon retest entries were fragile during trend and whipsaw regimes. The cost-geometry map shows that EURUSD H4 swing trades have structurally better cost geometry: Capital.com EURUSD H4 swing cost_R was approximately `0.00975` at P95 spread before slippage and financing.

The intended edge is simple: when EURUSD has an established daily/H4 trend, a controlled H4 pullback that does not break the trend structure may resume in the trend direction. The H4 timeframe is chosen because spread is small relative to ATR-based stop distance, making a real net edge possible if the entry has any genuine directional information.

This is not a retest hypothesis. It is not a round-number hypothesis. It is not a session scalping hypothesis. It is a low-cost swing trend-continuation hypothesis.

## Fixed Mechanical Definition

All rules use completed bars only. No future-bar confirmation, centered pivots, revised values, or same-bar hindsight is allowed.

Primary symbol:

- `EURUSD`

Primary broker/data cell:

- `capital_com`

Decision timeframe:

- `H4`

### Trend Eligibility

Long trend is eligible only when both are true:

- D1 EMA50[1] - D1 EMA50[6] > `0`.
- H4 EMA20[1] > H4 EMA50[1].

Short trend is eligible only when both are true:

- D1 EMA50[1] - D1 EMA50[6] < `0`.
- H4 EMA20[1] < H4 EMA50[1].

The D1 slope is a direction filter only. No D1 price-location veto is used in V0.

### Pullback Eligibility

The pullback window is the last `6` completed H4 candles ending at H4 bar `[1]`.

Long pullback is eligible only when all are true:

- At least one candle in the pullback window has low <= H4 EMA20[1] + `0.20 x H4 ATR14[1]`.
- No candle in the last `3` completed H4 bars closes below H4 EMA50[1].
- Pullback depth from the highest high of the last `10` completed H4 bars to the lowest low of the pullback window is between `0.50 x H4 ATR14[1]` and `2.00 x H4 ATR14[1]`.

Short pullback is eligible only when all are true:

- At least one candle in the pullback window has high >= H4 EMA20[1] - `0.20 x H4 ATR14[1]`.
- No candle in the last `3` completed H4 bars closes above H4 EMA50[1].
- Pullback depth from the lowest low of the last `10` completed H4 bars to the highest high of the pullback window is between `0.50 x H4 ATR14[1]` and `2.00 x H4 ATR14[1]`.

### H4 Trigger

Long trigger requires all:

- H4 close[1] > H4 EMA20[1].
- Candle body/range >= `0.25`.
- Close location `(close - low) / (high - low) >= 0.60`.

Short trigger requires all:

- H4 close[1] < H4 EMA20[1].
- Candle body/range >= `0.25`.
- Close location `(close - low) / (high - low) <= 0.40`.

Do not add London/New York/Dubai session filters to V0. The H4 timeframe intentionally crosses sessions.

### Entry, Stop, Target, And Time Stop

- Entry: next H4 bar open, adjusted by half spread in the trade direction.
- Long stop distance: `max(3.0 x H4 ATR14[1], entry - pullback_window_low + 0.25 x H4 ATR14[1], 3 x spread_points)`.
- Short stop distance: `max(3.0 x H4 ATR14[1], pullback_window_high - entry + 0.25 x H4 ATR14[1], 3 x spread_points)`.
- Target: `1.5R`.
- Time stop: close at the first available H4 close after `30` completed H4 bars if neither SL nor TP is reached.
- Exposure model: one virtual position at a time for this candidate.
- No partial closes, trailing stops, break-even moves, dynamic exits, martingale, averaging, or pyramiding.

## Cost Model Required For The Screen

The screen must score net results first. Gross results are diagnostic only.

Base cost:

- Entry spread: worse of realized spread or measured median spread for the entry hour.
- Entry slippage: at least `1` EURUSD point.
- Stop/time-exit slippage: at least `3` EURUSD points for SL or time-stop exits.
- Overnight financing/swap: charge the direction-specific Capital.com EUR/USD published overnight funding adjustment normalized to R. As of the 2026-06-19 lock, the source rates are long `-0.00813%` and short `-0.00009%` per broker funding event, funding time `21:00 UTC`. Wednesday funding counts as triple-swap.

Stress cost:

- Entry spread: worse of realized spread or measured P95 spread for the entry hour.
- Entry slippage: at least `2` EURUSD points.
- Stop/time-exit slippage: at least `5` EURUSD points for SL or time-stop exits.
- Overnight financing/swap: charge `1.25 x` the measured direction-specific Capital.com funding adjustment, with Wednesday triple-swap.

Cost reporting must separate:

- spread cost_R,
- slippage cost_R,
- swap/financing cost_R,
- total cost_R.

## Screen Requirements

Primary screen:

- Capital.com EURUSD H4 bars.

Supplemental comparison:

- Dukascopy EURUSD H4 may be shown only as robustness context if a conservative Capital.com cost proxy is applied. It cannot overrule a Capital.com primary failure.

Before scoring performance, report:

- closed trades,
- long trades,
- short trades,
- calendar years covered,
- weeks with at least one closed trade,
- average trades per year,
- median H4 bars held,
- median broker midnights held,
- p95 total cost_R.

## Acceptance Bar

V0 can advance to reviewer discussion only if all discovery gates pass on the raw deduped net-cost book:

| Gate | Required |
| --- | ---: |
| Closed trades | `>= 100` |
| Long trades | `>= 25` |
| Short trades | `>= 25` |
| Net expectancy | `>= +0.10R/trade` |
| Net profit factor | `>= 1.25` |
| P95-stress net expectancy | `>= +0.10R/trade` |
| P95-stress net profit factor | `>= 1.25` |
| t-stat | `>= 2.0` |
| Max drawdown | `<= 8R` |
| Worst closed day | `> -4R` |
| Best 1 day removed | `still positive` |
| Best 2 days removed | `still positive` |
| Worst 1 day removed | `still positive` |
| Up-regime aggregate | `positive` |
| Down-regime aggregate | `positive` |
| P95 total cost_R | `<= 0.05` |
| Max accepted trade total cost_R | `<= 0.12` |

Promotion beyond discovery requires net expectancy `>= +0.15R/trade`, net PF `>= 1.30`, and all discovery gates still passing.

## Threshold Provenance

- `EURUSD H4 swing_atr_3x`: selected by the cost-geometry map before any hypothesis design, not by performance.
- D1 EMA50 six-day slope: round-number prior for daily trend direction without fitting a point threshold.
- H4 EMA20 versus H4 EMA50: expert-prior trend alignment check.
- Six H4 pullback window: one trading day of H4 pullback context.
- Three H4 invalidation window: half-day trend-integrity check.
- `0.20 x H4 ATR14` EMA touch tolerance: expert prior to avoid exact-touch fragility.
- `0.50-2.00 x H4 ATR14` pullback depth: broad expert prior to exclude microscopic pauses and deep reversals.
- Body/range `0.25`: loose non-doji filter for an H4 continuation candle.
- Close location `0.60/0.40`: symmetric directional close-quality prior.
- Stop `3.0 x H4 ATR14`: inherited from the selected cost-geometry cell, not selected from performance.
- Pullback-extreme buffer `0.25 x H4 ATR14`: structural buffer prior for swing trades.
- Target `1.5R`: kept consistent with the existing research framework.
- Time stop `30` H4 bars: approximately five trading days, chosen to bound swap/financing exposure.
- Capital.com EUR/USD swap: selected from the published Capital.com EUR/USD trading-conditions page before the screen; long `-0.00813%`, short `-0.00009%`, funding time `21:00 UTC`.

No threshold in V0 is selected from a V0 performance screen. If reviewer considers any value too arbitrary, revise before lock, not after screening.

## What Would Falsify This Hypothesis

Any of the following falsifies V0:

- Capital.com primary screen has fewer than `100` closed trades.
- Long or short side has fewer than `25` trades.
- Raw deduped net PF < `1.25`.
- Raw deduped expectancy < `+0.10R`.
- P95-stress PF < `1.25`.
- P95-stress expectancy < `+0.10R`.
- t-stat < `2.0`.
- Max drawdown > `8R`.
- Worst closed day <= `-4R`.
- P95 total cost_R > `0.05`.
- Any accepted trade total cost_R > `0.12`.
- Positive result depends on gross metrics, ignored swap, removing one direction, removing a bad month, or keeping only a post-hoc cost-filter survivor slice.

## Forbidden Changes After Lock

- No changing symbol, broker cell, timeframe, or stop geometry.
- No changing EMA periods, ATR period, pullback window, body/range, close-location, stop multiplier, target, or time stop.
- No adding session filters after seeing results.
- No adding macro/news filters after seeing results.
- No replacing the EURUSD hypothesis with XAU, USDJPY, GBPUSD, or Pepperstone evidence under the same version.
- No removing or softening swap/financing cost after seeing results.
- No approval from gross or pre-cost metrics.

## Allowed Bug Fixes After Lock

- Timestamp alignment fixes.
- Indicator calculation bugs independently reproduced from completed bars.
- Broker symbol point/digit normalization bugs.
- Spread, slippage, or swap normalization bugs where the fix makes cost accounting more faithful.
- Reporting-only fixes that do not change candidate decisions.

## Lock Decision

- Claude Round 10 verified the cost-geometry map and recommended Capital.com EURUSD H4 swing geometry.
- Owner approved `Capital.com / EURUSD / H4 / swing_atr_3x`.
- Claude Round 11 approved this draft for lock after replacing the placeholder swap floor with measured Capital.com EUR/USD direction-specific funding and dropping the redundant `close > open` / `close < open` trigger check.
- The screen must run on full multi-year Capital.com H4 history and report time-stop exits separately.

## Locking Rule

Do not place a hash inside this hypothesis file. Store SHA256 values in the Phase 0R hypothesis manifest.
