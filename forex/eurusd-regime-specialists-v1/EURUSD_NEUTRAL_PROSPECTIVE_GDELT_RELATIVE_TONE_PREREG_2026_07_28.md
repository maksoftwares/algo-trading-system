# EURUSD Neutral prospective GDELT relative-tone expert

Date: `2026-07-28`

Status: `FROZEN_BEFORE_PROSPECTIVE_START_AND_FIRST_SIGNAL`

This is a new causal, shadow-only Regime 1 expert. The historical GDELT work
tested source capacity and the behavior of one source-only transform. It did
not load EURUSD prices, returns, oracle rows, or P&L.

## Decision-time rule

On each UTC weekday, request exactly the previous date's 23:00, 23:15,
23:30, and 23:45 GDELT GKG batches. Every archive must be observed locally,
strictly validated, and hashed by 00:15 UTC. Late or incomplete evidence
cannot be backfilled into a signal.

The date must also be owned by the existing frozen Neutral classifier using
only completed prior H1 bars. Both ECB and Fed sides need at least two unique
sources, with no source contributing more than half of a side.

For each side, compute the median document tone per source and then the
median across sources. Relative tone is ECB minus Fed. Divide its absolute
value by the larger of `0.5` and the pooled source-score median absolute
deviation. Strength below `1.0` produces no signal. Positive relative tone
is long EURUSD and negative relative tone is short.

## Shadow execution

The signal decision is fixed at 00:15 UTC. The shadow entry is the first
Dukascopy bid/ask tick at or after 00:20, strictly after all evidence. Apply
the larger of actual spread and a 0.7-pip retail floor, reject entry spread
above 1.5 pips, and add 0.1 pip adverse slippage per side.

Risk is fixed at four pips with a six-pip target (`1.5R`) and a four-hour
maximum hold. Long barriers are evaluated on bid and short barriers on ask;
the stop wins any same-timestamp ambiguity. Only one Neutral-expert position
may be open. There is no trade-frequency quota.

## Evaluation

The expert remains research-only for at least 12 calendar months and 30
closed prospective trades. Profitability requires the frozen win-rate,
payoff, profit-factor, side, cost-stress, concentration, and drawdown gates.
Profitability review is separate from same-day and full temporal
hindsight-oracle resemblance.

Historical backtesting or retuning this exact rule is forbidden. A failed
prospective rule is rejected without parameter search. No demo or broker
action is authorized.
