# A1 XAU R2 Pullback-Rejection Short V1 Exact-MT5 Preregistration

Date: 2026-07-08

## Purpose

Build a strict Router V1 R2 short specialist for failed relief rallies inside structural XAUUSD downtrends.

This is not a generic breakdown-continuation retry. Prior short work showed that chasing downside breaks tends to create low win rate, high payoff, and weak standalone durability. This test waits for:

- strict Router V1 `R2_DOWNTREND`;
- relief rally into H1 EMA20 or H1 EMA50;
- completed bearish rejection candle;
- short-only entry;
- fixed 2R target.

The current R1 book remains the best uptrend shadow book. This R2 test is a separate specialist and cannot promote the whole system to demo by itself.

## Runtime Boundary

Research-only exact-MT5 backtest.

This preregistration does not authorize demo, live, forward, broker-action, chart, preset, account, profile, or runtime changes. Existing live/demo safety defaults must remain unchanged.

## Router Gate

Use only strict Router V1 R2:

- `InpRegimeRouterMode=REGIME_ROUTER_SHORT_R2_DOWNTREND_ONLY`

R2 definition remains unchanged from Router V1:

- D1 close[1] < D1 EMA20[1] < D1 EMA50[1].
- D1 EMA20[1] <= D1 EMA20[6].
- D1 EMA50[1] <= D1 EMA50[6].
- D1 condition persists for 2 completed D1 bars.
- H4 EMA20[1] < H4 EMA50[1].
- H4 EMA20 and EMA50 are falling.

No relaxed R2, non-uptrend router, H4-confirm removal, or priority-cascade change is allowed.

## Direction

Short only:

- `InpDirectionMode=MOMENTUM_SHORT_ONLY`

## New EA Signal

Add default-off signal mode:

- `SIGNAL_R2_H1_PULLBACK_REJECTION_SHORT = 21`

Add safe/default-off inputs:

- `InpR2PullbackConfirmTimeframe = 15`
- `InpR2PullbackLookbackBars = 6`
- `InpR2PullbackH1FastEmaPeriod = 20`
- `InpR2PullbackH1SlowEmaPeriod = 50`
- `InpR2PullbackTouchAtr = 0.25`
- `InpR2PullbackStopBufferAtr = 0.25`
- `InpR2PullbackMinBodyFraction = 0.35`
- `InpR2PullbackCloseLocation = 0.35`

All signal logic must use completed bars only. Bar 0 is forbidden for signal and regime decisions.

## Common Trade Rules

- Symbol: XAUUSD.
- Window: 2022-07-01 through 2026-06-30.
- Fixed lot: 0.01.
- Risk/reward: fixed 2.00R.
- No breakeven.
- No partial close.
- No trailing.
- No profit lock.
- Existing spread and estimated-cost controls remain active.
- Existing isolated MT5 tester root must be used.
- No demo/live runtime state may be touched.

## Variant A: r2_pullback_short_m15_confirm

Hypothesis: in strict R2 downtrend, a short edge appears after a relief rally reaches the H1 EMA20/EMA50 zone and then rejects bearish on M15.

Rules, completed bars only:

1. Router state is `R2_DOWNTREND`.
2. Direction is short only.
3. H1 trend confirms: H1 close[1] < H1 EMA20[1] < H1 EMA50[1], and H1 EMA20[1] <= H1 EMA20[6].
4. In the last 6 completed M15 bars, the M15 high touches within `0.25 * H1 ATR14` of H1 EMA20 or H1 EMA50.
5. Confirmation candle is the latest completed M15 candle.
6. Confirmation candle must be bearish: close < open.
7. Confirmation close must be below H1 EMA20.
8. Confirmation body/range must be >= 0.35.
9. Confirmation close location must be <= 0.35.
10. Stop is above the pullback swing high plus `0.25 * M15 ATR14`.
11. Target is fixed 2R.

If the existing tester framework only supports market-style execution, entry may occur through the existing market execution path after the completed confirmation bar. Do not add pending-order behavior for this prereg.

## Variant B: r2_pullback_short_h1_confirm

Hypothesis: M15 rejection may be too noisy; slower H1 confirmation may produce higher quality with lower frequency.

Rules, completed bars only:

1. Router state is `R2_DOWNTREND`.
2. Direction is short only.
3. H1 trend confirms: H1 close[1] < H1 EMA20[1] < H1 EMA50[1], and H1 EMA20[1] <= H1 EMA20[6].
4. In the last 3 completed H1 bars, the H1 high touches within `0.25 * H1 ATR14` of H1 EMA20 or H1 EMA50.
5. Confirmation candle is the latest completed H1 candle.
6. Confirmation candle must be bearish: close < open.
7. Confirmation close must be below H1 EMA20.
8. Confirmation body/range must be >= 0.35.
9. Confirmation close location must be <= 0.35.
10. Stop is above the H1 pullback swing high plus `0.25 * H1 ATR14`.
11. Target is fixed 2R.

## Forbidden Variants

Do not add or run:

