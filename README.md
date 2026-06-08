# algo-trading-system

Research and validation workspace for algorithmic trading systems.

The repository is organized by symbol or instrument family so future symbols can be added without mixing research artifacts, data contracts, or reports.

## Current Packages

- `xau-usd/xauusd-phase0`: Phase 0 statistical validation package for the XAUUSD Master EA project.
- `xau-usd/xauusd-phase1`: Phase 1 dry-run shell for MT5 telemetry and lifecycle/risk/router contracts.
- `xau-usd/xauusd-phase0r`: Separate Phase 0R research lane for draft candidate hypotheses and cost feasibility checks.
- `xau-usd/xauusd-phase2b-passive-observers`: Separate Phase 2B passive observer lane for draft candidate telemetry only.

## Separate EA Research Lane - Phase 0R / Phase 2B Passive Observers

- These are not current canonical EAs.
- They are not execution-authorized.
- They do not modify current accepted/rejected experts.
- They are dry-run/passive-observer only.
- They must pass Phase 0R before any future paper-mode consideration.

## XAUUSD Phase 0

The XAUUSD package tests candidate expert behavior before any live-trading EA logic is built. It includes:

- hypothesis SHA256 locking
- raw tick validation and normalization
- bar generation
- indicators and mechanical strategy simulators
- event-driven backtesting
- matrix, decile, multisymbol, and adversarial validation
- reference, holdout, intrabar, and real-artifact audit checks
- markdown reports and consolidated verdict
- audit snapshot generation
- passive MT5 spread logger and spread-log analyzer

## Quick Start

```powershell
cd xau-usd\xauusd-phase0
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m phase0 run-all --synthetic-sample
.venv\Scripts\python.exe -m phase0 generate-snapshot
```

See `xau-usd/xauusd-phase0/README.md` for the full workflow.

Agent handoff and current gate status are maintained in `agent.md`.

## Status Dashboard

Open `status.html` in a browser for the current project dashboard. It summarizes Phase 0, Phase 1, Phase 2 readiness, soak progress, the active-market 72h gate, the process/code-freeze 96h gate, measured-cost status, experimental-demo governance, and all accepted/rejected EA candidates in one page.

The dashboard is generated from repo artifacts by:

```powershell
cd xau-usd\xauusd-phase1
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_project_status_page.py
```

The hourly Phase 1 periodic check also regenerates it while the machine is online.

## XAUUSD Phase 1

Phase 1 dry-run is authorized for infrastructure telemetry only. It does not include broker-side execution. The shell logs one heartbeat per M5 bar and records lifecycle, spread, router, risk, and blocked-reason fields.

`breakout_retest` passed the historical Phase 0 package, but the breakout-retest family is currently `COST_SUSPENDED_CANONICAL`: the fresh measured-cost model is PASS, measured-cost revalidation is FAIL, measured-cost assumption delta is FAIL, and the sanity check confirms the conversion path. Execution eligibility remains `BLOCKED`. `swing_breakout_retest_v0`, `symbol_normalized_round_retest_v0`, `quarter_round_retest_v0`, `round_number_retest_v0`, and `session_extreme_retest_v0` are same-family variants; they are not independent diversification and cannot become canonical Phase 2 execution streams while the family-level cost suspension stands. `trend_pullback`, `range_mr`, and the non-level independent research attempts remain rejected.

## Current Phase Label

The active project phase is:

```text
Phase 1 - Master EA dry-run shell
```

Phase 1 remains dry-run only. Paper-mode and live expert behavior stay out of scope until the dry-run shell has clean telemetry, measured-cost revalidation passes for an eligible candidate/family, Phase 2 readiness returns to `PASS`, and the project owner explicitly authorizes the next phase.

## Latest Review Status

As of 2026-05-21, the XAUUSD Phase 0 real-data workflow has imported all required broker/timeframe bar sets and completed a fresh post-hypothesis-lock `phase0 run-all`.

