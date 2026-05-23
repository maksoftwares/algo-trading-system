# Review 5 Reflection And Action Plan

Date: 2026-05-23

## Verdict

Review #5 is accepted. The repo remains in Phase 1 dry-run / Phase 2 preparation only.

The main conclusion is that process quality is strong, but the edge family is still concentrated in level-and-pullback behavior. Same-family provisional passes are useful research evidence, but they do not diversify the system.

## Accepted Changes

| Finding | Response |
| --- | --- |
| N1 carry-forward: uninterrupted soak is not tracked | Implemented 72-hour active-market streak tracking in Phase 1 status, acceptance, readiness, soak history, and dashboard artifacts. |
| N2 carry-forward: +0.10R floor too soft | Raised the Phase 2 minimum measured-cost net expectancy floor to +0.15R. |
| S2: only one execution-eligible paper expert | Documented `breakout_retest` as the only first-slice paper stream; same-family variants are observer-only. |
| N4: slow reference level is not timeframe diversification | Added required hypothesis metadata and clarified that entry/decision timeframe controls classification. |
| N5: stop authoring same-family variants by default | Added a no-new-same-family forcing rule until a non-level-family result-producing candidate is completed. |
| Candidate universe sequencing | Added the 30-candidate Reality Check alpha-tightening rule. |
| Final review: Reality Check should use fixed-notional R | Re-ran D2 on monthly R series; `breakout_retest` remained winner with White p=0.0002 and max SPA p=0.0188. |

## Current Phase 2 Boundary

Phase 2 paper-mode implementation remains blocked until all of these are true:

- Phase 1 five-trading-day soak passes.
- Phase 1 uninterrupted active-market streak reaches at least 72 hours.
- Measured cost model passes.
- Measured-cost revalidation passes at or above +0.15R net expectancy.
- Phase 1 review index passes.
- VPS selection passes.
- Owner approval is signed with `minimum_net_expectancy_r >= 0.15`.

## Research Direction

The next candidate must not be another breakout-retest, retest-of-level, sweep-retest, or level-and-pullback variant.

Planned next candidate:

```text
d1_compression_h4_expansion_v0
```

Required shape:

- D1 directional state.
- H4 decision/entry timing.
- Expected median hold time greater than 24 hours.
- Expected trade count below 100 per year.
- No M5 entry trigger.
- Note: `d1_momentum_h4_pullback_v0` completed the initial forcing-function requirement and was rejected first-pass, so it must not be tuned in place.
- Note: `d1_volatility_expansion_reversal_v0` was also run as a true H4/D1 attempt and rejected first-pass.

## Still Wall-Clock Dependent

- Passive measured-cost collection.
- Five-day Phase 1 soak.
- 72-hour uninterrupted active-market streak.

No live orders, broker execution hooks, `OrderSend`, `CTrade`, or position modification are authorized.
