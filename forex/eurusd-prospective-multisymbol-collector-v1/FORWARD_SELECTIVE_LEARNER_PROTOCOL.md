# Frozen forward-only daily selective learner

Campaign: `EURUSD_FORWARD_SELECTIVE_LEARNER_V1`

Status: `LOCKED_BEFORE_FIRST_FORWARD_FEATURE_ROW`

Frozen on: `2026-07-30`

## Purpose

All archived EURUSD price, cross-pair, tick, flow, macro, and regime model
families in the research registry have been adaptively inspected. This learner
is not another historical backtest. It is the one forward-only selective
learner explicitly left open by the causal verdict.

It aims for at most one EURUSD decision per active weekday without forcing a
trade when its estimated edge is below the fixed admission margin. It is a
shadow research process and has no broker-order path.

## Causal sequence

1. At 08:00 UTC, use only exact completed M5 observations ending before 08:00.
2. Require contiguous observations for EURGBP, EURJPY, GBPUSD, and USDJPY.
3. Build oriented EUR-minus-USD strength and agreement features over fixed
   15-, 60-, and 240-minute horizons.
4. Add one signed cross-pair activity feature and one EURUSD spread-pressure
   feature.
5. Score LONG and SHORT with the weights learned only from earlier resolved
   prospective days.
6. Log one shadow side. During the first 20 resolved days, log it as warm-up.
7. Thereafter, mark it eligible only if the higher target probability is at
   least 45% and exceeds the other side by at least three percentage points.
8. Resolve both sides on the exact EURUSD bid/ask path from 08:00 through
   14:00 UTC using 8-pip risk, 12-pip target, 0.1-pip entry slippage,
   0.1-pip exit slippage, and stop-first same-bar collisions.
9. Apply one averaged two-side logistic-gradient update after resolution.
10. Never revise an earlier decision using a later weight state.

The full numerical contract is
`config/frozen_forward_selective_learner_v1.json`.

## Why this is different from the failed archive models

The algorithm is not claimed to be novel machine learning. Its evidentiary
status is different:

- weights start at zero rather than being fitted to an inspected archive;
- only post-floor `PROSPECTIVE_DEMO` rows are accepted;
- each probability is prequential, using earlier forward labels only;
- the feature family, clock, costs, threshold, and update law are frozen before
  the first admissible row; and
- failure closes the family without reversal or threshold rescue.

This prevents historical selection from being mislabeled as validation. It
does not guarantee that the future edge exists.

## Admission and frequency

The process emits a maximum of one shadow decision per complete weekday.
Warm-up and low-confidence decisions remain cash for ordering purposes.

No new sleeve may be admitted until it has at least 50 eligible untouched
trades across at least 40 active validation days, base PF above 1.10, payoff
above 1.25, positive additional-half-pip stress, PF at least 1.0 after removing
the five best trades, acceptable month concentration, MT5 parity, and a
separate shadow-demo soak.

The one-trade-per-day objective is measured on the final portfolio only after a
new sleeve passes those edge gates. A forced daily shadow prediction is not
treated as a deployable trade.
