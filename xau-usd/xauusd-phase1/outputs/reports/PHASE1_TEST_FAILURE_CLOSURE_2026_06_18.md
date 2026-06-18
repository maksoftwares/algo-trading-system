# Phase1 Test Failure Closure - 2026-06-18

Status: `PASS`

Scope:

- Repair false-positive Phase1 source safety failures after A3 broker-action/governance files entered the repo.
- Resolve the EURUSD/GBPUSD fixed-lot contract drift in favor of the signed `0.01` floor decision.
- Regenerate stale Phase2 demo preflight artifacts.
- Leave MT5 runtime, portable profiles, charts, positions, and orders untouched.

## Commands

```text
cd xau-usd/xauusd-phase1
..\xauusd-phase0\.venv\Scripts\python.exe scripts\audit_phase1_safety.py
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase2_demo_preflight_report.py --root .
..\xauusd-phase0\.venv\Scripts\python.exe scripts\audit_experimental_executor_governance.py --root .
..\xauusd-phase0\.venv\Scripts\python.exe scripts\verify_phase2_transition_artifacts.py --root . --repo-root ..\.. --status-path ..\..\status.html
..\xauusd-phase0\.venv\Scripts\python.exe -m pytest -q
```

## Results

| Check | Result |
| --- | --- |
| Phase1 safety audit | `PASS` |
| Phase2 transition artifact verifier | `PASS` |
| Full Phase1 pytest suite | `415 passed, 0 failed` |

## Resolved Items

| Prior failure | Resolution |
| --- | --- |
| Broad safety audit flagged guarded experimental broker-action files | Split audit into canonical strict sources and policy-governed experimental sources. Unknown broker-action files now fail closed. |
| Acceptance/status tests returned `FAIL` because of safety false positives | Acceptance/status fixtures now return their intended incomplete-evidence `PENDING` state. |
| EURUSD lot test expected stale `0.05` | Active source, attach scripts, and tests now align to the safer signed `0.01` floor decision for EURUSD and GBPUSD. |
| `PHASE2_DEMO_PREFLIGHT.json` stale | Regenerated JSON and Markdown. Safety check is now `PASS`. |

## Current Gate State

`PHASE2_DEMO_PREFLIGHT.json` still has overall status `FAIL` for real gate reasons outside this repair:

- `phase2_readiness` is `FAIL`.
- Project owner approval is `PENDING`.
- VPS first-day verification is `PENDING`.
- Demo countdown remains `DEMO_NOT_READY`.
- Local network baseline context remains `WARN` because it documents live-server network context only.

This is expected and keeps canonical Phase2/demo attachment gates closed.

## Runtime Boundary

No MT5 runtime was touched. No terminal profile, chart file, order, position, preset deployed to terminal, or account state was changed by this closure.
