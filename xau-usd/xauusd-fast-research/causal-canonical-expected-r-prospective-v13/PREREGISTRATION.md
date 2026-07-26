# Expected-R V13 Prospective Preregistration

## Purpose

This package performs the missing forward confirmation of the frozen Expected-R
V11 research policy. It is locked before `2026-07-27T00:00:00Z`.

## Frozen population

Every post-boundary deterministic candidate emitted by the nine V60 source
streams is captured. The R1 box and R1 pullback streams share the historical
`R1_UPTREND` family. `R5_TRANSITION` remains absent because it is not in the V60
executable source set.

## Frozen treatment

1. Build the same B1 deterministic and B2 XAU feature columns used by V10.
2. Use Capital.ComMena demo ticks from account `1033030`, making cross-broker
   feature portability an explicit part of the test.
3. Apply the byte-bound V10 Expected-R model and its frozen family thresholds.
4. If mandatory features are unavailable, abstain and retain the candidate.
5. Resolve every retained and vetoed candidate independently from executable
   bid/ask ticks under the original Step 3 label geometry and stress costs.
6. Route the take-all baseline and frozen retained scenario independently
   through the locked V60 source, sleeve, daily-entry, overlap, event,
   account-risk, directional-risk, and V57 same-direction 120-minute
   post-realized-loss cooldown constraints.
7. Compare only the routed account portfolios. Raw candidate economics are not
   accepted as deployment evidence.

The evaluator records individual scores and counterfactual outcomes. Aggregate
economics remain sealed until a locked stage endpoint is complete. Validation
requires at least 40 resolved model-scored candidates across five families.
Confirmation can open only after validation passes and requires 120 new
candidates across six families. Both stages enforce minimum selected counts,
per-family coverage, winner-removal stress, and deterministic weekly-block
bootstrap lower confidence bounds.

## No trading authority

This is offline prospective research, not ML shadow trading. It does not write
inside an MT5-consumable directory, does not alter V60, does not send a score to
an EA, and cannot place, modify, or close an order. A pass does not authorize
demo or live use.
