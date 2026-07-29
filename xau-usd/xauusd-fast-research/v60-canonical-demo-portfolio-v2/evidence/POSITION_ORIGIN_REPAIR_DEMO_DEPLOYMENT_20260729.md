# V60 Position-Origin Repair Demo Deployment

Status: **ACTIVE_DEMO_PROSPECTIVE_VALIDATION_ONLY**

The canonical V60 demo executor on account `1033030` now reconstructs closed
P/L from complete MT5 position-ID lifecycles. Guardian and manual exits are
counted when the opening deal belongs to a canonical V60 source magic.

## Deployment checks

- State reset: no.
- Funding change: no.
- Risk-limit change: no.
- Open XAUUSD positions during restart: zero.
- Pre/post closed P/L: `$11.803948264125257`.
- Pre/post closed drawdown: `$0.00`.
- Attribution after restart: `POSITION_ORIGIN`.
- Attributed history: 5 positions and 10 deals.
- Runtime: `ACTIVE_DEMO_BROKER_ACTION`.
- Feeds ready: yes.
- Active maintenance halts: zero.
- Executor stderr: zero bytes.

The prior runtime state and status were backed up under
`C:/MT5PortableTier1BestEA/MQL5/Files/v60_canonical_demo_v2/position_origin_repair_backup_20260729_121219`.

## Evidence boundary

All 32 canonical package tests and all 8 tick-replay tests passed. The repaired
`$3,000` funded/reinitialized replay passed its operability and risk gates. The
actual roughly `$988` activation-capital replay still ended in permanent
suspension after 118 trades, despite remaining within its effective risk caps.

The accounting defect is repaired on demo, but the current-capital system is
not approved as economically demo-ready from the historical replay. Funding
and activation-state reinitialization remain separate owner decisions. Live
trading remains unauthorized.
