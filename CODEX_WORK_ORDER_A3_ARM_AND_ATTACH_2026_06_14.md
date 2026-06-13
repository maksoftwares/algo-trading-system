# CODEX WORK ORDER — A3 Arm and Attach (EA-T1 + EA-T2) (2026-06-14)

## Owner Authorization (this section is the signed packet)

Owner: Ali (mohdalikhans97.com@gmail.com). Account: A3 demo, login `1033669`,
Capital.ComMena-Demo, AED currency. Demo capital only.

Decision: the owner explicitly **waives** the
`dry_run_session_both_eas_pass` gate in
`A3_COMBINED_PREFLIGHT_REPORT.md`. Rationale: this is a demo account; the
owner wants to observe live trade data from EA-T1/EA-T2 directly rather than
spend a session on dry-run-only logging. This document, dated 2026-06-14, is
the recorded owner signature/authorization for arming and attaching both EAs
to A3 (`1033669`).

This authorization covers ONLY:
- Flipping `InpDryRunOnly`/`InpBrokerActionAllowed` to armed in a **local-only
  preset** (not committed source defaults) for
  `Account3RoundRetestGuardedExecutor.mq5` (EA-T1, magic 933000) and
  `Account3RoundRetestStructuredExecutor.mq5` (EA-T2, magic 933100).
- Attaching those two EAs to the A3 terminal (`1033669`) on XAUUSD M5.

It does NOT authorize: any change to A1 (`1025742`) or A2 (`1033030`), any
change to G1-G6 guard logic, locked parameters, magic numbers, or the
hypothesis files/hash manifest, or any EA-T3 code.

## Global boundaries (repeat in every report)

- A3 demo login `1033669` only. A2 (`1033030`) untouched. A1 (`1025742`)
  untouched in this work order.
- Demo only, no live trading, canonical Phase 2 status unchanged.
- Committed source defaults (`InpDryRunOnly=true`,
  `InpBrokerActionAllowed=false`) stay as-is in the repo — arming happens only
  via a local, uncommitted `.set` preset applied in the A3 terminal.
- G1-G6 guard logic, locked parameters, magic bands (933000-933099 /
  933100-933199), and `A3_HYPOTHESIS_HASH_MANIFEST.json` must not be edited.
  EA-T3 band 933200-933299 stays reserved/unused.
- The shared kill-switch file (`A3_KILL.txt` mechanism per G6) must remain
  functional after attach — confirm it still halts both EAs if present.

## TA1 — Record the waiver in the report trail

Update, with raw before/after diffs in the final report:

- `A3_DRY_RUN_SESSION_REPORT.md`: change `dry_run_session_both_eas_pass`
  (and the underlying `ea_t1_dry_run_logs_present` /
  `ea_t2_dry_run_logs_present` / `active_session_verified` rows) from
  `PENDING` to `WAIVED_BY_OWNER`, citing this work order file and date.
  `zero_a3_orders_observed` row can be removed or left as historical context
  for the pre-attach period.
- `A3_OWNER_AUTHORIZATION_STATUS.md`: change `owner_signature_recorded` from
  `PENDING` to `RECORDED`, evidence = path to this work order file.
  `owner_execution_preset_local_only` stays `PENDING` until TA2 produces it,
  then becomes `RECORDED` with the local preset file path (local-only,
  outside canonical committed paths if your tooling distinguishes that).
- `A3_COMBINED_PREFLIGHT_REPORT.md`: update the two PENDING rows to reflect
  TA1/TA2/TA3 results. Attach Decision changes from `DO_NOT_ATTACH` to
  `ATTACHED` only after TA3 confirms both EAs are live on the A3 terminal.

## TA2 — Build local arming presets

For each EA, create a local `.set` preset (not committed as a new canonical
default) that is identical to the locked hypothesis parameters EXCEPT:

- `InpDryRunOnly = false`
- `InpBrokerActionAllowed = true`

Confirm `InpAllowedAccountLoginsCsv` (or equivalent G6 login allowlist) is
exactly `1033669` for both — do not widen it. Confirm
`InpExpectedServerMarker` still requires the demo marker and that the
live/real-account refusal logic in `OnInit` is untouched. Record the preset
file paths and a diff against the locked parameter values from
`A3_ROUND_RETEST_GUARDED_HYPOTHESIS_2026_06_13.md` /
`A3_ROUND_RETEST_STRUCTURED_HYPOTHESIS_2026_06_13.md` showing only the two
flags above changed.

## TA3 — Attach to A3 terminal

1. Attach `Account3RoundRetestGuardedExecutor.mq5` (magic 933000) and
   `Account3RoundRetestStructuredExecutor.mq5` (magic 933100) to XAUUSD M5
   charts on the A3 terminal (login `1033669`), using the TA2 armed presets.
2. Confirm via startup log rows that:
   - Account login is `1033669` (G6 check passed).
   - Server marker check passed (demo).
   - GV-mutex namespace self-test passed for both
     `FAMMUX_RD_XAUUSD_*` (EA-T1) and `FAMMUX_RDSTRUCT_XAUUSD_*` (EA-T2)
     namespaces, with no collision against A1/A2's `FAMMUX_*` keys on the
     same broker/terminal session.
   - Startup row shows `ATTACHED_A3_RDGUARD_V1` (or EA-T2 equivalent), not
     `INIT_FAILED`.
3. Confirm `InpBrokerActionAllowed=true` / `InpDryRunOnly=false` are in effect
   for both (from the startup log's boolean fields), so signals that pass
   G1-G6 will actually call `OrderSend`.
4. Do not place any manual test orders. Let the EAs run on their own M5 timer
   cadence.

## TA4 — Confirm scope after attach

- Confirm A1 (`1025742`) and A2 (`1033030`) terminals/EAs are unchanged —
  paste `git status`/process checks showing no modification.
- Confirm no orders/positions with magics 933000/933100 existed before this
  attach (carry forward `zero_a3_orders_observed=PASS` as the pre-attach
  baseline for comparison).
- Update `A3_DEPLOYMENT_ORDER_STATUS_2026_06_13.md` (or a new
  `..._2026_06_14.md`) to `ATTACHED`, with attach timestamp (UTC and Dubai
  local).

## Reporting

Write `A3_ARM_AND_ATTACH_REPORT_2026_06_14.md` with raw command output for
every check above (same standard as the T0/T12 reverify2 reports — actual
terminal output, file paths, timestamps, not summaries). Include a short
"How to pause" section restating the kill-switch mechanism and that flipping
the local preset's `InpBrokerActionAllowed` back to `false` and re-attaching
stops new orders immediately (existing open positions are unaffected by that
flag and must be managed manually if needed).
