# XAUUSD COMEX Auction-Profile Specialists V1

Date: `2026-07-17`

## Research Question

Can a causal volume-at-price profile built from individual COMEX gold futures
trades identify XAUUSD opportunities that survive native Bid/Ask execution and
remain independent of the R1 daily/H4 compression breakout?

This is new information geometry. The rejected COMEX studies used short-window
trade imbalance, session VWAP, futures/spot basis, and broad ML ranking. They did
not use the prior regular-session volume distribution, its value area, or a
causally evolving session point of control.

## Frozen Families

1. `COMEX_PRIOR_VALUE_ACCEPTANCE_CONTINUATION_V1` trades the first three-bar
   acceptance beyond the prior COMEX regular-session value area. The futures
   cumulative delta must agree, and the signal cannot be more than `0.75` spot
   ATR beyond the boundary.
2. `COMEX_PRIOR_VALUE_FAILED_AUCTION_V1` trades back into prior value after a
   completed futures M5 bar probes at least `0.20` spot ATR outside and closes
   at least `0.05` ATR back inside. This is an auction failure, not a generic
   spot sweep or VWAP fade.
3. `COMEX_OPENING_VALUE_MIGRATION_V1` trades at `08:50 America/New_York` only
   when the causal opening point of control and close have migrated beyond the
   prior value boundary, cumulative delta agrees, and opening volume is at
   least `0.75` of its prior 20-session median.

The COMEX regular session is fixed at `08:20-13:30 America/New_York`. Value area
is the contiguous `70%` of traded volume expanded from the point of control in
`$0.10` price bins. Ties are deterministic. Every futures M5 row is available
only after the bucket closes.

## Causal Execution

- Signals use completed COMEX and Dukascopy M5 rows with identical availability
  timestamps.
- Entry is the next contiguous spot M5 open: Ask for long and Bid for short.
- Exits use Bid for long and Ask for short. Same-bar collisions are stop-first.
- Native spread is included. Stress adds `$0.30`, `$0.35` per 24 hours, and
  `0.05R` adverse slippage.
- Families use fixed ATR stops, targets, maximum holds, one active trade per
  family, a one-hour cooldown, and at most one entry per family per UTC day.

## Chronological Firewall

- Fit: `2022-07-01` through `2023-07-01`.
- Development: `2023-07-01` through `2024-07-01`.
- Exam: `2024-07-01` through `2026-07-01`.

The exam is decision-ineligible unless the unchanged family passes fit and
development. No exam result may be used to tune V1. A family must pass trade
count, frequency, stress PF, average stress R, positive-month share, drawdown,
and top-five-winners-removed gates in every eligible stage.

This study grants no Python prediction, EA, demo, live, or broker authority.