- Data readiness: `25/25` required timeframe sets ready.
- Verification: Phase 0 and Phase 1 test suites pass locally; passive safety audits pass.
- Historical Phase-0-passed candidate: `breakout_retest`; current lifecycle is `COST_SUSPENDED_CANONICAL`, so execution eligibility is `BLOCKED`.
- Same-family historical/provisional variants: `swing_breakout_retest_v0`, `symbol_normalized_round_retest_v0`, `quarter_round_retest_v0`, `round_number_retest_v0`, and `session_extreme_retest_v0`; none is independent diversification and no same-family candidate is execution-eligible while the cost-suspension lock is active.
- Current provisional same-family research candidates: `round_number_retest_v0` and `session_extreme_retest_v0`; their experimental demo evidence is quarantine-review-only and cannot authorize canonical Phase 2.
- Latest candidate-search status: one hundred nineteen result-producing candidates have now been hash-registered, smoke-tested where applicable, matrix-tested, and resolved without tuning, plus one CYB/UUP yuan-dollar lane is data-blocked because public Yahoo coverage ends in 2023. The newest two Phase 0R lower-cost H4/D1 contraction candidates passed structural P95 cost_R prechecks, but both were rejected first-pass: `h4_d1_volatility_contraction_expansion_v0` had 0/9 PF cells >= 1.30, and `h4_d1_contraction_trend_continuation_v0` had every cell below PF 1.0. No new independent candidate is approved.
- Audit status: older real-data results are exploratory only because the hash-registered hypothesis files still contained placeholders at run time; the latest run was regenerated after completing and locking hypotheses.
- Reviewer-prompt cleanup: reference status, hypothesis completeness checks, holdout manifest fields, review bundle generation, intrabar ambiguity reporting, and real artifact verification commands are now part of the package.
- Current verdict: `breakout_retest` passed automated matrix, decile, multisymbol, hash, and Gate 9 manual adversarial gates, but confirmed measured-cost revalidation failure blocks canonical execution eligibility.
- Phase 0 closure: `outputs/reports/PHASE0_VERDICT.md` marks `breakout_retest` as `PASS`; `verify-real-artifacts` returns `PASS`.
- EA coding status: Phase 1 dry-run shell is authorized for telemetry only. Paper-mode implementation and live execution remain blocked because measured-cost revalidation is `FAIL`, measured-cost assumption delta is `FAIL`, and the breakout-retest family cost suspension is active.

Large generated market data remains intentionally ignored by Git because it can be environment-specific. Small review artifacts, selected reports, and bundles may be committed when they are useful for third-party review. The current local handoff in `agent.md` records the latest artifact paths and regeneration commands.

## Current Review Follow-Ups

The latest reviewer feedback is tracked in:

- `docs/REVIEW_02_REFLECTION_AND_ACTION_PLAN.md`
- `xau-usd/xauusd-phase0/docs/REVIEW_RESPONSE_2026_05_21.md`
- `xau-usd/xauusd-phase0/docs/COST_REPORTING_POLICY.md`
- `xau-usd/xauusd-phase0/docs/PHASE0_INDEPENDENT_VALIDATION.md`
- `xau-usd/xauusd-phase0/docs/SECOND_CANDIDATE_RESEARCH_PLAN.md`
- `xau-usd/xauusd-phase1/docs/REPORTING_POLICY.md`
- `xau-usd/xauusd-phase1/docs/WORKSPACE_OWNERSHIP.md`
- `docs/REVIEW_06_REFLECTION_AND_ACTION_PLAN.md`
- `docs/REVIEW_07_REFLECTION_AND_ACTION_PLAN.md`
- `docs/REVIEW_08_REFLECTION_AND_ACTION_PLAN.md`
- `xau-usd/xauusd-phase0/docs/DIVERSIFICATION_AVAILABILITY_FINDING.md`

Review #9 keeps Phase 1 telemetry, limited Phase 2 documentation, and independent-candidate research moving, but Phase 2 implementation is blocked by measured-cost revalidation FAIL, measured-cost assumption delta FAIL, and owner approval PENDING. The 2026-06-02 Phase 2 review adds a cost-suspension closure package, clean-clone source reconciliation, broker-action boundary audit, and experimental-executor governance parity audit while keeping canonical Phase 2 broker execution NO-GO. It also confirms that the current approved/provisional candidates are one correlated breakout-retest family, not independent diversification.

