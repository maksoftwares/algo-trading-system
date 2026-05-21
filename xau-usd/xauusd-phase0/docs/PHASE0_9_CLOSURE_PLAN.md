# Phase 0.9 Closure Plan

Last updated: 2026-05-21

Phase 0.9 was the bridge between automated Phase 0 evidence and approved Phase 1 dry-run work. It is now closed for the reduced one-expert package.

## Current Decision

| Item | Status |
| --- | --- |
| Data readiness | PASS |
| Hypothesis completeness | PASS |
| Fresh real-data rerun after hypothesis lock | COMPLETE |
| `breakout_retest` automated gates | PASS |
| `breakout_retest` Gate 9 manual review | PASS |
| `verify-real-artifacts` | PASS |
| Phase 1 dry-run shell | AUTHORIZED |
| Expert execution logic | BLOCKED |

The active decision rule is:

```text
IF breakout_retest adversarial review = PASS
AND PHASE0_VERDICT.md = PASS for breakout_retest
AND verify-real-artifacts = PASS
THEN Phase 1 dry-run Master EA can be treated as authorized.

ELSE remain in Phase 0.9.
```

Result on 2026-05-21: the PASS branch is satisfied for `breakout_retest`.

## Human-Owned Gate 9 Review

File to annotate:

```text
outputs/adversarial_review/breakout_retest_losing_trades_review.csv
```

There are 120 sampled losing trades. Gate 9 passes only when no more than 30 reviewed rows are classified as `LOGIC_GAP`. The project owner confirmed all 120 sampled losses are valid losses with no logic gaps.

Allowed classifications:

| Class | Meaning |
| --- | --- |
| `VALID_LOSS` | The setup was mechanically valid and the market simply failed to continue. |
| `ROUTER_OPPORTUNITY` | The setup was valid, but a future router may have blocked the context. |
| `LOGIC_GAP` | The strategy should not have allowed the trade. |
| `DATA_ISSUE` | The trade cannot be trusted because the source bars look defective. |
| `EXECUTION_AMBIGUITY` | Bar data cannot prove the sequence with enough confidence. |

Each row should fill:

```text
manual_failure_class
manual_notes
reviewer
reviewed_at_utc
```

Recommended note shape:

```text
Level valid: yes/no
Break valid: yes/no
Retest valid: yes/no
Confirmation valid: yes/no
Entry realistic: yes/no
SL/TP correct: yes/no
Final class: <class>
Reason: <short explanation>
```

## Developer-Owned Commands After Review

Run from `xau-usd/xauusd-phase0` after the CSV is fully annotated:

```powershell
.\.venv\Scripts\phase0.exe score-adversarial-review --expert breakout_retest
.\.venv\Scripts\phase0.exe generate-intrabar-ambiguity-report --expert breakout_retest
.\.venv\Scripts\phase0.exe aggregate-results --expert all
.\.venv\Scripts\phase0.exe generate-verdict
.\.venv\Scripts\phase0.exe verify-real-artifacts
.\.venv\Scripts\phase0.exe generate-review-bundle
.\.venv\Scripts\phase0.exe generate-snapshot
```

Expected clean state:

```text
Reviewed trades: 120
Logic-gap failure pct: <= 25%
breakout_retest final verdict: PASS
verify-real-artifacts: PASS
```

## Phase 0.9 Deliverables

| Deliverable | Current owner | Status |
| --- | --- | --- |
| Annotated `breakout_retest_losing_trades_review.csv` | Human reviewer | COMPLETE |
| Scored `breakout_retest_adversarial_score.md` | Codex after review | PASS |
| Intrabar ambiguity report | Codex | COMPLETE |
| `PHASE0_VERDICT.md` final PASS/FAIL | Codex after review | PASS for `breakout_retest` |
| Review bundle | Codex after review | COMPLETE |
| Snapshot | Codex after review | COMPLETE |
| `agent.md` status | Codex | UPDATED as work changes |
| Phase 1 dry-run spec | Codex | AUTHORIZED |

## Boundary

The passive MT5 shell may continue running for telemetry and startup validation. It must remain dry-run only. `breakout_retest` is the only approved future expert; live execution behavior remains blocked.
