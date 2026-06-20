# Project Status Summary

Generated UTC: `2026-06-19T19:35:18.683455Z`
Artifact generation base commit: `077184ed501001748ef0e5c372f4ae2fecde5520`
Branch: `main`

This small file is the audit-friendly companion to the large `status.html` dashboard.

## Accounts

| Account | Login | Role | Round quarantine active | Touched by round quarantine |
| --- | ---: | --- | ---: | ---: |
| A1 | `1025742` | standard/noisy demo account | `true` | `true` |
| A2 | `1033030` | Tier-1 clean breakout account | `false` | `false` |
| A3 | `1033669` | repair / Tier-1 compatibility demo account | `false` | `false` |

## A1 Round-Family Quarantine

Status: `ROUND_FAMILY_QUARANTINE_APPLIED`
Scope: `A1 XAUUSD round-family only`
Keep active through forward week: `true`
Rollback required now: `false`

| Chart | Candidate | Dry run | Broker action | Status |
| --- | --- | ---: | ---: | --- |
| `chart09.chr` | `symbol_normalized_round_retest_v0` | `true` | `false` | `OWNER_APPROVED_ROUND_FAMILY_QUARANTINED` |
| `chart11.chr` | `round_number_retest_v0` | `true` | `false` | `OWNER_APPROVED_ROUND_FAMILY_QUARANTINED` |

## Protected Breakout Core

| Chart | Candidate | Dry run | Broker action | Status |
| --- | --- | ---: | ---: | --- |
| `chart03.chr` | `breakout_retest` | `false` | `true` | `EXPERIMENTAL_QUARANTINE_REVIEW_ONLY` |
| `chart06.chr` | `swing_breakout_retest_v0` | `false` | `true` | `EXPERIMENTAL_QUARANTINE_REVIEW_ONLY` |

## A3 Runtime Decision

Effective runtime authorization: `A3_ENTRY_LANES_PAUSED`
Runtime snapshot UTC: `2026-06-18T07:44:27.604179Z`
Open positions: `0`
Pending orders: `0`
Artifact integrity: `PASS`
Runtime performance: `FAIL`
Shadow candidate performance: `NOT_EVALUATED`
Pause artifact/runtime consistency: `PASS`
Emergency pause report: `PASS`
Test suite: `PASS` (425 passed, 0 failed)
Family mutex: `NOT_IMPLEMENTED`
Containment: `NOT_IMPLEMENTED`
Shadow hypothesis: `REGISTERED_LOCKED`
Reactivation gate: `BLOCKED`

| Runtime lane | Current state |
| --- | --- |
| `933200` plain | `PAUSED` |
| `933300` improved | `PAUSED` |
| `933400` Tier1 compat | `PAUSED` |
| Profit-lock manager | `DRY_RUN_DISARMED` |

## A3 Historical Authorization

Tier1 `933400` owner authorization: `OWNER_AUTHORIZED_DEMO_BROKER_ACTION`
Current permission of that authorization: `SUPERSEDED_BY_EMERGENCY_PAUSE`

| Metric | Value |
| --- | ---: |
| Closed trades | `23` |
| Wins | `1` |
| Losses | `22` |
| Net PnL AED | `-758.79` |
| Duplicate events | `5` |
| Profit-lock actions | `0` |

## Authorization Boundary

| Item | Value |
| --- | --- |
| Canonical Phase 2 PASS | `false` |
| Live trading authorized | `false` |
| Real capital authorized | `false` |
| A3 Tier-1 demo broker action | `OWNER_AUTHORIZED_DEMO_BROKER_ACTION` |
| A3 current runtime authorization | `A3_ENTRY_LANES_PAUSED` |

## Next Evidence Required

- SQ-01 hash-locked A3_SIGNAL_QUALITY_V1_IMPLEMENTATION_ADDENDUM_01.md
- SQ-02 hash-locked A3_SIGNAL_QUALITY_DIAGNOSTIC_SWEEP_V1_2026_06_18.md
- SQ-03 offline Python discovery sweep with frequency-quality and loss-attribution table
- Green CI run tied to the exact source commit before any shadow-terminal attachment
- A3 remains paused; no broker action, profile arming, or runtime attach before evidence gates pass
