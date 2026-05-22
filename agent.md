# Agent Handoff

Last updated: 2026-05-22

## Workspace

- Root: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system`
- Canonical source: `https://github.com/maksoftwares/algo-trading-system`
- Note: Windows workspace and MT5 paths are machine-local evidence paths, not reviewer requirements. See `xau-usd\xauusd-phase1\docs\WORKSPACE_OWNERSHIP.md`.
- Active package: `xau-usd\xauusd-phase1`
- Active phase label: Phase 1 - Master EA dry-run shell.
- Current branch: `main`
- Remote: `https://github.com/maksoftwares/algo-trading-system.git`

## Standing Rules

- Do not add live EA trade execution until Phase 0 real-data gates approve an expert.
- No `OrderSend`, `OrderSendAsync`, `CTrade`, `trade.Buy`, `trade.Sell`, or position-opening logic in Phase 0.
- Keep all MT5 tools passive: file export, logging, or diagnostics only.
- Phase 1 currently means dry-run shell only: telemetry, lifecycle, risk, router contracts, dashboard/logging work, and blocked reasons.
- Prefer generated manifests, snapshots, and hashable artifacts over informal notes.
- Do not push unless explicitly asked.

## Current State

- Latest committed acquisition helper: `generate-mt5-bar-presets`.
- Passive MT5 tools exist for spread logging and historical bar export.
- Passive spread logger is deployed and compiled under `C:\MT5PortableGoldMission\MQL5\Experts\Phase0\PassiveSpreadLogger_XAUUSD.ex5`; compile log `C:\MT5PortableGoldMission\compile_PassiveSpreadLogger_XAUUSD.log` shows 0 errors / 0 warnings.
- Passive spread logger is running in an isolated portable clone at `C:\MT5PortableSpreadLogger\terminal64.exe` so the active Phase 1 dry-run chart in `C:\MT5PortableGoldMission` is not restarted or replaced.
- Passive spread logger output path: `C:\MT5PortableSpreadLogger\MQL5\Files\spread_log_121409_Capital.ComMena-Live_XAUUSD_20260522.csv`.
- Passive spread logger deployment report: `xau-usd\xauusd-phase0\outputs\reports\PASSIVE_SPREAD_LOGGER_DEPLOYMENT.md`, status PASS for the logger clone.
- MT5 passive exports and public Dukascopy acquisition are complete for the Phase 0 required bar set.
- Latest bar import status: `25 imported, 0 missing, 0 failed`.
- Latest data readiness status: `PASS`, `25/25` required timeframe sets ready.
- Fresh post-review real-data `run-all` completed successfully on 2026-05-21 after hypothesis completion and re-registration:
  - Matrix output sets: 27.
  - Decile files: 3.
  - Multisymbol summaries: 3.
  - Adversarial packets: 3.
  - Aggregation files: 3.
- Latest verdict: `breakout_retest` has a full final PASS and is the only approved future expert.
  - `breakout_retest` passed automated 9-cell, decile, multisymbol, hash, and Gate 9 manual adversarial gates.
  - `trend_pullback` and `range_mr` are rejected by the current Phase 0 verdict.
