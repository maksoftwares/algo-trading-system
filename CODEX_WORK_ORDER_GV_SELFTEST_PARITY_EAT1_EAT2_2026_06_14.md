# CODEX WORK ORDER — GV Mutex Namespace Self-Test Parity for EA-T1/EA-T2 (2026-06-14)

## Owner Authorization

Owner: Ali (mohdalikhans97.com@gmail.com). This work order authorizes a
**source code change** to EA-T1 and EA-T2, to be done while the market is
closed (Sunday), with detach-before-edit and reattach-after-verify so the
live A3 (`1033669`) session is never running a stale/uncompiled binary.

## Background / Why

`A3_ARM_AND_ATTACH_REPORT_2026_06_14.md` self-flagged a gap: A1's executor
(`Phase2ExperimentalDemoExecutor.mq5`) runs a GV-mutex namespace self-test in
`OnInit` (function `RunFamilyMutexNamespaceSelfTest`, lines ~985-1009) and
logs the result via `WriteStartupRow(gv_mutex_self_test_status)` before
`ATTACHED_DEMO_EXECUTOR_ENABLED` (lines ~1521-1531). EA-T1
(`Account3RoundRetestGuardedExecutor.mq5`) and EA-T2
(`Account3RoundRetestStructuredExecutor.mq5`) do not have this self-test or
startup row. The actual mutex-claim mechanism
(`GlobalVariableSetOnCondition(mutex_name, InpMagicNumber, 0)` at lines
875/966, namespaces `FAMMUX_RD_XAUUSD_*` / `FAMMUX_RDSTRUCT_XAUUSD_*`) is
present and correct — this work order only adds the missing self-test +
startup log row for parity and observability.

## Global boundaries (repeat in every report)

- A3 demo login `1033669` only. A1 (`1025742`) and A2 (`1033030`) must not be
  touched, edited, or have their terminals/processes restarted.
- Demo only, no live trading change, canonical Phase 2 status unchanged.
- Do NOT change G1-G6 guard logic, locked hypothesis parameters, magic
  numbers (933000 / 933100), magic bands, or
  `A3_HYPOTHESIS_HASH_MANIFEST.json`. EA-T3 band 933200-933299 stays
  reserved/unused.
- Do NOT change committed default values of `InpDryRunOnly` /
  `InpBrokerActionAllowed` (must remain `true` / `false` in repo source).
- The only source change permitted: add a GV-mutex namespace self-test
  function + one `OnInit` startup-row call, mirroring A1's pattern, scoped
  exactly as below.

## TA1 — Detach before editing

Both EA-T1 and EA-T2 are currently live-attached to A3
(`C:\MT5PortableRepairLane\terminal64.exe`, login `1033669`, armed presets,
`dry_run=false`/`broker_action_allowed=true`). Before any source edit:

1. Remove both EAs from their XAUUSD M5 charts in the A3 terminal (clean
   detach, not a crash).
2. Confirm via the terminal journal and `a3_rdguard_v1_startup.csv` /
   `a3_rdstruct_v1_startup.csv` that no orders were placed and no new signal
   rows were written during detach (market is closed; XAUUSD M5 ceiling
   should remain `2026-06-12 20:55:00`, same as
   `PHASE2_T12_BAR_SHADOW_REFRESH_REVERIFY2_2026_06_14.md`).
3. Record the detach timestamp (UTC and Dubai local).

## TA2 — Add the self-test function + OnInit wiring

For **EA-T1** (`Account3RoundRetestGuardedExecutor.mq5`, magic `933000`,
family namespace `FAMMUX_RD_XAUUSD_*`):

- Add a function equivalent to A1's `RunFamilyMutexNamespaceSelfTest`, but
  with a family-specific test-variable name so it cannot collide with A1's
  `FAMMUX_SELFTEST_<login>_<datetime>` or with EA-T2's self-test on the same
  account/login:
  - `test_name = "FAMMUX_SELFTEST_RD_" + IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)) + "_" + CompactDateTimeForGlobalVariable(TimeGMT())`
