# Transition Weighted Portfolio V8

## Purpose

Test whether complementary transition mechanisms can satisfy the unchanged
portfolio gates when risk is allocated by component quality. Entries, exits,
directions, costs, and component-level overlap rules are frozen and unchanged.

## Components

Core components:

- 23925: macro ancestry reacceleration, weight 0.75 or 1.00 R
- 24995: single-factor resolution, weight 0.75 or 1.00 R

Diversifiers:

- 24877: residual breakout, weight 0.00, 0.25, or 0.50 R
- 25048: ancestry overshoot reversal, weight 0.25, 0.50, 0.75, or 1.00 R

Component 23925 is regenerated exactly from its sealed V1 manifest and must
reproduce its published bar-level metrics. The V6 component trade file supplies
the other three components and is hash-locked.

## Search space

The Cartesian weight grid contains 48 allocations. Each uses attempt-ascending
and attempt-descending tie priority, creating 96 policies, attempts 25142 through
25237. All 96 policies count in the selection adjustment.

Weights are fractions of account portfolio risk. A 0.25/0.50/0.75/1.00 ratio is
implementable through integer lot ratios when the final account scale permits.
This screen does not authorize a lot size or trading.

## Gates

The economic gates are unchanged. Weighted component stress R is measured in
portfolio-risk units. Trade count is not multiplied by weight. Zero-weight
components are excluded before overlap selection. Exact raw-tick confirmation,
independent-period evidence, and prospective shadow observation remain required.

This is post-selection discovery on exposed component outcomes. Same-version
repair, paid data, model training, and trading authorization are prohibited.

