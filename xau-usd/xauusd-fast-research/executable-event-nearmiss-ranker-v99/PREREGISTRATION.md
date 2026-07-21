# V99 Executable Event Near-Miss Ranker Preregistration

## Correction Scope

V98 opened Discovery but produced no policy metric or P&L result. Its locked
grid failed because several exit profiles could not supply their requested
calibration frequency after side-correct spread and risk feasibility. V99 is
an engineering successor, not a post-outcome economic rescue.

V99 locks the only V98 profile with at least 1.2273 executable calibration
events per weekday in every Discovery fold: 1.0 ATR stop, 1.5R target, and
three-hour hold. It tests five event pools whose minimum diagnosed support is
at least 1.0909/day. Any target exceeding actual support saturates to all
available scored candidates and then fails or passes the unchanged frequency
gate normally; it cannot crash the campaign.

## Attempt Registry

Attempts `130001-131000` are exactly five feature sets, four fixed nonlinear
model specifications, five fixed event pools, and ten score-density targets
from 0.85 through 1.075 add-on trades per weekday. This is 1,000 policies, 200
per feature set.

The event rules, rolling 36-month model training, two-month score-only
calibration, chronological folds, execution costs, and all economic gates are
unchanged from the V98 preregistration. V98 had no economic result, and V99 may
not be changed after its outcome marker opens.

## Success

A stage pass is not program success. Final survivors must also pass the frozen
shared-account audit with byte-identical V59/V60 and at least `2.0` combined
trades per weekday separately in Development-2, Confirmation, and Final, while
all PF, correlation, position-risk, and buffered floating-drawdown gates pass.

Research fitting only. No deployment, Python prediction serving, EA, MT5 demo
or live action, paid data, Databento, or broker authority is granted.
