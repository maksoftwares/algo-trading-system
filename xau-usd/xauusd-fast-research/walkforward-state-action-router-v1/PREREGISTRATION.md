# XAUUSD Walk-Forward State/Action Router V1 Preregistration

## Research question

Prior fixed-rule, anti-signal, clock/session, and passive-entry campaigns did not produce a robust CHOP or TRANSITION specialist. V1 tests a different hypothesis: the missing edge is conditional state selection rather than another entry-price variation.

The router is an interpretable empirical-Bayes table. It is not a boosted tree, neural network, direct price forecaster, or unrestricted strategy optimizer. At each frozen hourly decision it estimates the historical stress return of LONG and SHORT actions in the current discrete state, using only outcomes that completed before that walk-forward block. It may select one action or abstain.

## Data and causality

- Source: the hash-pinned continuous Dukascopy Bid/Ask M5 foundation from 2010-01-01 through 2026-06-30.
- The 2010-06/2016 replay portion and the 2016-07/2026 feature-cache portion remain separately hash verified by the existing source contract.
- H4 regimes are attached causally to completed M15 bars.
- Decisions occur only when a completed M15 bar ends on the UTC hour.
- Entry is the next M15 executable Ask for LONG and Bid for SHORT.
- Stops and targets use executable side-specific OHLC. An ambiguous same-bar stop/target event is scored stop-first.
- Each training outcome must exit before the test block minus a 24-hour purge.
- Walk-forward estimates are frozen for six-month test blocks beginning 2012-01-01.
- Historical periods are discovery evidence, not untouched holdouts.

Feature-bin boundaries were selected from outcome-blind feature distributions before this contract was locked. No trade return, win/loss label, policy metric, or future regime was inspected to choose them.

## State/action estimator

Each policy owns either CHOP or TRANSITION. Ten small state schemas per owner combine two or three categorical features such as session, aligned momentum, VWAP displacement, range location, H4 trend strength, volatility, spread, activity, transition age, and ancestry.

For a state/action cell with `n` completed historical outcomes, the estimator:

1. Computes the cell mean and second moment.
2. Shrinks them toward the same-regime, same-direction baseline using a locked prior strength.
3. Computes a posterior standard error and lower-confidence bound (LCB).
4. Requires locked minimum cell support, global support, LCB, and action-gap thresholds.
5. Chooses the higher-LCB direction; exact ties abstain.

No policy learns from its own test block. Selected OOS trades enforce one open position per specialist and a locked UTC daily cap.

## Attempts

- Attempts: 22120 through 23119 inclusive.
- Total: 1,000 policies, exactly 500 CHOP and 500 TRANSITION.
- Each owner has ten schemas and exactly 50 deterministic hash-selected definitions per schema.
- Search dimensions are frozen geometry, expanding/rolling history, minimum support, prior strength, LCB multiplier, minimum LCB, action gap, and daily cap.
- Definitions are generated independently of outcomes.
- Same-version post-outcome tuning and reruns are forbidden.

## Economic and statistical gates

The four OOS eras are 2012-2015, 2015-2018, 2018-2022, and 2022-2026-07. A candidate must pass all of:

- at least 120 total trades;
- at least 15 trades in every OOS era;
- stress PF at least 1.10 and average stress return at least 0.02R in every era;
- total stress PF at least 1.25;
- closed-trade drawdown no more than 30R;
- positive stress net return after removing the five largest winners.

One-sided daily p-values include zero-trade OOS source days. Benjamini-Hochberg FDR is applied across all 1,000 policies at `q <= 0.10`. Only a policy passing both economic gates and FDR may enter exact raw-tick confirmation.

## Authorization boundary

This package is research-only. A historical survivor is discovery-selected and still requires exact raw-tick replay, independent implementation parity, and prospective shadow evidence. It does not authorize model training for execution, EA consumption, broker action, or payment for data. Shock remains an abstain state and is not searched.
