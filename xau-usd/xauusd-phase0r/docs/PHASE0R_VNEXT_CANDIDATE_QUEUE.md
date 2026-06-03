# Phase 0R vNext Candidate Queue

Status: DRAFT_QUEUE_ONLY

Entries below are proposal sketches or draft registrations. A registered draft is still not locked, not active, not an observer, and not a Phase 0R result-producing test subject.

## Queue

| proposed_candidate | parent | status | main failure addressed | registration_allowed |
| --- | --- | --- | --- | --- |
| `round_number_retest_v1_cost_aware` | `round_number_retest_v0` | DRAFT_UNREGISTERED | Same-family duplicate exposure and cost_R sensitivity | no |
| `session_extreme_retest_v1_htf_confirmed` | `session_extreme_retest_v0` | DRAFT_REGISTERED_NOT_LOCKED | Weak provisional win rate and session-context losses | approved |
| `h4_d1_contraction_expansion_v1_directional` | `h4_d1_volatility_contraction_expansion_v0` | DRAFT_UNREGISTERED | Cost-viable but no durable first-pass edge | no |
| `gld_flow_reversal_v2_satellite` | `h4_gld_etf_flow_reversal_v0` | DRAFT_UNREGISTERED | Interesting cells but low trade count and concentration risk | no |
| `macro_context_router_filter_v0` | failed macro/intermarket standalone candidates | DRAFT_UNREGISTERED | Standalone entry weakness, possible context value | no |

## Candidate Notes

### `round_number_retest_v1_cost_aware`

Purpose: test whether round-number retests survive only when stop geometry and measured spread leave enough net R.

Pre-registration requirements:

- median stop target at least 500 points
- explicit p95 cost_R ceiling
- same-family duplicate audit
- no reuse of v0 parameters as hidden tuning

### `session_extreme_retest_v1_htf_confirmed`

Purpose: keep the session-extreme idea only if higher-timeframe context explains why a reversal should exist.

Registration status: DRAFT_REGISTERED_NOT_LOCKED.

Pre-registration requirements:

- higher-timeframe rejection condition
- session bucket survival gate
- loss-quality review before promotion
- no direct rescue of the weak v0 sample

### `h4_d1_contraction_expansion_v1_directional`

Purpose: add a pre-registered directional mechanism to a cost-viable but edge-weak compression-release idea.

Pre-registration requirements:

- directional bias rule justified before testing
- no wick-only breakout trigger
- H4/D1 hold-time and stop-distance assumptions
- standard Phase 0R matrix and decile gates

### `gld_flow_reversal_v2_satellite`

Purpose: treat GLD-flow behavior as a possible satellite or context feature instead of a primary EA.

Pre-registration requirements:

- satellite classification before testing
- concentration review in R terms
- separate gate expectations from primary EAs
- no standalone capital-allocation assumption

### `macro_context_router_filter_v0`

Purpose: test whether failed macro/intermarket candidates can reduce bad exposure as a context router.

Pre-registration requirements:

- no entry generation
- blocked-opportunity audit
- out-of-sample impact review
- proof that the filter does not simply remove losing historical rows by hindsight

## Activation Rule

`session_extreme_retest_v1_htf_confirmed` is registered as a draft hypothesis only. It may not be locked, run, observed, or promoted until the owner explicitly approves the next gate.

All other queue entries may not be registered, run, observed, or promoted until the owner explicitly approves that specific candidate for registration.
