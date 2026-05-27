# Phase 2 VPS Selection Matrix

Overall status: PENDING

This document prepares the VPS decision for Phase 2 paper-mode operations. It does not authorize Phase 2 implementation, paper trading, live capital, broker-side actions, or any order execution.

## Decision State

Status remains `PENDING` because no provider has been selected, no VPS has been provisioned, and no real latency test has been run against `Capital.ComMena-Live`.

Prepared state:

- shortlist complete
- minimum requirements defined
- owner-selection rule defined
- first-day VPS verification packet defined
- approval still pending

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
- fresh latency test captured from the selected VPS to the broker server or MT5 endpoint

Recommended owner-selection rule:

```text
Choose the lowest-latency Windows VPS that meets the minimum spec,
has recoverable backups,
can run MT5 Portable continuously,
and remains acceptable in monthly cost.

If latency is similar, prefer stronger operational controls over lower price.
If the cheapest option lacks 4 GB RAM or reliable backups, reject it for Phase 2.
```

## Minimum Requirements

| Area | Minimum requirement | Status |
| --- | --- | --- |
| Region | Near `Capital.ComMena-Live` or lowest measured latency region available to the owner | PENDING |
| CPU / RAM | At least 2 vCPU and 4 GB RAM for MT5 plus monitoring scripts | READY_FOR_OWNER_SELECTION |
| Storage | SSD/NVMe, at least 60 GB usable space | READY_FOR_OWNER_SELECTION |
| Operating system | Windows Server compatible with MT5 Portable and MetaEditor compilation | READY_FOR_OWNER_SELECTION |
| Clock sync | NTP enabled and timezone documented | READY_FOR_OWNER_SELECTION |
| Access | Administrator access plus documented recovery login | PENDING |
| Backup | Weekly image/file backup plus repo/config backup after every release slice | PENDING |
| Monitoring | Separate scheduler or external host can run health checks outside MT5 | READY_FOR_OWNER_SELECTION |
| Security | Password/key rotation and limited credential sharing | READY_FOR_OWNER_SELECTION |
| Cost | Monthly cost acceptable to owner | PENDING |

## Candidate Comparison

Provider details were checked on 2026-05-27 from provider pages. Pricing and promotions can change, so confirm at checkout before selection.

| Candidate | Region to Test First | CPU/RAM | Storage | Monthly cost shown | Backup support | Recovery access | Monitoring fit | Notes | Status |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| ForexVPS.net Core | Lowest-latency region from broker-latency tool; test London/Dubai/nearest available | 2 CPU / 4 GB RAM | 100 GB | S$52 monthly, S$32.80/mo annual display | Automated backups included | RDP/client-area control expected | Good | Meets minimum spec cleanly; 22 locations; Windows Server 2016/2019/2022; stronger fit than under-4GB plans | SHORTLISTED |
| FXVM Advanced VPS | Dubai, Mumbai, Singapore, London | 2 CPU / 4 GB RAM | 90 GB SSD | $50/mo list, $42.50/mo promo display | Automatic backups listed | RDP/client-area control expected | Good | Meets minimum spec; useful Asia/Middle East regions; Basic is below 4 GB RAM, so Advanced is the minimum acceptable FXVM plan | SHORTLISTED |
| QuantVPS Lite | Only if US/Chicago latency to broker is unexpectedly best | 4 cores / 8 GB RAM | 75 GB NVMe | From $59.99/mo | RAID10 redundant storage listed; verify backup option | Full admin access listed | Good | Strong hardware but Chicago/futures-oriented; likely overkill unless latency test wins | WATCHLIST |

## Source Notes

- ForexVPS.net Core page displayed 2 CPU, 4 GB memory, 100 GB storage, 22 locations, automated backups, dedicated IP, and Windows Server 2016/2019/2022.
- FXVM page displayed Lite/Basic/Advanced/High Freq plans. Advanced VPS is the first FXVM plan in the table that reaches 4 GB RAM. FXVM locations include Dubai, Mumbai, Singapore, London, New York, Tokyo, Hong Kong, and others.
- QuantVPS pricing page displayed VPS Lite from $59.99/mo with 4 cores, 8 GB RAM, 75 GB NVMe, Windows/Linux support, full admin access, and 99.999% uptime SLA.
- All provider claims must be treated as vendor claims until verified by our own latency, restart, logging, and recovery tests.

## Recommended Selection

Current recommendation for owner review:

```text
Primary trial: FXVM Advanced VPS in Dubai, Mumbai, or Singapore.
Backup trial: ForexVPS.net Core in the lowest-latency available region.
Defer: QuantVPS unless broker latency testing favors US/Chicago.
```

Reasoning:

- FXVM Advanced meets the minimum 2 CPU / 4 GB / 60 GB requirement and offers Dubai/Mumbai/Singapore regions to test against the current broker account geography.
- ForexVPS.net Core is a clean minimum-spec alternative with stronger entry resources than FXVM Basic and an explicit 4 GB / 100 GB profile.
- QuantVPS has excellent specs but is more expensive and appears more Chicago/futures oriented, so it should not be chosen for XAU/Capital.com paper mode unless latency proves it.

## Latency Test Plan

Run this only after a trial VPS is provisioned:

```powershell
ping <broker_or_mt5_endpoint>
tracert <broker_or_mt5_endpoint>
Test-NetConnection <broker_or_mt5_endpoint> -Port 443
```

Then generate the canonical report:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase2_vps_latency_report.py `
  --provider "<provider>" `
  --region "<region>" `
  --endpoint "<broker_or_mt5_endpoint>" `
  --ping-output outputs\reports\vps_ping.txt `
  --tracert-output outputs\reports\vps_tracert.txt `
  --test-net-output outputs\reports\vps_test_net.txt
```

Also record from MT5:

- broker server name
- account server ping shown by MT5, if available
- latest `timestamp_broker`
- latest `timestamp_utc`
- latest `timestamp_local`
- average decision-log write gap for the first hour

Pass preference:

```text
median ping <= 50 ms: preferred
median ping 51-100 ms: acceptable for Phase 2 paper-cost measurement
median ping > 100 ms: owner review required
packet loss > 0%: reject or retest before selection
```

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
| Latency evidence path | `outputs/reports/PHASE2_VPS_LATENCY_REPORT.md` after VPS provision |
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
- latency test output
- RDP recovery-login confirmation