- EMA20-only or EMA50-only variants.
- alternate ATR touch thresholds.
- M5 confirmation.
- session, hour, day, or month filters.
- body-threshold grids.
- close-location grids.
- alternate D1 or H4 gates.
- relaxed R2 or non-uptrend router.
- RR changes.
- breakeven, partial close, trailing, or profit lock.
- combined portfolio optimization.

## Standalone Gates

A variant becomes a standalone R2 review candidate only if all are true:

- trades >= 80;
- WR >= 45% for watchlist;
- WR >= 50% for true pass;
- W/L >= 1.90;
- PF >= 1.25;
- stress PF after -$0.30/trade >= 1.15;
- stress net > 0;
- top 10 winning trades removed net > 0;
- top 3 winning days removed net > 0;
- no single month contributes more than 35% of net.

Conditional period gates:

- If trades exist in June 2026, June 2026 net must be >= 0.
- If trades exist in Apr-Jun 2026, recent 3 months net must be >= 0.
- If trades exist in 2023 and 2024, combined 2023+2024 net must be >= 0.
- A period with zero trades is marked no exposure, not failed.

## Combined Gates

Combine each R2 result only with the current R1 book:

- `box_plus_r1_pullback_long_v2_m15_session_09_15`

No R4 rows. No frequency filler.

Reference current R1 book:

- trades: 558
- WR: 50.18%
- W/L: 2.7028
- PF: 2.7223
- net: +$8,716.36
- active weekdays: 16.11%
- max closed DD: $889.69
- recent 3 months: 0 trades / $0
- best month share: 30.92%

Combined pass requires all:

- full-window net > current R1 book net;
- recent 3 months trades > 0;
- recent 3 months net >= 0;
- WR >= 49%;
- W/L >= 2.00 or stress W/L >= 1.90;
- PF >= 2.00;
- max closed DD not worse than current R1 by more than 10%;
- top 10 winning trades removed net > 0;
- top 3 winning days removed net > 0;
- best-month share <= current R1 best-month share.

## Decision Labels

Use exactly these labels:

- `R2_PULLBACK_REJECTION_SHORT_V1_REVIEW_CANDIDATE`: standalone and combined gates pass.
- `R2_PULLBACK_REJECTION_SHORT_V1_SHADOW_ONLY`: standalone is positive but combined fails.
- `R2_PULLBACK_REJECTION_SHORT_V1_NO_SURVIVOR`: both variants fail.
- `R2_PULLBACK_REJECTION_SHORT_V1_INVALID_TEST`: implementation or methodology is invalid.

Invalid test examples:

- wrong router mode;
- non-strict R2 used;
- exact-MT5 output missing;
- EA uses bar 0 for signal;
- session, hour, day, or month filter accidentally enabled;
- RR changed;
- breakeven, partial close, trailing, or profit lock enabled;
- runtime/demo state changed.

## Stop Path

Stop the R2 pullback-rejection path if both variants fail any of:

- WR < 40%;
- PF < 1.10;
- stress net <= 0;
- top 10 winning trades removed net <= 0;
- top 3 winning days removed net <= 0;
- combined W/L < 1.90;
- combined PF < 1.80.

If stopped:

- do not relax R2;
- do not tune short thresholds;
- do not run R2 session/hour/month filters;
- downgrade R2 shorts to hedge-only or observer-only;
- move to R3 compression breakout only after reviewer signoff.

## Required Report Sections

The exact-MT5 report must include:

1. Scope and runtime boundary.
2. Preregistration path and SHA256.
3. EA source commit hash.
4. Exact tester input hash or full parameter table.
5. MT5 raw component evidence path.
6. Standalone results table.
7. Combined results table.
8. Router block reasons.
9. Yearly table.
10. Monthly table.
11. Recent 3 months table.
12. June 2026 table.
13. 2023+2024 table.
14. Top10-removed net.
15. Top3-days-removed net.
16. Max DD.
17. Best-month share.
18. Failed checks.
19. Verdict label.
20. Next allowed action.

## Validation Checks

Required static checks:

- new signal mode exists and is default-off;
- no demo/live defaults loosened;
- no `OrderSend` behavior changed outside the existing execution path;
- no breakeven, partial close, or trailing enabled by the test runner;
- R2 runner sets `REGIME_ROUTER_SHORT_R2_DOWNTREND_ONLY`;
- R2 runner does not set hour/day/month/session filters;
- R2 runner uses fixed RR 2.00;
- report includes prereg SHA256;
- report includes standalone and combined gates;
- R2 test emits router block reasons.

Required implementation checks:

- signal uses completed bars only;
- no bar 0 for signal or regime decision;
- H1 EMA/ATR values use completed H1 bars;
- M15/H1 confirmation uses completed confirmation bar;
- pullback lookback uses completed bars only;
- stop distance is positive before signal is accepted;
- router block reason is logged when blocked.

## Next Allowed Action

After this preregistration is committed and hashed, implement the default-off EA signal and the exact-MT5 runner. Run only the two fixed variants above, then stop after the first R2 exact-MT5 report and send for review.
