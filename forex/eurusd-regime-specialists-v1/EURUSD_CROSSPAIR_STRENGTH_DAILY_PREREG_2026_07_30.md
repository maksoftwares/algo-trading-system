# EURUSD cross-pair strength daily preregistration

Status: `LOCKED_BEFORE_EURUSD_OUTCOME_INSPECTION`

## Hypothesis

Synchronized strength in EUR crosses and weakness in USD pairs may lead a cost-clearing EURUSD move even when no EURUSD price is used to choose direction.

Four completed-bar votes are evaluated:

1. positive EURGBP 15-minute mid return votes LONG;
2. positive EURJPY 15-minute mid return votes LONG;
3. positive GBPUSD 15-minute mid return votes LONG;
4. negative USDJPY 15-minute mid return votes LONG.

The opposite sign votes SHORT. At least three of four votes must agree. EURUSD is prohibited from signal construction.

## Candidate timing

- Decision clocks are 06:00 through 18:00 UTC, hourly.
- Every decision uses the bar closing five minutes before the clock and its exact timestamp minus 15 minutes.
- The first qualifying decision per UTC weekday is the only candidate.
- Missing or non-adjacent source bars fail closed.
- The source-only census contains 2,594 candidates on 2,601 synchronized weekdays: 1,243 LONG and 1,351 SHORT.
- Candidate capacity is 0.997 per synchronized weekday. These counts were established without loading future EURUSD paths or P&L.

## Frozen execution

- Enter EURUSD at the exact next M5 open.
- LONG uses ask; SHORT uses bid.
- Apply 0.1 pip adverse entry slippage and 0.1 pip adverse exit slippage.
- Fixed stop: 8 pips.
- Fixed target: 12 pips, nominal 1.5R.
- Maximum holding time: 360 minutes.
- Stop-first treatment when stop and target occur inside the same M5 bar.
- Use exact bid path for LONG exits and exact ask path for SHORT exits.
- One position maximum and one filled trade maximum per UTC date.
- Fixed research/demo lot: 0.01.
- Add 0.5 pip round trip for the primary stress test.

No threshold, clock, vote, stop, target, hold, side, session, regime, or cost parameter may be changed after outcomes are opened.

## Chronological gates

All gates are conjunctive:

- at least 0.85 and at most 1.05 completed trades per synchronized weekday;
- full PF at least 1.25;
- win rate from 45% through 55%;
- realized payoff ratio from 1.35 through 1.65;
- positive full net;
- +0.5-pip stressed PF at least 1.15 and positive stressed net;
- positive net in each frozen chronological block;
- at least three of four blocks with PF at least 1.15;
- last-12-month PF at least 1.20;
- at least 60% positive active months;
- PF at least 1.00 after removing the best 5% of trades;
- maximum closed-trade drawdown no greater than 25R.

Frozen blocks are 2016-07 through 2018, 2019-2021, 2022-2024, and 2025 through 2026 H1.

Failure means `REJECT_CROSSPAIR_STRENGTH`. A historical pass would authorize MT5 parity work, not demo or live trading.
