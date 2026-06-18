# A3 Tier-1 Compat Governance Override - 2026-06-17

Status: `OWNER_APPROVED_DEMO_ONLY_OVERRIDE`

This note records the governance difference between the reviewer recommendation and the owner decision for the A3 Tier-1 compatibility lane.

## Reviewer Recommendation

The reviewer recommended attaching `A3_BREAKOUT_TIER1_COMPAT_V1` as observer/dry-run first, then considering broker-action demo attachment only after observer evidence was reviewed.

## Owner Decision

The owner explicitly approved direct demo broker-action attachment instead of observer-only attachment.

Approved scope:

| Field | Value |
| --- | --- |
| Account | `1033669` |
| Server | `Capital.ComMena-Demo` |
| Symbol | `XAUUSD` |
| EA | `Account3BreakoutTier1CompatExecutor` |
| Magic | `933400` |
| Comment | `A3_BREAKOUT_TIER1_COMPAT` |
| Fixed lot | `0.01` |
| Mode | Demo broker-action only |

## Boundaries

This override does not authorize:

- canonical Phase 2 approval,
- live trading,
- real capital,
- additional symbols,
- lot increases,
- changing A1/A2 lanes,
- changing the A1 round-family quarantine,
- promoting the shadow trend guard into a hard runtime guard.

## Evidence Requirement

Because the dry-run stage was skipped by owner decision, the forward-week A3 Tier-1 evidence is the real validation, not a formality.

Required evidence:

- direct MT5 history for account `1033669`,
- `933400` order delta and PnL,
- whether the lane actually trades in the server-hour `12-15` window,
- shadow trend-guard would-block review,
- duplicate/family-stack review against A3 plain/improved lanes.
