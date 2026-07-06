# A1 XAU M5 Step 4 Breakout-Retest Probe Pre-Registration

Generated UTC: `2026-07-05T08:27:45Z`

## Reason

Step 1 split-shape grid and Step 2 internal regime gate did not produce a survivor. The tradeoff is stable enough to stop tuning that family for now:

- high WR cells stay near W/L `1.0-1.6`
- W/L `>2.0` cells fall below WR `50%`
- active-day coverage remains around `60-62%` before filters

This probe moves to a different existing MT5-backed entry family: XAU 920101 breakout-retest.

## Boundary

- Exact MT5 Strategy Tester only.
- Isolated tester root: `C:\MT5A1M5MomentumBacktest`.
- EA: `Phase2ExperimentalDemoExecutor.mq5`.
- No live/demo runtime chart, preset, order, position, or broker-action state may be touched.

## Window

`2022.07.01 -> 2026.06.30`, matching the completed Step 1 window.

## Frozen Variants

Run exactly these six existing variants from `run_xau_920101_breakout_retest_backtest_variants.py`:

1. `baseline_24h_no_smart`
2. `current_24h_h1_smart`
3. `repair_24h_h1_faststop_min800`
4. `repair_24h_h1_faststop_min800_lock100_050`
5. `revise_short_24h_h1_faststop_min800_lock100_050`
6. `repair_24h_h1_faststop_min800_be075`

## Decision

This probe uses the runner's existing MT5/manual CSV metrics. A row is not a survivor unless it reaches, at signal/trade level:

- WR `>=50%`
- average winner / average loser `>=2.0`
- acceptable activity for the owner goal, reported honestly

Any positive row is diagnostic only until reviewed, split-tested, and packaged with a frozen forward spec.
