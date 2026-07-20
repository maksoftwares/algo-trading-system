# V81 Three-FX Dollar-Breadth Overreaction-Fade Preregistration

Date: `2026-07-20`

## Independent Hypothesis

V78-V80 used EURUSD and USDJPY to test whether XAU had not yet responded to a
dollar event. V81 tests the opposite economic state with a new causal input.
EURUSD, GBPUSD, and USDJPY must all agree on dollar direction, and XAU must
already have moved unusually far in its expected inverse-dollar direction. V81
then fades that completed XAU overreaction. It does not reuse a V78-V80 event,
threshold, selected policy, entry clock, or direction rescue.

For positive dollar strength, EURUSD and GBPUSD returns are negated and USDJPY
is not. All three signed returns must have the same nonzero sign. Expected XAU
direction is opposite the dollar sign; trade direction is opposite that
expected XAU direction. Every baseline quote is strictly earlier than the event
clock and every current quote is no later than it. Entry is the first
side-correct XAU quote strictly after the completed feature timestamp.

## Outcome-Blind Calibration

July-August 2018 registers exactly 1,000 policies from five causal horizons,
five minimum per-leg moves, five minimum three-leg sums, four minimum signed XAU
response ratios, and two minimum source quote counts. Selection can use only
candidate timestamps, frequency, active-day share, and direction balance. It
targets 0.80 candidate per eligible weekday and cannot open post-entry prices,
labels, P&L, stops, targets, or markouts.

## Frozen Economic Test

Development is September 2018-June 2021, confirmation July 2021-June 2022,
validation July 2022-June 2023, and exam July 2023-June 2024. A later stage
remains sealed unless every prior stage passes. One ounce is entered with
verified bid/ask ticks. Stop distance is the maximum of 0.50 completed M5 ATR,
four entry spreads, and USD 1.00; target is 1.00R; maximum hold is ten minutes.
Baseline cost is USD 0.30 per ticket and stress adds 0.05R slippage.

Each stage must retain 0.65-1.00 resolved trades per eligible weekday, positive
base and stress net, base PF at least 1.30, stress PF at least 1.20, at least 45%
positive days and 60% positive months, at least 20% in each direction, both
chronological-half stress PFs at least 1.10, positive stress net after removing
the five largest winners, stressed closed drawdown no greater than USD 200, and
a five-day block-bootstrap one-sided p-value no greater than 0.00125.

Failure is terminal. No mirror, threshold, horizon, timing, exit, cost, quota,
regime, or model rescue may be selected from exposed outcomes. A historical
pass remains provisional until shared-account testing and untouched forward
proof. V59/V60 remain byte-identical and outside selection.

The source-freezing sequence is refined by
`PRELOCK_STAGED_SOURCE_AMENDMENT.md`, written before any post-calibration
economic outcome was opened. It changes only when raw holdout source slices are
acquired and audited; the selected policy, execution, gates, and stage dates are
unchanged.
