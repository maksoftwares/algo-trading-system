# EURUSD Neutral capacity-selective post-event preregistration

This contract and its exact 75-candidate manifest are hash-locked before
loading a forward outcome for this rule.

The parent N29 aggregate outcomes were already known, so this remains adaptive
research. The threshold selection below used only model scores and candidate
counts—not P&L, wins, oracle membership, or a forward label.

## Fixed model

The learner, features, training window, labels, standardization, coefficients,
and side mapping are identical to the locked N30 selective screen:

- 13 decision-time features;
- LONG and SHORT stacked with shared coefficients;
- one standardized L2 logistic fit with `C=0.1`;
- 285 training candidates and 570 side rows from 2019-2022;
- no class weighting, feature search, interactions, calibration, or refit.

The only new operation is an outcome-blind capacity ladder.

## Frozen capacity ladder

Evaluate thresholds in descending order: 0.42, 0.41, and 0.40. Select the
highest threshold producing at least eight candidates in every forward
window.

| Threshold | 2023 | 2024 | 2025 | 2026 H1 | Capacity pass |
|---:|---:|---:|---:|---:|---:|
| 0.42 | 11 | 5 | 9 | 3 | No |
| 0.41 | 16 | 12 | 13 | 5 | No |
| 0.40 | 24 | 18 | 24 | 9 | Yes |

The selected threshold is therefore 0.40. This is the theoretical 1.5R
break-even probability before costs and the bottom of the fixed ladder. It
will not be lowered after outcomes.

## Forward-outcome-blind manifest

| Window | Source candidates | Selected | Cash | Selected LONG |
|---|---:|---:|---:|---:|
| 2023 validation | 54 | 24 | 30 | 50.00% |
| 2024 validation | 55 | 18 | 37 | 44.44% |
| 2025 pseudo-OOS | 64 | 24 | 40 | 70.83% |
| 2026 H1 pseudo-OOS | 37 | 9 | 28 | 55.56% |
| Forward total | 210 | 75 | 135 | 56.00% |

Selected candidate manifest SHA-256:

`d81f8fe7d3bc579ee0c46c41cedec1f1e5fb2d7ea3ea3f64e5d77c918b1d3ebd`

There is at most one trade per Neutral date. Frequency is descriptive and not
an admission target.

## Execution and admission

Execution is unchanged from N29:

- causal bid/ask entry at the selected post-event M5 open;
- observation-structure stop with 4-25 pip risk bounds;
- 1.5R target and 12-hour maximum hold;
- 0.7-pip minimum spread and 0.1-pip adverse slippage per side;
- stop first on an ambiguous M5 bar;
- one open position and 0.25 portfolio R per ticket.

Each window requires at least eight trades, 40-60% wins, 1.35-1.75 realized
payoff, positive net R, and ticket and daily PF strictly above 1.00.

Forward overall PF must reach 1.15 with a 45-55% win rate. It must remain
positive under an extra half-pip stress and after removing the best 5% of
winners. Daily portfolio drawdown cannot exceed 20R.

The latest six months require at least eight trades, positive net R, and
ticket and daily PF above 1.00. Exact oracle precision must reach 5% and
same-side 15-minute precision 20%. Frequency is not a gate.

## Prohibitions

No threshold, model, feature, event subgroup, year activation, or execution
parameter may change after outcomes. In particular, a favorable 2026 H1 block
cannot rescue failures in earlier windows.

## Evidence status

Even a complete historical pass remains research-only. Demo promotion would
require at least 100 new observations and six post-lock calendar months from
2026-07-29. No broker action is authorized.
