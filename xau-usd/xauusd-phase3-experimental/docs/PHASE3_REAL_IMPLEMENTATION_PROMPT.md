# Phase 3 Real Implementation Prompt

Status: DRAFT_FOR_FUTURE_USE

This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

Use this prompt only after Phase 1 acceptance and Phase 2 readiness are both PASS, measured-cost revalidation is PASS, VPS evidence is PASS, and the owner has signed explicit paper/demo approval.

```markdown
# Codex Task: Implement Real Phase 3 Paper-Shadow Layer

The repository has passed Phase 1 acceptance and Phase 2 readiness. Implement Phase 3 paper-shadow only.

## Hard boundaries

Do not add:
- OrderSend
- OrderSendAsync
- CTrade
- trade.Buy
- trade.Sell
- PositionOpen
- PositionModify
- PositionClose
- live capital behavior

## Scope

1. Add paper-shadow state machine using the approved Phase 2 ledger schema.
2. Consume the Phase 1 dry-run decision stream.
3. Generate paper-shadow events only for `breakout_retest` primary family rows.
4. Keep same-family variants observer-only unless separately approved.
5. Apply cost-aware blocks:
   - net after measured/projected cost `< +0.15R` => `SUSPEND_FAMILY`
   - net after measured/projected cost `< +0.1888R` => `COST_WATCH`
   - stop distance `<250` points => review/block unless owner explicitly accepts
   - spread near/above P95 => review/block
6. Deduplicate same-family observer rows.
7. Block direction or execution conflicts.
8. Write complete paper ledger rows for all would-open, block, state update, and close events.
9. Add runtime dashboard fields for family state, cost state, paper-shadow state, and last ledger write.
10. Add tests and safety audit coverage proving no broker-action code exists.

## Acceptance

- Paper-shadow layer compiles or tests cleanly.
- Safety audit PASS.
- Ledger schema verifier PASS.
- Dashboard freshness PASS.
- Phase 2 readiness remains the authority.
- No real broker order path exists.
```

## Note

If measured-cost revalidation later fails, do not use this prompt. Mark the family `COST_SUSPENDED` and return to research.
