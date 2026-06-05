# Phase 2 Demo Shadow Forward Test Plan - 2026-06-04

```text
status: SHADOW_FORWARD_TEST_PLAN_ONLY
runtime_change_authorized: false
shadow_filter_enforced: false
current_demo_eas_touched: false
canonical_phase2_authority: false
```

## Boundary

This is a plan for measurement only. It does not enforce a router/session filter, does not alter current demo EAs, and does not promote any cost-suspended family to canonical Phase 2.

## Source Artifacts

- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\review_exports\PHASE2_DEMO_ACTUAL_TRADES_REVIEW_2026_06_04\PHASE2_DEMO_ACTUAL_BROKER_TRADES_DIRECT_MT5_2026_06_04.csv`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\PHASE2_DEMO_LOSS_CASE_STUDY_2026_06_04.md`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\PHASE2_DEMO_SHADOW_FILTER_REPORT_2026_06_04.md`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\review_exports\PHASE2_DEMO_ACTUAL_TRADES_REVIEW_2026_06_04.zip`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\review_exports\PHASE2_DEMO_ACTUAL_TRADES_REVIEW_2026_06_04\PHASE2_DEMO_LOSS_CASE_STUDY_TRADES_2026_06_04.csv`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\review_exports\PHASE2_DEMO_ACTUAL_TRADES_REVIEW_2026_06_04\PHASE2_DEMO_SHADOW_FILTER_TRADES.csv`

## Hypothetical Rule Under Test

- Block `session_extreme_retest_v0`.
- Block XAUUSD entries in Morning `06:00-11:59` and Afternoon `12:00-15:59`.
- Keep evening/night XAUUSD.
- Keep non-XAUUSD unless the candidate is `session_extreme_retest_v0`.

## Current Retrospective Measurement

| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | Floating AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline duplicate-hidden | 119 | 116 | 3 | 43 | 73 | 37.07% | -135.38 | 13.34 | 0.90 | 27.02 | -17.77 |
| Would keep | 59 | 57 | 2 | 27 | 30 | 47.37% | 279.86 | 6.80 | 1.55 | 29.26 | -17.01 |
| Would block | 60 | 59 | 1 | 16 | 43 | 27.12% | -415.24 | 6.54 | 0.47 | 23.23 | -18.30 |

Current shadow delta: `415.24 AED` versus the duplicate-hidden baseline.

## Block Reason Counts

| Reason | Count |
|---|---:|
| BLOCK_PROVISIONAL_SESSION_EXTREME_RETEST | 31 |
| BLOCK_XAUUSD_MORNING_AFTERNOON | 29 |

## Evidence Requirement

- Collect at least 300 unique duplicate-hidden closed trades/events or 20 active market days, whichever is more conservative.
- Do not change the rule while collecting the forward sample.
- Record daily kept/blocked counts, raw and duplicate-hidden results, per candidate, per symbol, and per time bucket.
- Keep open and floating PnL separate from closed-trade statistics.
- Report raw duplicated trades and duplicate-hidden trades side by side.
- Treat a positive retrospective result as overfit-risk until the forward sample survives.

## Review Decision Required Later

The future owner decision should be based on forward evidence, not this retrospective sample alone. Passing this plan would still not override canonical measured-cost suspension unless the cost evidence is separately repaired.
