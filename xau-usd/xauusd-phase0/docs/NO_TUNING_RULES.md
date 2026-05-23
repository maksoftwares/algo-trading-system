# No-Tuning Rules

Phase 0 is evidence gathering, not optimization.

Forbidden after results exist:

- adding filters to rescue failed cells
- changing parameters to improve PF
- excluding outlier trades
- changing data windows
- treating pending manual reviews as passes
- touching the true holdout period without explicit approval

If a hypothesis changes, create a new version and re-register it before any new result-producing run.

## Same-Family Forcing Rule

No new same-family breakout-retest or level-and-pullback candidate may be authored until at least one genuinely non-level-family candidate has been:

- written as a complete hypothesis with the required timeframe metadata
- SHA256 registered before testing
- implemented as a disabled research candidate
- run through a result-producing first pass
- recorded as PASS, FAIL, or PROVISIONAL with no post-result tuning

Same-family provisional passes may be manually reviewed, but they must not be marketed as diversification and must not be added to the execution roadmap while this forcing rule is open.
