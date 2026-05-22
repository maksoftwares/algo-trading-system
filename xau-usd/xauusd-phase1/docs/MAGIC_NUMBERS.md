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

Rules:

- a disabled expert slot cannot be reactivated from an input file
- a rejected expert requires a new hypothesis version and new Phase 0 approval
- every future signal log must include the selected magic number, even in dry-run mode
- shell telemetry uses `910000`