- Audit correction: the previous real-data run is exploratory evidence only because the registered hypothesis files still contained placeholder text when the run was produced.
- Do not treat automated PASS as final PASS until hypothesis completeness, fresh hash registration, rerun evidence, manual adversarial review, and review bundle are complete.
- Reviewer-prompt cleanup now includes reference validation, true-holdout run context manifests, intrabar ambiguity reporting, review-bundle generation, and real-artifact verification.
- Latest snapshot: `xau-usd\xauusd-phase0\outputs\snapshots\phase0_snapshot_20260521_111442.zip`.
- Latest result manifest: `xau-usd\xauusd-phase0\outputs\manifests\PHASE0_RESULT_MANIFEST.csv`.
- Latest review bundle: `xau-usd\xauusd-phase0\outputs\review_bundles\PHASE0_REVIEW_BUNDLE_20260522_064147.zip`.
- Verification after code changes: Phase 0 `148 passed`, Phase 1 `49 passed`; both safety audits OK.
- `verify-real-artifacts` returns PASS after Gate 9 closure.
- Phase 1 dry-run shell is started under `xau-usd\xauusd-phase1`; it now observes `breakout_retest` plus same-family `swing_breakout_retest_v0` telemetry while keeping all execution blocked.
- Phase 0.9 closure plan: `xau-usd\xauusd-phase0\docs\PHASE0_9_CLOSURE_PLAN.md`.
- Phase 1 dry-run spec: `xau-usd\xauusd-phase1\docs\PHASE1_MASTER_EA_DRY_RUN_SPEC.md`.
- Latest Phase 0 review bundle: `xau-usd\xauusd-phase0\outputs\review_bundles\PHASE0_REVIEW_BUNDLE_20260522_064147.zip`.
- Latest Phase 0 snapshot: `xau-usd\xauusd-phase0\outputs\snapshots\phase0_snapshot_20260521_121022.zip`.
- Latest Phase 1 shell version: `phase1-dry-run-v0.6`.
- Phase 1 module slices implemented:
  - v0.2: market snapshot, session detection, execution guard, news guard, router regime classification, decision logger, and dashboard.
  - v0.3: feature telemetry, server-time validation, magic-number allocator, and expert lifecycle manager.
  - v0.4: simulated daily/weekly/monthly/manual risk locks plus startup and shutdown CSV logs.
  - v0.5: breakout-retest dry-run observer that reports level/break/retest/confirmation state, would-signal status, and synthetic entry/stop/target telemetry while keeping execution blocked.
  - v0.6: swing_breakout_retest_v0 dry-run observer added as a second same-family observation lane with `sbr_*` decision-log telemetry; execution remains blocked.
- MT5 Portable compile result for `Phase1DryRunShell.mq5`: 0 errors, 0 warnings.
- Latest MT5 Portable decision log: `C:\MT5PortableGoldMission\MQL5\Files\decision_log.csv`.
- Previous v0.2/v0.3 mixed-schema log was archived as `C:\MT5PortableGoldMission\MQL5\Files\decision_log_pre_v0_3_20260521_162557.csv`.
- Previous v0.3 decision log was archived as `C:\MT5PortableGoldMission\MQL5\Files\decision_log_pre_v0_4_20260521_163517.csv`.
- Previous v0.4 decision log was archived as `C:\MT5PortableGoldMission\MQL5\Files\decision_log_pre_v0_5_20260521_174742.csv`.
- Latest decision row confirms `phase1-dry-run-v0.6`, `DRY_RUN`, `DRY_RUN_ONLY`, `magic_namespace_ok=true`, `server_time_status=CLOCK_OK`, `risk_state=NORMAL`, `risk_ok=true`, `would_have_allowed_experts=breakout_retest;swing_breakout_retest_v0`, `trade_permission=false`, and `block_reason=phase1_dry_run_only`.
- Latest v0.6 row includes `sbr_stage`, `sbr_direction`, `sbr_would_signal`, `sbr_reason_code`, `sbr_level_kind`, `sbr_entry_price`, `sbr_stop_loss`, and `sbr_take_profit`.
- Phase 1 v0.5 logs were archived before the v0.6 schema change:
  - `C:\MT5PortableGoldMission\MQL5\Files\decision_log_pre_v0_6_20260522_150335.csv`
  - `C:\MT5PortableGoldMission\MQL5\Files\startup_log_pre_v0_6_20260522_150335.csv`
- Current v0.6 would-signal report has 4 post-reset dry-run would-signal rows across 4 setup clusters; all stayed dry-run and permission-locked.
- Runtime risk simulations verified `LOCKED_DAILY_LOSS`, `LOCKED_WEEKLY_LOSS`, `LOCKED_MONTHLY_LOSS`, and `MANUAL_LOCK` under the v0.6 `sbr_*` schema; the normal safe preset was restored afterward.
- Latest MT5 lifecycle logs:
  - `C:\MT5PortableGoldMission\MQL5\Files\startup_log.csv`
  - `C:\MT5PortableGoldMission\MQL5\Files\shutdown_log.csv`
