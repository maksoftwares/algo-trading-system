# V6 Causal ML Early Exit Utility V4 Preregistration

## Motivation

V3 achieved mean annual AUC 0.678 and 68.8% trigger precision, but its 24
incorrect early exits cost more than 53 beneficial exits saved. V4 therefore
optimizes conservative economic benefit instead of binary classification.

## Frozen Policy

- Population, causal features, checkpoints, costs, annual boundaries, and
  48-hour purge: exactly V3.
- Model: shallow histogram gradient-boosting quantile regressor.
- Target: `(early stressed P&L - frozen stressed P&L) / initial risk`.
- Quantile: 0.25.
- No target clipping, calibration, threshold search, or neighbor testing.
- Exit threshold: predicted 25th-percentile benefit is at least 0.00R.
- Adverse-state guards:
  - current unrealized result is at most -0.10R;
  - maximum adverse excursion is at least 0.25R;
  - signed return over the latest 15 minutes is at most 0.00R.
- Action: the first eligible checkpoint exits at the following M5 open.

## Pass Conditions

- Mean annual target rank correlation is at least 0.05 and at least three years
  are above zero.
- At least three target years have positive realized first-action benefit.
- First-action positive-benefit precision is at least 70%.
- Total realized first-action benefit is positive.
- Early exits cover 1% to 20% of frozen V1 nominations.
- V4 must not reduce V1 net or PF or increase V1 closed drawdown in any required
  window or full history.
- The shared account must not worsen V1 net, PF, closed drawdown, or floating
  drawdown, and inherited exposure limits must pass.

## Governance

All inspected history is development evidence. Same-version tuning is
forbidden. A failed V4 is quarantined. A passing V4 remains research-only and
would require a separately locked prospective period and MT5 parity.
