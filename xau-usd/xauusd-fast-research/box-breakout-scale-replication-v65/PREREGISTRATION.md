# V65 Box-Breakout Scale Replication

V65 translates the frozen D1/H4 box-breakout mechanism to H4/H1 and H1/M15.
It tests 256 deterministic variants covering both directions, strict or
parent-supportive trend ownership, two box widths, two volatility ceilings, two
range ceilings, two signal-body floors, and two reward targets.

All entries and exits use Dukascopy bid/ask M5 bars. Longs enter on ask and exit
on bid; shorts enter on bid and exit on ask. Same-bar ambiguity is stop-first.
Ticket cost, holding cost, and slippage stress are charged. Each variant permits
one open position and two entries per UTC day.

Selection ends before 2025-07-01 and requires positive, concentrated-winner-
removed performance in development 1, development 2, and confirmation. V65 does
not load final-year price rows into its outcome simulation and cannot authorize
execution.
