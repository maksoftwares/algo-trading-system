# US500 V41 Git-verified demo deployment

## Runtime identity

- Account: `1033030`
- Server: `Capital.ComMena-Demo`
- Terminal: `C:\MT5PortableTier1BestEA`
- Chart: `US500,M5`
- EA: `SharedAccount1033030\US500V41CausalSharedDemoEA.ex5`
- Contract: `SHARED_1033030_US500_V41_CAUSAL_CORE_20260804`
- Source and binary compile result: `0 errors, 0 warnings`
- Deployment revision: `2026-08-10-observability-only`

The 2026-08-10 revision adds best-effort runtime telemetry for terminal
connectivity, trading permissions, broker ping, tick freshness, server-clock
lag, and entry/exit request latency. It adds no retry, order gate, signal,
threshold, stop, target, sizing, or trading-window change. The regression test
removes only the instrumentation and recovers the exact prior frozen source
SHA-256 `91926cd40f33840096478471ab806b8f2b3e91e10775e721eaaf7613bcbb40b7`.

The checked-in preset is intentionally disarmed. The authorized preset remains
terminal-local. The authorization token is not included in this document or in
verification output.

## Immutable artifacts

The frozen manifest records SHA-256 hashes for the MQ5 source, EX5 rollback
binary, contract config, compile log, and disarmed preset. Verify the running
binary against an actual Git commit with:

```powershell
python multi-asset\operations\shared-demo-account-1033030-v1\verify_us500_git_deployment.py --git-ref <commit>
```

`VERIFIED` means every artifact exists in the resolved commit with the frozen
hash and the deployed EX5 is byte-for-byte identical to the committed binary.
The verifier is read-only and never connects to MT5 or submits an order.

Verify the attached EA's fresh operational heartbeat with:

```powershell
python multi-asset\operations\shared-demo-account-1033030-v1\verify_us500_runtime_health.py
```

The runtime verifier reads
`SHARED_1033030_US500_V41_HEALTH.csv` from MT5 Common Files. `DEGRADED`
reports high broker-request latency for diagnosis only; it never changes or
blocks trading behavior.

## Recovery

1. Check out the verified commit.
2. Copy `mql5\US500V41CausalSharedDemoEA.ex5` to
   `C:\MT5PortableTier1BestEA\MQL5\Experts\SharedAccount1033030\`.
3. Attach it only to `US500,M5` on demo account `1033030`.
4. Use the private terminal-local armed preset only after confirming the same
   account, server, contract hash, and order authorization.
5. Require a fresh `V41_INIT_OK` and healthy audit heartbeat before relying on
   the runtime.

No live-account authorization is provided by these artifacts.
