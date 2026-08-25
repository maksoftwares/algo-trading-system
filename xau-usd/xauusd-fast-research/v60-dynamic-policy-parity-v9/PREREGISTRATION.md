# V60 Dynamic Policy Parity V9

## Question

Does the prospective dynamic-union policy reproduce the nominal historical V6
veto decisions, and how much of each stressed result comes from trades admitted
after vetoes free portfolio capacity?

## Frozen method

- Use the existing V6 thresholds without modification.
- Re-run the exact deployed V60 baseline at $0.00, $0.10, and $0.20 additional
  cost per accepted trade.
- Feed the resulting baseline opportunities and closed outcomes through the
  prospective V6 policy implementation.
- Define the conservative common path as baseline executions minus vetoed
  executions; do not add replacement trades.
- Compare this path with the already-recorded full dynamic V6 replay.

## Acceptance

Nominal prospective-policy veto IDs, trade count, and P/L must exactly reproduce
the historical V6 result. Cost-stress results must report replacement-capacity
effects separately. No result authorizes broker action or deployment.
