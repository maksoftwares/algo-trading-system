# A3 Deployment Runbook

Status: T17_PREFLIGHT_REQUIRED_BEFORE_ARMING

## Order

1. Confirm T0 A1 mutex report is PASS.
2. Compile `Account3RoundRetestGuardedExecutor.mq5` and `Account3RoundRetestStructuredExecutor.mq5`.
3. Run the A3 source/preset tests.
4. Verify `A3_HYPOTHESIS_HASH_MANIFEST.json` exists and both hypotheses are locked before first trade.
5. Prepare `C:/MT5PortableRepairLane` and A3 position-path observer evidence.
6. Confirm WR50 and old P2WEAKNESS decommission report is PASS.
7. Attach both EAs with committed safe presets for at least one active dry-run session.
8. Verify zero orders, plausible EA-T1 impulse fields, plausible EA-T2 structural fields, and fresh startup/signal rows.
9. Owner signs the A3 packet.
10. Owner creates local-only execution presets; do not commit them.
11. Attach EA-T1 and EA-T2 to A3 login `1033669` only.

## Monday Attach Rule

The Monday attach is gated by the combined preflight. If any mandatory gate is FAIL or PENDING, keep both EAs in dry-run or do not attach them.

## Daily During Window

- Generate `A3_GUARD_ATTRIBUTION_DAILY_YYYY_MM_DD.md`.
- Keep A1/A3 treatment-control matching readable per magic.
- Keep EA-T1 and EA-T2 PnL/WR separate by magic.
- Do not change thresholds mid-window.
