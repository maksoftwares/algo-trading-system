# V26 Gap-Restart Forward Preregistration

## Hypothesis

After a short quote silence, a fast, one-sided restart in XAUUSD quote revisions
may continue for two minutes after paying observed spread and fixed adverse
slippage. This is a liquidity-restart event clock, not a threshold repair or
direction mirror of V24.1.

## Prior Information And Calibration

- Calibration source is only the finalized Capital tick file from 2026-07-17.
- Source-only inspection found quote gaps from 2,001 through 5,000 ms in the
  observed 8.17 hours.
- The one registered rule produced 13 raw events and three first-per-block
  candidates across three observed four-hour blocks: one long and two short.
- Candidate times were 12.0 to 65.0 minutes away from the nearest V24.1
  calibration event; none overlapped within the 120-second label horizon.
- The full file was loaded to enumerate separate events. No post-candidate price
  was used to label or economically evaluate any candidate, and no return, P&L,
  win rate, or economic metric was calculated.
- These structural facts are development calibration, not evidence of edge.

## Frozen Candidate

1. Sort by broker `tick_time_msc`; keep the last quote at duplicate milliseconds.
2. A restart begins at the first quote after an interquote gap from 2,001 through
   5,000 ms, inclusive.
3. Observe at most the first 1,000 ms beginning with the restart quote.
4. At each quote, use only restart-to-current information and require:
   - at least five nonzero mid-price updates;
   - absolute signed update imbalance at least 0.60;
   - absolute midpoint displacement from the restart quote at least 0.30;
   - imbalance and displacement with the same nonzero sign;
   - current spread no more than 0.35.
5. Keep the first qualifying quote in the restart episode.
6. Keep only the first restart event in each fixed four-hour UTC block. There are
   at most six candidates per UTC day, and empty blocks remain empty.
7. Trade continuation: long for positive imbalance and short for negative.

V24.1 permits an internal gap no greater than 2,000 ms. V26 requires a preceding
gap of at least 2,001 ms, so the clocks are mechanically disjoint while the gap
remains inside V24.1's rolling five-second feature window.

## Frozen Economic Label And Costs

- Entry: first valid quote strictly later than the candidate, at most 2,000 ms
  late.
- Exit: first valid quote at or after entry plus 120 seconds, at most 2,000 ms
  late.
- Long uses entry ask and exit bid; short uses entry bid and exit ask.
- Base adverse slippage: 0.05 price units per side.
- Stress adverse slippage: 0.15 price units per side.
- Reference size: fixed 0.01 lot and USD 1 per XAU price unit.

## Complete Day And Sequential Stages

The complete-day rule is byte-equivalent in meaning to V24.1: at least 100,000
unique quotes, no more than 5% duplicate milliseconds, coverage from no later
than 02:00 UTC through at least 22:00 UTC, and 99th-percentile interquote gap no
more than five seconds.

- Forward boundary: `2026-07-20T00:00:00Z`.
- Validation: first 20 eligible complete weekdays.
- Confirmation: next 20 eligible complete weekdays.
- Validation opens once. Failure is terminal.
- Confirmation can open only on a later invocation after an immutable passing
  validation audit exists.

## Gates And Multiplicity

Every original V24.1 gate applies unchanged: 40 trades, 2-6 trades per complete
weekday, 20% minimum direction share, base PF 1.20, stress PF 1.05, positive base
and stress net, 50% profitable days, USD 100 maximum closed drawdown, recovery
factor 1.0, PF 1.0 in both chronological halves, and positive 90% day-bootstrap
lower bound.

V26 also requires a one-sided p-value no greater than 0.025 from a circular
moving-block bootstrap of the chronological daily base P&L. The block length is
five weekdays; the centered-null bootstrap uses 10,000 samples, seed 2601, and
the finite-sample formula
`(1 + count(null mean >= observed mean)) / (samples + 1)`. The 0.025 threshold is
the 0.05 family alpha divided across the two registered Capital forward
hypotheses. Before selection from this family, V24.1 must pass the same external
admission recheck; its original frozen runner is not retroactively modified.

## No Rescue And Authorization

V26 contains one event rule, one direction mapping, and one horizon. Parameter,
direction, session, horizon, model, and cost grids are prohibited. Failure is
terminal and cannot be repaired under V26. Even dual validation and confirmation
passage nominates research shadow only; model training, Python prediction, EA
consumption, demo, live, and broker action remain unauthorized.
