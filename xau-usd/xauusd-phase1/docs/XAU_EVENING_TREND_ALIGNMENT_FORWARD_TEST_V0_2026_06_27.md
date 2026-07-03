# XAU Evening Trend Alignment Forward Test V0

Status: PROPOSED_LOCK_PENDING_REVIEW

This is not a runtime deployment approval. It is a forward-test hypothesis
created after broker-joining available factor rows to realized XAU fills.

## Rule

For XAUUSD breakout_retest-family signals, mark TAKE only when:

- Dubai session is Evening 16:00-19:59.
- d1_trend_score_aligned >= 0.25.
- h1_ema20_slope_aligned_atr >= 0.35.
- Direction is already encoded as aligned in the factor columns.

All other signals are marked SKIP.

## Forward-Test Minimum

- Minimum 150 broker-joined forward trades or 6 full weeks, whichever comes later.
- Must be positive after removing the top 3 winners.
- Must not depend on one day for more than 35% of total net PnL.
- Must show PF >= 1.10 at interim review and PF >= 1.25 for promotion.
- Must remain account-transferable, not A1-only.

## Kill Rule

- Rolling 50-trade PF < 0.90.
- Any one day contributes more than 50% of cumulative net PnL.
- Second half PF is more than 0.30 below first half PF.
- A3 or clean-control evidence remains materially negative while A1 is positive.

## Guardrails

- No lot increase.
- No extra symbols.
- No threshold tuning on the same historical window.
- No runtime filter until separately approved by owner and reviewer.
