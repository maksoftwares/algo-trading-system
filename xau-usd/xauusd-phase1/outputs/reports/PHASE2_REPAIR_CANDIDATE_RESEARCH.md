# Phase 2 Repair Candidate Research

Status: `REPAIR_RESEARCH_READY`

Research only. This report does not change MT5 charts, EA inputs, presets, orders, open positions, canonical Phase 2 status, or live-capital permissions.

Generated at UTC: `2026-06-09T06:50:40.536273Z`
Source CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv`

## Promotion Rule

- Create a versioned repair hypothesis before implementation.
- Forward-test as observer-only first.
- Promote to demo execution only if duplicate-hidden PF and PnL improve.
- Do not destroy trade count.
- Improve or preserve win rate.
- Survive at least one fresh week of actual demo data.
- Record owner/reviewer approval before runtime changes.

## Portfolio View

| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL | Floating | Total PnL | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Repair targets baseline | 128 | 124 | 4 | 44 | 80 | 35.48% | -426.80 | 12.24 | -414.56 | 0.76 | 29.99 | -21.83 |
| Repair targets would keep | 55 | 51 | 4 | 24 | 27 | 47.06% | 168.29 | 12.24 | 180.53 | 1.33 | 28.48 | -19.08 |
| Repair targets would block | 73 | 73 | 0 | 20 | 53 | 27.40% | -595.09 | 0.00 | -595.09 | 0.52 | 31.81 | -23.23 |

## session_extreme_retest_v0

Repair ID: `session_extreme_retest_v0_repair_v1`
Status: `REPAIR_CANDIDATE_FOR_OBSERVER_FORWARD_TEST`
Hypothesis status: `RESEARCH_HYPOTHESIS_ONLY`

| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL | Floating | Total PnL | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Raw actual trades | 49 | 47 | 2 | 14 | 33 | 29.79% | -90.95 | 8.96 | -81.99 | 0.79 | 24.64 | -13.21 |
| Duplicate-hidden baseline | 44 | 42 | 2 | 12 | 30 | 28.57% | -133.23 | 8.96 | -124.27 | 0.66 | 21.21 | -12.92 |
| Repair would keep | 25 | 23 | 2 | 9 | 14 | 39.13% | 5.90 | 8.96 | 14.86 | 1.04 | 18.26 | -11.31 |
| Repair would block | 19 | 19 | 0 | 3 | 16 | 15.79% | -139.13 | 0.00 | -139.13 | 0.39 | 30.06 | -14.33 |

Shadow delta closed PnL AED: `139.13`
Kept closed trade pct: `54.76%`
Shadow status: `REPAIR_SHADOW_CANDIDATE`

### Proposed v1 Rules

| Rule | Symbol | Time | Direction | Closed | Win Rate | PnL | PF | Rationale |
|---|---|---|---|---:|---:|---:|---:|---|
| BLOCK_CLUSTER | XAUUSD | Night 20:00-05:59 | SELL | 7 | 14.29% | -64.71 | 0.44 | Negative duplicate-hidden cluster with weak PF/win-rate. |
| BLOCK_CLUSTER | XAUUSD | Night 20:00-05:59 | BUY | 3 | 0.00% | -48.23 | 0.00 | Negative duplicate-hidden cluster with weak PF/win-rate. |
| BLOCK_CLUSTER | XAUUSD | Afternoon 12:00-15:59 | BUY | 6 | 16.67% | -23.61 | 0.62 | Negative duplicate-hidden cluster with weak PF/win-rate. |
| BLOCK_CLUSTER | USDJPY | Afternoon 12:00-15:59 | SELL | 3 | 33.33% | -2.58 | 0.40 | Negative duplicate-hidden cluster with weak PF/win-rate. |
| PREFERRED_CLUSTER | EURUSD | Night 20:00-05:59 | SELL | 3 | 66.67% | 7.15 | 2.87 | Positive duplicate-hidden cluster worth observer-forward testing. |
| PREFERRED_CLUSTER | XAUUSD | Evening 16:00-19:59 | SELL | 4 | 50.00% | 13.95 | 1.28 | Positive duplicate-hidden cluster worth observer-forward testing. |
| PREFERRED_CLUSTER | XAUUSD | Afternoon 12:00-15:59 | SELL | 5 | 60.00% | 44.99 | 2.38 | Positive duplicate-hidden cluster worth observer-forward testing. |

### Worst Clusters

| symbol | time_bucket | direction | Closed | Wins | Losses | Win Rate | PnL | PF | Avg Win | Avg Loss |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| XAUUSD | Night 20:00-05:59 | SELL | 7 | 1 | 6 | 14.29% | -64.71 | 0.44 | 50.19 | -19.15 |
| XAUUSD | Night 20:00-05:59 | BUY | 3 | 0 | 3 | 0.00% | -48.23 | 0.00 | n/a | -16.08 |
| XAUUSD | Evening 16:00-19:59 | BUY | 2 | 0 | 2 | 0.00% | -47.79 | 0.00 | n/a | -23.89 |
| XAUUSD | Afternoon 12:00-15:59 | BUY | 6 | 1 | 5 | 16.67% | -23.61 | 0.62 | 38.26 | -12.37 |
| USDJPY | Evening 16:00-19:59 | BUY | 2 | 0 | 2 | 0.00% | -6.26 | 0.00 | n/a | -3.13 |
| USDJPY | Night 20:00-05:59 | BUY | 2 | 0 | 2 | 0.00% | -5.76 | 0.00 | n/a | -2.88 |
| USDJPY | Evening 16:00-19:59 | SELL | 1 | 0 | 1 | 0.00% | -4.09 | 0.00 | n/a | -4.09 |
| EURUSD | Afternoon 12:00-15:59 | BUY | 1 | 0 | 1 | 0.00% | -3.67 | 0.00 | n/a | -3.67 |

### Best Clusters

| symbol | time_bucket | direction | Closed | Wins | Losses | Win Rate | PnL | PF | Avg Win | Avg Loss |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| XAUUSD | Afternoon 12:00-15:59 | SELL | 5 | 3 | 2 | 60.00% | 44.99 | 2.38 | 25.89 | -16.34 |
| XAUUSD | Evening 16:00-19:59 | SELL | 4 | 2 | 2 | 50.00% | 13.95 | 1.28 | 32.33 | -25.35 |
| EURUSD | Night 20:00-05:59 | SELL | 3 | 2 | 1 | 66.67% | 7.15 | 2.87 | 5.49 | -3.83 |
| EURUSD | Night 20:00-05:59 | BUY | 1 | 1 | 0 | 100.00% | 5.51 | inf | 5.51 | n/a |
| EURUSD | Afternoon 12:00-15:59 | SELL | 1 | 1 | 0 | 100.00% | 5.51 | inf | 5.51 | n/a |
| EURUSD | Evening 16:00-19:59 | BUY | 0 | 0 | 0 | n/a | 0.00 | n/a | n/a | n/a |
| USDJPY | Afternoon 12:00-15:59 | SELL | 3 | 1 | 2 | 33.33% | -2.58 | 0.40 | 1.72 | -2.15 |
| EURUSD | Evening 16:00-19:59 | SELL | 1 | 0 | 1 | 0.00% | -3.64 | 0.00 | n/a | -3.64 |

### v1 Hypothesis Notes

- Keep original entry/SL/TP mechanics unchanged.
- Apply only pre-entry symbol/session/direction filters derived from actual demo weakness clusters.
- Run observer-only before any demo-order promotion.

Falsification:

- Fails if observer-forward duplicate-hidden PF does not improve over the current candidate.
- Fails if win rate falls below current duplicate-hidden baseline.
- Fails if kept trade count is too small for a useful demo comparison.
- Fails if reviewer finds lookahead, tuning, or post-hoc parameter changes beyond the listed filters.

## symbol_normalized_round_retest_v0

Repair ID: `symbol_normalized_round_retest_v0_repair_v1`
Status: `REPAIR_TOO_NARROW`
Hypothesis status: `RESEARCH_HYPOTHESIS_ONLY`

| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL | Floating | Total PnL | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Raw actual trades | 89 | 87 | 2 | 35 | 52 | 40.23% | -289.29 | 3.28 | -286.01 | 0.79 | 31.79 | -26.96 |
| Duplicate-hidden baseline | 84 | 82 | 2 | 32 | 50 | 39.02% | -293.57 | 3.28 | -290.29 | 0.78 | 33.29 | -27.18 |
| Repair would keep | 30 | 28 | 2 | 15 | 13 | 53.57% | 162.39 | 3.28 | 165.67 | 1.46 | 34.61 | -27.44 |
| Repair would block | 54 | 54 | 0 | 17 | 37 | 31.48% | -455.96 | 0.00 | -455.96 | 0.54 | 32.13 | -27.08 |

Shadow delta closed PnL AED: `455.96`
Kept closed trade pct: `34.15%`
Shadow status: `FAIL_TRADE_COUNT`

### Proposed v1 Rules

| Rule | Symbol | Time | Direction | Closed | Win Rate | PnL | PF | Rationale |
|---|---|---|---|---:|---:|---:|---:|---|
| BLOCK_CLUSTER | XAUUSD | Morning 06:00-11:59 | BUY | 17 | 29.41% | -155.73 | 0.53 | Negative duplicate-hidden cluster with weak PF/win-rate. |
| BLOCK_CLUSTER | XAUUSD | Evening 16:00-19:59 | BUY | 5 | 20.00% | -128.12 | 0.25 | Negative duplicate-hidden cluster with weak PF/win-rate. |
| BLOCK_CLUSTER | XAUUSD | Afternoon 12:00-15:59 | BUY | 4 | 0.00% | -88.40 | 0.00 | Negative duplicate-hidden cluster with weak PF/win-rate. |
| BLOCK_CLUSTER | XAUUSD | Night 20:00-05:59 | BUY | 15 | 40.00% | -44.13 | 0.78 | Negative duplicate-hidden cluster with weak PF/win-rate. |
| BLOCK_CLUSTER | XAUUSD | Morning 06:00-11:59 | SELL | 13 | 38.46% | -39.58 | 0.82 | Negative duplicate-hidden cluster with weak PF/win-rate. |
| PREFERRED_CLUSTER | XAUUSD | Evening 16:00-19:59 | SELL | 5 | 60.00% | 127.82 | 3.24 | Positive duplicate-hidden cluster worth observer-forward testing. |

### Worst Clusters

| symbol | time_bucket | direction | Closed | Wins | Losses | Win Rate | PnL | PF | Avg Win | Avg Loss |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| XAUUSD | Morning 06:00-11:59 | BUY | 17 | 5 | 12 | 29.41% | -155.73 | 0.53 | 34.56 | -27.38 |
| XAUUSD | Evening 16:00-19:59 | BUY | 5 | 1 | 4 | 20.00% | -128.12 | 0.25 | 43.65 | -42.94 |
| XAUUSD | Afternoon 12:00-15:59 | BUY | 4 | 0 | 4 | 0.00% | -88.40 | 0.00 | n/a | -22.10 |
| XAUUSD | Night 20:00-05:59 | BUY | 15 | 6 | 9 | 40.00% | -44.13 | 0.78 | 25.54 | -21.93 |
| XAUUSD | Morning 06:00-11:59 | SELL | 13 | 5 | 8 | 38.46% | -39.58 | 0.82 | 35.29 | -27.00 |
| GBPUSD | Evening 16:00-19:59 | SELL | 0 | 0 | 0 | n/a | 0.00 | n/a | n/a | n/a |
| USDJPY | Afternoon 12:00-15:59 | BUY | 0 | 0 | 0 | n/a | 0.00 | n/a | n/a | n/a |
| EURUSD | Evening 16:00-19:59 | BUY | 2 | 1 | 1 | 50.00% | 1.46 | 1.40 | 5.10 | -3.64 |

### Best Clusters

| symbol | time_bucket | direction | Closed | Wins | Losses | Win Rate | PnL | PF | Avg Win | Avg Loss |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| XAUUSD | Evening 16:00-19:59 | SELL | 5 | 3 | 2 | 60.00% | 127.82 | 3.24 | 61.63 | -28.53 |
| XAUUSD | Night 20:00-05:59 | SELL | 18 | 8 | 10 | 44.44% | 16.62 | 1.06 | 39.08 | -29.60 |
| EURUSD | Morning 06:00-11:59 | SELL | 1 | 1 | 0 | 100.00% | 5.51 | inf | 5.51 | n/a |
| EURUSD | Evening 16:00-19:59 | SELL | 1 | 1 | 0 | 100.00% | 5.51 | inf | 5.51 | n/a |
| EURUSD | Afternoon 12:00-15:59 | BUY | 1 | 1 | 0 | 100.00% | 5.47 | inf | 5.47 | n/a |
| EURUSD | Evening 16:00-19:59 | BUY | 2 | 1 | 1 | 50.00% | 1.46 | 1.40 | 5.10 | -3.64 |
| GBPUSD | Evening 16:00-19:59 | SELL | 0 | 0 | 0 | n/a | 0.00 | n/a | n/a | n/a |
| USDJPY | Afternoon 12:00-15:59 | BUY | 0 | 0 | 0 | n/a | 0.00 | n/a | n/a | n/a |

### v1 Hypothesis Notes

- Keep original entry/SL/TP mechanics unchanged.
- Apply only pre-entry symbol/session/direction filters derived from actual demo weakness clusters.
- Run observer-only before any demo-order promotion.

Falsification:

- Fails if observer-forward duplicate-hidden PF does not improve over the current candidate.
- Fails if win rate falls below current duplicate-hidden baseline.
- Fails if kept trade count is too small for a useful demo comparison.
- Fails if reviewer finds lookahead, tuning, or post-hoc parameter changes beyond the listed filters.

## round_number_retest_v0

Repair ID: `round_number_retest_v0_repair_v1`
Status: `DUPLICATE_ONLY_REBUILD_REQUIRED`
Hypothesis status: `RESEARCH_HYPOTHESIS_ONLY`

| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL | Floating | Total PnL | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Raw actual trades | 85 | 84 | 1 | 29 | 55 | 34.52% | -343.51 | 2.36 | -341.15 | 0.76 | 36.93 | -25.72 |
| Duplicate-hidden baseline | 0 | 0 | 0 | 0 | 0 | n/a | 0.00 | 0.00 | 0.00 | n/a | n/a | n/a |
| Repair would keep | 0 | 0 | 0 | 0 | 0 | n/a | 0.00 | 0.00 | 0.00 | n/a | n/a | n/a |
| Repair would block | 0 | 0 | 0 | 0 | 0 | n/a | 0.00 | 0.00 | 0.00 | n/a | n/a | n/a |

Shadow delta closed PnL AED: `0.0`
Kept closed trade pct: `n/a`
Shadow status: `NO_DATA`

### Proposed v1 Rules

| Rule | Symbol | Time | Direction | Closed | Win Rate | PnL | PF | Rationale |
|---|---|---|---|---:|---:|---:|---:|---|
| DUPLICATE_ONLY_REBUILD | ANY | ANY | ANY | 84 | 34.52% | -343.51 | 0.76 | Raw broker rows exist, but all are duplicate-hidden under the current priority; rebuild with standalone observer evidence before any demo execution. |

### Worst Clusters

| symbol | time_bucket | direction | Closed | Wins | Losses | Win Rate | PnL | PF | Avg Win | Avg Loss |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|

### Best Clusters

| symbol | time_bucket | direction | Closed | Wins | Losses | Win Rate | PnL | PF | Avg Win | Avg Loss |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|

### v1 Hypothesis Notes

- Keep original entry/SL/TP mechanics unchanged.
- Apply only pre-entry symbol/session/direction filters derived from actual demo weakness clusters.
- Run observer-only before any demo-order promotion.

Falsification:

- Raw broker rows exist only as duplicate-hidden entries or no rows exist at all.
- Do not promote from duplicate-only evidence; rebuild as standalone observer evidence first.
- Fails if a fresh observer-forward sample cannot produce unique duplicate-hidden decisions.

## Rules CSV

`PHASE2_REPAIR_CANDIDATE_RULES.csv` contains the machine-readable shadow rules. All rows have `runtime_action=NONE_SHADOW_ONLY`.
