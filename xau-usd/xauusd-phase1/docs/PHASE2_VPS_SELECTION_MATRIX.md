# Phase 2 VPS Selection Matrix

Overall status: PENDING

This document prepares the VPS decision for Phase 2 paper-mode operations. It does not authorize Phase 2 implementation, paper trading, live capital, broker-side actions, or any order execution.

## Decision Rule

The status may be changed to `PASS` only after the project owner selects a provider and fills the decision record below with real values.

Required before `PASS`:

- provider selected
- region selected
- minimum machine specification confirmed
- backup method selected
- recovery access documented
- monitoring approach selected
- expected monthly cost documented
- owner accepts that Phase 2 is paper-mode only

## Minimum Requirements

| Area | Minimum requirement | Status |
| --- | --- | --- |
| Region | Near the broker trade server or lowest practical latency region available to the owner | PENDING |
| CPU / RAM | At least 2 vCPU and 4 GB RAM for MT5 plus monitoring scripts | PENDING |
| Storage | SSD, at least 60 GB usable space | PENDING |
| Operating system | Windows environment compatible with MT5 Portable and MetaEditor compilation | PENDING |
| Clock sync | NTP enabled and timezone documented | PENDING |
| Access | Administrator access plus documented recovery login | PENDING |
| Backup | Weekly image/file backup plus repo/config backup after every release slice | PENDING |
| Monitoring | Separate scheduler or external host can run health checks outside MT5 | PENDING |
| Security | Password/key rotation and limited credential sharing | PENDING |
| Cost | Monthly cost acceptable to owner | PENDING |

## Candidate Comparison

Fill this table when provider choices are available. Do not use marketing uptime claims as the only criterion.

| Candidate | Region | CPU/RAM | Storage | Monthly cost | Backup support | Recovery access | Monitoring fit | Notes | Status |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| Candidate A | Pending | Pending | Pending | 0 | Pending | Pending | Pending | Pending owner research | PENDING |
| Candidate B | Pending | Pending | Pending | 0 | Pending | Pending | Pending | Pending owner research | PENDING |
| Candidate C | Pending | Pending | Pending | 0 | Pending | Pending | Pending | Pending owner research | PENDING |

## Decision Record

| Field | Value |
| --- | --- |
| Selected provider | Pending owner selection |
| Selected region | Pending owner selection |
| Selected plan | Pending owner selection |
| Monthly cost | Pending owner selection |
| Backup method | Pending owner selection |
| Monitoring endpoint or scheduler | Pending owner selection |
| Recovery access owner | Pending owner selection |
| Decision date | Pending owner selection |
| Owner acceptance | Pending owner selection |

## Deployment Boundary

The VPS is for Phase 2 paper-mode evidence only after all readiness gates pass. It must start with the same safety posture as the local Phase 1 shell:

```text
dry_run=true
trade_permission=false until explicitly changed by an approved future paper-mode design
no live capital
no broker order API calls
no trade helper object usage
no broker-side execution behavior
```

## First-Day VPS Verification

After selection and setup, the first VPS verification packet must include:

- repository commit hash
- MT5 terminal path
- MT5 data path
- compile log
- latest startup log
- latest decision log row
- `PHASE1_EXTERNAL_HEALTH.json`
- `PHASE1_STATUS_SUMMARY.json`
- `PHASE2_READINESS_REPORT.md`
- screenshot or text evidence of NTP/time sync
- backup configuration evidence
