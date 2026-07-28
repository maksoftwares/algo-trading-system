# EURUSD Neutral selective post-event verdict

## Verdict

`STOPPED_BEFORE_FORWARD_PNL_INSUFFICIENT_CAPACITY`

The fixed 0.42 selective learner is closed without loading its 2023-2026 trade
outcomes.

The screen retained 28 of 210 forward candidates. Counts were 11 in 2023,
five in 2024, nine in 2025, and three in 2026 H1. The latter two deficient
windows violate the frozen minimum of eight trades each, so even profitable
realizations would be too sparse for the requested chronological validation.

This is not a rejection of low-frequency demo trading. It is a rejection of a
three-trade six-month sample as evidence of profitability.

## Integrity

The outcome-blind screening artifact is:

`outputs/neutral_selective_post_event/SCREEN.json`

No `RESULT.json` exists and no forward P&L table is reported. Lowering the
threshold after observing this capacity distribution is prohibited for this
version.

Final status remains `RESEARCH_FAILURE_NOT_DEMO_READY`; Regime 1 remains
`CASH`.
