# Agent Handoff

Last updated: 2026-05-27

## Workspace

- Root: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system`
- Canonical source: `https://github.com/maksoftwares/algo-trading-system`
- Note: Windows workspace and MT5 paths are machine-local evidence paths, not reviewer requirements. See `xau-usd\xauusd-phase1\docs\WORKSPACE_OWNERSHIP.md`.
- Active package: `xau-usd\xauusd-phase1`
- Active phase label: Phase 1 - Master EA dry-run shell.
- Current branch: `main`
- Remote: `https://github.com/maksoftwares/algo-trading-system.git`
- Single-page status dashboard: `status.html` at the repo root.

## Standing Rules

- Do not add live EA trade execution until Phase 0 real-data gates approve an expert.
- No `OrderSend`, `OrderSendAsync`, `CTrade`, `trade.Buy`, `trade.Sell`, or position-opening logic in Phase 0.
- Keep all MT5 tools passive: file export, logging, or diagnostics only.
- Phase 1 currently means dry-run shell only: telemetry, lifecycle, risk, router contracts, dashboard/logging work, and blocked reasons.
- Prefer generated manifests, snapshots, and hashable artifacts over informal notes.
- Always keep the root `status.html` dashboard up to date. After any status-affecting Phase 0, Phase 1, soak, cost, report, or candidate change, regenerate it directly or through `run_phase1_periodic_checks.py` before committing or pushing.
- Do not push unless explicitly asked.

## Current State

- 2026-05-27 refresh:
  - Phase 1 schema acceptance fix is deployed to `C:\MT5PortableGoldMission`, compiled with 0 errors / 0 warnings, and the terminal was restarted. The logger rotated stale CSVs to `MQL5\Files\logs\archive`; live `decision_log.csv` now uses `phase1_decision_schema_v2` with `decision_schema_hash`, `br_lifecycle_state`, and `sbr_lifecycle_state`.
  - Soak evidence was recovered after schema rotation: archived old-schema decision rows were migrated into the current v2 schema with `scripts\migrate_phase1_decision_log_schema.py`; live `decision_log.csv` now preserves 613 rows from the original 2026-05-22 start while keeping the v2 schema hash fields.
  - Phase 1 acceptance is `PENDING`. Runtime verification is `WARN` rather than `FAIL` because schemas are valid and the remaining warnings are soak/cadence/health maturity gates, not a broken log format.
  - Latest refreshed runtime snapshot: 613 clean-schema decision rows, latest bar `2026.05.27 00:40:00`, `dry_run=true`, `trade_permission=false`, `server_time_status=CLOCK_OK`, would-signal evidence `65` rows / `65` clusters.
  - Five-day soak evidence is preserved at `91.39%` (`4.5694/5.00` observed calendar days), from `2026-05-22 11:00:00` to `2026-05-27 00:40:00`. Active-market streak remains `22.92h/72h` longest and `2.67h/72h` current.
  - Code-freeze was correctly reset by the real deployment: code-freeze `0.16h/96h`, marker `2026-05-27T00:31:23Z`. Do not backdate or fake this gate.
  - Regression coverage exists for the migration path: `tests\test_phase1_decision_log_migration.py` checks that archived old-schema rows are migrated into v2 without losing soak timestamps.
  - Status dashboard fix: the Milestone Rail `Five-day soak` row now uses the actual soak counters (`observed_days` vs `required_days`) instead of inheriting overall Phase 1 acceptance status. It should show `PENDING` until the five-day wall-clock target is reached; Phase 1 acceptance failures remain separate.
  - Measured-cost forensics corrected the coverage gate: legacy spread logs from `2026-05-22` through `2026-05-26` lacked `tick_fresh` / `seconds_since_tick`, so they are no longer admitted as authoritative measured-cost rows. Weekend/closed-market rows are also excluded before coverage is counted.
  - Passive spread logger was redeployed to `C:\MT5PortableSpreadLogger` from the repo source, compiled with 0 errors / 0 warnings, restarted, and is now writing `tick_fresh=true` rows in `spread_log_121409_Capital.ComMena-Live_XAUUSD_20260527.csv`.
  - Measured cost model is now `PENDING` with 205 authoritative fresh rows over 1 observed market day; measured-cost revalidation and assumption delta are also `PENDING` until 500 fresh rows across 5 observed market days exist.
  - Phase 2 readiness is `PENDING`; do not add paper-mode broker execution while measured-cost revalidation, Phase 1 acceptance, VPS selection, and owner approval are not PASS.
