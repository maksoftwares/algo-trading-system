# Forex MT5 USDJPY London120 M15 Range-Quality Guard Predeclaration

Date: 2026-07-04

Status: PREDECLARED_SINGLE_TEST

Scope: Forex only, USDJPY only, actual MT5 Strategy Tester only.

## Frozen Base Rule

- Candidate: `USDJPY london120_break_m15`
- EA: `ForexSessionBreakoutScout.mq5`
- Baseline: broker-server `06:00-08:00` range, M15 breakout decisions from `08:00` for four hours, both directions, RR `1.00`, fixed `0.01` lot.
- Baseline range filters remain unchanged: `InpMinRangeAtr=0.45`, `InpMaxRangeAtr=3.20`, `InpMinBodyFraction=0.30`.

## One Added Guard

Add one structural range-quality guard:

```text
Skip the signal if:

  (06:00-08:00 session_range) / previous_completed_D1_ATR(14) < 0.20
```

Implementation input:

```text
InpMinDailyRangeAtrFraction = 0.20
```

Rationale: a two-hour range below one-fifth of daily ATR is a compressed/chop-day setup where the later breakout is more likely to be noise than a real London volatility handoff. `0.20` is a round first-principles threshold chosen before running the test. No other threshold may be tried in this iteration.

## Test

Run exactly one actual-MT5 Strategy Tester replay:

- Symbol: `USDJPY`
- Chart period: `M5`
- Signal timeframe: `M15`
- Tester model: `Model=0` every tick
- Window: `2018-01-01` through `2026-07-02`
- Direction: both
- RR: `1.00`
- Fixed lot: `0.01`

## Acceptance Rule

This guard does not approve demo by itself. It can replace the v0 watchlist rule only if the one run satisfies all of the following:

- Full 2018-2026 PF remains at least `1.20`.
- Full 2018-2026 trade count remains at least 70% of baseline (`>= 801` of 1144 trades).
- Recent 2025-2026 PF improves to at least `1.15`.
- Trailing 12M PF after `+0.5` pip round-trip slippage stress is at least `1.15`.

If any condition fails, the guard is rejected for this candidate and the frozen v0 remains the watchlist lead. No second threshold, hour filter, direction cut, RR change, or session change is allowed from this result.
