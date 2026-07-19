# V24 Preregistration

## Hypothesis

A short, unusually one-sided burst of Capital XAUUSD bid/ask quote updates may
continue for two minutes after paying the observed spread and fixed adverse
slippage. This is a new millisecond quote-information lane, not another bar,
cross-venue, quota, or ML variation.

## Frozen Information Boundary

- Calibration source: the finalized 2026-07-17 prospective tick file only.
- Calibration may reveal source quality, causal feature values, candidate count,
  candidate times, and direction balance.
- Calibration may not calculate or expose any price after a candidate timestamp.
- Forward evidence begins at 2026-07-20 00:00 UTC.
- Validation is the first 20 complete eligible weekdays after the boundary.
- Confirmation is the next 20 complete eligible weekdays and remains sealed until
  validation passes all frozen gates.
- Any exposed stage permanently becomes development evidence.

## Frozen Candidate

1. Sort by broker `tick_time_msc`; for duplicate milliseconds keep the last
   source row deterministically.
2. Require valid non-crossed quotes and exact source identity.
3. Use only quotes at or before the candidate timestamp.
4. Over the trailing five seconds, require:
   - no internal quote gap above 2,000 ms;
   - the boundary quote no more than 1,000 ms before the exact lookback time;
   - at least 15 nonzero mid-price updates;
   - absolute signed update imbalance at least 0.75;
   - absolute mid-price displacement at least 0.60 price units;
   - imbalance and displacement with the same sign;
   - current spread no more than 0.35 price units.
5. A raw event is the first false-to-true gate crossing.
6. Divide UTC time into fixed four-hour blocks starting at 00:00 UTC. Keep only
   the first raw event in each block. A block with no event remains empty.
7. Long when imbalance is positive; short when it is negative.

This creates at most six candidates per UTC day without forcing a candidate.

## Frozen Economic Label

- Entry: first valid quote strictly later than the candidate, no more than
  2,000 ms late.
- Exit: first valid quote at or after entry plus 120 seconds, no more than
  2,000 ms late.
- Long uses entry ask and exit bid; short uses entry bid and exit ask.
- Base adverse slippage: 0.05 price units per side.
- Stress adverse slippage: 0.15 price units per side.
- Reference size: fixed 0.01 lot and USD 1 per XAU price unit.
- No overlapping candidate can exist within one four-hour block.

## Complete Evidence Day

A weekday is eligible only when it has at least 100,000 unique millisecond
quotes, spans from no later than 02:00 UTC to no earlier than 22:00 UTC, has a
99th-percentile interquote gap no greater than 5,000 ms, and has no more than 5%
duplicate millisecond rows. These are source-quality rules, not outcome filters.

## Frozen Gates Per Stage

- At least 40 executable trades across exactly 20 full weekdays.
- Candidate frequency from 2.0 through 6.0 trades per full weekday.
- Both long and short shares at least 20%.
- Base net positive and base PF at least 1.20.
- Stress net positive and stress PF at least 1.05.
- Profitable-day share at least 50%.
- Closed-trade drawdown no more than USD 100 at the fixed reference size.
- Recovery factor at least 1.0.
- Both chronological ten-day halves must have base PF at least 1.0.
- The 90% one-sided day-bootstrap lower bound on mean daily base P&L must exceed
  zero, using 10,000 samples and seed 2401.

Passing validation only permits opening the unchanged confirmation stage. Passing
confirmation only nominates continued research shadow and independent MT5
reproduction. It does not authorize any execution or model training.

## Multiple Testing And No Rescue

V24 contains one candidate rule, one direction mapping, and one horizon. No
threshold, cooldown, session, direction, horizon, feature, label, or cost grid is
registered. Failure is terminal for V24. A new version must count as another
attempt and wait for later untouched evidence; V24 may not be reversed or tuned
after any outcome is opened.
