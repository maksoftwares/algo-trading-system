# Magic Number Plan

Phase 1 reserves magic-number bands before any expert is enabled.

| Band | Purpose | Range |
| --- | --- | --- |
| Core shell | dry-run shell, router, lifecycle telemetry | 910000-910099 |
| Breakout-Retest | future approved expert slot | 910100-910199 |
| Swing Breakout-Retest v0 | same-family future expert candidate slot | 910110 |
| Trend Pullback | rejected v1 slot, disabled | 910200-910299 |
| Range MR | rejected v1 slot, disabled | 910300-910399 |
| Experimental | future hypotheses after separate Phase 0 | 911000-911999 |
| A3 RDGUARD V1 | Account 3 round-retest guarded executor, demo-only repair lane | 933000-933099 |
| A3 RDSTRUCT V1 | Account 3 round-retest structured executor, demo-only repair lane | 933100-933199 |
| A3 breakout plain | Account 3 breakout plain control lane, demo-only | 933200-933299 |
| A3 breakout improved | Account 3 breakout improved treatment lane, demo-only | 933300-933399 |
| A3 breakout Tier1-compatible | Account 3 breakout repair copy, dry-run/observer until separate owner packet | 933400-933499 |

Rules:

- a disabled expert slot cannot be reactivated from an input file
- a rejected expert requires a new hypothesis version and new Phase 0 approval
- every future signal log must include the selected magic number, even in dry-run mode
- shell telemetry uses `910000`
- A3 bands are demo-only and do not change canonical Phase 2 lifecycle status
- `933400` must not be broker-action armed until an owner packet, MetaEditor compile proof, startup proof, and dry-run observer validation are recorded
