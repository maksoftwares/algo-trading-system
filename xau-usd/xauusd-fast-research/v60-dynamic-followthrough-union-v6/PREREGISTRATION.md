# V60 Dynamic Follow-Through Union V6 Preregistration

## Purpose

V3-V5 incorrectly reused V2's nominal veto IDs during cost stress. V2 is stateful:
its rolling per-source profit factor changes when costs or earlier vetoes change the
closed-trade path. V6 replaces that static approximation with a dynamic causal replay.

## Frozen dynamic policy

At each otherwise executable candidate, using only information available then:

1. Recompute V2 independently for that source from the challenger path's prior
   closed outcomes, using the frozen V2 rank, lookback, maturity, and PF thresholds.
2. Independently evaluate the V57 long anti-chase rule: mature source, rank below
   0.10, ATR ratio at least 1.20, distance below 1.00 ATR from the prior 24-hour high,
   positive 24-hour return, and `ret_4h / ret_24h < 0.70`.
3. Veto when either rule fires. Duplicate decisions count once.
4. A vetoed trade never enters the future source-health state.
5. Missing or nonfinite features retain V60 behavior.

No daily veto budget is used. Every cost-stress replay recalculates all state from
scratch under that stressed P/L path.

## Evidence status

All historical and August outcomes were exposed before V6. The follow-through rule
was selected post-hoc. Historical results can only nominate a frozen prospective
observer; they cannot authorize deployment.

## Acceptance gates

- Every nominal benchmark, performance, drawdown, retention, calendar-year,
  recent-window, and veto-cohort gate passes.
- Every comparative gate passes at +$0.10 and +$0.20 per trade.
- Exposed August net/PF improve and closed drawdown does not worsen.
- Dukascopy same-timing delta is positive and no year is harmed.
- Clean causal forward evidence is mandatory before any deployment decision.
