# Mega-Search Result — 28,800 backtests

Date: 2026-08-01
Status: **`NO_EDGE_FOUND_SURVIVORS_INDISTINGUISHABLE_FROM_NOISE`**

## What was run

14,400 strategy configurations on real US500 CFD M5 bid/ask quotes, and the
**identical pipeline** on sign-flipped data with the same volatility structure
and no drift. 28,800 backtests in total.

Execution used the full 24-hour M5 path, so the overnight-bar error that
invalidated the previous lane (U11, +96.5pp of phantom profit) is structurally
impossible here.

Search space: 8 entry families × family parameters × 5 timeframes (M15–H4) ×
2 directions × 4 ATR stop multiples × 5 reward:risk ratios × 3 session filters.

## Stage counts

| Stage | Gate | REAL | NULL | Expected | z |
|---|---|---:|---:|---:|---:|
| 1 design 2016–19 | PF ≥ 1.20, ≥100 trades | 382 | 349 | 349.0 | +1.79 |
| 2 validation 2020–21 | PF ≥ 1.10, ≥30 trades | 201 | 116 | 127.0 | +8.04 |
| 3 **holdout 2022–23** | PF ≥ 1.10, ≥30 trades | **28** | **29** | 50.2 | **−3.62** |

The preregistered bar was **survivors must exceed chance by more than 3 standard
deviations**. On the holdout the real data came in *below* chance.

## The decisive comparison — effect sizes, not just counts

Survivor counts alone could mislead, so the survivors themselves were compared:

| | n | Holdout PF median | Holdout PF max | Net median | Net max |
|---|---:|---:|---:|---:|---:|
| REAL | 28 | 1.190 | 1.319 | +407.9 | +895.7 |
| **NULL (noise)** | 29 | **1.283** | **1.574** | +368.0 | +651.4 |

**Strategies mined from sign-flipped noise have a higher median and higher
maximum profit factor than those mined from real market data.** 41% of null
survivors match or beat the real survivors' median net.

That is the whole result. A three-stage filter with an untouched holdout,
applied to data with no signal in it by construction, extracts 29 "systems" that
look as good as the 28 extracted from the real market.

## Why the stage-2 z of +8.04 is not evidence

Real strategies persisted design → validation far better than chance. That looks
like edge and is not: 2016–2019 and 2020–2021 were both strongly rising windows
(buy-and-hold +59.77% and +47.57%), so anything long-biased persisted across
both. The holdout then contained 2022, and persistence collapsed to below chance.
All 28 real survivors are long-only, which is the signature of that effect.

## The one genuinely surprising number

All 28 survivors beat buy-and-hold on the holdout (+12.7% to +21.6% against
−0.31%). That is *not* dismissible as market beta and was worth checking
carefully. It does not rescue the result, because the null survivors clear the
same bar on data containing no signal at all — beating a flat benchmark is what
a survivorship filter does, not evidence that the strategy will repeat.

## Verdict

**No edge found in 14,400 attempts.** The correct action is not to deploy the
best of the 28; it is to record that this search space is empty and stop mining
it. Picking the top cell here is precisely the error that produced this repo's
PF 1.99 → 0.82 ladder.

## What the null run bought

Without it, the honest-looking report would have been: *"14,400 attempts, a
rigorous three-stage filter with an untouched holdout, 28 survivors, best one
PF 1.32 on the holdout beating buy-and-hold by 21 points."* Every word true, and
the conclusion completely wrong.

The null run cost one extra command and is the only reason that report was not
written. Any future search in this repository should carry one.
