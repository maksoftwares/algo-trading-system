# Experimental Demo Authorization

Last updated: 2026-06-02

Overall status: PENDING_OWNER_AUTHORIZATION

This file is an authorization template and current-state record. It is not a Phase 2 approval and it does not authorize live trading.

## Current State

| Field | Value |
| --- | --- |
| Canonical Phase 2 readiness | FAIL |
| Experimental lane status | QUARANTINE_REVIEW_ONLY |
| Owner authorization for new hardened executor profile | PENDING |
| Allowed account logins | PENDING_OWNER_INPUT |
| Authorized candidates | `breakout_retest` by default only |
| Live trading authorized | false |
| Real capital authorized | false |

## Required Owner Fields Before Re-Attach

```text
owner:
decision_date_utc:
allowed_account_logins_csv:
authorized_candidates_csv:
experimental_authorization_token:
ack_phase2_not_authorized: true
ack_experimental_results_non_authoritative: true
ack_no_live_capital: true
ack_same_family_not_diversification: true
```

The token should only be supplied at runtime when the owner explicitly wants the experimental demo executor armed. Do not commit account numbers, secrets, credentials, or broker login details.

## Boundary

An experimental authorization does not close measured-cost revalidation, does not approve Phase 2, and does not permit live or real-capital trading.