The 2026-06-02 Phase 2 resolution package formalizes `canonical_phase2_status = BLOCKED_BY_MEASURED_COST`, adds measured-cost forensic reports, a Phase 2 blocker summary, canonical block verification, experimental quarantine verification, passive observer spec, and Phase 0R cost-feasibility requirements. The current forensic decision remains `CALCULATION_CONFIRMED`, so `breakout_retest_family_status = COST_SUSPENDED_CANONICAL`.

The 2026-06-04 actual-broker demo loss case study adds a committed review export for the `1025742 Capital.ComMena-Demo` account. The latest shadow-only review report is `xau-usd/xauusd-phase1/docs/PHASE2_DEMO_SHADOW_FILTER_REPORT_2026_06_04.md`; it measures, but does not enforce, a hypothetical block for `session_extreme_retest_v0` and XAUUSD morning/afternoon trades. The repo-only no-runtime-touch review verdict is `xau-usd/xauusd-phase1/docs/PHASE2_DEMO_LOSS_REVIEW_VERDICT_2026_06_04.md`; it confirms the pattern is experimental evidence only and does not authorize canonical Phase 2, router/session-filter changes, or demo EA runtime changes.

The latest week-to-date direct-MT5 trade export for reviewer inspection is packaged at `xau-usd/xauusd-phase1/docs/review_exports/PHASE2_DEMO_TRADE_WEAKNESS_REVIEW_2026_06_06.zip`, with extracted review request notes under `xau-usd/xauusd-phase1/docs/review_exports/PHASE2_DEMO_TRADE_WEAKNESS_REVIEW_2026_06_06/README_REVIEW_REQUEST.md`. It asks reviewers to diagnose win/loss drivers, duplicate/same-family exposure, viable EA-symbol-time buckets, and whether any trade families should be suspended, narrowed, or researched further. This packet supersedes the 2026-06-04 actual-trade packet for current reviewer triage, but remains experimental demo evidence only.

The current weakness-fix layer is shadow-only. `xau-usd/xauusd-phase1/outputs/reports/PHASE2_EA_WEAKNESS_SHADOW_REPORT.md` and `PHASE2_EA_WEAKNESS_SHADOW_TRADES.csv` measure duplicate-family mutex, XAUUSD morning/afternoon filtering, and quarantine candidates for `session_extreme_retest_v0` plus `symbol_normalized_round_retest_v0` against the duplicate-hidden actual-trade view. `xau-usd/xauusd-phase1/docs/PHASE2_DEMO_GUARD_ROUTER_SPEC.md` is a future demo-only guard/router spec, not a deployment authorization.

The replacement logger lane is isolated from actual demo trading EAs. `Phase2ShadowFixObserver` runs under `C:\MT5PortableShadowFixObservers`, writes `shadow_fix_observer_*` CSV files, and records `shadow_action` / `shadow_reason` for the proposed rules. Reports are tracked at `xau-usd/xauusd-phase1/outputs/reports/PHASE2_SHADOW_FIX_OBSERVER_TERMINAL.md` and `PHASE2_SHADOW_FIX_OBSERVER_ATTACHMENTS.md`.

The `P2WEAKNESS_BR_V1` package is a separate owner-requested experimental demo-only response to the 2026-06-06 weakness review. Runtime notes are tracked at `xau-usd/xauusd-phase1/docs/P2WEAKNESS_BR_V1_RUNTIME_NOTES.md`; source and launch/deploy helpers are under `xau-usd/xauusd-phase1/mt5/Experts/Phase2WeaknessBreakoutRetestExecutor.mq5` and `xau-usd/xauusd-phase1/scripts/setup_phase2_weakness_portable_demo_terminal.py`. It does not authorize canonical Phase 2, live trading, or replacement/modification of existing running EAs.

The 2026-06-08 code review keeps canonical Phase 2 and broker-side execution at NO-GO. New experimental demo deployments are paused until governance review. `P2WEAKNESS_BR_V1` source/presets now default to non-executing review-only mode, use the isolated `931000-931099` namespace with active magic `931000`, and publish P2WEAKNESS-specific governance, magic-audit, deployment-boundary, clean-clone, runtime-reconciliation, and daily-risk reports under `xau-usd/xauusd-phase1/outputs/reports/`.
