# NP1-G1 Clean-Root Probe — Incomplete Stop Packet

Status: `NP1_G1_EVIDENCE_INVALID`

The single authorized compilation succeeded. The first authorized Strategy Tester invocation (`warmup`) completed with zero trades, zero deals, zero positions, zero orders, and zero-byte sentinels, but the locked runner stopped because `Reports/np1_g1_warmup.htm` was absent.

The invocation ledger is final for this phase execution:

- MetaEditor compilations: `1`
- Strategy Tester invocations: `warmup` only (`1` of maximum `3`)
- `probe1`: not invoked
- `probe2`: not invoked
- retry/fourth invocation: not performed and not authorized

No spread provenance classification is made from this incomplete packet. Canonical NP1-C, census, profitability evaluation, deployment, and broker action remain blocked.
