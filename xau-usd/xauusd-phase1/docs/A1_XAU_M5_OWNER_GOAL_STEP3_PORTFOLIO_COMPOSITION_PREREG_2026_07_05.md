# A1 XAU M5 Owner Goal Step 3 Portfolio Composition Preregistration

Generated: 2026-07-05

## Purpose

Step 1 and Step 2 did not find a single exact-MT5 stream that simultaneously reached the owner goal:

- signal-level win rate >= 50%;
- realized average win / average loss >= 2.0;
- one trade on nearly every trading day, with 90%+ active weekday coverage considered worth showing if the first two constraints hold.

This Step 3 pass tests whether already-run exact MT5 streams can be combined into a portfolio layer without changing exits, entries, or gates.

## Boundary

- Exact MT5 Strategy Tester trade CSVs and exact MT5 signal ledgers only.
- No live/demo runtime attach.
- No Strategy Tester launch in this diagnostic.
- No Python-invented exits, take profits, stops, or prices.
- Python may only normalize rows, dedupe overlapping signals, and calculate realized signal-level metrics from MT5 output rows.

## Fixed Source Pool

The pool is intentionally limited to streams already generated during the owner-goal chase:

- Step 1 split-grid exact signal ledgers: `f33_r30_be_1r`, `f33_r30_be_never`, `f67_r20_be_tp1`.
- Early-adverse-exit exact signal ledgers: all four preregistered cells.
- Break-distance guard exact signal ledger: the exact `MinBreakDistanceAtr=0.8994` probe.
- RR2 stretch exact MT5 variants from V7/V8/V11/V13.
- RR2 stretch exact MT5 variants from V9/V10.
- RR2 baseline/profit-lock exact exam variants from the external macro traffic-light report.
- Opening-range reversal exact exam variants from the external macro traffic-light report.

## Composition Rules

- Rows are standardized to one signal record with `source_id`, `family_group`, `entry_time`, `entry_date`, `direction`, realized `pnl_usd`, `tickets`, `lots`, and `source_csv`.
- Combinations may use 1 to 5 streams.
- To avoid clone stacking, each portfolio may include at most one stream from a broad `family_group`.
- Within a portfolio, same-direction entries from different source streams within 5 minutes are treated as overlapping signals; the earlier signal wins, and source priority breaks ties at the same timestamp. Same-source signals are left intact because each source is already an exact MT5 signal ledger or trade CSV.
- Kept and dropped rows for the best frontier portfolio must be written to CSV.

## Metrics

The report must calculate, from the standardized signal rows:

- signals, wins, losses, win rate;
- gross profit, gross loss, realized average win / average loss, profit factor, net PnL;
- active weekday count and active weekday percentage for 2022-07-01 through 2026-06-30;
- last-12-month signal metrics;
- max closed-equity drawdown;
- net after removing top 10, 25, 50, and 100 winning signals;
- stress metrics after subtracting USD 0.10 and USD 0.30 per ticket from every signal.

## Decision Rules

- `OWNER_GOAL_HIT`: WR >= 50%, avg win/loss >= 2.0, and active weekday coverage >= 90%.
- `CORE_SHAPE_FREQUENCY_GAP`: WR >= 50% and avg win/loss >= 2.0, but active weekday coverage < 90%.
- `NEAR_OWNER_SHAPE`: WR >= 48%, avg win/loss >= 1.9, positive net, and at least 50% active weekday coverage.
- Otherwise reject.

Reviewer token is preserved unless this pass reaches `OWNER_GOAL_HIT`, `CORE_SHAPE_FREQUENCY_GAP`, or a genuinely non-trivial `NEAR_OWNER_SHAPE`.
