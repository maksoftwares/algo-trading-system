# V97 Causal Hourly Action Router Preregistration

## Conditional Target

V97 may run only after the artifact-bound V96 terminal Discovery failure. V60
already owns the `>=1/day` result. V97 succeeds only if its unchanged survivors
lift the byte-identical V59/V60 shared account to at least `2.0/day` separately
in Development-2, Confirmation, and Final while all economic, correlation, and
floating-drawdown gates pass.

V93-V96 rejected direct level, lead-lag, sign-reversal, and acceleration rules
from the free USA500, copper, and USD/CNH source foundation. V97 changes the
architecture rather than rescuing a threshold: every source-complete H1 decision
in Asia, London, or New York exposes symmetric LONG and SHORT actions, and a
regularized model ranks those actions or abstains.

## Causality And Model

All predictors are complete at the H1 decision. They contain completed XAU H1
price state, the last completed XAU M5 microstructure bar, completed source H1
returns normalized by prior-only rolling distributions, and deterministic UTC
time encodings. Directional features are multiplied by the candidate action;
the label is whether the side-correct fixed trade has positive stressed R.

Each semiannual test fold trains only on trades whose exits precede its two-month
calibration interval. Calibration uses score density, not calibration P&L, to
set a target opportunity rate. The next six months are out of sample. Discovery
has four such folds; Confirmation and Final have two each and remain sealed
until the preceding stage advances an unchanged policy.

## Registry

Exactly 1,000 attempts, `128001-129000`, are fixed before V97 outcomes:

- five feature sets;
- four L2 strengths;
- five fixed stop/target/hold profiles; and
- ten target add-on rates from `0.9` through `1.8` per weekday.

This is `200` policies per feature set. Full-family Benjamini-Hochberg control,
winner removal, every-fold frequency and AUC, direction balance, every-segment
profitability, worst-segment PF, drawdown, and cost-stressed expectancy all
apply. At most one policy per feature set may advance.

## Execution And Authority

Entry is the next contiguous XAU M5 quote, at Ask for LONG and Bid for SHORT.
Stops are checked before targets on ambiguous bars. Spread, ticket cost, holding
cost, and `0.05R` extra slippage are charged. A policy takes at most two entries
per UTC date, one per session, and two concurrent model positions.

V97 authorizes retrospective research-model fitting only. It grants no deployed
prediction, Python service, EA consumption, demo/live order, paid data,
Databento, or broker action. Exposed V97 outcomes cannot change this version.
The strategy program stops after V100 if the two-trades-per-day target is still
unmet.
