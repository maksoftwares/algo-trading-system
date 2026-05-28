# Phase 2 VPS Latency Report

Overall status: PENDING

## Decision

VPS latency evidence is not complete yet. Keep VPS selection and Phase 2 readiness pending.

## Candidate

| Provider | Region | Endpoint | Average Ping | Packet Loss | Local Median | Improvement |
| --- | --- | --- | --- | --- | --- | --- |
| Pending | Pending | Pending |  |  | 129.78 ms |  |

## Checks

| Check | Status | Evidence |
| --- | --- | --- |
| selection_fields | PENDING | Missing field(s): provider, region, endpoint. |
| ping_evidence | PENDING | No ping evidence file provided. |
| packet_loss | PENDING | Packet loss evidence is not available yet. |
| latency_threshold | PENDING | Average latency evidence is not available yet. |
| local_baseline_comparison | PENDING | VPS average latency is not available for local-baseline comparison. |
| traceroute_evidence | PENDING | No traceroute evidence file provided. |
| port_reachability_evidence | PENDING | No Test-NetConnection evidence file provided. |

## Evidence Paths

- Ping output: `pending`
- Traceroute output: `pending`
- Test-NetConnection output: `pending`
- Local MT5 baseline: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_LOCAL_MT5_NETWORK_BASELINE.md`

## Capture Commands

Run these commands on the candidate VPS after it is provisioned:

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
- Keep `dry_run=true` and `trade_permission=false` until all Phase 2 readiness gates pass and the owner signs approval.
- Workspace root: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1`
