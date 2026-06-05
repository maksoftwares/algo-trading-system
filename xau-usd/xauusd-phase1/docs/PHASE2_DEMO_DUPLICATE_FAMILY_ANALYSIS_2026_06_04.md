# Phase 2 Demo Duplicate Family Analysis - 2026-06-04

```text
status: DUPLICATE_FAMILY_RISK_FOUND
runtime_change_authorized: false
current_demo_eas_touched: false
same_family_guard_implemented: false
canonical_phase2_authority: false
```

## Boundary

This analysis is generated from committed CSV artifacts only. It does not read terminal state, touch current demo EAs, change any chart, or implement the proposed guard.

## Source Artifacts

- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\review_exports\PHASE2_DEMO_ACTUAL_TRADES_REVIEW_2026_06_04\PHASE2_DEMO_ACTUAL_BROKER_TRADES_DIRECT_MT5_2026_06_04.csv`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\PHASE2_DEMO_LOSS_CASE_STUDY_2026_06_04.md`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\PHASE2_DEMO_SHADOW_FILTER_REPORT_2026_06_04.md`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\review_exports\PHASE2_DEMO_ACTUAL_TRADES_REVIEW_2026_06_04.zip`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\review_exports\PHASE2_DEMO_ACTUAL_TRADES_REVIEW_2026_06_04\PHASE2_DEMO_LOSS_CASE_STUDY_TRADES_2026_06_04.csv`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\review_exports\PHASE2_DEMO_ACTUAL_TRADES_REVIEW_2026_06_04\PHASE2_DEMO_SHADOW_FILTER_TRADES.csv`

## Duplicate Definition

A duplicate family is defined as the same entry minute, same symbol, same direction, and same volume. This matches the committed actual-trade export `duplicate_key` when present.

## Raw vs Duplicate-Hidden

| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | Floating AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Raw grouped actual trades | 202 | 197 | 5 | 72 | 125 | 36.55% | -299.67 | 25.02 | 0.87 | 28.37 | -18.74 |
| Duplicate-hidden decision view | 119 | 116 | 3 | 43 | 73 | 37.07% | -135.38 | 13.34 | 0.90 | 27.02 | -17.77 |

- Duplicate groups found: `77`.
- Duplicate rows beyond the first kept event: `83`.
- Closed PnL difference raw minus duplicate-hidden: `-164.29 AED`.
- Raw trade counts are useful for broker-account accounting. Duplicate-hidden counts are better for strategy decision review because they collapse same-family stack entries into one event.

## Worst Duplicate Examples

| Entry Minute | Symbol | Direction | Volume | Count | Closed | Closed PnL AED | Candidates | Tickets Sample |
|---|---|---|---:|---:|---:|---:|---|---|
| 2026-06-02 12:00 | XAUUSD | BUY | 0.01 | 5 | 5 | -103.77 | breakout_retest, round_number_retest_v0, session_extreme_retest_v0, swing_breakout_retest_v0, symbol_normalized_round_retest_v0 | 3775798, 3775799, 3775803, 3775804, 3775805 |
| 2026-06-01 17:40 | XAUUSD | BUY | 0.01 | 2 | 2 | -91.12 | round_number_retest_v0, symbol_normalized_round_retest_v0 | 3762684, 3762680 |
| 2026-06-02 05:55 | XAUUSD | SELL | 0.01 | 2 | 2 | -83.19 | round_number_retest_v0, symbol_normalized_round_retest_v0 | 3772509, 3772510 |
| 2026-06-03 09:40 | XAUUSD | BUY | 0.01 | 2 | 2 | -76.97 | round_number_retest_v0, symbol_normalized_round_retest_v0 | 3793379, 3793380 |
| 2026-06-04 06:00 | XAUUSD | BUY | 0.01 | 2 | 2 | -75.25 | round_number_retest_v0, symbol_normalized_round_retest_v0 | 3804968, 3804973 |
| 2026-06-04 04:15 | XAUUSD | SELL | 0.01 | 3 | 3 | -75.04 | round_number_retest_v0, session_extreme_retest_v0, symbol_normalized_round_retest_v0 | 3804203, 3804204, 3804205 |
| 2026-06-03 12:00 | XAUUSD | SELL | 0.01 | 3 | 3 | -67.44 | breakout_retest, round_number_retest_v0, symbol_normalized_round_retest_v0 | 3794738, 3794739, 3794741 |
| 2026-06-03 05:15 | XAUUSD | SELL | 0.01 | 2 | 2 | -66.80 | round_number_retest_v0, symbol_normalized_round_retest_v0 | 3791960, 3791961 |
| 2026-06-01 16:40 | XAUUSD | BUY | 0.01 | 2 | 2 | -62.10 | round_number_retest_v0, symbol_normalized_round_retest_v0 | 3759907, 3759908 |
| 2026-06-04 08:20 | XAUUSD | BUY | 0.01 | 2 | 2 | -59.60 | round_number_retest_v0, symbol_normalized_round_retest_v0 | 3806188, 3806189 |
| 2026-06-04 06:50 | XAUUSD | BUY | 0.01 | 2 | 2 | -55.70 | round_number_retest_v0, symbol_normalized_round_retest_v0 | 3805529, 3805530 |
| 2026-06-03 06:25 | XAUUSD | BUY | 0.01 | 2 | 2 | -54.67 | round_number_retest_v0, symbol_normalized_round_retest_v0 | 3792404, 3792405 |

## Candidate Combinations

| Candidate Combination | Count |
|---|---:|
| round_number_retest_v0, symbol_normalized_round_retest_v0 | 43 |
| breakout_retest, swing_breakout_retest_v0 | 27 |
| round_number_retest_v0, session_extreme_retest_v0, symbol_normalized_round_retest_v0 | 2 |
| breakout_retest, round_number_retest_v0, session_extreme_retest_v0, swing_breakout_retest_v0, symbol_normalized_round_retest_v0 | 1 |
| breakout_retest, round_number_retest_v0, symbol_normalized_round_retest_v0 | 1 |
| breakout_retest, symbol_normalized_round_retest_v0 | 1 |
| round_number_retest_v0, session_extreme_retest_v0 | 1 |
| session_extreme_retest_v0, swing_breakout_retest_v0 | 1 |

## Future Guard

A future family-level mutex should allow at most one open/entry event per duplicate key: same entry minute, symbol, direction, and volume. The guard must be designed, reviewed, tested, and explicitly authorized before any runtime deployment.

No same-family mutex, router block, or one-event-one-trade guard was implemented by this analysis.
