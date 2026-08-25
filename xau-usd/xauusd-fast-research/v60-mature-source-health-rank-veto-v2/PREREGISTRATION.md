# V60 Mature Source-Health Rank Veto V2

Status: post-V1 retrospective challenger research only.

V1 improved P/L and drawdown but missed its 99% retention gate by one trade.
Its only veto from a low-sample source was an R3 winner. V2 records the
mechanism correction transparently: a source must have 50 completed executions
before a recent-health veto can be considered. This rule was nominated after
seeing V1, so the full replay is confirmation within exposed data, not untouched
evidence.

## Locked policy

For every specialist independently, retain a candidate unless all are true:

1. The source has at least 50 earlier retained trades closed.
2. Its latest-20 retained executed trades have profit factor below `1.0`.
3. The candidate's pre-existing causal ML rank is below `0.10`.

Missing rank means retain. Vetoed trades never enter future health. All
thresholds are locked before running the V2 full replay. The strict V1 gates are
unchanged, including 99% trade retention and no negative calendar-year delta.

A pass creates a historical challenger only. Deployment remains forbidden until
new prospective broker outcomes support it.
