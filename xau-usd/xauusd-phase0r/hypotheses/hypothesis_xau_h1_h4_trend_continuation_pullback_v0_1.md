# Hypothesis: XAU H1/H4 Trend Continuation Pullback V0.1

Expert candidate ID: `xau_h1_h4_trend_continuation_pullback_v0_1`
Version: `v0.1`
Status: LOCKED
Mechanic family: `trend_continuation_pullback`
Entry / decision timeframe: `M5`
Reference timeframe: `M15`, `H1`, `H4`
Expected median hold bars M5-equivalent: `6-36`
Expected median hold hours: `0.5-3.0`
Expected decisions per week: `15-60`
Expected trades per year: `250-900`
Timeframe diversification qualifies: `YES`
Same-family as breakout_retest: `NO`
Expected median stop distance points: `ATR-relative; expected 700-1600, not fixed`
Expected median cost_R under measured P95 spread: `<= 0.10`
Expected PF after measured cost: `>= 1.25 discovery, >= 1.30 promotion`
Expected average net R: `>= +0.10R discovery, >= +0.15R promotion`
Expected win rate range: `40%-55%`
Expected worst month R: `>= -8R`
Expected losing-month percentage: `<= 40%`
Expected max zero-trade months: `1`
Why this behavior should exist on XAUUSD: XAU frequently trends after macro repricing; a shallow pullback inside an established H1/H4 trend may offer better cost geometry than the falsified high-frequency retest entry.
What would falsify this hypothesis: See the fixed falsification section below; any failure of the raw deduped net-cost acceptance bar falsifies V0.1.
Forbidden changes after lock: See the fixed forbidden-changes section below; no threshold tuning, no D1 veto add-back, no session retrofit, and no stop-floor tuning.
Allowed bug fixes after lock: Timestamp, indicator, point/digit normalization, and reporting-only fixes that do not change candidate decisions.

## Status And Boundary

This hypothesis is locked after Claude Round 6 final pre-lock approval. It is authorized for offline Phase 0R screening only. It is not authorized for MT5 runtime. A3 stays paused.

This V0.1 replaces the over-specified V0 draft for review purposes. V0 is retained only as historical draft context.

## Why This Behavior Should Exist On XAUUSD

The A3 breakout-retest family was falsified net-of-cost because entries repeatedly fought trend days, over-traded noisy retests, and depended on high-frequency cost-fragile triggers. This hypothesis deliberately changes the entry family: it enters with an established H1/H4 trend after a shallow pullback, seeking continuation rather than level retest, mean reversion, or reversal.

The intended edge is not "a retest holds." The intended edge is "a higher-timeframe trend resumes after a controlled pullback." This should reduce counter-trend shorting during strong up days and reduce cost pressure by using ATR-relative stops rather than scalp-sized stops.

## Fixed Mechanical Definition

All rules use completed bars only. No lookahead is allowed.

### Trend Eligibility

Long trend is eligible only when both are true:

- H4 EMA50[1] - H4 EMA50[4] > `0`.
- H1 EMA20[1] > H1 EMA50[1].

Short trend is eligible only when both are true:

- H4 EMA50[1] - H4 EMA50[4] < `0`.
- H1 EMA20[1] < H1 EMA50[1].

No D1 veto is used in V0.1. If D1 context later appears useful, it must be registered as a separate version after V0.1 is scored.

### Rolling Pullback Reference Definition

All pullback-depth references are causal. At decision time, only completed bars up to the latest completed H1 bar may be used.

Recent H1 high for long pullback depth:

- Search the last `12` completed H1 bars ending at H1 bar `[1]`.
- Use the highest high of those `12` completed H1 bars.

Recent H1 low for short pullback depth:

- Search the last `12` completed H1 bars ending at H1 bar `[1]`.
- Use the lowest low of those `12` completed H1 bars.

This replaces the prior causal-fractal draft because rolling high/low is causal by construction, simpler to reproduce, and avoids a two-bar confirmation lag.

### Pullback Eligibility

Long pullback is eligible only when all are true:

- Current M15 close[1] remains above H1 EMA50[1].
- At least one of the last six completed M15 candles has low <= H1 EMA20[1] + `0.20 x M15 ATR14`.
- None of the last three completed M15 candles closes below H1 EMA50[1].
- Pullback depth from the recent 12-bar H1 high is between `0.25 x H1 ATR14` and `1.25 x H1 ATR14`.

Short pullback is eligible only when all are true:

