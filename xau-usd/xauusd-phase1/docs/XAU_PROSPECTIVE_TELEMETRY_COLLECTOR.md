# XAU Prospective Telemetry Collector

`XauProspectiveTelemetryCollector` is a passive MT5 Expert Advisor for collecting
new, causally timestamped XAUUSD evidence. It cannot place, modify, or close an
order. It is not a trading or prediction authorization.

The collector writes separate daily CSV ledgers for:

- every XAUUSD tick, including bid, ask, spread, tick flags, and millisecond time;
- every available market-depth snapshot and an explicit empty snapshot when the
  broker subscribes successfully but reports no levels;
- every account trade transaction observed after startup, including request and
  result fields needed to measure fill slippage and rejection behavior; and
- five-second health snapshots with connection, account, quote, depth, and row
  counters.

A startup ledger records symbol-contract properties, swap settings, account mode,
and whether market-depth subscription succeeded. Depth is broker-dependent. A
successful terminal connection does not imply that the broker exposes useful
XAUUSD depth.

## Safety contract

- `InpDryRunOnly` must remain `true`.
- The attached chart must be exactly `XAUUSD`.
- The server name must contain `Demo` by default.
- The login must be in the explicit demo allowlist.
- The terminal startup configuration has `AllowLiveTrading=0` and
  `AllowDllImport=0`.
- The attached chart has EA-level trading permission disabled, and the EA refuses
  startup if MT5 nevertheless reports `MQL_TRADE_ALLOWED=true`.
- The collector source contains no order-send, position-modification, or
  position-close call.

## Deployment

The deployment script creates a separate portable terminal. It refuses to alter
the existing A1, A2, A3, Gold Mission, or standard MT5 roots.

```powershell
python scripts/deploy_xau_prospective_telemetry_collector.py `
  --allow-prepare --allow-deploy --allow-launch `
  --source-terminal-root C:\MT5PortableRepairLane `
  --startup-login 1033669 `
  --startup-server Capital.ComMena-Demo
```

Runtime evidence stays under the dedicated terminal's `MQL5/Files` directory and
is not committed to Git. No data-provider account creation, billing, or paid API
call is part of this collector.
