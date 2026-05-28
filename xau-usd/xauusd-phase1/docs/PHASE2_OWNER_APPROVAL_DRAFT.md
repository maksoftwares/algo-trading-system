# Phase 2 Owner Approval Draft

Overall status: PENDING

This is a draft only. It does not authorize Phase 2, paper trading, live capital, broker-side actions, or any order execution.

Do not copy this document to `outputs/reports/PHASE2_OWNER_APPROVAL.md` until every objective readiness gate has passed and the project owner explicitly approves paper-mode implementation.

If the live approval file is created before every objective gate is PASS, `PHASE2_READINESS_REPORT.md` rejects the owner approval gate as early/invalid even if the approval fields are otherwise complete.

## Current Gate State

| Gate | Current state | Required state |
| --- | --- | --- |
| Five trading-day wall-clock soak | PASS | PASS |
| Active-market 72-hour soak | PENDING | PASS |
| Process/code-freeze 96-hour gate | PENDING | PASS |
| Measured cost model | PENDING | PASS |
| Measured-cost revalidation | PENDING | PASS |
| Measured-cost assumption delta | PENDING | PASS |
| VPS selection | PENDING | PASS |
| VPS latency evidence | PENDING | PASS |
| VPS first-day verification | PENDING | PASS |
| Phase 1 acceptance | PENDING | PASS |
| Phase 1 review index | PENDING | PASS |
| Project owner approval | PENDING | PASS |

## Draft Approval Fields

Keep these values blank until signing. The live approval file must use these exact keys.

```text
owner:
decision_date_utc:
decision:
scope: Phase 2 paper-mode only; no live capital
minimum_net_expectancy_r: 0.15
single_edge_risk_ack: false
no_live_capital_ack: false
measured_cost_ack: false
selected_vps_provider:
selected_vps_region:
selected_vps_plan:
selected_vps_monthly_cost:
latency_evidence_path:
```

The live approval file is rejected if any required value is a placeholder, if the scope does not explicitly include `no live capital`, if the scope mixes paper approval with live-capital or broker-execution wording, or if the selected VPS provider, region, plan, monthly cost, or latency evidence path does not match `docs/PHASE2_VPS_SELECTION_MATRIX.md`.

Forbidden mixed-scope wording includes:

```text
plus live capital
live trading
broker execution
broker-side execution
order execution
real money
```

## Scope Boundary To Accept

```text
Phase 2 paper-mode implementation only.
No live capital.
No live order execution.
Approved edge family: breakout-retest only if no longer COST_REVALIDATION_PENDING or COST_SUSPENDED.
Approved future experts: breakout_retest, swing_breakout_retest_v0, and symbol_normalized_round_retest_v0 as same-family observation/paper candidates only after measured-cost eligibility.
Minimum net expectancy after measured cost: +0.15R.
Suspend the family if measured paper execution pushes net expectancy below +0.15R.
```

## Owner Checklist Before Signing

- I understand Phase 2 is a cost-measurement experiment, not a profit-confirmation phase.
- I understand the approved candidates are one correlated breakout-retest family, not independent diversification.
- I understand measured cost is still pending until 5 fresh observed market days are available.
- I understand paper-mode implementation still cannot include live capital.
- I understand no `OrderSend`, `OrderSendAsync`, `CTrade`, `trade.Buy`, `trade.Sell`, `PositionOpen`, or broker-side execution helper is authorized by this draft.
- I understand VPS selection must be backed by first-day latency/recovery/backup evidence and a verified periodic readiness task.
- I understand `outputs/reports/PHASE2_VPS_LATENCY_REPORT.md` must be PASS before VPS selection closes.
- I understand `outputs/reports/PHASE2_VPS_FIRST_DAY_VERIFICATION.md` must be PASS before owner approval is valid.

## Activation Rule

Only after all readiness gates are PASS, create:

```text
outputs/reports/PHASE2_OWNER_APPROVAL.md
```

The live file must include:

- `PHASE2_PAPER_PREP_APPROVED`
- owner name
- approval timestamp
- accepted paper-only scope
- minimum net expectancy threshold
- selected VPS provider and region
- latency evidence path
- first-day VPS verification path
- explicit single-edge risk acknowledgement
- explicit no-live-capital boundary
- reference to the latest `PHASE2_READINESS_REPORT.md`
