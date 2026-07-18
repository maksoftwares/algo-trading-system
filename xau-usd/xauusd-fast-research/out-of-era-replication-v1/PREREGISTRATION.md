# XAUUSD Out-of-Era Replication V1 Preregistration

Date: `2026-07-17`

## Purpose

The 2010-01-01 through 2016-06-30 Dukascopy period was not available when the
candidate mechanisms below were evaluated. This lane uses it only as an
independent, out-of-era replication period. It is not a new parameter search.

## Frozen Candidate Mechanisms

1. `R1_UPTREND_PORTABILITY_EXACT`: byte-identical signal and execution rules
   from `mt5-r1-uptrend-portability-v1`. This is the only price-mechanical
   near-survivor with positive stress expectancy in all previously reported
   stages. The portfolio-constrained view is binding.
2. `NFP_FADE_RR2_EXACT`: byte-identical `EVENT_NFP_FADE_RR2` rule and V3
   execution contract from `macro-event-reaction-replication-v3`. V3 delegates
   to the frozen V2 implementation and corrects only the timeout quote grace.
   Official BLS release dates and the fixed 08:30 America/New_York release time
   are binding.
3. `GLD_FLOW_REVERSAL_V0_EXACT`: byte-identical signal thresholds from
   `h4_gld_etf_flow_reversal_v0`. This is a falsification track, not a current
   near-survivor, because its later full-window test failed. It may advance only
   if both the old-period test and a combined all-era audit pass unchanged.

The three mechanisms are mechanically distinct: price trend/breakout, scheduled
macro-event rejection, and lagged ETF participation stress.

## Data Boundary

- XAUUSD source: official Dukascopy historical Bid/Ask ticks.
- Replication period: `2010-01-01T00:00:00Z` to
  `2016-07-01T00:00:00Z`.
- NFP calendar: official BLS Employment Situation archive links only.
- GLD input: public Yahoo chart API daily OHLCV, shifted one observation before
  joining to an H4 decision.
- Any incomplete raw month, hash mismatch, crossed quote, ambiguous event date,
  duplicate timestamp, or future feature fails closed.

## Decision Firewall

The candidate definitions, source hashes, costs, stages, and gates are locked
before outcomes are generated. No same-version threshold repair, inversion,
window change, selective direction removal, or gate change is permitted.

All three candidates are included in a single Holm family at alpha `0.05`.
Candidate-specific economic gates are frozen in the JSON contract. In addition,
winner removal must leave positive stress net R and at least half of active years
must be positive. The NFP rule must participate in at least 20% of official
events. GLD cannot advance from this test alone because its combined-era evidence
must also overcome the already recorded full-window failure.

Passing this historical replication does not itself authorize model training or
execution. It creates evidence eligible for a combined-era and prospective
review only.

## Authority

Research only. Paid data requests, Databento use, broker interaction, Python
serving, EA consumption, demo trading, and live trading are all prohibited.
