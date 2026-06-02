# Phase 0R Replacement Research Plan

Status: ACTIVE

Phase 0R exists because the breakout-retest family is cost-suspended under measured XAUUSD spread evidence.

## Objective

Find a lower-frequency, wider-stop, measured-cost-aware candidate that can pass Phase 0 without tuning a failed same-family retest variant.

## Priority Classes

| Priority | Candidate class | Notes |
| --- | --- | --- |
| 1 | D1 compression to H4 expansion | Volatility/compression family, not M5 retest |
| 2 | H4 trend pullback with D1 bias | Trend/pullback family with wider stops |
| 3 | Weekly/Daily level rejection with H4 confirmation | Level rejection, not retest continuation |
| 4 | Post-news delayed H1/H4 continuation | Cooldown after spread normalization only |
| 5 | Intermarket blocker research | Router/blocker first, not entry expert |

## Avoid For Now

- new M5 breakout-retest variants
- round-number retest variants
- session-extreme retest variants
- high-frequency scalping
- short-stop mean reversion
- news spike entries
- same strategy plus one extra filter

## First Active Draft

`h4_d1_volatility_contraction_expansion_v0` is drafted with a measured-cost structural precheck PASS. It still needs SHA256 registration, implementation, smoke testing, matrix testing, measured-cost revalidation, concentration/frequency audit, and adversarial review.
