# EURUSD Neutral synchronous cross-asset preregistration

Frozen: 2026-07-27 18:45 UTC

Campaign: `eurusd-neutral-synchronous-crossasset-v1`

## Hypothesis

The direct oracle-imitation baseline learned the oracle's midnight timing
but could not identify direction. Exact completed five-minute DXY and U.S.
Treasury-bond reactions may separate the future-winning direction better
than the lagged hourly state used by earlier Neutral experts.

This is adaptive historical research. The oracle and previous campaign
results are already known. Later windows are chronological pseudo-OOS
falsification, not pristine evidence.

## Controlled change

The candidate timestamps, Neutral regime filter, historical oracle label,
12-hour label purge, EURUSD/tick features, L2 model class, development
periods, threshold grid, online routing, four-position limit, fixed 4-pip
risk, 1.50R target, costs, and admission gates remain unchanged from
`eurusd-neutral-oracle-imitation-v1`.

The only model-input change is adding the 18 columns frozen in
`config/frozen_neutral_synchronous_crossasset.json`.

## Causal alignment

The external row timestamp is the M5 bar start. For a candidate with
`signal_time = t` and `completion_time = t + 5 minutes`, only the exact DXY
and Treasury row timestamped `t` may be joined. That bar is complete at the
decision time. Both symbols must be available. Missing rows are dropped and
never forward-filled.

Returns, bar location, range, tick intensity, spread intensity, joint
pressure, and DXY/bond agreement use the completed current bar and trailing
bars only. Rolling baselines exclude the current bar where they estimate a
normal level. Directional features are aligned so positive values support
the candidate EURUSD side.

The 525,099-row historical source has SHA-256
`3982a3bb56741a5c5139f0381696d4ec4f50d7b1be7588a0efa2664bbf51ffa4`.
Its separately collected prospective continuation reproduced 266 overlap
rows with maximum absolute error 0.0.

## Evaluation and rejection

Fit 2019-2020, select one threshold on 2021-2022, then refit annually for
2023, 2024, 2025, and 2026 H1 using only label-complete earlier rows.

Every forward window must have at least 50 trades, win 45%-55%, realize
1.35-1.75 payoff, reach PF 1.10, and have positive expectancy. Overall
behavioral gates require at least 10% exact precision, 5% exact recall, and
15% same-side precision within 15 minutes. Extra half-pip stress must remain
positive.

Any failure rejects the expert. Improvement over the prior PF 0.654 or exact
precision 23.03% is diagnostic only and cannot substitute for an absolute
gate. No post-outcome feature, threshold, hour, or direction repair is
permitted.
