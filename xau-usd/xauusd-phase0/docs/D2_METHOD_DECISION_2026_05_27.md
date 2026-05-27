# D2 Method Decision

Decision date: 2026-05-27

Overall status: METHOD_DECIDED_PHASE2_STILL_BLOCKED

## Decision

Keep the current fixed-notional monthly R-series White Reality Check / SPA as the canonical D2 gate for Phase 2 readiness.

Do not reclassify the current D2 result as PASS by collapsing same-family candidates after seeing the failing pairwise SPA result. The current report remains:

| Field | Value |
| --- | --- |
| Canonical report | `outputs/reports/PHASE0_REALITY_CHECK.md` |
| Current status | FAIL |
| Approved expert under test | `breakout_retest` |
| Non-empty candidate universe | 66 |
| Winner | `breakout_retest` |
| White Reality Check p-value | 0.0002 |
| Effective accepted p-value | 0.01 |
| Max pairwise SPA p-value | 0.0174 |
| Failing same-family alternatives | `round_number_retest_v0`, `symbol_normalized_round_retest_v0` |

## Why This Decision

The failing alternatives are not independent diversification candidates. They are close level-and-retest variants of the same breakout-retest edge family. That means the result is best interpreted as same-family selection ambiguity, not as proof that the family has no edge.

However, changing the D2 unit from candidate-level to family-level after observing a candidate-level FAIL would weaken the audit chain. The clean decision is therefore:

1. Preserve the current D2 FAIL.
2. Keep Phase 2 paper-mode implementation blocked.
3. Allow a separately pre-registered family-clustered D2 study as a new method candidate, not as a retroactive override.

## Phase Boundary

| Work item | Decision |
| --- | --- |
| Phase 1 dry-run telemetry | Allowed |
| Passive spread logging | Allowed |
| Phase 2 documentation and evidence prep | Allowed |
| Phase 2 paper-mode broker execution | Blocked |
| Live trading | Blocked |

## Pre-Registered Family-Clustered D2 Candidate Method

The project may implement a new diagnostic named:

```text
D2_FAMILY_CLUSTERED_V0
```

This method must be reviewed as a new statistical method before it can affect Phase 2 readiness.

### Purpose

Answer this narrower question:

```text
Does the breakout-retest edge family outperform the tested independent behavior families after multiple-testing adjustment?
```

It must not answer:

```text
Which same-family variant should be deployed?
```

Within-family deployment selection remains a separate engineering and paper-trading decision.

### Family Assignment Rule

Candidates are assigned to a family from pre-existing hypothesis text and research-result notes, not from performance ranking.

Initial required family labels:

| Family | Members |
| --- | --- |
| `breakout_retest_family` | `breakout_retest`, `swing_breakout_retest_v0`, `round_number_retest_v0`, `symbol_normalized_round_retest_v0`, `session_extreme_retest_v0`, and other explicitly same-family level/retest variants |
| `independent_candidate` | All non-level or non-retest candidates remain separate unless their hypothesis documents explicitly define a shared mechanism before testing |

If a candidate is ambiguous, classify it conservatively as its own family until a reviewer approves a family assignment.

### Representative Rule

The family representative must not be selected by highest backtest return after the fact.

For `breakout_retest_family`, the representative is:

```text
breakout_retest
```

Reason:

- earliest full Phase 0 PASS in the current package
- current Phase 1 dry-run observer base
- already cost-profiled and independently reproduced
- simpler and more established than later variants

Same-family alternatives may appear in a separate within-family comparison table, but they must not be used to choose a better historical performer for D2.

### Return Series Rule

Use the same fixed-notional monthly R construction as the current D2 report:

- one monthly R series per family representative
- same matrix-ledger source set
- same cost treatment
- same month alignment
- same circular block bootstrap
- same block length unless a reviewer pre-approves a change

Do not use compounding-dollar returns, percent account returns, or cell-level ledgers as separate candidates.

### Acceptance Rule

`D2_FAMILY_CLUSTERED_V0` can be marked PASS only if all are true:

1. White Reality Check p-value <= effective alpha.
2. All pairwise SPA checks against independent family representatives pass.
3. The report lists excluded same-family variants and explains why they are excluded from candidate-level pairwise SPA.
4. The report states that same-family variants are not diversification.
5. A reviewer or owner explicitly accepts the method decision before Phase 2 readiness uses it.

### Failure Rule

`D2_FAMILY_CLUSTERED_V0` fails if any independent family representative is statistically too close to the breakout-retest representative under the selected alpha, or if the method cannot produce a transparent family assignment table.

## Required Implementation Artifacts

If the family-clustered method is implemented, generate:

```text
outputs/reports/PHASE0_REALITY_CHECK_FAMILY_CLUSTERED.md
outputs/reports/PHASE0_REALITY_CHECK_FAMILY_ASSIGNMENTS.csv
outputs/manifests/PHASE0_REALITY_CHECK_FAMILY_CLUSTERED_MANIFEST.json
```

Add tests proving:

- same-family variants are excluded from pairwise SPA only after appearing in the assignment table
- `breakout_retest` remains the `breakout_retest_family` representative
- independent families are not silently collapsed
- the current candidate-level D2 report remains unchanged

## Current Go / No-Go Effect

| Milestone | Effect |
| --- | --- |
| Phase 1 dry-run | Not blocked |
| Passive spread logging | Not blocked |
| Phase 2 prep docs | Not blocked |
| Phase 2 paper-mode implementation | Blocked |
| Live trading | Blocked |

This document decides the method policy. It does not authorize broker execution and does not convert the current D2 FAIL into PASS.
