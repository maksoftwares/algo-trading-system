# XAUUSD Phase 3 Experimental Sandbox

This package is a repo-only experiment. It assumes Phase 2 might pass later, but it does not change the real project gate state.

Phase 3 experimental work is now frozen as a repo-side complete design package. See `docs/PHASE3_EXPERIMENTAL_FREEZE.md`.

## Boundary

- Real Phase 2 remains PENDING until the objective readiness reports pass.
- This sandbox is not deployable to MT5.
- It must not touch `C:\MT5PortableGoldMission` or `C:\MT5PortableSpreadLogger`.
- It must not contain broker-action code.
- It reads Phase 1 dry-run evidence and writes offline reports only.
- It is excluded from the owner approval flow for real Phase 2 or real Phase 3.

This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

## Purpose

The experiment lets us design and test Phase 3 concepts while Phase 2 evidence continues to mature:

- execution lifecycle states
- kill-rule behavior
- cost-survival checks
- paper-to-micro promotion criteria
- emergency stop design
- reviewable experimental ledgers
- family-level observer de-duplication
- explicit cost-mode stress checks
- cost-in-R gates, stop-distance buckets, spread-regime buckets, and family kill-state summaries
- suspend-family decision rows
- paper-shadow side-experiment lifecycle rows
- synthetic shadow-open lifecycle and risk-lock accounting
- guarded lifecycle controller comparison
- non-deploying demo rehearsal package
- promotion/rollback criteria
- observer conflict playbook
- future implementation prompt
- experimental freeze note
- review bundle generation
- source-hash manifests

## Commands

From this directory:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\simulate_phase3_from_would_signals.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\audit_phase3_experimental_safety.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\analyze_phase3_suspend_family.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase3_suspend_family_decision.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase3_cost_mode_comparison.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase3_cost_gate_review.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase3_family_dedup_audit.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase3_paper_shadow_experiment.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase3_shadow_lifecycle_experiment.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase3_lifecycle_guard_experiment.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase3_demo_rehearsal_package.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase3_experimental_status.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase3_experimental_manifest.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase3_experimental_status.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase3_completion_audit.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase3_experimental_status.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase3_review_bundle.py
```

The status command is intentionally run again after the manifest and completion audit so the dashboard can show both states.

The default input is:

```text
..\xauusd-phase1\outputs\reports\PHASE1_WOULD_SIGNAL_REVIEW.csv
```

The default outputs are under:

```text
outputs\reports\
```

Important generated outputs:

| Output | Purpose |
| --- | --- |
| `PHASE3_EXPERIMENTAL_LEDGER.csv` | Offline event ledger built from blocked Phase 1 would-signals. |
| `PHASE3_EXPERIMENTAL_SIMULATION.md` | Human-readable simulation summary. |
| `PHASE3_SUSPEND_FAMILY_REVIEW.md` | Review of offline rows that fail the +0.15R cost-survival threshold. |
| `PHASE3_SUSPEND_FAMILY_DECISION.md` | Explicit keep-suspended decisions and future rules for primary suspended family events. |
| `PHASE3_COST_MODE_COMPARISON.md` | Comparison of all supported cost modes against the same blocked would-signals. |
| `PHASE3_COST_GATE_REVIEW.md` | Cost-in-R gate prototypes, stop-distance buckets, spread-regime buckets, and family kill-state summary. |
| `PHASE3_FAMILY_DEDUP_AUDIT.md` | Review-only audit of same-bar family grouping and duplicate/conflict classifications. |
| `PHASE3_PAPER_SHADOW_SUMMARY.md` | Side-experiment paper-shadow lifecycle summary that keeps demo authorization false. |
| `PHASE3_PAPER_SHADOW_LEDGER.csv` | Offline paper-shadow lifecycle rows derived from the experimental ledger. |
| `PHASE3_SHADOW_LIFECYCLE_SUMMARY.md` | Synthetic post-open lifecycle summary for would-open rows; not a backtest or paper trading. |
| `PHASE3_SHADOW_LIFECYCLE_LEDGER.csv` | Synthetic lifecycle rows with close reasons, net R, drawdown, and risk-lock states. |
| `PHASE3_LIFECYCLE_GUARD_SUMMARY.md` | Guarded controller comparison that blocks cost-watch, high-cost, and risk-locked synthetic exposure. |
| `PHASE3_LIFECYCLE_GUARD_LEDGER.csv` | Guarded lifecycle rows with block reasons, running equity, and daily/portfolio lock states. |
| `PHASE3_DEMO_REHEARSAL_CHECKLIST.md` | Non-deploying demo rehearsal checklist that keeps real authorization false. |
| `PHASE3_DEMO_REHEARSAL_LEDGER.csv` | Rehearsal sequence for shadow open/close, blocked, and no-exposure events. |
| `PHASE3_TO_DEMO_HANDOFF.md` | Non-authorizing handoff from Phase 3 experiment to a future real paper-shadow/demo branch after Phase 2 gates pass. |
| `PHASE3_COMPLETION_AUDIT.md` | Explicit repo-side completion audit and external gate list before demo/paper work. |
| `PHASE3_EXPERIMENTAL_SAFETY_REPORT.md` | Safety-boundary scan for broker-action references. |
| `PHASE3_EXPERIMENTAL_MANIFEST.md` | Source-hash manifest for inputs, scripts, status, and reports. |
| `outputs\review_bundles\PHASE3_EXPERIMENTAL_REVIEW_BUNDLE_LATEST.zip` | Portable Phase 3 review bundle. |

## Family De-Duplication

The simulator treats `breakout_retest` as the only primary stream. `swing_breakout_retest_v0` and `symbol_normalized_round_retest_v0` are observer-only streams in this experiment. Provisional or disabled variants are rejected from the experimental ledger.

Key output fields:

```text
family_event_id
family_duplicate_group_id
family_event_role
primary_stream_allowed
raw_observer_event_count
family_unique_event_count
observer_duplicate_count
observer_conflict_count
```

## Cost Modes

Default:

```text
entry_exit_proxy
```

Available modes:

```text
entry_only_proxy
entry_exit_proxy
p95_fresh_proxy
stress_2x_p95_proxy
```

## Family De-Dup Audit

The audit classifies same-bar family groups as:

```text
TRUE_DUPLICATE
SAME_BAR_DISTINCT_LEVEL
SAME_BAR_DIRECTION_CONFLICT
SAME_BAR_EXECUTION_CONFLICT
```

The audit is review-only. It does not change execution eligibility.

## Current Real-Project Effect

None. This lane is informational and must remain separate from Phase 1 dry-run and Phase 2 readiness gates.
