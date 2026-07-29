# EURUSD Neutral specialist-agreement census V1.1 preregistration

Date: `2026-07-29`

Status: `SUPERSEDING_OPERATIONS_CONTRACT_BEFORE_SIGNAL_CENSUS`

V1.1 changes only the verifier return value. The V1 verifier validated every
hash and safety flag but returned only the checked-file mapping; the frozen unit
test expects the returned lock metadata so it can assert that outcome and oracle
loading are disabled.

No signal row or combined outcome was loaded before this correction. The expert
set, allowed columns, exact-clock agreement, conflict veto, daily routing,
capacity gates, P&L boundary, and promotion restrictions are unchanged.
