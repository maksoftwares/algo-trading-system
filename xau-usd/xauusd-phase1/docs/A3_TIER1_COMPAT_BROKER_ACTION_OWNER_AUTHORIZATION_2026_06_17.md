# A3 Tier1 Compat Broker-Action Owner Authorization - 2026-06-17

Status: `APPROVED_BY_OWNER_CHAT`

Scope: demo-only A3 account `1033669`, `Capital.ComMena-Demo`, `XAUUSD` only, `A3_BREAKOUT_TIER1_COMPAT_V1`, magic `933400`, fixed lot `0.01`.

This authorization does not approve canonical Phase 2, live trading, real capital, or any change to A1/A2/A3 existing lanes. It only approves attaching the new A3 Tier1-compatible breakout lane in broker-action mode on the A3 demo terminal.

## Owner Approval Evidence

Owner instruction recorded in chat on 2026-06-17:

```text
We don't do observing we directly start placing orders, Do the needful I approve.
```

## Approved Action

Attach `Account3BreakoutTier1CompatExecutor.mq5` to the A3 demo terminal as a broker-action chart:

| Field | Value |
| --- | --- |
| Terminal | `C:\MT5PortableRepairLane` |
| Account | `1033669` |
| Server marker | `Demo` |
| Symbol | `XAUUSD` |
| Timeframe | `M5` |
| EA | `Account3BreakoutTier1CompatExecutor.mq5` |
| Run id | `A3_BREAKOUT_TIER1_COMPAT_V1_ARMED_20260617` |
| Magic | `933400` |
| Comment | `A3_BREAKOUT_TIER1_COMPAT` |
| Lot | `0.01` fixed |
| Broker action | `true` |
| Dry run | `false` |
| Session gate | Server hour `12-15` |
| XAU stop-distance floor | Enabled |
| Trend guard | Disabled, shadow logged |
| Breakeven / partial | Disabled |

## Required Runtime Evidence

| Gate | Required evidence |
| --- | --- |
| Compile proof | MetaEditor compile log with `0 errors / 0 warnings` |
| A3 profile backup | Backup path recorded before profile change |
| Zero duplicate attachment | No pre-existing chart with magic `933400` |
| Demo scope lock | Startup log shows account `1033669`, demo server marker, XAUUSD scope |
| Broker-action proof | Startup log shows `InpDryRunOnly=false`, `InpBrokerActionAllowed=true` |
| Isolation | Existing A3 plain `933200` and improved `933300` charts remain present and unchanged except terminal restart |

## Boundaries

- Demo only.
- No live trading.
- No real capital.
- No canonical Phase 2 status change.
- No committed armed preset.
- No change to existing A1/A2/A3 running lanes except briefly restarting the A3 terminal so the new chart can be loaded.
- Orders are allowed only when the new EA receives a valid XAUUSD M5 breakout-retest signal inside its configured session gate.
