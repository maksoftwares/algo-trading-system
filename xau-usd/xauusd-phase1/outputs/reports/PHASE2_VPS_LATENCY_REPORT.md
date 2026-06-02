# Phase 2 VPS Latency Report

Overall status: PASS

## Decision

The owner selected the local workstation as the Phase 2 runtime host for the next few months; local MT5 baseline evidence is accepted for this host-selection gate.

## Candidate

| Provider | Region | Endpoint | Average Ping | Packet Loss | Local Median | Improvement |
| --- | --- | --- | --- | --- | --- | --- |
| LOCAL_SYSTEM_RUNTIME | Local Windows workstation / Asia-Dubai operator timezone | Capital.ComMena MT5 local authorization ping baseline | 129.78 ms | n/a | 129.78 ms |  |

## Checks

| Check | Status | Evidence |
| --- | --- | --- |
| selection_fields | PASS | provider=LOCAL_SYSTEM_RUNTIME; region=Local Windows workstation / Asia-Dubai operator timezone; endpoint=Capital.ComMena MT5 local authorization ping baseline. |
| local_baseline_comparison | PASS | Owner selected LOCAL_SYSTEM_RUNTIME; local MT5 median latency is 129.78 ms across 5761 sample(s). No VPS-improvement claim is made. |
| local_runtime_owner_exception | PASS | Owner selected local workstation runtime for the next few months and accepts power/internet/restart risk. |

## Evidence Paths

- Ping output: `pending`
- Traceroute output: `pending`
- Test-NetConnection output: `pending`
- Local MT5 baseline: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_LOCAL_MT5_NETWORK_BASELINE.md`

## Capture Commands

Run these commands on the candidate VPS after it is provisioned, unless `Provider` is `LOCAL_SYSTEM_RUNTIME`:

```powershell
.\scripts\capture_phase2_vps_latency_evidence.ps1 -Provider "<provider>" -Region "<region>" -Endpoint "<broker_or_mt5_endpoint>" -SampleCount 20
```

Manual fallback:

```powershell
$endpoint = "<broker_or_mt5_endpoint>"
ping -n 20 $endpoint | Tee-Object -FilePath outputs\reports\vps_ping.txt
tracert $endpoint | Tee-Object -FilePath outputs\reports\vps_tracert.txt
Test-NetConnection $endpoint -Port 443 | Tee-Object -FilePath outputs\reports\vps_test_net.txt
python scripts\generate_phase2_vps_latency_report.py --provider "<provider>" --region "<region>" --endpoint $endpoint --ping-output outputs\reports\vps_ping.txt --tracert-output outputs\reports\vps_tracert.txt --test-net-output outputs\reports\vps_test_net.txt
```

## Boundary

- This report is evidence-only and does not authorize Phase 2 paper-mode implementation.
- Passing latency evidence does not authorize live capital or broker-side execution.
- A VPS latency PASS requires a PASS local MT5 baseline and at least 10% better average ping than the local median.
- A LOCAL_SYSTEM_RUNTIME PASS means the owner has selected the local workstation instead of claiming any VPS latency improvement.
- Keep `dry_run=true` and `trade_permission=false` until all Phase 2 readiness gates pass and the owner signs approval.
- Workspace root: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1`
