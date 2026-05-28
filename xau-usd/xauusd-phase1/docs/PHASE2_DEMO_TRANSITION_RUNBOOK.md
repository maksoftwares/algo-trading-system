# Phase 2 Demo Transition Runbook

Status: PREPARED_NOT_AUTHORIZED

This runbook prepares the moment when real Phase 2 gates pass. It does not authorize Phase 2, paper trading, demo trading, broker execution, live capital, or order placement.

## Authority Rule

outputs/reports/PHASE2_READINESS_REPORT.md is the sole readiness authority.

Phase 3 experimental reports may be used only as design input. They cannot close any real Phase 2 gate, cannot enter the owner approval flow, and cannot authorize demo or paper-mode implementation.

## Required PASS Evidence Before Starting

| Gate | Required source |
| --- | --- |
| Phase 1 acceptance | `outputs/reports/PHASE1_ACCEPTANCE_REPORT.md` |
| Phase 1 review index | `outputs/reports/PHASE1_REVIEW_INDEX.md` |
| Observer parity | `outputs/reports/PHASE1_OBSERVER_PARITY_REPORT.md` |
| Active-market 72-hour soak | `outputs/reports/PHASE1_STATUS_SUMMARY.json` |
| Process/code-freeze 96-hour gate | `outputs/reports/PHASE1_STATUS_SUMMARY.json` |
| Measured cost model | `../xauusd-phase0/outputs/reports/MEASURED_COST_MODEL.md` |
| Measured-cost revalidation | `../xauusd-phase0/outputs/reports/BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md` |
| Measured-cost assumption delta | `../xauusd-phase0/outputs/reports/MEASURED_COST_ASSUMPTION_DELTA.md` |
| Local MT5 broker-access baseline | `outputs/reports/PHASE2_LOCAL_MT5_NETWORK_BASELINE.md` |
| VPS selection | `docs/PHASE2_VPS_SELECTION_MATRIX.md` |
| VPS latency evidence | `outputs/reports/PHASE2_VPS_LATENCY_REPORT.md` |
| VPS first-day verification | `outputs/reports/PHASE2_VPS_FIRST_DAY_VERIFICATION.md` |
| Demo preflight | `outputs/reports/PHASE2_DEMO_PREFLIGHT_REPORT.md` |
| Owner approval | `outputs/reports/PHASE2_OWNER_APPROVAL.md` |

Do not proceed unless every item above is PASS and `PHASE2_DEMO_COUNTDOWN.md` no longer says `DEMO_NOT_READY`.

## Go / No-Go Sequence

1. Refresh evidence:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\run_phase1_periodic_checks.py --files-dir C:\MT5PortableGoldMission\MQL5\Files --spread-files-dir C:\MT5PortableSpreadLogger\MQL5\Files
```

2. Verify the dashboard:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\verify_status_dashboard_freshness.py --repo-root ..\.. --status-path ..\..\status.html
```

3. Read these reports end to end:

```text
outputs/reports/PHASE2_READINESS_REPORT.md
outputs/reports/PHASE2_DEMO_PREFLIGHT_REPORT.md
outputs/reports/PHASE2_OWNER_ACTION_PACKET.md
outputs/reports/PHASE2_VPS_BOOTSTRAP_PACKET.md
outputs/reports/PHASE2_LOCAL_MT5_NETWORK_BASELINE.md
```

4. Confirm all authorization flags are still safe:

```text
paper_mode_authorized: false until the real implementation branch exists
demo_trading_authorized: false
broker_execution_authorized: false
live_trading_authorized: false
```

5. Confirm the live MT5 Phase 1 runtime remains untouched:

```text
dry_run=true
trade_permission=false
server_time_status=CLOCK_OK
no OrderSend / CTrade / broker-side execution code
```

6. Compare selected VPS latency against the local MT5 baseline:

```text
local baseline: outputs/reports/PHASE2_LOCAL_MT5_NETWORK_BASELINE.md
selected VPS: outputs/reports/PHASE2_VPS_LATENCY_REPORT.md
```

The selected VPS should materially improve on local median ping and show 0% packet loss. If it does not beat the local baseline, owner review is required before the VPS can be treated as an operational improvement.

7. Only then create a new implementation branch for Phase 2 paper-mode design review.

## First Implementation Scope After Go

The first implementation branch must be paper-shadow only:

- read the existing Phase 1 decision stream
- create a paper ledger
- calculate projected entry, stop, target, spread, slippage, and cost-in-R
- apply cost-aware blocks from the Phase 3 experiment as review logic only
- keep all broker-side execution disabled
- keep live capital disabled
- keep emergency/manual locks central

The first branch must not add:

- `OrderSend`
- `OrderSendAsync`
- `CTrade`
- `trade.Buy`
- `trade.Sell`
- `PositionOpen`
- real position modification
- live capital behavior

## No-Go Conditions

Stop and stay in Phase 1 dry-run if any of these are true:

- `PHASE2_READINESS_REPORT.md` is not PASS
- `PHASE2_DEMO_PREFLIGHT_REPORT.md` is not PASS
- measured-cost revalidation is below +0.15R
- the breakout-retest family is `COST_REVALIDATION_PENDING` or `COST_SUSPENDED`
- Phase 3 reports claim deployment authority
- latest MT5 row is not `dry_run=true` and `trade_permission=false`
- VPS latency, backup, recovery-login, NTP, or periodic scheduler evidence is missing
- selected VPS latency is not compared against `PHASE2_LOCAL_MT5_NETWORK_BASELINE.md`
- selected VPS decision record, latency report, and first-day manual evidence disagree on provider or region
- owner approval is absent, placeholder-filled, or mismatched with the VPS selection record

## Promotion Boundary

Passing this runbook permits only an owner-reviewed Phase 2 paper-mode implementation branch. It does not permit live trading.

Live-capital authorization requires a later phase, separate owner approval, and a separate evidence package.
