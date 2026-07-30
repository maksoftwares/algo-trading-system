# EURUSD forward demo-shadow operations deployment

Deployment verified: `2026-07-30 06:40:03 UTC`

Status: **RUNNING_PRESTART / NO_ORDER_AUTHORIZATION**

## Runtime

- Demo account: `1033669`
- Server: `Capital.ComMena-Demo`
- Terminal root: `C:\MT5PortableProspectiveCollector`
- State root: `C:\MT5PortableProspectiveCollector\EURUSDForwardState`
- Collector audit: `PASS_RUNNING_PRESTART`
- Feature rows: `0`, as required before `2026-08-01 00:00 UTC`
- Heartbeat age at verification: `18.595616` seconds
- Collector trade permission: `NONE`
- Learner status: `WAITING_FORWARD_DATA`
- Resolved training days: `0`
- Eligible trades: `0`
- Demo-order authorization: `false`

## Scheduled operations

Both tasks use limited privileges and interactive logon. Their actions call
Windows PowerShell with `-NoProfile -NonInteractive -ExecutionPolicy Bypass`.

| Task | Trigger | Manual verification |
|---|---|---|
| `Codex-EURUSD-Prospective-Health` | Every five minutes | Exit code `0` |
| `Codex-EURUSD-Forward-Learner` | Daily 18:10 Dubai / 14:10 UTC | Exit code `0` |

The daily operation reverified the existing `2026-07-30` snapshot against its
SHA-256 ledger, marked all four snapshot files read-only, and completed with
`WAITING_MINIMUM_EVIDENCE`.

## Deployed artifact hashes

```text
4d4637c55d2a83c40205b89a29517ad06b1f4bcc69a96879842483459f64fd97  mt5\Experts\EurUsdProspectiveMultiSymbolCollector.ex5
c2d240bcdfb6abfec9fb01e2b98839b2d0caf25a860821cdad0abf36393f5856  mt5\Presets\EURUSD_PROSPECTIVE_MULTISYMBOL_COLLECTOR_DEMO.set
c7f873b27a3a63c0207cc5f85cd78487763801b44c1cdedbb9b1e79a05927bdf  mt5\Config\EURUSD_PROSPECTIVE_MULTISYMBOL_COLLECTOR_LIVE_DEMO_SHADOW.ini
```

The operations runner refuses execution if any deployed hash differs from
these packaged artifacts or if the startup configuration does not contain
`AllowLiveTrading=0` and `AllowDllImport=0`.

## Evidence boundary

This deployment proves unattended collection, integrity checks, and no-order
safety. It does not prove a profitable daily-frequency strategy. The forward
learner remains ineligible until its frozen minimum sample and every robustness
gate pass.
