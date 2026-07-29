# V60 Absolute-USD Demo Risk Deployment

Decision: **PASS - ACTIVE ON DEMO ACCOUNT 1033030**

Deployed at `2026-07-29T10:27:12Z`.

## What changed

The canonical demo executor no longer scales entry-risk or drawdown limits from
the account's activation equity. The runtime now enforces
`ABSOLUTE_USD_ONLY`.

There is no minimum-balance eligibility gate. Broker margin requirements still
apply because they are imposed by MT5 and the broker.

## Effective limits

| Control | Before | After |
|---|---:|---:|
| Account concurrent initial risk | $59.2597 | $60.00 |
| Directional concurrent initial risk | $59.2597 | $60.00 |
| Closed-drawdown suspension | $74.0747 | $225.00 |
| Closed-drawdown resume | $59.2597 | $180.00 |
| Combined closed-drawdown hard stop | $98.7662 | $300.00 |
| Floating-drawdown hard stop | $148.1494 | $449.7675 |

The fixed safety limits remain active. This deployment removes equity scaling,
not risk management.

## Verification

- Canonical executor tests: **34 passed**.
- Tick replay tests: **9 passed**.
- Full 2021-2026 tick replay: **PASS at current deployed capital**.
- Position-origin full-runtime replay: 1,431 accepted trades, `$1,304.56` net,
  PF `1.3090`, `$189.52` maximum lifetime equity drawdown, and no deadlock.
- Live status: `ACTIVE_DEMO_BROKER_ACTION`.
- Chart, feed, and broker-geometry preflights: **ready**.
- Entry halt files: none.
- Open XAU positions during restart: zero.

## State continuity

No state reset was performed. Activation time, activation-equity telemetry,
closed P/L, 13 seen candidates, five position records, and four daily-entry
records were preserved. The only position-record updates after restart were
fresh observation timestamps for already closed positions.

The predeployment state and status are backed up under:

`C:/MT5PortableTier1BestEA/MQL5/Files/v60_canonical_demo_v2/deployment_backups/absolute_usd_only_20260729T102654Z`
