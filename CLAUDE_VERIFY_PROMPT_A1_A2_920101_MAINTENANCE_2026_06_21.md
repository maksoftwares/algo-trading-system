# Claude Verification Prompt - A1/A2 920101 Maintenance - 2026-06-21

Claude, please independently verify the runtime correction that Codex applied after the forensic finding that A1's profitable XAU 920101 lane had gone missing.

Boundary: verification only. Do not touch MT5 runtime, charts, profiles, presets, orders, or positions. A3 must remain paused.

## Main Report To Review

`xau-usd/xauusd-phase1/outputs/reports/A1_A2_920101_MAINTENANCE_APPLIED_2026_06_21.md`

JSON companion:

`xau-usd/xauusd-phase1/outputs/reports/A1_A2_920101_MAINTENANCE_APPLIED_2026_06_21.json`

Script used:

`xau-usd/xauusd-phase1/scripts/apply_a1_a2_920101_maintenance.py`

## Supplemental Runtime Verification

Please also review this newer supplemental report, generated after your warning that the first runtime inventory CSV was stale:

`xau-usd/xauusd-phase1/outputs/reports/A1_A2_920101_MAINTENANCE_SUPPLEMENTAL_VERIFICATION_2026_06_21.md`

JSON companion:

`xau-usd/xauusd-phase1/outputs/reports/A1_A2_920101_MAINTENANCE_SUPPLEMENTAL_VERIFICATION_2026_06_21.json`

Fresh chart inventory CSV:

`xau-usd/xauusd-phase1/outputs/reports/RUNTIME_CHART_INVENTORY_FORENSIC_2026_06_21.csv`

Read-only generator:

`xau-usd/xauusd-phase1/scripts/generate_a1_a2_920101_supplemental_verification.py`

Supplemental status is `PASS_WITH_ORDER_LOG_PENDING`. The pending order-log item is expected because no post-maintenance A1/A2 920101 order has fired yet; startup logs and source-derived magic proof are present now, and the first Monday order should provide the order-log proof.

Forensic context:

- `FORENSIC_RUNTIME_DRIFT_AND_TRADE_DROP_2026_06_21.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_A2_920101_RULE_IDENTITY_RECONCILIATION_2026_06_20.md`
- `xau-usd/xauusd-phase1/docs/A1_XAU_920101_EVENING_CORE_FORWARD_V0_SPEC_2026_06_20.md`

## What Codex Claims Was Fixed

1. A1 standard account `1025742` now has exactly one active broker-action XAU `Phase2ExperimentalDemoExecutor` chart:
   - chart: `chart03.chr`
   - symbol: `XAUUSD`
   - candidate: `breakout_retest`
   - account allowlist: `1025742`
   - dry-run: `false`
   - broker action: `true`
   - session: server hours `12 -> 15`
   - lot: `0.01`
   - max open positions per instance: `1`
   - max estimated cost R: `0.30`
   - max measured spread: `75.0`
   - kill switch: `experimental_demo_kill_switch.txt`

2. A1 losing/non-spec broker-action lanes are disabled:
   - EURUSD `breakout_retest` standard executor: dry-run `true`, broker action `false`
   - GBPUSD `breakout_retest` standard executor: dry-run `true`, broker action `false`
   - XAU repair `symbol_normalized_round_retest_v0_repair_v1`: dry-run `true`, broker action `false`
   - XAU repair `session_extreme_retest_v0_repair_v1`: dry-run `true`, broker action `false`
   - EUR repair `session_extreme_retest_v0_repair_v1`: dry-run `true`, broker action `false`
   - WR50 XAU: `InpAllowDemoTrading=false`

3. A2 clean account `1033030` remains aligned on XAU `920101`:
   - chart: `chart02.chr`
   - symbol: `XAUUSD`
   - candidate: `breakout_retest`
   - account allowlist: `1033030`
   - dry-run: `false`
   - broker action: `true`
   - session: server hours `12 -> 15`
   - lot: `0.01`
   - max open positions per instance: `1`
   - max estimated cost R: `0.30`
   - max measured spread: `75.0`
   - kill switch: `tier1_bestea_kill_switch.txt`

4. A1 and A2 now both have active daily profit/loss guardians:
   - A1 guardian halt file: `experimental_demo_kill_switch.txt`
   - A2 guardian halt file: `tier1_bestea_kill_switch.txt`
   - daily floor: `+100 AED`
   - daily loss stop: `-100 AED`
   - dry-run: `false`
   - close action allowed: `true`

5. A3 was not touched:
   - report check says A3 profile hashes unchanged
   - A3 remains paused/dry-run/broker-action false

6. Compile and startup proof:
   - `Phase2ExperimentalDemoExecutor` compiled 0 errors / 0 warnings for A1 and A2
   - `Account1DailyProfitFloorGuardian` compiled 0 errors / 0 warnings for A1 and A2
   - A1 and A2 executor startup logs show `ATTACHED_DEMO_EXECUTOR_ENABLED`
   - A1 and A2 guardian startup logs show initialized active guardians
   - A1 and A2 startup logs show mutex self-test names containing derived magic `920101`
   - `920101` is runtime-derived by `Phase2ExperimentalDemoExecutor.mq5`: `920000 + CandidateMagicOffset(breakout_retest=10) * 10 + SymbolMagicOffset(XAUUSD=1)`

## Verification Requests

Please verify independently from the report and current profile/log files:

1. Is the A1 XAU `920101` lane actually restored and enabled?
2. Are A1 EURUSD/GBPUSD and repair/WR50 losing lanes actually disarmed from broker action?
3. Are A1 and A2 now identical enough for the locked forward test, or is there any remaining rule mismatch?
4. Are the A1/A2 guardians correctly configured, especially the `-100 AED` daily loss stop and the correct account-specific halt file?
5. Did Codex touch A3 or leave it paused?
6. Are the compile logs and startup logs sufficient proof that the corrected state loaded?
7. Any hidden risk from disabling old lanes while positions might still exist?
8. What should we monitor on Monday's first trading session to confirm the fix held?
9. Does the refreshed `RUNTIME_CHART_INVENTORY_FORENSIC_2026_06_21.csv` now supersede the stale pre-fix inventory you warned about?
10. Is `PASS_WITH_ORDER_LOG_PENDING` the right state until the first post-maintenance order creates order-log proof?

Return a verdict:

- `APPROVE_RUNTIME_FIX`
- `APPROVE_WITH_WARNINGS`
- `REJECT_FIX`

Please include exact file/chart evidence and any required follow-up.