- Current measured-cost decision: `MEASURED_COST_MODEL.md` is `PENDING` after the freshness audit. Treat the prior measured-cost `FAIL` as a non-authoritative legacy diagnostic, not a final gate result. `breakout_retest` may remain in Phase 1 telemetry, but it is not Phase 2 paper-mode execution eligible until the fresh measured-cost model reaches PASS and revalidation passes.
- Phase 2 paper-mode implementation is blocked by pending measured-cost evidence plus pending Phase 1 acceptance. Continue Phase 1 dry-run and passive spread logging; do not add broker-side execution.
- New review blockers being addressed: expected market-break classification, measured-cost diagnostic/audit/delta reports, passive spread quote-freshness filtering, cost-suspended lifecycle docs, and magic-number external registry/readiness gates. Schema-versioned Phase 1 log rotation is implemented and verified.
- 2026-05-23 resume after planned one-day shutdown is complete.
  - `C:\MT5PortableGoldMission\terminal64.exe` is running with `/portable /config:C:\MT5PortableGoldMission\Config\phase1_dry_run_startup.ini`.
  - `C:\MT5PortableSpreadLogger\terminal64.exe` is running with `/portable /config:C:\MT5PortableSpreadLogger\Config\phase0_spread_logger_startup.ini`.
  - Phase 1 startup now reports `server_time_status=CLOCK_OK` after changing the expected local UTC offset input from whole hours to minutes for India Standard Time (`330` minutes).
  - Weekend/offline resume gaps are tolerated by the Phase 1 verifier, soak analyzer, runtime-health report, and external-health check when the latest row is a stale weekend market-break row.
  - Historical periodic-check note: earlier Phase 2 readiness was PENDING while measured-cost evidence was incomplete. Current status must be read from generated reports; after measured-cost revalidation FAIL, Phase 2 implementation is blocked by failed cost evidence.
  - Latest refreshed soak snapshot: 56 decision rows, latest M5 bar `2026.05.22 20:55:00`, soak progress `8.26%`, Phase 1 acceptance `PENDING`.
  - Latest measured cost model snapshot: `11435` observed spread rows across `2` observed days; still `PENDING` until 5 observed days are available.
- Latest committed acquisition helper: `generate-mt5-bar-presets`.
- Passive MT5 tools exist for spread logging and historical bar export.
- Passive spread logger is deployed and compiled under `C:\MT5PortableGoldMission\MQL5\Experts\Phase0\PassiveSpreadLogger_XAUUSD.ex5`; compile log `C:\MT5PortableGoldMission\compile_PassiveSpreadLogger_XAUUSD.log` shows 0 errors / 0 warnings.
- Passive spread logger is running in an isolated portable clone at `C:\MT5PortableSpreadLogger\terminal64.exe` so the active Phase 1 dry-run chart in `C:\MT5PortableGoldMission` is not restarted or replaced.
- Passive spread logger latest output path: `C:\MT5PortableSpreadLogger\MQL5\Files\spread_log_121409_Capital.ComMena-Live_XAUUSD_20260523.csv`.
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
- Latest decision row confirms `phase1-dry-run-v0.6`, `DRY_RUN`, `DRY_RUN_ONLY`, `magic_namespace_ok=true`, `server_time_status=CLOCK_OK`, `risk_state=NORMAL`, `would_have_allowed_experts=breakout_retest;swing_breakout_retest_v0`, `trade_permission=false`, and `block_reason=STALE_TICK` while the market is in weekend state.
- Latest v0.6 row includes `sbr_stage`, `sbr_direction`, `sbr_would_signal`, `sbr_reason_code`, `sbr_level_kind`, `sbr_entry_price`, `sbr_stop_loss`, and `sbr_take_profit`.
- Phase 1 v0.5 logs were archived before the v0.6 schema change:
  - `C:\MT5PortableGoldMission\MQL5\Files\decision_log_pre_v0_6_20260522_150335.csv`
  - `C:\MT5PortableGoldMission\MQL5\Files\startup_log_pre_v0_6_20260522_150335.csv`
