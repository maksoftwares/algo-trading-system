# A3 ML Six-Iteration Campaign V1 Preregistration

## Objective

Test whether point-in-time rates, dollar, and COMEX positioning information can add economically useful XAUUSD specialists to the existing low-frequency R1/R2 foundation. The research target is a combined 0.8 to 2.0 qualified trades per source day. Frequency is not a pass condition when expectancy is negative.

## Frozen chronology

- Fit/train: 2018-07-01 through 2020-06-30.
- Validation: 2020-07-01 through 2021-06-30.
- Internal test: 2021-07-01 through 2022-06-30.
- Exam: 2022-07-01 through 2024-06-30.
- A later segment opens only after the earlier segment passes every applicable gate.

## Iteration 1: data foundation

- Treasury real and nominal yield observations are delayed by one calendar day.
- The Federal Reserve broad-dollar index is delayed by seven calendar days.
- CFTC Tuesday positions become available Friday at 21:00 UTC.
- Intraday COMEX trades/depth, consensus forecasts, and ICE DXY history are absent and must not be synthesized from spot quotes.

## Iteration 2: macro repricing specialists

Test three mechanically distinct families on M15 execution:

1. Real-yield shock: trade opposite a sufficiently large one-day change in the 10-year real yield during the next liquid session.
2. Yield-dollar agreement: trade the gold direction implied when five-day real-yield and broad-dollar changes agree.
3. Inflation repricing: trade with a sufficiently large five-day change in 10-year breakeven inflation when the broad dollar does not strongly oppose it.

Signals are evaluated only at frozen UTC decision hours. Entries use the next M15 ask for longs or bid for shorts. Stops, targets, expiry, collision policy, and stress costs are fixed in the machine-readable contract before outcomes are run.

## Iteration 3: futures-positioning specialists

Test three CFTC families:

1. Managed-money trend confirmation.
2. Managed-money crowded-position reversal.
3. Producer-positioning change with short-term price confirmation.

CFTC inputs remain weekly and stale between releases. No claim of intraday order flow is permitted.

## Iteration 4: shared-account portfolio

Only specialists that pass chronological gates may be added to the deterministic foundation. The portfolio simulator must enforce one XAUUSD account, overlapping-trade accounting, directional exposure, maximum concurrent risk, daily loss controls, and a rolling drawdown response. It must report trade/day, daily P&L, overlap, regime attribution, and shared equity drawdown.

## Iteration 5: ML ranker

ML may rank or veto mechanically generated candidates; it may not invent entries. Training is chronological. Required predictive evidence is AUC at least 0.52 and Spearman correlation at least 0.03, followed by economic gates. Thresholds are fit without later outcomes.

## Iteration 6: qualification

Run cost stress, top-ten-winners-removed, rolling six-month stability, block bootstrap/Monte Carlo drawdown and risk-of-ruin analysis. Demo activation remains unauthorized unless all gates pass and the execution packet is complete.

## Economic gates

- Validation stress PF at least 1.15; internal at least 1.20; exam at least 1.25.
- Average stress return at least 0.03R, 0.04R, and 0.05R respectively.
- Positive month share at least 50%, 52%, and 55% respectively.
- Top ten winners removed must leave positive net R.
- At least 70% of rolling six-month blocks nonnegative at final qualification.
- Preferred shared-account drawdown below 12%; hard rejection above 15% at intended sizing.
- Monte Carlo risk of ruin below 1%.
- No strategy is required to trade when its evidence is absent.

## Research integrity

Every run records contract and artifact hashes. A failed family is reported as failed; its thresholds are not retuned on the same outcome segment. A materially changed mechanism requires a new preregistered campaign.
