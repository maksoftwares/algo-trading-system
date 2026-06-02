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

## Latest Closed Drafts

`h4_d1_volatility_contraction_expansion_v0` was SHA256-registered, implemented, smoke-tested, and real matrix-tested. It passed measured-cost structural precheck but is `REJECTED_FIRST_PASS` because 0/9 PF cells reached 1.30 and Dukascopy was negative across costs.

`h4_d1_contraction_trend_continuation_v0` was SHA256-registered, implemented, smoke-tested, and real matrix-tested. It passed measured-cost structural precheck but is `REJECTED_FIRST_PASS` because every real matrix cell had PF below 1.0.

Next action: continue Phase 0R with a new pre-registered candidate, preferably from a stronger data class than OHLC-only range/ATR/EMA structure.
