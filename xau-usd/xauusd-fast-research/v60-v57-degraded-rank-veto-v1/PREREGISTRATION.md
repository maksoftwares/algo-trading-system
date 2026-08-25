# V60 V57 Degraded-Rank Veto V1

Status: retrospective challenger research only.

The deployed V60 portfolio is the immutable benchmark. This package cannot write
to MT5, runtime state, account files, or the deployed configuration.

## Evidence boundary

All historical outcomes through 2026-06-30 and the demo outcomes through
2026-08-24 were already exposed before this package was created. The policy was
nominated after an exploratory accepted-trade diagnostic, so this is not an
untouched preregistration and cannot authorize deployment.

## Hypothesis

V57's bottom-decile causal ML scores are positive expectancy during normal
conditions, so a permanent bottom-tail veto is invalid. They may become harmful
when V57's own recently executed outcomes are degraded. Test exactly one policy:

1. Apply only to `V57_BREAK_SWING_H4ADX_HIGH`.
2. Retain the trade unless at least 20 earlier executed V57 trades have closed.
3. Calculate profit factor from the latest 20 closed V57 outcomes, before the
   candidate decision.
4. Veto only when prior-20 PF is below `1.0` and the causal score rank is below
   `0.10`.
5. Missing ranks retain the baseline trade.
6. Vetoed trades do not enter the executed-outcome health window.

The natural thresholds PF `1.0` and bottom decile `0.10` are fixed. No threshold
sweep may nominate a replacement policy in this package.

## Evaluation

Run the deployed mixed-risk, full-runtime five-second Dukascopy replay from
2021-01-01 through 2026-06-30 twice: unchanged V60 and the single challenger.
The candidate population, quotes, costs, guardian, cooldown, portfolio limits,
position-origin accounting, and V8 quarantine remain identical.

## Acceptance gates

- Baseline identity reproduces 1,390 trades and USD 3,603.565 net within fixed
  numerical tolerances.
- Challenger net P/L, PF, closed drawdown, and floating-equity drawdown are no
  worse than baseline.
- At least 99% of baseline trade count and 95% of baseline frequency remain.
- No calendar year has negative challenger-minus-baseline P/L.
- Final 3-, 6-, and 12-month P/L are no worse than baseline.
- The veto cohort contains at least five executed decisions and has PF below
  `1.0` under the unchanged baseline path.

A gate failure means `KEEP_DEPLOYED_V60`. A pass creates a historical challenger
only; genuinely new prospective demo evidence remains mandatory.
