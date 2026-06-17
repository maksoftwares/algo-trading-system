# A3 Tier1 Compat Owner Authorization Packet - 2026-06-17

Status: `PENDING_OWNER_DECISION`

Scope: A3 demo account `1033669`, XAUUSD only, `A3_BREAKOUT_TIER1_COMPAT_V1`, magic `933400`.

This packet does not authorize canonical Phase 2, live trading, real capital, or broker-action order placement. It only records whether the owner approves attaching the new lane as a non-executing observer/dry-run chart after compile proof and pre-attachment evidence are complete.

## Owner Decision

Owner name:

Decision: `APPROVE` / `DECLINE`

Signed at Dubai time:

## Lane Covered

| Field | Value |
| --- | --- |
| EA | `Account3BreakoutTier1CompatExecutor.mq5` |
| Run id | `A3_BREAKOUT_TIER1_COMPAT_V1` |
| Account | `1033669` |
| Symbol | `XAUUSD` |
| Magic | `933400` |
| Comment | `A3_BREAKOUT_TIER1_COMPAT` |
| Lot | `0.01` |
| Session gate | Server hour `12-15` |
| XAU stop-distance floor | Enabled |
| Trend guard | Shadow-only |
| Breakeven / partial | Disabled |
| Initial attach mode | Observer/dry-run only |

## Required Acknowledgments

I acknowledge that the current review verdict is `PASS_WITH_CONDITIONS`, not unconditional deployment approval.

I acknowledge that the strict A3 estimate proves loss-cluster avoidance only: the new gate would have allowed 0 historical A3 plain trades and avoided `-96.39 AED`, but this does not prove forward profit.

I acknowledge that the A2 proxy (`+104.92 AED`) and full XAU evening breakout proxy (`+478.66 AED`) are small-sample, regime-exposed, indicative-only numbers.

I acknowledge that no execution-enabled preset may be committed.

I acknowledge that broker-action arming requires a later, separate owner decision after observer/dry-run evidence is reviewed.

## Mandatory Preconditions Before Observer/Dry-Run Attachment

| Gate | Required evidence | Status |
| --- | --- | --- |
| Owner approval | This packet signed `APPROVE` | `PENDING` |
| Compile proof | MetaEditor compile log, 0 errors / 0 warnings | `PENDING` |
| A3 profile backup | Backup path recorded before attach | `PENDING` |
| Safe preset | `InpDryRunOnly=true`, `InpBrokerActionAllowed=false` | `READY` |
| Zero pre-existing magic | No open/pending `933400` orders or positions | `PENDING` |
| Startup proof | Login `1033669`, demo server, magic `933400`, scope locks pass | `PENDING` |
| Runtime boundary | A1, A2, A3 plain `933200`, A3 improved `933300` untouched | `PENDING` |

## Approved Initial Action If Signed

Attach `Account3BreakoutTier1CompatExecutor.mq5` to A3 XAUUSD M5 using the committed safe preset or an equivalent local non-executing preset:

```text
InpDryRunOnly=true
InpBrokerActionAllowed=false
InpAllowedAccountLoginsCsv=1033669
InpTargetSymbol=XAUUSD
InpMagicNumber=933400
```

Expected result: the lane logs would-signals, session-gate decisions, stop-floor fields, and trend-shadow decisions. It must not place orders.

## Not Approved By This Packet

- Broker-action order placement.
- Live trading.
- Real capital.
- Any change to A1, A2, A3 plain, or A3 improved.
- Any committed armed preset.
- Any change to canonical Phase 2 status.
