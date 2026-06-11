# Phase 0 Low-Frequency Gate Set V1

Status: LOCKED_FOR_SECOND_EA_RESEARCH
Author: Codex
Created UTC: 2026-06-10T00:00:00Z

This gate set applies to new second-EA research candidates whose median matrix-cell trade count is below 500. High-frequency candidates remain under the existing Phase 0 gate set. All gates use fixed-notional, cost-adjusted R-series unless a gate states otherwise.

## G1 - PF Survival

At least 7 of 9 cells must have PF >= 1.30.

## G2 - Sample Size

Every cell must have trade_count >= 40.

## G3 - Catastrophic Failure

Use the canonical Phase 0 loss caps from `config/phase0.yaml`:

- max_drawdown_pct_every_cell <= 30.0
- total_return_pct_every_cell >= -25.0
- worst-cell protection is evaluated per 9-cell matrix cell.

## G4 - Low-Frequency Concentration

The candidate must have net PnL above zero in every passing context. Frequency-normalized concentration is:

```text
norm_top  = top_positive_trade_R / (mean_abs_R * sqrt(n_trades)) <= 1.00
norm_top5 = top5_positive_sum_R  / (mean_abs_R * sqrt(n_trades)) <= 2.50
```

Legacy absolute concentration metrics remain report-only context:

- largest_single_trade_pct_of_net_pnl
- top5_trades_pct_of_net_pnl
- single_month_pct_of_net_pnl

If net PnL <= 0, the candidate cannot pass regardless of concentration.

## G5 - Activity

Use the canonical Phase 0 cap from `config/phase0.yaml`: max_consecutive_zero_trade_months <= 3.

## G6 - Cost Sensitivity

For each broker, P95-cell PF / best-cell PF must be >= 0.50.

## G7 - Cross-Venue Floor

For every cost model, mean(Pepperstone PF, Dukascopy PF) must be >= 1.20. Missing or owner-accepted partial venue data must be reported explicitly and cannot be silently ignored.

## G8 - Modern-Era Integrity

For the 2022-01-01 to 2025-06-30 median-cost slice, PF must be >= 1.10 in at least 2 of 3 brokers. A decade-level pass cannot hide a dead modern era.

## G9 - Measured-Cost Feasibility

G9A structural pre-check before running:

- expected_median_stop_points >= 375 preferred
- expected_median_stop_points >= 250 absolute minimum
- expected_median_cost_R_at_measured_50_75_spread <= 0.15 preferred
- expected_median_cost_R_at_measured_50_75_spread <= 0.30 absolute maximum

If a candidate cannot plausibly satisfy the absolute limits, block before running and mark `BLOCKED_COST_FRAGILE_BY_DESIGN`.

G9B realized post-run gate:

- realized_median_cost_R <= 0.15 preferred
- realized_P95_cost_R <= 0.30 absolute maximum
- stop-distance distribution must be reported

A candidate with realized P95 cost_R > 0.30 cannot advance.

## G10 - Decile Persistence

Using full-history deciles:

- PF > 1.0 in at least 8 of 10 deciles
- no single decile PF > 2x median decile PF

If trade count per decile is too low, report decile reliability as LOW and require manual review.

## G11 - D2 / Reality Check Inclusion

The D2 universe includes every SHA-locked candidate with a non-empty matrix ledger, including rejected candidates, same-family candidates, Lane A candidates, Lane B candidates, and prior Phase 0R candidates.

Report both candidate-level D2 and family-clustered D2. Candidate-level D2 must pass for an independent second EA. Family-clustered D2 is supplemental only.

Alpha policy:

- if candidate_universe_count < 30: required_alpha = 0.05
- if candidate_universe_count >= 30: required_alpha = 0.01

## G12 - Adversarial Review

Any candidate passing G1-G10 must receive an adversarial packet and score before final approval. Required checks:

- mechanic actually matches hypothesis
- not just long-gold drift
- not carried by one era
- not carried by one direction
- not carried by one broker
- not carried by one event-clock bug
- not secretly same-family with a rejected candidate

## No-Tuning Notice

This gate set is locked before second-EA candidate result runs. Any post-result rule change creates a new versioned candidate and restarts hypothesis locking.
