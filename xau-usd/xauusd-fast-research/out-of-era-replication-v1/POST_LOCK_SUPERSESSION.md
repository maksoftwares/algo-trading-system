# Out-of-Era Replication V1 Supersession

Date: `2026-07-18`

Status: `LOCKED_BUT_NEVER_OPENED_SUPERSEDED`

V1 outcomes remain unopened. This definition lock must not be finalized or run.

Two correctness defects were identified before the 2010-2016 outcome period was
opened:

1. `NFP_FADE_RR2_EXACT` inherited the event timestamp-resolution defect recorded
   by `macro-event-reaction-replication-v2/POST_RUN_INVALIDATION.md`. Its prior
   near-survivor evidence is invalid and it is no longer eligible for exact
   replication.
2. `run_research.py` passes the normalized replay directory to
   `VerifiedSpotTickStore`. That verifier requires the Dukascopy storage root,
   where the acquisition manifests and raw hourly payloads live.

The locked definition is retained as an audit artifact. It is superseded by
`out-of-era-specialist-replication-v2`, which uses the corrected event logic on
contract-hashed exact-tick partitions, a unified multiplicity family, and no NFP
claim.
