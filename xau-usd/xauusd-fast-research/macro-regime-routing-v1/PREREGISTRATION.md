# XAUUSD Macro-Regime Routing V1 Preregistration

## Decision question

Can independently observed intraday dollar-index and Treasury total-return
pressure define an economically robust specialist inside either the frozen
`CHOP` or `TRANSITION_UNKNOWN` gold regime?

This is a changed information source, not another XAU indicator permutation.
Earlier macro specialists traded three global rules without routing by the
unresolved gold regimes. Earlier regime campaigns used gold price, session,
microstructure, or ancestry without this exact macro-regime interaction.

## Locked attempts

- Attempt numbers: `23120` through `24119` inclusive.
- Total definitions: `1,000`.
- Owners: `500` `CHOP` and `500` `TRANSITION` definitions.
- Five causal mechanics per owner and 100 deterministic definitions per
  mechanic.
- Admission uses only raw signal coverage, never returns or trade outcomes.
- No same-version tuning is authorized after an outcome file exists.

## Mechanisms

The CHOP owner tests macro-consensus catch-up, isolated DXY catch-up, isolated
Treasury catch-up, consensus overshoot fade, and balanced macro-disagreement
gold fade. The TRANSITION owner tests macro-consensus catch-up, isolated DXY
resolution, isolated Treasury resolution, prior-trend reacceleration, and
macro-confirmed prior-trend reversal.

Dollar pressure maps inversely to gold. Treasury total-return pressure maps in
the same direction as gold. Returns are standardized by rolling dispersion
computed from prior completed M15 observations. Current returns never enter
their own scale.

## Causality and execution

- Regimes use only the latest completed H4 state.
- Signals use only completed M15 gold and macro bars with exact timestamps.
- A return is valid only when its full elapsed-time interval is contiguous.
- No forward fill or backward fill is permitted across sources.
- Entry is the next verified M15 open: long at Ask and short at Bid.
- Long exits use Bid; short exits use Ask.
- Stops, targets, gaps, and fixed horizons use native Dukascopy bid/ask paths.
- Same-bar stop/target collisions are stop-first.
- One position per definition and at most four entries per UTC day.
- Stress subtracts `$0.30`, `$0.35` per 24 hours held, and `0.05R` slippage.

Recent observed broker spreads are recorded only as later sensitivity evidence.
They do not replace historical Dukascopy spread in this screen.

## Chronological portability gates

The four equal 21-month eras run from 2019-07-01 through 2026-07-01. A
definition passes only with at least 100 trades overall, at least 15 trades in
every era, PF at least 1.10 and average return at least 0.02R in every era,
whole-period PF at least 1.25, drawdown no greater than 25R, and positive net
return after removing the five largest winners.

Daily one-sided p-values receive Benjamini-Hochberg correction across all 1,000
attempts at FDR 0.10. Statistical support cannot override an economic failure.

## Authority boundary

All historical periods are discovery evidence. Any survivor requires a new
locked exact raw-tick replay and prospective shadow collection. Shock remains
an abstain state. This package grants no training, Python serving, EA, demo,
live, paid-data, or broker-action authority.
