# Future Experimental Demo Runtime Change Requests

```text
status: FUTURE_OWNER_DECISION_REQUIRED
runtime_change_authorized: false
not_implemented: true
```

This note lists possible future runtime changes suggested by the 2026-06-04 demo loss review. It is not an implementation ticket and does not authorize any change to currently running demo EAs.

## Current Owner Override

As of 2026-06-09, the owner instruction is that active experimental demo EAs should not be stopped from placing trades. Future runtime changes that would suppress valid signal-based demo orders are not allowed unless the owner explicitly asks for that exact runtime change.

See `DEMO_EA_EXECUTION_CONTINUITY_NOTE_2026_06_09.md`.

## Future-Only Requests

| Request | Purpose | Current State |
|---|---|---|
| Family-level one-event-one-trade guard | Prevent same-family variants from stacking duplicate entries with the same entry minute, symbol, direction, and volume. | Not implemented |
| XAUUSD morning/afternoon shadow block | Test whether the weak XAUUSD Morning/Afternoon clusters persist forward. | Measurement-only |
| `session_extreme_retest_v0` quarantine | Keep the provisional session-extreme candidate from being treated as a production-grade stream until it earns a larger forward sample. | Review-only |
| Candidate/session demotion policy | Convert repeated weak candidate/session clusters into a formal demotion rule. | Not implemented |

## Required Approval Before Any Future Runtime Change

- Owner approval for the exact rule.
- Reviewer acceptance of forward evidence.
- Separate implementation PR.
- MQL5 source review.
- Compile result with zero errors and zero warnings.
- Demo-only deployment plan.
- Rollback plan.
- Confirmation that canonical Phase 2 remains blocked unless measured-cost evidence is separately repaired.
