# A3 Preflight Report

Status: **PENDING**

## Boundary

- A3 login: `1033669`.
- Demo only; canonical Phase 2 unchanged.
- A2 remains untouched.
- Committed defaults remain non-executing.

## Checks

| Check | Status | Evidence |
|---|---|---|
| a3_login_documented | PASS | 1033669 |
| server_marker_demo_practice_required | PASS | EA source refuses live/real and expects Demo marker. |
| login_allowlist_exact | PASS | 1033669 |
| safe_presets_committed_non_executing | PASS | T1/T2 safe presets |
| owner_preset_local_only | PENDING | See A3_OWNER_AUTHORIZATION_STATUS. |
| magic_no_collision | PASS | 933000 and 933100 |
| hypothesis_hash_locked | PASS | LOCKED_BEFORE_FIRST_TRADE |
| source_tests_pass | PASS | ============================= 22 passed in 0.12s ============================== |
| kill_switch_drill_pass | PENDING | See A3_KILL_SWITCH_DRILL_REPORT. |
| dry_run_session_pass | PENDING | See A3_DRY_RUN_SESSION_REPORT. |
| guardian_stage_a_startup_pass | PENDING | No A3 startup log yet. |
| decommission_report_pass | PASS | See A3_DECOMMISSION_REPORT. |
| a1_a2_state_snapshot_documented | PASS | A1=1025742; A2=1033030; A2 untouched. |
| owner_signed_demo_packet | PENDING | See A3_OWNER_AUTHORIZATION_STATUS. |
