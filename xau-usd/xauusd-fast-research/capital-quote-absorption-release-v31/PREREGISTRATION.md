# V31 Quote Absorption Release Preregistration

## Frozen Hypothesis

At each quote, examine the causal trailing 30 seconds. An absorption state exists
when:

- there are at least 100 nonzero mid-price updates;
- absolute signed update imbalance is no greater than 0.10;
- the full mid-price range is no greater than USD 0.75;
- no internal quote gap exceeds two seconds;
- the spread is no greater than USD 0.75.

Only a false-to-true absorption transition arms a range. The arm expires after
10 seconds and is never extended. A quote at least USD 0.75 above the frozen
range produces a long candidate; a quote at least USD 0.75 below produces a
short. After a trigger, the event clock is refractory for 60 seconds. Keep only
the first candidate in each fixed four-hour UTC block, for at most six per day.
Zero-candidate blocks remain valid.

Entry is the first strictly later quote within two seconds. Exit is the first
quote at least 120 seconds later within two seconds. Observed bid/ask spread is
charged plus USD 0.05 slippage per side in base and USD 0.15 per side in stress.

## Information Boundary

- July 17 Capital telemetry may be read only through candidate timestamps for
  schema and frequency calibration. No post-candidate price or P&L is opened.
- The exact June A1 files are hashed into the contract before outcomes open.
- The MT5 export's whole-second `time_utc` is accepted only when it exactly
  matches `floor(time_msc / 1000)`; unchanged `time_msc` is authoritative.
- There is one hypothesis and no parameter, direction, horizon, session, or
  cost grid.

## Development Gates

At least 20 executable trades, 2-6 trades per eligible weekday, at least 20% in
each direction, positive base and stress net, base PF at least 1.20, stress PF
at least 1.05, at least 50% profitable days, drawdown no more than USD 100,
recovery at least one, PF at least one in both chronological halves, and a
positive 10th-percentile daily bootstrap mean.

V31 is the fifth registered Capital quote-path claim. Any eventual forward
admission must use a familywise one-sided threshold no greater than 0.01 and
recheck the older claims. Historical passage alone cannot authorize execution.