- Same create -> claim -> verify -> delete sequence as A1 (lines 988-1009),
  producing `gv_mutex_self_test_status` =
  `GV_MUTEX_NAMESPACE_SELF_TEST_PASS name=<test_name>` or
  `GV_MUTEX_NAMESPACE_SELF_TEST_FAIL name=<test_name> created=... claimed=... deleted=...`.
- In `OnInit`, call this self-test after the existing log-header setup and
  before the EA's normal `ATTACHED_A3_RDGUARD_V1` startup row. Write
  `WriteStartupRow(gv_mutex_self_test_status)`. On FAIL, write that row and
  `return INIT_FAILED` (same as A1) — do not proceed to attach.

For **EA-T2** (`Account3RoundRetestStructuredExecutor.mq5`, magic `933100`,
family namespace `FAMMUX_RDSTRUCT_XAUUSD_*`): same pattern, with
`test_name = "FAMMUX_SELFTEST_RDSTRUCT_" + IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)) + "_" + CompactDateTimeForGlobalVariable(TimeGMT())`.

Do not modify any other function, guard, or input default. Paste a unified
diff of both files in the report.

## TA3 — Compile and test

1. Recompile both EAs via MetaEditor; paste raw compile output (expect 0
   errors, 0 warnings, as in the prior attach report).
2. Run the existing A3 test suite (same tests referenced in prior T0/T12/A3
   reports) and paste raw `pytest` output — expect no new failures.

## TA4 — Reattach with the existing armed presets

1. Reattach both EAs to the same A3 XAUUSD M5 charts using the **same**
   local armed presets already on disk:
   - `C:\MT5PortableRepairLane\MQL5\Presets\Account3RoundRetestGuardedExecutor.armed_owner_20260614.set`
   - `C:\MT5PortableRepairLane\MQL5\Presets\Account3RoundRetestStructuredExecutor.armed_owner_20260614.set`
2. Confirm these presets are unchanged (`InpDryRunOnly=false`,
   `InpBrokerActionAllowed=true`, `InpAllowedAccountLoginsCsv=1033669`) —
   paste the file contents.
3. Confirm new startup rows show, in order: the self-test row
   (`GV_MUTEX_NAMESPACE_SELF_TEST_PASS name=FAMMUX_SELFTEST_RD_1033669_...` /
   `...RDSTRUCT_1033669_...`), then `ATTACHED_A3_RDGUARD_V1` /
   `ATTACHED_A3_RDSTRUCT_V1`, with `dry_run=false`,
   `broker_action_allowed=true`, `account_login=1033669`,
   `account_server=Capital.ComMena-Demo`.
4. Record the reattach timestamp (UTC and Dubai local) and confirm the gap
   between detach and reattach produced zero new M5 bars / zero orders
   (market still closed).

## TA5 — Confirm scope

- `git status` / `git diff --name-only` showing only the two `.mq5` files
  changed (plus this report and any updated status docs) — no changes under
  hypothesis docs, hash manifest, A1/A2 source, or EA-T3.
- Confirm A1 (`1025742`) and A2 (`1033030`) terminals/processes untouched.
- MT5 read-only query: login `1033669`, balance `4000.0` AED, 0 positions, 0
  orders for magics 933000/933100 (unchanged from yesterday).
- Update `A3_COMBINED_PREFLIGHT_REPORT.md` evidence block with the new
  startup rows (status stays `ATTACHED`); note in
  `A3_ARM_AND_ATTACH_REPORT_2026_06_14.md` (or an addendum) that the
  GV-selftest limitation is now closed, with a pointer to this report.

## Reporting

Write `GV_SELFTEST_PARITY_REPORT_2026_06_14.md` with raw command output for
every step above (diffs, compile logs, pytest output, startup CSV rows,
timestamps, git status) — same standard as prior reverify reports. Include a
"How to pause" section unchanged from the arm/attach report (A3_KILL.txt;
flipping `InpBrokerActionAllowed=false` and reattaching stops new orders).