- Current v0.6 would-signal report has 10 dry-run would-signal rows across 10 setup clusters; all stayed dry-run and permission-locked.
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
- Latest would-signal status: PASS with 10 rows and 10 setup clusters; both long and short observations have appeared in dry-run telemetry.
- Runtime health report generator: `xau-usd\xauusd-phase1\scripts\generate_phase1_runtime_health_report.py`.
- Latest Phase 1 runtime health report: `xau-usd\xauusd-phase1\outputs\reports\PHASE1_RUNTIME_HEALTH_REPORT.md`.
- Latest runtime health status: PASS. Runtime files exist, latest row is fresh or weekend-paused, dry-run and permission locks hold, latest server-time status is clean, no exact duplicate rows were found, and the planned offline/weekend resume gap is classified as expected.
- Status summary generator: `xau-usd\xauusd-phase1\scripts\generate_phase1_status_summary.py`.
- Latest Phase 1 status summary JSON: `xau-usd\xauusd-phase1\outputs\reports\PHASE1_STATUS_SUMMARY.json`.
- Latest status summary shows 56 decision rows, 8.26% of the five-day soak target, `log_verification=PASS`, `soak_analysis=PASS`, `runtime_health=PASS`, `would_signal=PASS`, and `acceptance=PENDING`.
- Review #7 direct-control items are reflected in the repo: the ten-candidate diversification result is codified in `xau-usd\xauusd-phase0\docs\DIVERSIFICATION_AVAILABILITY_FINDING.md`, future low-frequency concentration/cross-venue gates are pre-registered in `xau-usd\xauusd-phase0\docs\HYPOTHESIS_LOCKING.md`, fixed-notional monthly R-series remains the canonical D2 evidence in `xau-usd\xauusd-phase0\docs\PHASE0_INDEPENDENT_VALIDATION.md`, and `phase1_soak_streak.py` now explicitly rejects weekend/stale/market-closed rows for active-market streak continuity.
- Review #6/#7 soak policy is implemented in status/acceptance/readiness reports: `weekend_policy=weekend_breaks_active_market_streak`; the active-market 72-hour bar-continuity gate is separate from the 96-hour process/code-freeze gate. Code-freeze marker file: `C:\MT5PortableGoldMission\MQL5\Files\phase1_code_freeze_started_at.txt`.
- Review #2 reflection and action plan is tracked in `docs\REVIEW_02_REFLECTION_AND_ACTION_PLAN.md`.
- Review #6 reflection and action plan is tracked in `docs\REVIEW_06_REFLECTION_AND_ACTION_PLAN.md`.
- Review #7 reflection and action plan is tracked in `docs\REVIEW_07_REFLECTION_AND_ACTION_PLAN.md`.
- Review #8 final repo review action plan is tracked in `docs\REVIEW_08_REFLECTION_AND_ACTION_PLAN.md`. It keeps Phase 1 dry-run and Phase 2 preparation as GO, but Phase 2 paper implementation, broker execution, and live trading remain NO-GO until the soak, active-market 72h, process/code-freeze 96h, measured-cost, revalidation, VPS, and owner-approval gates all pass.
- Review #2 reframes `breakout_retest` as high-frequency and cost-sensitive; Phase 2 is now treated as a real-cost measurement phase, not a profit-confirmation phase.
- External review follow-up on 2026-05-21 is tracked in `xau-usd\xauusd-phase0\docs\REVIEW_RESPONSE_2026_05_21.md`.
- D1-D4 status is tracked in `xau-usd\xauusd-phase0\docs\PHASE0_INDEPENDENT_VALIDATION.md`; CPCV, Reality Check/SPA, true-holdout audit, and independent reproduction are closed for the current evidence package.
- D1 CPCV command: `phase0 run-cpcv-validation --expert breakout_retest`.
- Latest D1 result: PASS. 135 CPCV paths across 9 matrix cells, 100% pass rate, median OOS PF 1.379, minimum OOS PF 1.135.
- D2 Reality Check command: `phase0 run-reality-check --approved-expert breakout_retest --iterations 5000 --block-months 3 --max-pvalue 0.10`.
- Latest D2 result after switching to fixed-notional monthly R and adding the first two H4/D1 attempts: PASS. `breakout_retest` remained the family winner across 29 non-empty matrix-ledger candidates, White Reality Check p-value 0.0002, max pairwise SPA p-value 0.0188.
- Fixed-notional monthly R-series is the canonical D2 evidence. Earlier percent-return/compounding Reality Check variants are superseded.
- Review #3 rejected-candidate gate audit: `xau-usd\xauusd-phase0\outputs\reports\PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.md`. Latest audit includes the expanded higher-timeframe search and treats `symbol_normalized_round_retest_v0` as approved same-family after Gate 9 owner attestation. `round_number_retest_v0` and `session_extreme_retest_v0` remain pending/non-matrix-rejection rows, not approved EAs.
- Review #6 frequency-normalized concentration audit: `xau-usd\xauusd-phase0\outputs\reports\PHASE0_CONCENTRATION_FREQUENCY_NORMALIZED_AUDIT.md`. It adds normalized top-trade/top-5 R ratios for concentration-failed candidates as review context only; it does not rescue or reclassify rejected v0 hypotheses.
- D3 true-holdout audit command: `phase0 audit-true-holdout`.
- Latest D3 result: PASS. 96 result CSV files scanned, no holdout-window timestamps found, latest audited result timestamp `2025-06-30T23:55:00+00:00`, unlock file absent.
- D4 independent reproduction command: `phase0 generate-independent-reproduction --expert breakout_retest --cell-id 2 --tolerance-pct 5`.
- Latest D4 result: PASS. `breakout_retest` cell 2 matched 7287 trades, PF 1.4119615864693404, win rate 0.4844243172773432, total PnL 18642279.988449715, and max drawdown within tolerance.
- Candidate research backlog targets mechanical hypotheses; see `xau-usd\xauusd-phase0\docs\CANDIDATE_RESEARCH_BACKLOG.md`.
- Second-candidate concentration-risk mitigation is tracked in `xau-usd\xauusd-phase0\docs\SECOND_CANDIDATE_RESEARCH_PLAN.md`; `opening_drive_failed_continuation_v0` is now REJECTED_FIRST_PASS.
- Latest independent-candidate hypothesis file: `xau-usd\xauusd-phase0\docs\hypothesis_opening_drive_failed_continuation_v0.md`.
- Second-candidate research hash manifest: `xau-usd\xauusd-phase0\outputs\hashes\research_hypothesis_hash_manifest.csv`.
- Latest independent-candidate matrix summary: `xau-usd\xauusd-phase0\docs\OPENING_DRIVE_FAILED_CONTINUATION_V0_FIRST_PASS.md`.
- Latest independent-candidate result-producing run status: rejected. Real 9-cell matrix produced 221-294 trades per cell, but 0/9 cells reached PF >= 1.30 and every cell had negative total return, so do not proceed to deciles or tune v0.
- Latest independent-candidate smoke command: `phase0 run-research-candidate-smoke --expert opening_drive_failed_continuation_v0 --hypothesis-file docs/hypothesis_opening_drive_failed_continuation_v0.md`.
- Latest independent-candidate smoke result: PASS. It generated 1 synthetic signal, produced a valid synthetic plan, and confirmed the hypothesis hash lock. The follow-up real matrix failed the first hard gate.
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
- Latest independent candidate `liquidity_sweep_reversal_v0` was registered, hash-locked, smoke-tested, and rejected first-pass. Real 9-cell matrix produced 393-482 trades per cell, but 0/9 cells reached PF >= 1.30, so do not proceed to deciles or tune v0.
- Latest independent candidate `daily_pivot_reclaim_v0` was registered, hash-locked, smoke-tested, and rejected first-pass. Real 9-cell matrix produced 486-558 trades per cell, but 0/9 cells reached PF >= 1.30, so do not proceed to deciles or tune v0.
- Latest independent candidate `m15_inside_bar_breakout_v0` was registered, hash-locked, smoke-tested, and rejected first-pass. Real 9-cell matrix produced 727-854 trades per cell, but 0/9 cells reached PF >= 1.30, so do not proceed to deciles or tune v0.
- Latest independent candidate `m5_impulse_continuation_v0` was registered, hash-locked, smoke-tested, and rejected first-pass. Real 9-cell matrix produced 2199-2363 trades per cell, but 0/9 cells reached PF >= 1.30, so do not proceed to deciles or tune v0.
- Latest candidate `round_number_retest_v0` was registered, hash-locked, smoke-tested, and promoted to `PROVISIONAL_PASS_PENDING_GATE9`. It passed all 9 matrix cells with PF 1.351-1.560, passed 10/10 deciles, had low intrabar ambiguity at 198/47,388 trades (0.42%), and passed multisymbol only with an XAU-specific mechanism note because EURUSD produced 0 trades while USDJPY PF was 1.435. Gate 9 is pending with 0/120 losses reviewed, so do not add it to Phase 1 or Phase 2 as an approved EA yet.
- Latest candidate `symbol_normalized_round_retest_v0` was registered, hash-locked, smoke-tested, and promoted to `APPROVED_FUTURE_EXPERT_CANDIDATE_SAME_FAMILY`. It passed all 9 matrix cells with PF 1.351-1.560, passed 10/10 deciles with PF 1.371-1.558, had low intrabar ambiguity at 198/47,388 trades (0.42%), improved multisymbol transfer with EURUSD 12,260 trades at PF 1.298 and USDJPY 14,380 trades at PF 1.559, and Gate 9 scored PASS with 120/120 owner-attested valid losses and 0 logic gaps. This is still same-family breakout-retest logic, so it does not solve independent diversification risk.
- Latest independent reversal candidate `symbol_round_sweep_reversal_v0` was registered, hash-locked, smoke-tested, and rejected first-pass. It produced 685-1,338 trades per cell, but 0/9 cells reached PF >= 1.30, total return was negative in 8/9 cells, and max drawdown reached 50.46%, so do not proceed to deciles or tune v0.
- Latest independent continuation candidate `liquidity_sweep_continuation_v0` was registered, hash-locked, smoke-tested, and rejected first-pass. It produced 1,281-1,423 trades per cell, but 0/9 cells reached PF >= 1.30 and every cell had PF below 1.0, so do not proceed to deciles or tune v0.
- Latest found candidate `session_extreme_retest_v0` is `PROVISIONAL_PASS_PENDING_GATE9`. It passed 9/9 matrix cells with PF 1.328-1.596 and 23,727 total matrix trades, passed deciles 10/10 with PF 1.321-1.657, passed multisymbol at P95 cost with EURUSD PF 1.181 and USDJPY PF 1.236, and had intrabar ambiguity of 240/23,727 trades (1.01%). Gate 9 is pending with 0/120 losses reviewed. This is still same-family breakout-retest logic, so it is a candidate found, but not true diversification and not approved for Phase 1/Phase 2 until manual review passes.
- Review #5 forcing-function result: `d1_momentum_h4_pullback_v0` was written, SHA256 registered, implemented, smoke-tested, and run through a result-producing 9-cell matrix before any new same-family candidate was authored. It is `REJECTED_FIRST_PASS`: 684 total trades, 69-80 trades per cell, only 3/9 PF cells >= 1.30, and concentration failed. Do not tune v0.
- Latest H4/D1 diversification attempt `d1_volatility_expansion_reversal_v0` is `REJECTED_FIRST_PASS`: 354 total trades, 30-53 trades per cell, 0/9 PF cells >= 1.30, and sample-size plus concentration failed. Do not tune v0.
- Latest H4/D1 diversification attempt `d1_compression_h4_expansion_v0` is `REJECTED_FIRST_PASS`: 783 total trades, 68-122 trades per cell, 0/9 PF cells >= 1.30, and concentration failed. Do not tune v0.
- Latest H4/D1 diversification attempt `d1_multi_day_exhaustion_reversion_v0` is `REJECTED_FIRST_PASS`: 291 total trades, 24-41 trades per cell, 0/9 PF cells >= 1.30, and trade-count, activity, and concentration gates failed. Do not tune v0.
- Latest H4/D1 diversification attempt `h4_d1_momentum_expansion_continuation_v0` is `REJECTED_FIRST_PASS`: 735 total trades, 81-83 trades per cell, 3/9 PF cells >= 1.30, all successful cells were Dukascopy, and concentration failed. Do not tune v0.
- Latest H4/D1 breakout attempt `h4_inside_bar_d1_momentum_breakout_v0` is `REJECTED_FIRST_PASS`: 741 total trades, 71-100 trades per cell, 2/9 PF cells >= 1.30, all cells were slightly positive, but cross-venue PF and concentration were insufficient. Do not tune v0.
- Latest W1/D1-scale attempt `w1_d1_momentum_continuation_v0` is `REJECTED_FIRST_PASS`: 498 total trades, 48-68 trades per cell, 3/9 PF cells >= 1.30, all cells were positive, but cross-venue PF and concentration were insufficient. Do not tune v0.
- Latest weekly-reference mean-reversion attempt `weekly_open_reversion_v0` is `REJECTED_FIRST_PASS`: 626 total trades, 197-220 trades per cell, 0/9 PF cells >= 1.30, and early broker/windows were negative. Do not tune v0.
- Latest D1 compression breakout attempt `d1_inside_day_breakout_v0` is `REJECTED_FIRST_PASS`: 192 total trades, 11-41 trades per cell, 3/9 PF cells >= 1.30, and only 3/9 cells met the minimum trade-count gate. Do not tune v0.
- Latest D1 outside-day follow-through attempt `d1_outside_day_followthrough_v0` is `REJECTED_FIRST_PASS`: 261 total trades, 22-33 trades per cell, 0/9 PF cells >= 1.30, and 0/9 cells met the minimum trade-count gate. Do not tune v0.
- Latest H1 volatility-regime attempt `h1_volatility_squeeze_breakout_v0` is `REJECTED_FIRST_PASS`: 116-300 trades per cell, 3/9 PF cells >= 1.30, all successful cells were Dukascopy, and concentration failed. Do not tune v0.
- Latest macro blocker-fix attempt `h4_real_yield_proxy_momentum_v0` is `REJECTED_FIRST_PASS`: FRED `DFII10` and `DTWEXBGS` data acquired, 18-64 trades per cell, 3/9 PF cells >= 1.30, all successful cells were Dukascopy, and sample-size/concentration/activity failed. Do not tune v0.
- Latest futures-positioning attempt `cot_gold_positioning_reversal_v0` is `REJECTED_FIRST_PASS`: official CFTC gold COT data acquired, 5-24 trades per cell, 0/9 PF cells >= 1.30, and sample-size/concentration/activity failed in every cell. Do not tune v0.
- Latest options-implied-volatility attempt `h4_gvz_volatility_panic_reversal_v0` is `REJECTED_FIRST_PASS`: public FRED `GVZCLS` data acquired, 48-60 trades per cell, 0/9 PF cells >= 1.30, sample size passed, and concentration/activity failed in every cell. Do not tune v0.
- Latest equity-risk implied-volatility attempt `h4_vix_risk_off_reversal_v0` is `REJECTED_FIRST_PASS`: public FRED `VIXCLS` data acquired, 47-61 trades per cell, 3/9 PF cells >= 1.30, all successful cells were Pepperstone, and concentration failed in every cell. Do not tune v0.
- Latest financial-conditions attempt `h4_financial_conditions_stress_reversal_v0` is `REJECTED_FIRST_PASS`: public FRED `NFCI` and `ANFCI` data acquired, 46-61 trades per cell, 0/9 PF cells >= 1.30, and concentration/activity failed in every cell. Do not tune v0.
- Latest breakeven-inflation attempt `h4_breakeven_inflation_momentum_v0` is `REJECTED_FIRST_PASS`: public FRED `T5YIE` and `T10YIE` data acquired, 183-273 trades per cell, 0/9 PF cells >= 1.30, and concentration failed in seven cells. Do not tune v0.
- Latest Treasury curve attempt `h4_treasury_curve_stress_momentum_v0` is `REJECTED_FIRST_PASS`: public FRED `DGS2`, `DGS10`, and `T10Y2Y` data acquired, 55-207 trades per cell, 3/9 PF cells >= 1.30, all successful cells were Pepperstone, and concentration/activity failed. Do not tune v0.
- Latest credit-spread attempt `h4_credit_spread_stress_momentum_v0` is `REJECTED_FIRST_PASS`: public FRED `BAA10Y` and `AAA10Y` data acquired, 153-211 trades per cell, 0/9 PF cells >= 1.30, and concentration/activity failed. Do not tune v0.
- Latest AI-style macro-composite attempt `h4_macro_composite_risk_state_v0` is `REJECTED_FIRST_PASS`: fixed transparent vote using public FRED macro/risk inputs, 34-98 trades per cell, 6/9 PF cells >= 1.30, all cells positive, but Capital.com sample size plus concentration/activity failed. Do not tune v0.
- Latest AI-style macro-composite v1 attempt `h4_macro_composite_risk_state_v1` is `REJECTED_FIRST_PASS`: broader fixed vote, 51-169 trades per cell, 3/9 PF cells >= 1.30, all successful cells were Pepperstone, and concentration/activity failed. Do not tune v1.
- Latest policy-uncertainty safe-haven attempt `h4_policy_uncertainty_safe_haven_v0` is `REJECTED_FIRST_PASS`: FRED `USEPUINDXD` data acquired, 142-181 trades per cell, 3/9 PF cells >= 1.30, all successful cells were Pepperstone, and concentration failed. Do not tune v0.
- Latest event-regime attempt `h1_macro_event_aftershock_v0` is `REJECTED_FIRST_PASS`: standardized US macro event slots tested, 85-93 trades per cell, 0/9 PF cells >= 1.30, and concentration failed in every cell. Do not tune v0.
- Review #5 forcing rule remains strategically active for diversification: no same-family breakout-retest / level-and-pullback candidate should be treated as diversification, and independent non-level/intermarket research must continue.
- Hypothesis timeframe coverage by entry/decision cadence: `M5_M15=30`, `M30_H1=12`, `H4_D1=19`, `W1_plus=1`. The real-yield macro blocker, GVZ options-implied-volatility lane, VIX equity-risk lane, NFCI/ANFCI financial-conditions lane, T5YIE/T10YIE breakeven-inflation lane, DGS2/DGS10/T10Y2Y Treasury curve lane, BAA10Y/AAA10Y credit-spread lane, fixed AI-style macro-composite lanes, USEPUINDXD policy-uncertainty lane, and standardized US macro event-regime lane are now cleared, but all locked first passes are rejected. No independent candidate has passed Phase 0 first pass yet.
- Review #6/#7 non-level diversification requirement before Phase 2 is satisfied for the current review cycle: twenty-three H4/D1/W1 non-level concepts plus additional H1 intermarket, volatility-regime, and event-regime concepts were hash-locked, implemented where data allowed, smoke-tested, matrix-tested, and rejected first-pass.
- Cost reporting policy: `xau-usd\xauusd-phase0\docs\COST_REPORTING_POLICY.md`.
- Fixed-notional report command: `phase0 generate-fixed-notional-report --expert breakout_retest`.
- Latest fixed-notional report: `xau-usd\xauusd-phase0\outputs\reports\FIXED_NOTIONAL_REPORT.md`.
- Current fixed-notional summary for `breakout_retest`: 66,759 trades, net expectancy 0.1888R, mean all-in cost 0.3228R, and cost-edge consumption flagged ORANGE.
- Measured cost model command: `phase0 generate-measured-cost-model --input-dir C:\MT5PortableSpreadLogger\MQL5\Files`.
- Latest measured cost model report: `xau-usd\xauusd-phase0\outputs\reports\MEASURED_COST_MODEL.md`, status PENDING with 11435 rows over 2 observed days; it still needs 5 observed days.
- Measured-cost revalidation command: `phase0 generate-measured-cost-revalidation --expert breakout_retest`.
- Latest measured-cost revalidation report: `xau-usd\xauusd-phase0\outputs\reports\BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md`, status FAIL in the current review; this is a hard Phase 2 paper-mode blocker unless the cost audit finds and fixes a conversion defect.
- Review #3 response and action plan: `docs\REVIEW_03_REFLECTION_AND_ACTION_PLAN.md`. Phase 2 remains framed as a paper-mode cost-measurement experiment for one breakout-retest edge family, not a profit-confirmation phase.
- Phase 1 canonical reporting policy is tracked in `xau-usd\xauusd-phase1\docs\REPORTING_POLICY.md`.
- Dedicated Phase 1 CI workflow: `.github\workflows\phase1.yml`.
- Soak history appender: `xau-usd\xauusd-phase1\scripts\append_phase1_soak_history.py`.
- Latest Phase 1 soak history CSV: `xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`.
- Soak history report generator: `xau-usd\xauusd-phase1\scripts\generate_phase1_soak_history_report.py`.
- Latest Phase 1 soak history report: `xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY_REPORT.md`.
- Latest soak history has 83 rows, status WARN because the historical progress ledger includes expected schema/reset decreases, and is appended by the bundle generator, periodic check runner, plus the hourly soak automation.
- Review index generator: `xau-usd\xauusd-phase1\scripts\generate_phase1_review_index.py`.
- Latest Phase 1 review index: `xau-usd\xauusd-phase1\outputs\reports\PHASE1_REVIEW_INDEX.md`.
- Latest review index status: PENDING, with all primary artifacts present and only final acceptance still pending.
- Phase 2 readiness generator: `xau-usd\xauusd-phase1\scripts\generate_phase2_readiness_report.py`.
- Latest Phase 2 readiness report: `xau-usd\xauusd-phase1\outputs\reports\PHASE2_READINESS_REPORT.md`.
- Latest Phase 2 readiness status: FAIL while measured-cost revalidation is FAIL. Phase 2 prep may continue, but paper-mode implementation remains blocked.
- Phase 1 deploy/compile helper: `xau-usd\xauusd-phase1\scripts\deploy_phase1_mt5.py`.
- Latest helper run deployed 41 files to `C:\MT5PortableGoldMission\MQL5` plus the mapped terminal data MQL5 root, and MetaEditor compile status was PASS.
- Hourly automation `phase1-mt5-soak-check` runs the Phase 1 runtime checks against `C:\MT5PortableGoldMission\MQL5\Files` and measured-cost checks against `C:\MT5PortableSpreadLogger\MQL5\Files` through `--spread-files-dir`.
- Acceptance report generator: `xau-usd\xauusd-phase1\scripts\generate_phase1_acceptance_report.py`.
- Latest Phase 1 acceptance report: `xau-usd\xauusd-phase1\outputs\reports\PHASE1_ACCEPTANCE_REPORT.md`.
- Latest acceptance status: PENDING. Compile/source-safety/log/soak/runtime-health/would-signal/dry-run/permission/latest-row gates pass; runtime freshness and soak-history are WARN due the weekend/stale-row/history-reset context; five-trading-day wall-clock soak, active-market 72-hour streak, and process/code-freeze 96-hour gate remain pending.
- Hourly automation `phase1-mt5-soak-check` also regenerates the acceptance report, checks source safety, and reports five-trading-day soak progress, the active-market 72-hour streak, and the process/code-freeze 96-hour gate.
- Hourly automation `phase1-mt5-soak-check` also regenerates `PHASE1_STATUS_SUMMARY.json`, appends `PHASE1_SOAK_HISTORY.csv`, regenerates `PHASE1_SOAK_HISTORY_REPORT.md`, regenerates `PHASE1_REVIEW_INDEX.md`, and regenerates `PHASE2_READINESS_REPORT.md`.
- Phase 1 bundle generator: `xau-usd\xauusd-phase1\scripts\generate_phase1_bundle.py`.
- Latest Phase 1 dry-run review bundle: `xau-usd\xauusd-phase1\outputs\review_bundles\PHASE1_DRY_RUN_BUNDLE_20260522_064156.zip`.
- Latest Phase 1 bundle manifest: `xau-usd\xauusd-phase1\outputs\review_bundles\PHASE1_DRY_RUN_BUNDLE_20260522_064156_manifest.json`.
- Phase 2 preparation spec: `xau-usd\xauusd-phase1\docs\PHASE2_DRY_RUN_TO_PAPER_PREP_SPEC.md`. This is spec-only and does not authorize broker-side behavior.
- Phase 2 paper-ledger schema: `xau-usd\xauusd-phase1\docs\PHASE2_PAPER_LEDGER_SCHEMA.md`. It defines the 40-column paper-only evidence contract for future paper-mode projections.
- Phase 2 paper-ledger schema report: `xau-usd\xauusd-phase1\outputs\reports\PHASE2_PAPER_LEDGER_SCHEMA_REPORT.md`, status PASS.
- Phase 2 paper-ledger column template: `xau-usd\xauusd-phase1\outputs\reports\PHASE2_PAPER_LEDGER_COLUMNS.csv`.
- Phase 2 authorization checklist: `xau-usd\xauusd-phase1\docs\PHASE2_AUTHORIZATION_CHECKLIST.md`.
- Phase 2 owner approval template: `xau-usd\xauusd-phase1\docs\PHASE2_OWNER_APPROVAL_TEMPLATE.md`; do not create `outputs\reports\PHASE2_OWNER_APPROVAL.md` until all objective readiness gates pass and the owner explicitly approves paper-mode implementation.
- Phase 2 operations prep spec: `xau-usd\xauusd-phase1\docs\PHASE2_OPERATIONS_PREP.md`.
- Phase 2 VPS selection matrix: `xau-usd\xauusd-phase1\docs\PHASE2_VPS_SELECTION_MATRIX.md`, status PENDING until the owner selects provider, region, specs, backup method, and monitoring approach.
- Phase 2 cost-measurement protocol: `xau-usd\xauusd-phase1\docs\PHASE2_COST_MEASUREMENT_PROTOCOL.md`; pre-commits suspension if measured costs push the breakout-retest family below +0.15R net expectancy.
- Phase 2 single-edge risk plan: `xau-usd\xauusd-phase1\docs\PHASE2_SINGLE_EDGE_RISK_PLAN.md`; treats `breakout_retest`, `swing_breakout_retest_v0`, and `symbol_normalized_round_retest_v0` as one correlated edge family.
- External health check script: `xau-usd\xauusd-phase1\scripts\check_phase1_external_health.py`.
- Periodic Phase 1 check runner: `xau-usd\xauusd-phase1\scripts\run_phase1_periodic_checks.py`.
- Latest periodic check status after project-status dashboard wiring: PASS; Phase 2 readiness and Phase 1 review index are correctly PENDING rather than FAIL while measured-cost, five-day soak, and owner approval remain open.
- Project status page generator: `xau-usd\xauusd-phase1\scripts\generate_project_status_page.py`.
- Latest project status page: `status.html`. The hourly periodic check regenerates it from Phase 0/Phase 1/Phase 2 artifacts, including all accepted/rejected EA candidates.
- Planned one-day shutdown checkpoint: `xau-usd\xauusd-phase1\docs\SHUTDOWN_RESUME_CHECKPOINT_2026_05_22.md`.
- Hourly local automation `phase1-mt5-soak-check` should be ACTIVE while the machine is online; pause it before any future planned shutdown.

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
