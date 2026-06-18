# Project Status Summary

Generated UTC: `2026-06-18T04:03:12.171209Z`
Commit: `bf6fbff3c8eaddb7bb33509b1c606ab37d8542ee`
Branch: `codex/a3-repair-lane-2026-06-13`

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

## Authorization Boundary

| Item | Value |
| --- | --- |
| Canonical Phase 2 PASS | `false` |
| Live trading authorized | `false` |
| Real capital authorized | `false` |
| A3 Tier-1 demo broker action | `OWNER_AUTHORIZED_DEMO_BROKER_ACTION` |

## Next Evidence Required

- XAUUSD_ROUND_FAMILY_FORWARD_WEEK_IMPACT_2026_06_xx.md
- XAUUSD_PROTECTED_BREAKOUT_CORE_FORWARD_WEEK_2026_06_xx.md
- XAUUSD_NON_ROUND_AFTERNOON_RESIDUAL_2026_06_xx.md
- A1/A2/A3 direct-history reconciliation after the forward week
- A3 Tier-1 compat order delta, PnL, and shadow trend-guard report
