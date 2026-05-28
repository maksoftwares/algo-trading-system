# Phase 2 Demo Countdown

This report is a countdown aid only. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

Overall status: DEMO_NOT_READY

## Gate Summary

| Field | Value |
| --- | --- |
| Phase 2 readiness | PENDING |
| Phase 1 acceptance | PENDING |
| Measured cost model | PENDING |
| Measured-cost revalidation | PENDING |
| Measured-cost delta | PENDING |
| Paper mode authorized | false |
| Broker execution authorized | false |
| Live trading authorized | false |
| Pending gates | 11 |

## Wait Gates

| gate | status | current | required | remaining | unit |
| --- | --- | --- | --- | --- | --- |
| Active-market 72-hour soak | PENDING | 26.83 | 72.0 | 45.17 | hours |
| Process/code-freeze 96-hour gate | PENDING | 27.91 | 96.0 | 68.09 | hours |
| Measured cost model | PENDING | 2.0 | 5.0 | 3.0 | fresh_market_days |

## Owner Actions

| gate | status | action |
| --- | --- | --- |
| VPS selection | PENDING | Owner selects provider/region/plan from PHASE2_VPS_SELECTION_MATRIX.md. |
| VPS latency evidence | PENDING | After VPS is provisioned, run scripts/capture_phase2_vps_latency_evidence.ps1 from the Phase 1 root. |
| VPS first-day verification | PENDING | After VPS setup, capture NTP, backup, recovery-login, MT5 path, compile, startup, decision, and health evidence. |
| Project owner approval | PENDING | Sign PHASE2_OWNER_APPROVAL.md only after all objective gates are PASS. |

## Runtime Snapshot

| Field | Value |
| --- | --- |
| decision_rows | 1057 |
| latest_bar | 2026.05.28 14:35:00 |
| dry_run | true |
| trade_permission | false |
| server_time_status | CLOCK_OK |

## Forbidden Until Ready

- paper-mode implementation
- MT5 runtime redeployment for trading behavior
- broker-side execution paths
- live capital
- treating Phase 3 experimental PASS as Phase 2 readiness

## Refresh Command

```powershell
.\xau-usd\xauusd-phase0\.venv\Scripts\python.exe xau-usd\xauusd-phase1\scripts\run_phase1_periodic_checks.py --files-dir C:\MT5PortableGoldMission\MQL5\Files --spread-files-dir C:\MT5PortableSpreadLogger\MQL5\Files
```
