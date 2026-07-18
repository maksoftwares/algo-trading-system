# R2 Downtrend Portability V1 Pre-Outcome Invalidation

Date: `2026-07-18`

V1 is invalidated before outcome opening. The locked candidate-only preflight
found one H1 decision at exactly `2026-07-01T00:00:00Z`, equal to the sealed
data end and therefore outside the executable interval.

No trade outcomes, P&L, profit factor, drawdown, significance result, outcome
marker, or result artifact was generated. V2 preserves attempts 11,114 through
11,117 unchanged and adds only an end-exclusive candidate-boundary filter plus
a regression test.

V1 must never be used for scoring, selection, training, or execution.
