# A1 XAU H4 Independent Observer Families Exact Probe Preregistration

Generated: 2026-07-05

## Purpose

The owner goal remains signal-level WR `>=50%`, realized average win / average loss `>=2.0`, and daily activity, with `90%+` active weekdays worth showing if the first two targets hold.

Recent work showed the existing A1 M5 derivative family has a stable tradeoff:

- high-WR variants compress W/L to roughly `1.0-1.6`;
- `2R` variants preserve payoff but collapse WR to roughly the high-30s;
- Step 3 portfolio composition improves frequency but still finds zero WR `>=50%` and W/L `>=2.0` rows.

This probe tests genuinely different entry premises already present as Phase 2B passive observer drafts, converted into exact MT5 Strategy Tester execution modes.

## Boundary

- Exact MT5 Strategy Tester only, isolated root `C:\MT5A1M5MomentumBacktest`.
- No live/demo runtime terminal, chart, preset, order, or position state may be changed.
- No tuning grid.
- No reviewer spend unless an exact row reaches WR `>=50%` and realized W/L `>=2.0`.

## Fixed Families

All variants use fixed `0.01` lot, market entry after the completed H4 decision bar, projected H4 stop distance, and `2.0R` target.

1. `d1_compression_h4_expansion_rr2p0`
   - D1 ATR(14) percentile over 252 completed D1 bars must be `<=30`.
   - Completed 5-D1 compression box average range must be no wider than the 20-D1 median range.
   - Completed H4 candle must close outside the D1 box with body/range `>=0.50`.
   - Stop distance is max(opposite side of D1 box, H4 ATR).

2. `h4_trend_pullback_d1_bias_rr2p0`
   - D1 EMA50/200 trend bias with EMA50 slope over 21 completed D1 bars.
   - Completed H4 pullback must touch EMA21 or EMA50 within `0.5 * H4 ATR`.
   - Completed H4 rejection candle must confirm in the D1 trend direction.
   - Stop is five-H4 swing extreme plus `0.25 * H4 ATR`.

3. `weekly_level_h4_rejection_rr2p0`
   - Completed H4 candle must reject previous-week or prior-four-week high/low.
   - Rejection wick must be at least `1.5x` candle body.
   - Stop is H4 wick extreme plus `0.25 * H4 ATR`.

## Metrics

The report must calculate manual signal/trade metrics from exported MT5 trade CSVs:

- trades, wins, losses, WR;
- gross profit/loss, PF, net PnL;
- realized average win / average loss;
- active weekday percentage over `2022-07-01 -> 2026-06-30`;
- max closed-equity drawdown;
- last-12-month WR/W-L;
- top-winner removal fields already produced by the owner metric helper.

## Decision

- `OWNER_GOAL_HIT_REVIEW_REQUIRED`: any row reaches WR `>=50%`, W/L `>=2.0`, and active weekdays `>=90%`.
- `CORE_SHAPE_HIT_FREQUENCY_GAP`: any row reaches WR `>=50%` and W/L `>=2.0`, but active weekdays `<90%`.
- Otherwise `REJECT_NO_OWNER_GOAL_HIT`.

Reviewer token is preserved unless one of the first two statuses occurs.
