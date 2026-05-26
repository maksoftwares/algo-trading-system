# Phase 2 Owner Approval Template

This is a template only. Do not copy it to `outputs/reports/PHASE2_OWNER_APPROVAL.md` until every objective Phase 2 readiness gate has passed and the project owner explicitly approves paper-mode implementation.

## Required Gate Evidence

| Gate | Required state | Evidence path |
| --- | --- | --- |
| Phase 1 acceptance | PASS | `outputs/reports/PHASE1_ACCEPTANCE_REPORT.md` |
| Phase 1 review index | PASS | `outputs/reports/PHASE1_REVIEW_INDEX.md` |
| Phase 2 readiness | PASS | `outputs/reports/PHASE2_READINESS_REPORT.md` |
| Five trading day soak | PASS | `outputs/reports/PHASE1_SOAK_DRIFT_REPORT.md` |
| Measured cost model | PASS | `../xauusd-phase0/outputs/reports/MEASURED_COST_MODEL.md` |
| Measured-cost revalidation | PASS after any required correction | `../xauusd-phase0/outputs/reports/BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md` |
| Measured-cost assumption delta | PASS | `../xauusd-phase0/outputs/reports/MEASURED_COST_ASSUMPTION_DELTA.md` |
| Measured-cost audit | REVIEWED | `../xauusd-phase0/outputs/reports/BREAKOUT_RETEST_MEASURED_COST_AUDIT.md` |
| Safety audit | PASS | `scripts/audit_phase1_safety.py` |
| Single-edge risk plan | Accepted | `docs/PHASE2_SINGLE_EDGE_RISK_PLAN.md` |
| Cost-measurement protocol | Accepted | `docs/PHASE2_COST_MEASUREMENT_PROTOCOL.md` |

## Owner Decision Fields

The live approval file must use these exact keys. Keep values blank until the project owner signs.

```text
owner:
decision_date_utc:
decision:
scope: Phase 2 paper-mode only; no live capital
minimum_net_expectancy_r: 0.15
single_edge_risk_ack: false
no_live_capital_ack: false
measured_cost_ack: false
```

Required values:

- `decision` must contain `APPROVED`
- `scope` must be paper-mode only and must not authorize live capital
- `minimum_net_expectancy_r` must be at least `0.15`
- `single_edge_risk_ack`, `no_live_capital_ack`, and `measured_cost_ack` must be `true`

## Approved Scope Text

```text
Phase 2 paper-mode implementation only.
No live capital.
No live order execution.
Approved edge family: breakout-retest only if no longer cost-suspended.
Approved future experts: breakout_retest and swing_breakout_retest_v0 as same-family observation/paper candidates.
Minimum net expectancy after measured cost: +0.15R.
Suspend the family if measured paper execution pushes net expectancy below +0.15R.
```

## Approval Token

Only add the following token to the live approval file after the owner signs the decision above:

```text
PHASE2_PAPER_PREP_APPROVED
```

## Live File Creation Rule

When all gates pass, create:

```text
outputs/reports/PHASE2_OWNER_APPROVAL.md
```

The live file must include:

- the approval token
- owner name
- approval timestamp
- accepted scope
- explicit single-edge risk acknowledgement
- explicit no-live-capital boundary
- reference to the latest Phase 2 readiness report
