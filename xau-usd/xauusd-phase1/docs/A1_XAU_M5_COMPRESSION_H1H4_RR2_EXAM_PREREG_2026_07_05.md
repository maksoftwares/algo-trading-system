# A1 XAU M5 Compression H1+H4 2R Exam Preregistration

Generated UTC: `2026-07-05`

## Purpose

Freeze the only remaining-built-in M5 design-window candidate and run one exact MT5 Strategy Tester exam on the recent window.

## Boundary

- Instrument: `XAUUSD`
- Timeframe: `M5`
- Exact tester root: `C:\MT5A1M5MomentumBacktest`
- EA: `A1XauM5MomentumContinuationExecutor`
- Design source: `A1_XAU_M5_REMAINING_BUILTIN_2R_DESIGN_201601_202112`
- Exam window: `2022.07.01 -> 2026.06.30`
- No optimizer.
- No live/demo chart attach.
- No broker/runtime state changes.
- No threshold edits after seeing the exam.

## Frozen Candidate

`compression_long_h1h4_rr2p0`

- Signal mode: compression expansion
- Direction: long only
- Trend filters: H1 and H4 enabled
- Risk/reward: `2.00`
- Max estimated cost R: `0.15`
- Stop ceiling: disabled
- Max trades/day: `24`
- Cooldown: `0`
- One-position-per-magic: `false`
- Max open positions: `16`
- Compression lookback bars: `8`
- Compression max range ATR: `1.20`
- Compression break ATR multiple: `0.10`

## Decision Rules

- `EXAM_OWNER_HIT_REVIEW_REQUIRED`: WR >= 50%, average win/loss >= 2.0, and active weekdays >= 90%.
- `EXAM_CORE_SHAPE_SPARSE_CLUE`: WR >= 50% and average win/loss >= 2.0, but active weekdays < 90%.
- `EXAM_NEAR_FRONTIER_CLUE`: WR >= 48%, average win/loss >= 1.8, active weekdays >= 30%, and PF >= 1.30.
- Otherwise reject this branch for owner-goal pursuit.

Any non-reject remains research-only until a reviewer signs off and a full robustness suite is complete.