- Current M15 close[1] remains below H1 EMA50[1].
- At least one of the last six completed M15 candles has high >= H1 EMA20[1] - `0.20 x M15 ATR14`.
- None of the last three completed M15 candles closes above H1 EMA50[1].
- Pullback depth from the recent 12-bar H1 low is between `0.25 x H1 ATR14` and `1.25 x H1 ATR14`.

### M5 Trigger

Long trigger requires all:

- M5 close[1] > M5 EMA20[1].
- M5 EMA20[1] - M5 EMA20[4] > `0`.
- Candle body/range >= `0.35`.
- Close location `(close-low)/(high-low) >= 0.65`.
- Estimated `cost_R <= 0.12`.

Short trigger requires all:

- M5 close[1] < M5 EMA20[1].
- M5 EMA20[1] - M5 EMA20[4] < `0`.
- Candle body/range >= `0.35`.
- Close location `(close-low)/(high-low) <= 0.35`.
- Estimated `cost_R <= 0.12`.

### Stop And Target

- Entry: next M5 bar open plus/minus half spread, matching the executor-faithful replay convention.
- Stop distance: `max(0.85 x H1 ATR14, distance to last M15 pullback extreme + 50 points, 3 x spread)`.
- There is no fixed 700-point or 800-point stop floor in V0.1.
- Target: `1.5R`.
- No trailing stop, no partial close, no dynamic exit in this hypothesis.
- One virtual position at a time.

## Session Rule

Primary discovery is all sessions. Session slices must be reported separately, especially Dubai morning, afternoon, evening, and night. Do not pre-filter by evening unless a separate session-specific hypothesis is registered before screening.

## Screen-Window Check

Before scoring performance, report whether the data window contains both:

- at least `25` eligible long trades, and
- at least `25` eligible short trades.

If one side cannot populate because the window lacks enough directional trend regimes, the screen should report `INSUFFICIENT_BOTH_DIRECTION_SAMPLE` rather than pretending the edge failed on expectancy.

## Threshold Provenance

- H4 EMA50 slope sign: expert-prior trend filter, simplified from V0's numeric 80-point slope to avoid overfitting.
- H1 EMA20 versus H1 EMA50: expert-prior trend alignment, retained as the second independent trend check.
- M15 six-candle pullback window: round-number prior representing roughly 90 minutes of pullback context.
- M15 three-candle invalidation window: round-number prior representing roughly 45 minutes of failed pullback protection.
- `0.20 x M15 ATR14` pullback-to-EMA tolerance: expert prior to allow near-EMA touches without requiring exact equality.
- `0.25-1.25 x H1 ATR14` pullback depth: expert prior to avoid microscopic pullbacks and deep reversals.
- M5 EMA20 slope sign: simplified direction confirmation, not a numeric fitted threshold.
- Candle body/range `0.35`: expert prior for a non-doji continuation trigger. It is deliberately looser than the retest-family trigger because trend and pullback context already do more filtering.
- Close location `0.65` long / `0.35` short: symmetric expert prior for directional close quality.
- `0.85 x H1 ATR14` stop component: expert prior for trend-pullback breathing room; must not be changed after lock.
- `50` point pullback-extreme buffer: operational buffer prior, not fitted to V0/V0.1 results.
- `3 x spread`: cost/stops safety invariant.

No threshold in V0.1 is selected from a V0.1 performance screen. If reviewer considers any value too arbitrary, revise before lock, not after screening.

## What Would Falsify This Hypothesis

Any of the following falsifies V0.1:

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
- No adding D1 veto after seeing results.
- No adding session filters after seeing results.
- No changing target R, EMA periods, ATR multipliers, or pullback windows.
- No adding a fixed 700/800-point stop floor after seeing results.
- No adding cost-filtered survivor interpretation as approval evidence unless the cost filter is part of the locked entry rule.

## Allowed Bug Fixes After Lock

- Timestamp parsing fixes.
- Indicator calculation bugs that are independently reproduced.
- Broker symbol point/digit normalization bugs.
- Reporting-only fixes that do not change candidate decisions.

## Lock Decision

- Claude Round 6 accepted the two-condition trend eligibility.
- Claude Round 6 requested pure rolling 12-bar H1 high/low instead of causal-fractal swing pivots.
- Claude Round 6 accepted the close-location threshold and asked for a principled body/range stance; this locked version uses `0.35` as a loose non-doji continuation trigger.
- The hypothesis is now locked for one honest screen under `ENTRY_ACCEPTANCE_BAR_V1_2026_06_19.md`.

## Locking Rule

Do not place a hash inside this hypothesis file. Store SHA256 values in the Phase 0R hypothesis manifest.
