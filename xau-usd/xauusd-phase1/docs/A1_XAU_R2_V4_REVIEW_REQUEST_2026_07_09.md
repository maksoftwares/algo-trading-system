# Review Request - XAUUSD R2 Short Specialist V4 Volatility Gate

Date: 2026-07-09

Please review the latest pushed GitHub commit for the XAUUSD exact-MT5 R2 short-specialist work.

## Context

We are building regime specialists:

- R1: long specialist for clean uptrend conditions.
- R2: short specialist for clean downtrend / downside continuation conditions.
- Future R3/R4: separate specialists or blockers for chop, compression, shock, and failed-breakdown regimes.

For this review, focus only on the R2 short specialist and the recent V4 volatility-gate layer. Do not assume this is demo-ready.

## Core Problem

The raw V1 R2 continuation leg was the best profit contributor among recent short additions, but it had a weakness:

- It traded too many weak/fake breakdowns.
- May 2026 was choppy and weak.
- June 2026 was clean downside continuation and profitable.

The goal of V4 was not to create a new strategy. It was to add one more layer to R2:

> Only allow R2 downside continuation when volatility/participation is high enough for a 2R breakdown trade to reasonably pay.

## Main Files To Review

Preregistrations:

- `xau-usd/xauusd-phase1/docs/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_PREREG_2026_07_09.md`
- `xau-usd/xauusd-phase1/docs/A1_XAU_R2_CONTINUATION_SHORT_V1_PREREG_2026_07_09.md`
- `xau-usd/xauusd-phase1/docs/A1_XAU_R2_CONTINUATION_SHORT_V2_REPAIR_PREREG_2026_07_09.md`
- `xau-usd/xauusd-phase1/docs/A1_XAU_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_PREREG_2026_07_09.md`
- `xau-usd/xauusd-phase1/docs/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_PREREG_2026_07_09.md`

Runners:

- `xau-usd/xauusd-phase1/scripts/run_a1_r2_pullback_rejection_short_v2_repair_exact.py`
- `xau-usd/xauusd-phase1/scripts/run_a1_r2_continuation_short_v1_exact.py`
- `xau-usd/xauusd-phase1/scripts/run_a1_r2_continuation_short_v2_repair_exact.py`
- `xau-usd/xauusd-phase1/scripts/run_a1_r2_continuation_short_v3_profit_guard_exact.py`
- `xau-usd/xauusd-phase1/scripts/run_a1_r2_continuation_short_v4_volatility_gate_exact.py`

EA:

- `xau-usd/xauusd-phase1/mt5/Experts/A1XauM5MomentumContinuationExecutor.mq5`

Summary evidence:

- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_EXACT_20260709.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V1_EXACT_20260709.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V2_REPAIR_EXACT_20260709.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_20260709.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709.md`

## Key Results

Best raw V1 combined book:

- `current_r1_best_r2_pullback_plus_r2_impulse_retest_body45`
- Trades: 1,060
- WR: 44.72%
- W/L: 3.0454
- PF: 2.4634
- Net: +$9,750.48
- Last 3 months: 88 trades, WR 55.68%, +$818.35

Best V4 combined book:

- `current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10`
- Trades: 678
- WR: 51.03%
- W/L: 2.6082
- PF: 2.7182
- Net: +$9,640.05
- Last 3 months: 59 trades, WR 62.71%, +$764.92
- April 2026: +$145.37
- May 2026: +$55.74
- June 2026: +$563.81

Tradeoff:

- V4 improved quality, WR, PF, and May behavior.
- V4 reduced full-window net by about $110 versus V1.
- V4 reduced last-three-month net by about $53 versus V1.
- V4 reduced trades from 1,060 to 678.

## Questions For Reviewer

1. Is the V4 ATR participation gate methodologically acceptable, or is it too close to recent-regime fitting?
2. Should we carry forward V1 raw as the profit leader, V4 as the quality leader, or both as shadow variants?
3. Does V4 genuinely solve the May-style failed-breakdown weakness, or does it simply trade less?
4. Is `InpMinAtrAbsoluteForEntry=4.50` defensible as a structural XAU participation threshold, or should this be expressed differently, such as ATR percentile or stop-distance participation?
5. Is combining ATR floor with daily loss stop `-10` acceptable, or does that stack too many filters for the current evidence?
6. What is the next best step: refine R2 further, freeze R2 and build a chop/failed-breakdown specialist, or build a router that chooses between V1/V4?
7. What additional diagnostics should be run before we ask for demo-readiness review?
8. Are there any code-level, exact-MT5, causality, artifact, or reporting problems in the runners or EA changes?

## Required Reviewer Output

Please return your answer as a Markdown document.

At the end, include a complete `.md` file body that we can save directly, with:

- strict verdict;
- findings ordered by severity;
- methodology assessment;
- result interpretation;
- recommended next action;
- exact questions that remain unresolved;
- whether V1, V4, both, or neither should be carried forward.

Suggested filename:

`A1_XAU_R2_V4_VOLATILITY_GATE_REVIEW_2026_07_09.md`
