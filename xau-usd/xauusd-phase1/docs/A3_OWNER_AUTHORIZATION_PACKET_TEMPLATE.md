# A3 Owner Authorization Packet Template

Status: TEMPLATE_ONLY_NOT_SIGNED

Scope: A3 demo account login `1033669`; demo only; no live trading; canonical Phase 2 status unchanged.

Owner name:

Owner signature:

Signed at Dubai time:

## EAs Covered

- EA-T1: `Account3RoundRetestGuardedExecutor`, magic `933000`, comment `RDGUARD_V1`.
- EA-T2: `Account3RoundRetestStructuredExecutor`, magic `933100`, comment `RDSTRUCT_V1`.

## Required Acknowledgments

I acknowledge that A1 remains the treatment-control reference and that any A1 control loss, contamination, outage, terminal interruption, broker-history gap, duplicate-accounting defect, or material runtime change weakens or can invalidate the A3 comparison.

I acknowledge the A1 pause floor: if A1 equity falls below `1,500 AED` or A1 declines by `1,000 AED` from the evaluation-window start, the A1 control obligation pauses until owner review.

I acknowledge that if Guardian Stage B is not yet armed for A3 in week 1, EA-T1 and EA-T2 provide entry-blocking only. They do not contain position-closing calls and they do not flatten open positions.

I acknowledge that committed presets are non-executing and that any owner-authorized execution preset is local-only and must not be committed.

I acknowledge that A3 evidence is experimental demo evidence only and cannot be used as canonical Phase 2 or live-readiness evidence.

## Preflight References

- `A3_COMBINED_PREFLIGHT_REPORT.md`
- `A3_HYPOTHESIS_HASH_MANIFEST.json`
- `A3_DECOMMISSION_REPORT.md`
- `A3_DRY_RUN_SESSION_REPORT.md`
- `A3_KILL_SWITCH_DRILL_REPORT.md`

Owner must not sign until every mandatory T17 gate is PASS.
