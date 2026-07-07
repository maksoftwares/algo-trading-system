# A1 XAU Short Hedge Preregistration - 2026-07-08

## Goal

Build a short specialist for XAUUSD that acts as a regime hedge for the existing long-box edge. It does not need to be a mirror copy of the long strategy, but it must be useful when the long engine is weak.

## Execution Boundary

- Exact MT5 strategy tester only.
- Sandbox terminal root: `C:\MT5A1M5MomentumBacktest`.
- No live/demo runtime, chart, profile, preset, open order, or broker-state change.
- Python is only used to orchestrate MT5 runs and recompute portfolio metrics from exported trades.

## Frozen Control

`short_hedge_v1_break_run_control` is the existing bear break-run idea rerun as a control. It is not new discovery.

Core shape:

- short-only,
- fixed 2R target,
- D1 bearish gate,
- H1 and H4 bearish trend filters,
- break-and-run M5 continuation,
- no post-result hour/month/session filter.

## New Test V2 - Breakdown Retest Short

Hypothesis: a better short hedge should sell failed retests after support breaks, not chase the first continuation bar.

Fixed rule:

- M5 support is the low of a fixed lookback before the break bar.
- A break bar must close below support by a fixed ATR buffer.
- Price must retest near the broken support without closing back above it.
- Entry is on a bearish M5 confirmation close below support.
- Stop is above the retest high plus a fixed ATR buffer.
- Direction is short-only; target remains fixed 2R.

## New Test V3 - Prior-Day-High Sweep/Reclaim Short

Hypothesis: in non-uptrend regimes, failed upside liquidity sweeps can hedge long-box weakness.

Fixed rule:

- D1 non-up gate required.
- Current or recent M5 bar sweeps above prior-day high.
- Current completed M5 bar closes back below prior-day high by a fixed ATR buffer.
- Stop is above the sweep high plus a fixed ATR buffer.
- Direction is short-only; target remains fixed 2R.

## Forbidden In This Iteration

- No bad-hour masking.
- No bad-month masking.
- No optimizing for a prettier win rate after seeing results.
- No deleting profitable long sources to satisfy a metric.
- No demo spec unless the combined and hedge gates pass and review agrees.

## Hedge Gates

Standalone short hedge:

- `PF >= 1.15` after `-$0.30` per trade stress,
- raw W/L `>= 2.00`,
- stressed W/L `>= 1.90`,
- stressed net `> 0`,
- Q2-2026 net `> 0`,
- at least 200 trades,
- top-1 trade contribution `<= 25%` of net,
- top-day contribution `<= 30%` of net.

Combined long-plus-short:

- combined WR `>= 48%`,
- raw W/L `>= 2.00`,
- stressed W/L `>= 1.90`,
- PF `> 1.50`,
- positive weeks must not get worse,
- Q2-2026 long-box loss must be reduced by at least 30%.
- If the current guarded long-box baseline has no Q2-2026 long-box exposure because the existing regime guard already removed it, record the repair test as not applicable and substitute: short Q2 net must be positive and combined recent-three-month net must improve.

If no variant reduces the long-box Q2 hole meaningfully, stop tuning this short family and switch to the older failed-rally/lower-high work order.
