# Expected-R Availability V11 Preregistration

V11 is explicitly motivated by the already-observed V10 fold results. It
changes no model, prediction, family threshold, or outcome. It adds one fixed
availability rule:

- if an outer fold has at least 1,000 eligible FIT rows, apply the frozen V10
  selection;
- otherwise ML abstains and retains every candidate.

The 1,000-row threshold is a round evidence floor placed between the two V10
failure populations (548 and 817 rows) and the first improving population
(1,162 rows). This choice is post-outcome development and cannot supply fresh
confirmation by itself.

The formal evaluation binds the verified V10 predictions, metrics, result,
model, contract, source implementation, and artifact manifest. It requires
nonnegative uplift in every fold, positive uplift in all active folds, at least
one selected candidate per weekday, positive bootstrap lower-bound uplift, and
controlled coverage and drawdown.

A pass defines a working offline research model and availability policy.
Prospective confirmation is still mandatory before any runtime authority.