- Restart resilience verifier: `xau-usd\xauusd-phase1\scripts\verify_phase1_logs.py`.
- Latest Phase 1 log report: `xau-usd\xauusd-phase1\outputs\reports\PHASE1_DRY_RUN_LOG_REPORT.md`.
- Latest log verification status: PASS. Duplicate headers, schemas, dry-run lock, permission lock, breakout-retest observer, startup append, shutdown rows, M5 cadence, and risk-state coverage all passed.
- Soak/drift analyzer: `xau-usd\xauusd-phase1\scripts\analyze_phase1_soak.py`.
- Latest Phase 1 soak/drift report: `xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_DRIFT_REPORT.md`.
- Latest soak/drift status: PASS. Dry-run state, permission state, lifecycle rows, per-run cadence, latest-row freshness, server-time status, and breakout-retest observer activity passed.
- Would-signal report generator: `xau-usd\xauusd-phase1\scripts\generate_phase1_would_signal_report.py`.
- Latest Phase 1 would-signal report: `xau-usd\xauusd-phase1\outputs\reports\PHASE1_WOULD_SIGNAL_REPORT.md`.
- Latest Phase 1 would-signal review CSV: `xau-usd\xauusd-phase1\outputs\reports\PHASE1_WOULD_SIGNAL_REVIEW.csv`.
- Latest would-signal status: PASS with 5 rows and 5 setup clusters; both long and short observations have appeared in dry-run telemetry.
- Runtime health report generator: `xau-usd\xauusd-phase1\scripts\generate_phase1_runtime_health_report.py`.
- Latest Phase 1 runtime health report: `xau-usd\xauusd-phase1\outputs\reports\PHASE1_RUNTIME_HEALTH_REPORT.md`.
- Latest runtime health status: PASS. Runtime files exist, latest row is fresh, dry-run and permission locks hold, server-time status is clean, no exact duplicate rows were found, and no larger-than-M5 gaps were found.
- Status summary generator: `xau-usd\xauusd-phase1\scripts\generate_phase1_status_summary.py`.
- Latest Phase 1 status summary JSON: `xau-usd\xauusd-phase1\outputs\reports\PHASE1_STATUS_SUMMARY.json`.
- Latest status summary shows 213 decision rows, 15.21% of the five-day soak target, `log_verification=PASS`, `soak_analysis=PASS`, `runtime_health=PASS`, `would_signal=PASS`, and `acceptance=PENDING`.
- Review #2 reflection and action plan is tracked in `docs\REVIEW_02_REFLECTION_AND_ACTION_PLAN.md`.
- Review #2 reframes `breakout_retest` as high-frequency and cost-sensitive; Phase 2 is now treated as a real-cost measurement phase, not a profit-confirmation phase.
- External review follow-up on 2026-05-21 is tracked in `xau-usd\xauusd-phase0\docs\REVIEW_RESPONSE_2026_05_21.md`.
- D1-D4 status is tracked in `xau-usd\xauusd-phase0\docs\PHASE0_INDEPENDENT_VALIDATION.md`; CPCV, Reality Check/SPA, true-holdout audit, and independent reproduction are closed for the current evidence package.
- D1 CPCV command: `phase0 run-cpcv-validation --expert breakout_retest`.
- Latest D1 result: PASS. 135 CPCV paths across 9 matrix cells, 100% pass rate, median OOS PF 1.379, minimum OOS PF 1.135.
- D2 Reality Check command: `phase0 run-reality-check --approved-expert breakout_retest --iterations 5000 --block-months 3 --max-pvalue 0.10`.
- Latest D2 result: PASS. `breakout_retest` remained the family winner, White Reality Check p-value 0.0200, max pairwise SPA p-value 0.0234.
- D3 true-holdout audit command: `phase0 audit-true-holdout`.
- Latest D3 result: PASS. 96 result CSV files scanned, no holdout-window timestamps found, latest audited result timestamp `2025-06-30T23:55:00+00:00`, unlock file absent.
- D4 independent reproduction command: `phase0 generate-independent-reproduction --expert breakout_retest --cell-id 2 --tolerance-pct 5`.
- Latest D4 result: PASS. `breakout_retest` cell 2 matched 7287 trades, PF 1.4119615864693404, win rate 0.4844243172773432, total PnL 18642279.988449715, and max drawdown within tolerance.
- Candidate research backlog targets 10 mechanical hypotheses; see `xau-usd\xauusd-phase0\docs\CANDIDATE_RESEARCH_BACKLOG.md`.
- Second-candidate concentration-risk mitigation is tracked in `xau-usd\xauusd-phase0\docs\SECOND_CANDIDATE_RESEARCH_PLAN.md`; `squeeze_breakout_long_v0` is now REJECTED_FIRST_PASS.
- Second-candidate hypothesis file: `xau-usd\xauusd-phase0\docs\hypothesis_squeeze_breakout_long_v0.md`.
- Second-candidate research hash manifest: `xau-usd\xauusd-phase0\outputs\hashes\research_hypothesis_hash_manifest.csv`.
- Latest second-candidate matrix summary: `xau-usd\xauusd-phase0\docs\SQUEEZE_BREAKOUT_LONG_V0_FIRST_PASS.md`.
- Latest second-candidate result-producing run status: rejected. Real 9-cell matrix produced 194-211 trades per cell, but only 0/9 cells reached PF >= 1.30, so do not proceed to deciles or tune v0.
- Second-candidate smoke command: `phase0 run-research-candidate-smoke --expert squeeze_breakout_long_v0 --hypothesis-file docs/hypothesis_squeeze_breakout_long_v0.md`.
- Latest second-candidate smoke result: PASS. It generated 1 synthetic signal, produced a valid synthetic plan, and confirmed the hypothesis hash lock. The follow-up real matrix failed the first hard gate.
- Third candidate `post_spike_short_v0` is also REJECTED_FIRST_PASS.
- Post-spike hypothesis file: `xau-usd\xauusd-phase0\docs\hypothesis_post_spike_short_v0.md`.
- Post-spike matrix summary: `xau-usd\xauusd-phase0\docs\POST_SPIKE_SHORT_V0_FIRST_PASS.md`.
- Latest post-spike result-producing run status: rejected. Real 9-cell matrix produced 192-234 trades per cell, but only 0/9 cells reached PF >= 1.30, so do not proceed to deciles or tune v0.
- Fourth candidate `emr_inactivity_long_v0` is also REJECTED_FIRST_PASS.
- EMR inactivity hypothesis file: `xau-usd\xauusd-phase0\docs\hypothesis_emr_inactivity_long_v0.md`.
- EMR inactivity matrix summary: `xau-usd\xauusd-phase0\docs\EMR_INACTIVITY_LONG_V0_FIRST_PASS.md`.
- Latest EMR inactivity result-producing run status: rejected. Real 9-cell matrix produced only 9-10 trades per cell and 0/9 cells reached PF >= 1.30, so do not proceed to deciles or tune v0.
- Fifth candidate `ny_failed_london_reversal_v0` is also REJECTED_FIRST_PASS.
- NY failed-London hypothesis file: `xau-usd\xauusd-phase0\docs\hypothesis_ny_failed_london_reversal_v0.md`.
- NY failed-London matrix summary: `xau-usd\xauusd-phase0\docs\NY_FAILED_LONDON_REVERSAL_V0_FIRST_PASS.md`.
- Latest NY failed-London result-producing run status: rejected. Real 9-cell matrix produced 322-415 trades per cell, but only 0/9 cells reached PF >= 1.30, so do not proceed to deciles or tune v0.
- Sixth candidate `london_fix_continuation_v0` is also REJECTED_FIRST_PASS.
- London fix continuation hypothesis file: `xau-usd\xauusd-phase0\docs\hypothesis_london_fix_continuation_v0.md`.
- London fix continuation matrix summary: `xau-usd\xauusd-phase0\docs\LONDON_FIX_CONTINUATION_V0_FIRST_PASS.md`.
- Latest London fix continuation result-producing run status: rejected. Real 9-cell matrix produced 463-658 trades per cell, but only 0/9 cells reached PF >= 1.30, so do not proceed to deciles or tune v0.
- Seventh candidate `extreme_activity_mean_reversion_v0` is also REJECTED_FIRST_PASS.
- Extreme activity mean-reversion hypothesis file: `xau-usd\xauusd-phase0\docs\hypothesis_extreme_activity_mean_reversion_v0.md`.
- Extreme activity mean-reversion matrix summary: `xau-usd\xauusd-phase0\docs\EXTREME_ACTIVITY_MEAN_REVERSION_V0_FIRST_PASS.md`.
- Latest extreme activity mean-reversion result-producing run status: rejected. Real 9-cell matrix produced 74-176 trades per cell, but only 0/9 cells reached PF >= 1.30, so do not proceed to deciles or tune v0.
- Eighth extended/bench candidate `compression_retest_continuation_v0` is also REJECTED_FIRST_PASS.
- Compression retest continuation hypothesis file: `xau-usd\xauusd-phase0\docs\hypothesis_compression_retest_continuation_v0.md`.
- Compression retest continuation matrix summary: `xau-usd\xauusd-phase0\docs\COMPRESSION_RETEST_CONTINUATION_V0_FIRST_PASS.md`.
- Latest compression retest continuation result-producing run status: rejected. Real 9-cell matrix produced 0 trades in every cell, so do not proceed to deciles or tune v0.
- Original 10-candidate research bench status: 1 approved future expert (`breakout_retest`) and 9 rejected v0 candidates.
- Extended bench candidate `asia_range_london_breakout_v0` is REJECTED_FIRST_PASS.
- Asia range London breakout hypothesis file: `xau-usd\xauusd-phase0\docs\hypothesis_asia_range_london_breakout_v0.md`.
- Asia range London breakout matrix summary: `xau-usd\xauusd-phase0\docs\ASIA_RANGE_LONDON_BREAKOUT_V0_FIRST_PASS.md`.
- Latest Asia range London breakout result-producing run status: rejected. Real 9-cell matrix produced 507-571 trades per cell, but only 0/9 cells reached PF >= 1.30, so do not proceed to deciles or tune v0.
- Extended bench candidate `previous_day_extreme_retest_v0` is REJECTED_FIRST_PASS.
- Previous-day extreme retest hypothesis file: `xau-usd\xauusd-phase0\docs\hypothesis_previous_day_extreme_retest_v0.md`.
- Previous-day extreme retest matrix summary: `xau-usd\xauusd-phase0\docs\PREVIOUS_DAY_EXTREME_RETEST_V0_FIRST_PASS.md`.
- Latest previous-day extreme retest result-producing run status: rejected. Real 9-cell matrix produced 478-704 trades per cell, but only 0/9 cells reached PF >= 1.30, so do not proceed to deciles or tune v0.
- Extended bench candidate `ny_am_pullback_continuation_v0` is REJECTED_FIRST_PASS.
- NY AM pullback continuation hypothesis file: `xau-usd\xauusd-phase0\docs\hypothesis_ny_am_pullback_continuation_v0.md`.
- NY AM pullback continuation matrix summary: `xau-usd\xauusd-phase0\docs\NY_AM_PULLBACK_CONTINUATION_V0_FIRST_PASS.md`.
- Latest NY AM pullback continuation result-producing run status: rejected. Real 9-cell matrix produced 326-382 trades per cell, but only 0/9 cells reached PF >= 1.30, so do not proceed to deciles or tune v0.
- Extended bench candidate `weekly_level_reclaim_v0` is REJECTED_FIRST_PASS.
- Weekly level reclaim hypothesis file: `xau-usd\xauusd-phase0\docs\hypothesis_weekly_level_reclaim_v0.md`.
- Weekly level reclaim matrix summary: `xau-usd\xauusd-phase0\docs\WEEKLY_LEVEL_RECLAIM_V0_FIRST_PASS.md`.
- Latest weekly level reclaim result-producing run status: rejected. Real 9-cell matrix produced 113-129 trades per cell, but only 0/9 cells reached PF >= 1.30, so do not proceed to deciles or tune v0.
- Extended bench candidate `asia_range_london_failed_break_reversal_v0` is REJECTED_FIRST_PASS.
- Asia range London failed-break reversal hypothesis file: `xau-usd\xauusd-phase0\docs\hypothesis_asia_range_london_failed_break_reversal_v0.md`.
- Asia range London failed-break reversal matrix summary: `xau-usd\xauusd-phase0\docs\ASIA_RANGE_LONDON_FAILED_BREAK_REVERSAL_V0_FIRST_PASS.md`.
- Latest Asia range London failed-break reversal result-producing run status: rejected. Real 9-cell matrix produced 326-372 trades per cell, but only 0/9 cells reached PF >= 1.30, so do not proceed to deciles or tune v0.
- Extended bench candidate `session_vwap_reclaim_v0` is REJECTED_FIRST_PASS.
- Session VWAP reclaim hypothesis file: `xau-usd\xauusd-phase0\docs\hypothesis_session_vwap_reclaim_v0.md`.
- Session VWAP reclaim matrix summary: `xau-usd\xauusd-phase0\docs\SESSION_VWAP_RECLAIM_V0_FIRST_PASS.md`.
- Latest session VWAP reclaim result-producing run status: rejected. Real 9-cell matrix produced 481-614 trades per cell, but only 0/9 cells reached PF >= 1.30, so do not proceed to deciles or tune v0.
- Extended bench candidate `swing_breakout_retest_v0` is `APPROVED_FUTURE_EXPERT_CANDIDATE`.
- Swing breakout-retest hypothesis file: `xau-usd\xauusd-phase0\docs\hypothesis_swing_breakout_retest_v0.md`.
- Swing breakout-retest matrix summary: `xau-usd\xauusd-phase0\docs\SWING_BREAKOUT_RETEST_V0_FIRST_PASS.md`.
- Latest swing breakout-retest result-producing run status: approved future expert candidate, but same-family with `breakout_retest`. Real 9-cell matrix produced 6,281-6,600 trades per cell, 7/9 cells reached PF >= 1.30, deciles passed 10/10 with median PF 1.450, multisymbol passed with EURUSD PF 1.375 and USDJPY PF 1.668, intrabar ambiguity was 342/57,897 trades (0.59%), and Gate 9 scored PASS with 120/120 reviewed losses and 0 logic gaps.
- Cost reporting policy: `xau-usd\xauusd-phase0\docs\COST_REPORTING_POLICY.md`.
- Fixed-notional report command: `phase0 generate-fixed-notional-report --expert breakout_retest`.
- Latest fixed-notional report: `xau-usd\xauusd-phase0\outputs\reports\FIXED_NOTIONAL_REPORT.md`.
- Current fixed-notional summary for `breakout_retest`: 66,759 trades, net expectancy 0.1888R, mean all-in cost 0.3228R, and cost-edge consumption flagged ORANGE.
- Measured cost model command: `phase0 generate-measured-cost-model --input-dir C:\MT5PortableSpreadLogger\MQL5\Files`.
- Latest measured cost model report: `xau-usd\xauusd-phase0\outputs\reports\MEASURED_COST_MODEL.md`, status PENDING with 629 rows over 1 observed day; it still needs 5 observed days.
- Measured-cost revalidation command: `phase0 generate-measured-cost-revalidation --expert breakout_retest`.
- Latest measured-cost revalidation report: `xau-usd\xauusd-phase0\outputs\reports\BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md`, status PENDING until measured cost model status is PASS.
- Phase 1 canonical reporting policy is tracked in `xau-usd\xauusd-phase1\docs\REPORTING_POLICY.md`.
- Dedicated Phase 1 CI workflow: `.github\workflows\phase1.yml`.
- Soak history appender: `xau-usd\xauusd-phase1\scripts\append_phase1_soak_history.py`.
- Latest Phase 1 soak history CSV: `xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`.
- Soak history report generator: `xau-usd\xauusd-phase1\scripts\generate_phase1_soak_history_report.py`.
- Latest Phase 1 soak history report: `xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY_REPORT.md`.
- Latest soak history has 37 rows, status PASS, and is appended by the bundle generator, periodic check runner, plus the hourly soak automation.
- Review index generator: `xau-usd\xauusd-phase1\scripts\generate_phase1_review_index.py`.
- Latest Phase 1 review index: `xau-usd\xauusd-phase1\outputs\reports\PHASE1_REVIEW_INDEX.md`.
- Latest review index status: PENDING, with all primary artifacts present and only final acceptance still pending.
- Phase 2 readiness generator: `xau-usd\xauusd-phase1\scripts\generate_phase2_readiness_report.py`.
- Latest Phase 2 readiness report: `xau-usd\xauusd-phase1\outputs\reports\PHASE2_READINESS_REPORT.md`.
- Latest Phase 2 readiness status: PENDING. Phase 2 prep spec, cost reporting policy, fixed-notional reporting, Phase 1 summary health, latest dry-run boundary, and would-signal evidence pass; measured cost model, measured-cost revalidation, Phase 1 acceptance, Phase 1 review index, five-day soak completion, and owner approval remain pending.
- Phase 1 deploy/compile helper: `xau-usd\xauusd-phase1\scripts\deploy_phase1_mt5.py`.
- Latest helper run deployed 41 files to `C:\MT5PortableGoldMission\MQL5` plus the mapped terminal data MQL5 root, and MetaEditor compile status was PASS.
- Hourly automation `phase1-mt5-soak-check` runs the Phase 1 runtime checks against `C:\MT5PortableGoldMission\MQL5\Files` and measured-cost checks against `C:\MT5PortableSpreadLogger\MQL5\Files` through `--spread-files-dir`.
- Acceptance report generator: `xau-usd\xauusd-phase1\scripts\generate_phase1_acceptance_report.py`.
- Latest Phase 1 acceptance report: `xau-usd\xauusd-phase1\outputs\reports\PHASE1_ACCEPTANCE_REPORT.md`.
- Latest acceptance status: PENDING. Compile/source-safety/log/soak/runtime-health/would-signal/soak-history/dry-run/permission/runtime-freshness/latest-row gates pass; only the five-trading-day wall-clock soak gate remains pending.
- Hourly automation `phase1-mt5-soak-check` also regenerates the acceptance report, checks source safety, and reports five-trading-day soak progress.
- Hourly automation `phase1-mt5-soak-check` also regenerates `PHASE1_STATUS_SUMMARY.json`, appends `PHASE1_SOAK_HISTORY.csv`, regenerates `PHASE1_SOAK_HISTORY_REPORT.md`, regenerates `PHASE1_REVIEW_INDEX.md`, and regenerates `PHASE2_READINESS_REPORT.md`.
- Phase 1 bundle generator: `xau-usd\xauusd-phase1\scripts\generate_phase1_bundle.py`.
- Latest Phase 1 dry-run review bundle: `xau-usd\xauusd-phase1\outputs\review_bundles\PHASE1_DRY_RUN_BUNDLE_20260522_064156.zip`.
- Latest Phase 1 bundle manifest: `xau-usd\xauusd-phase1\outputs\review_bundles\PHASE1_DRY_RUN_BUNDLE_20260522_064156_manifest.json`.
- Phase 2 preparation spec: `xau-usd\xauusd-phase1\docs\PHASE2_DRY_RUN_TO_PAPER_PREP_SPEC.md`. This is spec-only and does not authorize broker-side behavior.
- Phase 2 authorization checklist: `xau-usd\xauusd-phase1\docs\PHASE2_AUTHORIZATION_CHECKLIST.md`.
- Phase 2 operations prep spec: `xau-usd\xauusd-phase1\docs\PHASE2_OPERATIONS_PREP.md`.
- External health check script: `xau-usd\xauusd-phase1\scripts\check_phase1_external_health.py`.
- Periodic Phase 1 check runner: `xau-usd\xauusd-phase1\scripts\run_phase1_periodic_checks.py`.

