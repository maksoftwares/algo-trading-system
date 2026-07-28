# V60 ML Resolution Analysis

## Conclusion

The current ML blocker is execution granularity, not an undiscovered software
bug.

The causal continuous model contains allocation information, but account
`1033030` trades from a `0.01`-lot floor. It cannot express the model's
fractional `0.5x` through `1.5x` multipliers symmetrically:

- downward rounding can always skip a `0.01` trade;
- upward rounding to `0.02` is frequently rejected by source, account,
  directional, add-on, or unknown-risk controls.

That asymmetry removes profitable baseline trades more readily than it adds
high-ranked exposure.

## Locked V1

The preregistered source-aware dual model:

- used 1,625 known-risk training rows;
- proposed 174 top-ups and received 135 risk approvals;
- skipped no baseline trades;
- changed net from `$5,045.67` to `$5,047.13`;
- reduced PF from `1.721` to `1.681`;
- increased floating drawdown from `$335.34` to `$383.77`;
- improved four of six years; and
- produced a weekly-block one-sided 95% lower delta bound of `-$136.47`.

It is rejected.

## Development Diagnostics

These diagnostics were run after historical outcomes were exposed. They explain
the mechanism but are not validation evidence.

### Hard top-up after model maturity

Waiting for at least 1,000 prior trades, retaining every baseline trade, and
top-twenty-percent rounding produced:

- net `$5,252.61`, delta `+$206.94`;
- PF `1.718` versus baseline `1.721`;
- floating drawdown `$318.59` versus `$335.34`;
- net/floating drawdown `16.49` versus `15.05`; and
- weekly-block lower delta bound `+$51.22`.

The apparent gain is not a clean allocation win: the mean factor rises, PF
slips, and this policy was selected after its historical outcomes were known.

### Stochastic rounding

On mature, marginally top-up-eligible trades, 500 deterministic hash salts
produced:

- mean delta `+$82.16`;
- positive delta in 78.8% of salts;
- PF no worse than baseline in 76.0%;
- at least five nonnegative delta years in 82.6%; and
- all three conditions together in only 70.8%.

A policy whose result depends this heavily on an arbitrary salt is not suitable
for demo orders.

### Deterministic error diffusion

Causal cumulative rounding removed the arbitrary salt. Global rounding yielded:

- net `$5,045.26`, delta `-$0.41`;
- PF `1.719`;
- floating drawdown `$326.46`; and
- weekly-block lower delta bound `-$163.91`.

Source- and direction-specific variants also failed. Randomness was not hiding
a robust executable edge.

## Larger Candidate Corpus

The complete causal corpus contains 29,419 events and 73,116 labeled actions.
Its balanced-horizon study labeled 164,988 outcomes and registered 720 model
policies. It produced zero calibration survivors. Those labels come from
different candidate mechanisms and exits; forcing them into V60 does not create
high-quality V60 labels.

## What Reopens ML

ML broker action should be reconsidered only after at least one condition is
met:

1. A broker symbol or account supports lot increments below `0.01`.
2. Account equity and source risk limits safely support a larger baseline lot,
   allowing both upward and downward sizing around the baseline.
3. New prospective V60 observations demonstrate a fixed-lot veto group with
   negative expectancy and a dependence-aware confidence bound below zero.
4. A genuinely new causal feature source improves the ranking on data that was
   not used to choose the feature or policy.

Until then, deterministic V60 should remain the demo execution policy. Market,
candidate, trade, and observer logs can continue accumulating for later offline
retraining without enabling ML shadow or broker consumption.
