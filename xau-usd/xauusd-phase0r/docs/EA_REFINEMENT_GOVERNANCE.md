# EA Refinement Governance

Status: RESEARCH_GOVERNANCE_ONLY

This document defines how weak demo, passive observer, and Phase 0R findings may be used to improve the separate EA bench without damaging the locked-candidate discipline.

## Boundaries

Existing canonical and rejected candidates cannot be tuned in place.

Any improvement must create a new versioned hypothesis, such as a `*_v1` or `*_v2` draft, with its own pre-registered mechanics and falsification criteria.

The refinement lane may:

- diagnose cost_R, stop-distance, duplicate-family, session, and loss-quality problems
- generate reports from demo and passive observer logs
- propose draft vNext hypotheses
- recommend additional validation gates

The refinement lane may not:

- edit locked hypothesis files
- change canonical `breakout_retest` logic
- change rejected `*_v0` logic in place
- change Phase 1 dry-run behavior
- weaken Phase 2 readiness gates
- manually rewrite measured-cost reports
- add broker-side submission or position-management code

## Metric Priority

Raw win rate is not the target metric. The target metric is net expectancy in R after measured cost.

A candidate with a high win rate can still be structurally bad if:

- the average loss is too large
- the stop is too tight for measured spread
- duplicate-family rows create hidden concentration
- the edge appears only in one session or one tiny sample
- cost_R erases the gross edge

## Same-Family Rule

Same-family variants cannot be counted as diversification.

If `breakout_retest`, round-level retests, swing retests, and session-extreme retests fire together on the same bar, they must be treated as overlapping exposure unless a new registered hypothesis proves independent behavior.

## Demo Evidence Rule

Demo results may generate hypotheses. They may not directly patch locked candidates.

Allowed use:

- identify loss clusters
- identify high cost_R rows
- compare raw versus deduplicated exposure
- find candidate families that need wider stop geometry
- create draft vNext hypotheses

Disallowed use:

- tune a current candidate because a small demo sample lost money
- promote a candidate because a small demo sample made money
- use demo P/L to bypass measured-cost gates

## Required vNext Path

Every refinement must follow this path:

1. Diagnose failure mode from reports.
2. Write a new versioned draft hypothesis.
3. Lock the new hypothesis before testing.
4. Run Phase 0R gates from scratch.
5. Promote only if objective gates pass.

No draft vNext candidate is active until the owner explicitly approves registration.
