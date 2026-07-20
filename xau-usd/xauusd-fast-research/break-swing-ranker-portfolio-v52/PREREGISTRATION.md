# XAUUSD Break-Swing Ranker Portfolio V52 Preregistration

## Question

Can a family-specific Python ranker choose enough account-feasible 36-hour
break-and-run swing candidates to lift the unchanged V50 Core above one
completed trade per UTC weekday while preserving stressed marginal expectancy
and the account closed-drawdown budget?

V51 is terminal. It showed that allowing ML to choose among actions caused 496
of 542 final add-on trades to use the losing 12-hour action. V52 changes the
research mechanism: the action, risk, target, and maximum hold are fixed before
the later ranked outcomes are opened. ML may rank only.

## Known evidence and selection

The unranked 36-hour pure break action was already known to have positive net in
each broad historical block, but its latest PF was only about 1.05. That is
context, not acceptance evidence.

Five score quantiles were evaluated only on 2019-2021 development. The frozen
40th-percentile policy produced 408 trades, 0.520 per weekday, USD 283.36
stressed net, PF 1.265, and USD 155.22 closed drawdown. This selected the policy
and cannot count as confirmation.

## Frozen causal process

- Pure BREAK_AND_RUN rows only; no retest, opening reversal, or multi-family
  row is eligible.
- `SWING_2R_36H` is the only action.
- Every row must be executable at 0.01 lot with initial risk at most USD
  8.165487.
- At each calendar quarter, fit the fixed shallow gradient-boosting regressor
  only on rows whose signal and exit precede the quarter.
- Use the fixed PRICE_REGIME feature set. Labels, outcomes, IDs, timestamps,
  future regimes, P/L, MFE, and MAE are excluded.
- Set that quarter's score threshold from the model scores of the last 500
  completed training candidates at the frozen 40th percentile. No evaluation
  outcome enters the threshold.
- Accept at most one add-on trade per UTC weekday and one open add-on position.
- V50 Core is never filtered, changed, or subordinated.

## Acceptance and stop rule

Validation, final exam, and recent tail must each pass every locked gate. The
combined book must exceed 1.00 completed trade per weekday, PF 1.50, positive
net in each chronological half, positive winner-removal net, and the specified
positive-month threshold. The add-on must independently exceed PF 1.15 and
positive winner-removal net.

Combined closed drawdown may not exceed USD 300. After the frozen 1.25 buffer,
that is USD 375, below 15% of USD 2,998.45.

V52 makes no pristine-holdout claim because broad unranked family outcomes were
known. Ranked trade selection is evaluated causally. Any failed later gate is
terminal; there is no same-version threshold, action, feature, or gate repair.

Historical closed drawdown cannot prove whole-account floating drawdown. No
pass authorizes Python serving, an EA, demo/live trading, or broker action.
