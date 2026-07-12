# Exact R6-C1A.1 Machine-Lock Review — `77fc82e5`

**Repository:** `maksoftwares/algo-trading-system`  
**Branch:** `codex/xau-router-entry-hold-audit`  
**Exact commit:** `77fc82e57cbbf29be0139fcd72fa2668c19294d4`  
**Supplied tree:** `a678c29c85701a2cb2d3da7665571429ac43e5e7`  
**Reviewed C1A commit:** `04c7621e484193bc4c9c8ee74f634be436e9e2a2`

## Verdict

```text
R6-C1A.1: PASS
R6-C2:     AUTHORIZED, SIX FROZEN FILES ONLY
R6-C3:     NOT AUTHORIZED
P/L/MT5/H4/PORTFOLIO/RUNTIME: NOT AUTHORIZED
```

The four requested machine-lock corrections are present:

1. `impulse_bullish_bars` is constrained to `4..6` in the accepted-row schema.
2. The rule lock defines all emitted ratio formulas, including `breakdown_distance_atr` and `reclaim_touch_distance_atr`.
3. Early/late halves use explicit half-open broker timestamps.
4. Entry expiry is keyed to `decision_time`, with the superseded scheduled-close key removed.
5. The manifest hashes and sizes are regenerated and pins the C1A review SHA.

No threshold, incidence gate, status precedence, outcome-blind boundary, or phase boundary changed.

## Nonblocking documentation note

The original preregistration paragraph still contains the phrase “within 15 minutes of the scheduled H1 close.” The later C1A amendment and the machine-readable rule lock explicitly supersede it with `decision_time = next native H1 open` and `expiry_minutes_after_decision_time = 15`. This is therefore not a machine-lock blocker, but the stale sentence should be removed in a future documentation-only cleanup to avoid reader confusion. It must not be used to alter C2 behavior.

## R6-C2 authorized files

Only these files may be added:

```text
xau-usd/xauusd-phase1/scripts/
  build_a1_xau_r6_distribution_break_failed_reclaim_census.py
  validate_a1_xau_r6_outcome_blind_census.py

xau-usd/xauusd-phase1/tests/
  test_a1_xau_r6_distribution_break_failed_reclaim_definition.py
  test_a1_xau_r6_census_outcome_blind.py
  test_a1_xau_r6_census_contract_risk.py
  test_a1_xau_r6_census_manifest.py
```

C2 may implement detector/validator logic and synthetic or immutable market-only fixtures required by the frozen tests. It may not modify any C1 lock file.

## C2 prohibited actions

```text
No real census generation.
No R6 P/L, exits, targets, MFE/MAE, or future-path analysis.
No MT5 run or MQ5/MQH modification.
No H4 trade, position, exposure, P/L, drawdown, or episode join.
No portfolio join or correlation analysis.
No live/demo attachment, profile/preset arming, or broker action.
No threshold, gate, router, date, or status change.
```

## Exact-commit attestation required

The C2 validation must run after the C2 commit exists and must record:

```text
git rev-parse HEAD
git rev-parse HEAD^{tree}
git status --porcelain=v1  -> empty
exact test command
OS and architecture
Python version
dependency versions and lock hash
complete stdout and stderr
exit code 0
SHA256 of the complete test output
SHA256 of both scripts and all four tests
SHA256 of the final C1A.1 lock manifest
```

Preferred proof is immutable CI attached to the exact C2 SHA. Otherwise provide a hash-addressed exact-SHA local capture and make no code change after the capture.

## Single next action

Implement and commit **R6-C2 only** in the six authorized files, then run the exact-commit test/attestation procedure and return the exact commit and tree for review. Do not generate C3 census evidence in that commit.
