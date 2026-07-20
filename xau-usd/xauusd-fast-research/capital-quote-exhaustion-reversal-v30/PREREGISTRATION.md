# V30 Quote Exhaustion Reversal Preregistration

## Hypothesis

A sufficiently fast one-sided XAUUSD quote impulse sometimes exhausts immediate
liquidity. A confirmed retracement from the impulse extreme may therefore have
positive 120-second reversal expectancy after observed bid/ask spread and fixed
slippage.

This is one hypothesis. There is no direction, threshold, session, horizon,
cost, or model grid.

## Frozen Event

1. Deduplicate quotes by millisecond, keeping the last observed row.
2. At each quote, use only the previous three seconds and the current quote.
3. Arm an impulse only when there are at least 15 nonzero mid updates, absolute
   update-sign imbalance is at least 0.70, absolute mid displacement is at
   least USD 1.20, imbalance and displacement agree, no internal quote gap is
   above two seconds, the boundary quote is at most one second old, and spread
   is no more than USD 0.75.
4. An upward impulse arms a short reversal; a downward impulse arms a long.
5. The arm expires after five seconds. A new extreme updates the extreme but
   does not extend expiry.
6. Trigger only after at least three consecutive nonzero counter-direction mid
   updates and a USD 0.40 retracement from the extreme.
7. Keep only the first trigger in each fixed four-hour UTC block. Zero-candidate
   blocks are valid. The structural maximum is six candidates per UTC day.
8. Enter on the first strictly later quote within two seconds and exit on the
   first quote at least 120 seconds later, also within two seconds.

## Evidence Firewall

- The Capital July 17 file may be read only through each candidate timestamp.
  It is a frequency/schema calibration file. Post-candidate prices and P&L are
  forbidden.
- The declared June A1 MT5 tick packet is development evidence. It is opened
  only after the event definition and package are contract-locked.
- Forward evidence begins at 2026-07-21 00:00:00 UTC. July 20 is excluded
  because the day began before this hypothesis was frozen.
- Development must pass before any forward economic outcome can be opened.
- Forward validation uses the first 20 complete eligible weekdays; unchanged
  confirmation uses the next 20 only after validation passes.

## Costs And Gates

Observed bid/ask execution is charged plus USD 0.05 slippage per side in base
and USD 0.15 per side in stress. At 0.01 reference lot, one gold price unit is
USD 1.00.

Development requires at least 20 executable trades, 2.0-6.0 trades per eligible
weekday, at least 20% in each direction, positive base and stress net, base PF
at least 1.20, stress PF at least 1.05, at least half of days profitable, closed
drawdown no more than USD 100, recovery at least one, and PF at least one in
both chronological halves. Forward stages additionally require the registered
daily bootstrap lower bound and a selection-adjusted five-day moving-block
bootstrap p-value no greater than 0.0125.

V30 becomes the fourth registered Capital forward claim alongside V24.1, V26,
and V27. Before any Capital-forward claim can be promoted, all claims must be
rechecked under the stricter four-claim family threshold.

No historical or forward pass alone authorizes execution. Exact MT5 parity,
shared-account simulation, and a separate authorization decision remain required.
