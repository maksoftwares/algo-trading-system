# Project Status Summary

Generated UTC: `2026-06-18T07:44:36.784892Z`
Artifact generation base commit: `c9889cb2e7585be8c64cdea6800fb05726af3f52`
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

Artifact integrity: `PASS`
Runtime performance: `FAIL`
Runtime authorization: `A3_ENTRY_LANES_PAUSED`
Emergency pause report: `PASS`
Plain `933200` stopped: `true`
Improved `933300` paused: `true`
Tier1 compat `933400` paused: `true`
Profit-lock dry-run/disarmed: `true`

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

- XAUUSD_ROUND_FAMILY_FORWARD_WEEK_IMPACT_2026_06_xx.md
- XAUUSD_PROTECTED_BREAKOUT_CORE_FORWARD_WEEK_2026_06_xx.md
- XAUUSD_NON_ROUND_AFTERNOON_RESIDUAL_2026_06_xx.md
- A1/A2/A3 direct-history reconciliation after the forward week
- PHASE1_TEST_FAILURE_TRIAGE_2026_06_18.md review/cleanup
- A3_PER_MAGIC_ATTRIBUTION_2026_06_18.md reviewer follow-up
- A3 shadow-only signal-quality hypothesis with account-wide family mutex before any reactivation
