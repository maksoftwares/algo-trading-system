# Project Status Summary

Generated UTC: `2026-06-20T22:09:42.779366Z`
Artifact generation base commit: `077184ed501001748ef0e5c372f4ae2fecde5520`
Branch: `main`

This small file is the audit-friendly companion to the large `status.html` dashboard.

## Accounts

| Account | Login | Role | Round quarantine active | Touched by round quarantine |
| --- | ---: | --- | ---: | ---: |
| A1 | `1025742` | standard/noisy demo account | `false` | `true` |
| A2 | `1033030` | Tier-1 clean breakout account | `false` | `false` |
| A3 | `1033669` | repair / Tier-1 compatibility demo account | `false` | `false` |

## A1 Round-Family Quarantine

Status: `MISSING`
Scope: `A1 XAUUSD round-family only`
Keep active through forward week: `true`
Rollback required now: `false`

| Chart | Candidate | Dry run | Broker action | Status |
| --- | --- | ---: | ---: | --- |

## Protected Breakout Core

| Chart | Candidate | Dry run | Broker action | Status |
| --- | --- | ---: | ---: | --- |

## A3 Runtime Decision

Effective runtime authorization: `MISSING`
Runtime snapshot UTC: ``
Open positions: `0`
Pending orders: `0`
Artifact integrity: `MISSING`
Runtime performance: `MISSING`
Shadow candidate performance: `NOT_EVALUATED`
Pause artifact/runtime consistency: `MISSING`
Emergency pause report: `MISSING`
Test suite: `UNKNOWN` (None passed, None failed)
Family mutex: `NOT_IMPLEMENTED`
Containment: `NOT_IMPLEMENTED`
Shadow hypothesis: `NOT_REGISTERED`
Reactivation gate: `BLOCKED`

| Runtime lane | Current state |
| --- | --- |
| `933200` plain | `MISSING` |
| `933300` improved | `MISSING` |
| `933400` Tier1 compat | `MISSING` |
| Profit-lock manager | `MISSING` |

## A3 Historical Authorization

Tier1 `933400` owner authorization: `PENDING_OR_NOT_VISIBLE`
Current permission of that authorization: `SUPERSEDED_BY_EMERGENCY_PAUSE`

| Metric | Value |
| --- | ---: |
| Closed trades | `n/a` |
| Wins | `n/a` |
| Losses | `n/a` |
| Net PnL AED | `n/a` |
| Duplicate events | `n/a` |
| Profit-lock actions | `n/a` |

## Authorization Boundary

| Item | Value |
| --- | --- |
| Canonical Phase 2 PASS | `false` |
| Live trading authorized | `false` |
| Real capital authorized | `false` |
| A3 Tier-1 demo broker action | `PENDING_OR_NOT_VISIBLE` |
| A3 current runtime authorization | `MISSING` |

## Next Evidence Required

- SQ-01 hash-locked A3_SIGNAL_QUALITY_V1_IMPLEMENTATION_ADDENDUM_01.md
- SQ-02 hash-locked A3_SIGNAL_QUALITY_DIAGNOSTIC_SWEEP_V1_2026_06_18.md
- SQ-03 offline Python discovery sweep with frequency-quality and loss-attribution table
- Green CI run tied to the exact source commit before any shadow-terminal attachment
- A3 remains paused; no broker action, profile arming, or runtime attach before evidence gates pass