## Local MT5 Discovery

- Standard install: `C:\Program Files\MetaTrader 5\terminal64.exe`.
- Portable clone: `C:\Users\ZHAO ZHU INFORMATION\Documents\Codex\2026-04-18-open-metatrader\mt5portable_clone\terminal64.exe`.
- Portable Gold Mission install: `C:\MT5PortableGoldMission\terminal64.exe`.
- Terminal data roots:
  - `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075` -> standard install.
  - `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\FB0D851E25D6B0EABBB1517331AB5827` -> portable clone.
  - `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\FDAC074599BBCDE0F5549DAB937D2E01` -> `C:\MT5PortableGoldMission`.
- Capital.com bars were exported through the passive MT5 script from `C:\MT5PortableGoldMission` for XAUUSD, EURUSD, and USDJPY across M5, M15, H1, H4, D1.
- Pepperstone XAUUSD bars were exported through the passive MT5 script from the standard MT5 install across M5, M15, H1, H4, D1.
- Raw MT5 exports are staged under:
  - `xau-usd\xauusd-phase0\data\raw\capital_com\`
  - `xau-usd\xauusd-phase0\data\raw\pepperstone\`
- MT5 binary history caches were not parsed directly; they were only used to identify promising coverage and broker installs.
- No local Dukascopy MT5/cache source was found. Dukascopy XAUUSD was acquired through the public Dukascopy feed via `dukascopy-node`.
- Dukascopy M15 was derived from acquired Dukascopy M5 bars and normalized as `XAUUSD_dukascopy_M15_20220101_20250101.csv`.
- Hugging Face is authenticated as `wierdali`; it can help with remote compute/artifact storage, but dataset search did not find a high-confidence XAUUSD/Dukascopy broker-history replacement.

## Key Commands

```powershell
cd xau-usd\xauusd-phase0
.\.venv\Scripts\phase0.exe generate-data-requirements
.\.venv\Scripts\phase0.exe generate-mt5-bar-presets
.\.venv\Scripts\phase0.exe validate-reference
.\.venv\Scripts\phase0.exe validate-hypotheses-complete
.\.venv\Scripts\phase0.exe hash-hypotheses --register --force
.\.venv\Scripts\phase0.exe import-required-bars --fail-on-missing
.\.venv\Scripts\phase0.exe check-data-availability
.\.venv\Scripts\phase0.exe run-all
.\.venv\Scripts\phase0.exe run-all --synthetic-sample
.\.venv\Scripts\phase0.exe audit-safety
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\phase0.exe generate-snapshot
.\.venv\Scripts\phase0.exe score-adversarial-review --expert breakout_retest
.\.venv\Scripts\phase0.exe generate-intrabar-ambiguity-report --expert breakout_retest
.\.venv\Scripts\phase0.exe generate-review-bundle
.\.venv\Scripts\phase0.exe verify-real-artifacts
cd ..\xauusd-phase1
..\xauusd-phase0\.venv\Scripts\python.exe scripts\audit_phase1_safety.py
..\xauusd-phase0\.venv\Scripts\python.exe -m pytest tests
```

## Remaining Gates Before Live EA Coding

1. Continue the Phase 1 MT5 soak and hourly log verification.
2. Keep improving dry-run telemetry: breakout-retest observer coverage, data freshness, session/regime diagnostics, dashboard clarity, soak/drift summaries, and restart behavior.
3. Keep the soak-history ledger growing during scheduled checks so the five-day evidence trail is reviewable.
4. Add Phase 1 static/compile/review-bundle coverage whenever a new module slice is introduced.
5. Do not add live execution or position-management behavior until a later milestone explicitly approves it after dry-run soak evidence is reviewed.

## Current Recommendation

Phase 0 is closed for the reduced one-expert package. Proceed with Phase 1 Master EA dry-run shell work only: richer market data, session/regime/risk/execution/news state, dashboard, decision logs, restart safety, and MT5 demo telemetry. Do not add live execution or position-management behavior.
