# V60 Exit And Cluster Decomposition V17 Preregistration

Date: `2026-08-25`

Status: **READ-ONLY DIAGNOSTIC**

This package does not nominate, authorize, or deploy a trading rule. It tests
whether the next challenger should target portfolio profit protection,
same-source directional clustering, or neither. All historical, July, and
August outcomes are exposed; any mechanism suggested by this diagnostic must
receive a separate preregistration and clean forward confirmation.

## Questions

1. How does deployed portfolio protection change each accepted trade relative
   to its frozen source-endpoint outcome?
2. Is that effect stable by source, year, and month, or concentrated in a few
   large winners and losses?
3. Are later accepted trades in same-source, same-direction UTC-day clusters a
   stable negative cohort?
4. Are trades entered after an earlier same-source, same-direction loss on the
   same UTC day a stable negative cohort?
5. Did July's R1/R2/R3 silence survive an independent frozen-strategy
   reconstruction?
6. Do the exposed August broker records repeat the July cluster pattern?

## Frozen Definitions

- `endpoint_pnl_usd`: the candidate's frozen source exit, including the frozen
  source cost field already present in the canonical candidate ledger.
- `protected_pnl_usd`: the P/L produced by the deployed V60 tick-runtime replay.
- `protection_delta_usd`: protected minus endpoint P/L.
- `protection_changed`: protected exit time or P/L differs from the frozen
  endpoint by more than `1e-9`.
- `cluster`: at least two accepted trades sharing source, direction, and UTC
  entry date.
- `later_cluster_trade`: ordinal two or greater within such a cluster.
- `post_prior_loss_same_day`: an accepted trade whose entry follows the close
  of an earlier accepted trade with the same source and direction, on the same
  UTC date, whose protected P/L was negative.
- Analysis folds are fixed as `2021-2023`, `2024-2025`, `2026H1`, `2026-07`,
  and exposed `2026-08-through-25`.

No threshold search, veto simulation, parameter sweep, or deployment decision
is permitted in V17.

## Required Outputs

- `RESULT.json` and `RESULT.md`
- `PROTECTION_TRADE_AUDIT.csv`
- `PROTECTION_BY_SOURCE.csv`
- `PROTECTION_BY_SOURCE_YEAR.csv`
- `PROTECTION_BY_MONTH.csv`
- `CLUSTER_TRADE_AUDIT.csv`
- `CLUSTER_COHORTS.csv`
- `JULY_AUDIT.csv`
- `AUGUST_CLUSTER_AUDIT.csv`

## Interpretation Gates

These gates decide only whether a mechanism is eligible for separate research.
They cannot authorize trading.

### Profit-protection mechanism eligibility

Protection is eligible for a targeted follow-up only if all are true:

- a source has at least 30 protected closes;
- its protection delta is negative overall;
- the delta is negative in at least two of the three historical folds;
- removing protection is not claimed to be beneficial until a full
  path-dependent replay is separately preregistered.

### Cluster-control mechanism eligibility

Directional cluster control is eligible for a targeted follow-up only if all
are true:

- the cohort has at least 30 accepted trades overall;
- its protected profit factor is below `1.0`;
- its P/L is negative in at least two of the three historical folds;
- July and August are reported as exposed diagnostics, never as nomination
  evidence.

### Feed-integrity interpretation

The July core reconstruction is considered complete only when the frozen July
comparison reports explicit counts for R1 box, R1 pullback, R2 downtrend, and R3
compression and reports zero duplicate signals. Failed read-only confirmation
harnesses must not be treated as proof that deployed candidate generation was
silent.

## Decision Vocabulary

- `DIAGNOSTIC_SUPPORTS_TARGETED_PROTECTION_RESEARCH`
- `DIAGNOSTIC_SUPPORTS_TARGETED_CLUSTER_RESEARCH`
- `DIAGNOSTIC_SUPPORTS_BOTH_RESEARCH_LANES`
- `NO_STABLE_MECHANISM_KEEP_V60`

Every decision remains research-only. V60 broker behavior is unchanged.
