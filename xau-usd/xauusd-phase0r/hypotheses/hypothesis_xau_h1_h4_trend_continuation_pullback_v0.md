# Hypothesis: XAU H1/H4 Trend Continuation Pullback V0

Expert candidate ID: `xau_h1_h4_trend_continuation_pullback_v0`
Version: `v0`
Status: `DRAFT_FOR_REVIEW_LOCK_PENDING`
Mechanic family: `trend_continuation_pullback`
Entry / decision timeframe: `M5`
Reference timeframe: `M15`, `H1`, `H4`, `D1`
Expected median hold bars M5-equivalent: `6-36`
Expected median hold hours: `0.5-3.0`
Expected decisions per week: `20-80`
Expected trades per year: `300-1200`
Timeframe diversification qualifies: `YES`
Same-family as breakout_retest: `NO`
Expected median stop distance points: `700-1400`
Expected median cost_R under measured P95 spread: `<= 0.10`
Expected PF after measured cost: `>= 1.25 discovery, >= 1.30 promotion`
Expected average net R: `>= +0.10R discovery, >= +0.15R promotion`
Expected win rate range: `42%-55%`
Expected worst month R: `>= -8R`
Expected losing-month percentage: `<= 40%`
Expected max zero-trade months: `1`

## Why This Behavior Should Exist On XAUUSD

The A3 breakout-retest family was falsified net-of-cost because entries repeatedly fought trend days, over-traded noisy retests, and depended on high-frequency cost-fragile triggers. This hypothesis deliberately changes the entry family: it only enters with an already-established H1/H4 trend after a shallow pullback, seeking continuation rather than a level retest or reversal.

Gold often moves in directional impulse phases after macro repricing, liquidity shifts, or broad USD/rate repricing. A shallow pullback inside an established higher-timeframe trend may offer better cost geometry than scalping a retest because stop distance is wider and spread becomes a smaller fraction of risk.

## Fixed Mechanical Definition

All rules use completed bars only. No lookahead is allowed.

### Trend Eligibility

Long trend is eligible only when all are true:

- H4 close[1] > H4 EMA50[1].
- H4 EMA50[1] - H4 EMA50[4] >= +80 XAU points.
- H1 close[1] > H1 EMA50[1].
- H1 EMA20[1] > H1 EMA50[1].
- H1 EMA20[1] - H1 EMA20[4] >= +60 XAU points.
- D1 close[1] is not below D1 EMA50[1] by more than `0.25 x D1 ATR14`.

Short trend is eligible only when all are true:

- H4 close[1] < H4 EMA50[1].
- H4 EMA50[1] - H4 EMA50[4] <= -80 XAU points.
- H1 close[1] < H1 EMA50[1].
- H1 EMA20[1] < H1 EMA50[1].
- H1 EMA20[1] - H1 EMA20[4] <= -60 XAU points.
- D1 close[1] is not above D1 EMA50[1] by more than `0.25 x D1 ATR14`.

### Pullback Eligibility

Long pullback is eligible only when all are true:

- Current M15 close[1] remains above H1 EMA50[1].
- At least one of the last six completed M15 candles has low <= H1 EMA20[1] + `0.20 x M15 ATR14`.
- None of the last three completed M15 candles closes below H1 EMA50[1].
- Pullback depth from latest H1 swing high is between `0.25 x H1 ATR14` and `1.25 x H1 ATR14`.

Short pullback is eligible only when all are true:

- Current M15 close[1] remains below H1 EMA50[1].
- At least one of the last six completed M15 candles has high >= H1 EMA20[1] - `0.20 x M15 ATR14`.
- None of the last three completed M15 candles closes above H1 EMA50[1].
- Pullback depth from latest H1 swing low is between `0.25 x H1 ATR14` and `1.25 x H1 ATR14`.

### M5 Trigger

Long trigger requires all:

- M5 close[1] > M5 EMA20[1].
- M5 EMA20[1] - M5 EMA20[4] >= +15 XAU points.
- Candle body/range >= `0.45`.
- Close location `(close-low)/(high-low) >= 0.65`.
- Current spread cost estimate keeps total `cost_R <= 0.12`.

Short trigger requires all:

- M5 close[1] < M5 EMA20[1].
- M5 EMA20[1] - M5 EMA20[4] <= -15 XAU points.
- Candle body/range >= `0.45`.
- Close location `(close-low)/(high-low) <= 0.35`.
- Current spread cost estimate keeps total `cost_R <= 0.12`.

### Stop And Target

- Entry: next M5 bar open plus/minus half spread, matching the executor-faithful replay convention.
- Stop distance: `max(0.85 x H1 ATR14, last M15 pullback extreme distance + 50 points, 700 points, 3 x spread)`.
- Target: `1.5R`.
- No trailing stop, no partial close, no dynamic exit in this hypothesis.
- One virtual position at a time.

## Session Rule

Primary discovery is all sessions. Session slices must be reported separately, especially Dubai morning, afternoon, evening, and night. Do not pre-filter by evening unless a separate session-specific hypothesis is registered.

## What Would Falsify This Hypothesis

Any of the following falsifies V0:

- Raw deduped net PF < `1.25`.
- Raw deduped expectancy < `+0.10R`.
- P95-stress PF < `1.25`.
- P95-stress expectancy < `+0.10R`.
- t-stat < `2.0`.
- Max drawdown > `8R`.
- Worst day <= `-4R`.
- P95 cost_R > `0.10`.
- More than 20% of accepted trades have cost_R > `0.12`.
- Positive result depends on removing one direction, one session, or one best day after seeing results.

## Forbidden Changes After Lock

- No threshold tuning under this version.
- No converting it into a level-retest rule.
- No adding session filters after seeing results.
- No changing stop floor, target R, or EMA periods.
- No adding cost-filtered survivor interpretation as approval evidence unless the cost filter is part of the locked entry rule.

## Allowed Bug Fixes After Lock

- Timestamp parsing fixes.
- Indicator calculation bugs that are independently reproduced.
- Broker symbol point/digit normalization bugs.
- Reporting-only fixes that do not change candidate decisions.

## Review Questions Before Lock

- Are H4/H1 EMA50 and H1 EMA20 trend conditions sufficiently different from the falsified retest family?
- Are the fixed slope thresholds too instrument-specific or acceptable for XAU?
- Should the D1 anti-trend veto be simplified before lock?
- Is `700` points a defensible stop floor, or should it be tied only to ATR before lock?

## Locking Rule

Do not place a hash inside this hypothesis file. Store SHA256 values in the Phase 0R hypothesis manifest only after Claude/reviewer and owner approve the exact draft for screening.
