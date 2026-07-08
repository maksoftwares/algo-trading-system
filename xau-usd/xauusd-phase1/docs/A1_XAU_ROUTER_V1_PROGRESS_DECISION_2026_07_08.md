# A1 XAU Router V1 Progress Decision

Date: 2026-07-08

Reviewed commit: `23d52b49f55cebc406c9d54f3b4e76cff079901c`

Status: `ROUTER_V1_SHADOW_ONLY`

## Decision

Router V1 is methodologically useful and remains research-only. It is not demo-ready.

Keep the current R1 uptrend book as the best shadow book:

- `box_plus_r1_pullback_long_v2_m15_session_09_15`

Current R1 book:

| Metric | Value |
| --- | ---: |
| Trades | 558 |
| WR | 50.18% |
| W/L | 2.7028 |
| PF | 2.7223 |
| Net | +$8,716.36 |
| Active weekdays | 16.11% |
| Max closed DD | $889.69 |
| Recent 3 months | 0 trades / $0 |
| Status | `SHADOW_ONLY` |

Do not promote this book because recent Apr-Jun 2026 had zero R1 trades and the system still has no solved non-R1 specialist.

## What Is Frozen

Freeze the failed R4 simple chop attempts:

- `r4_chop_failed_break_v1_sweep_reclaim`
- `r4_chop_daily_extreme_reclaim_v1_liquid`

Do not run more R4 M5 sweep/reclaim, daily-extreme reclaim, session repair, hour repair, day repair, month repair, or frequency-filler variants without a new review-approved preregistration.

Freeze the current R1 book as the benchmark for any R2 combination test. Do not delete or alter the R1 book to improve combined win rate.

## Recent Regime Evidence

The EA-side Router V1 snapshot audit showed Apr-Jun 2026 was not an R1 uptrend regime:

| Regime | Apr-Jun 2026 bar share |
| --- | ---: |
| Chop | 59.15% |
| Downtrend | 38.56% |
| Uptrend | 0.00% |
| Shock | 2.29% |

This explains why the current R1 specialist correctly stayed flat in the last three months. The missing coverage is non-R1, especially strict R2 downtrend and R4 chop.

## Next Specialist

The next allowed specialist test is strict R2 pullback-rejection short:

- preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V1_PREREG_2026_07_08.md`
- preregistration SHA256: `D30C883B5C6F0113D7249F1233ACF3C8D0F8DFE605C113F468F9D4B19CF9C057`

The R2 path must use:

- strict `REGIME_ROUTER_SHORT_R2_DOWNTREND_ONLY`;
- short only;
- failed relief rallies into H1 EMA20/EMA50;
- bearish M15 or H1 rejection confirmation;
- fixed 2R;
- no breakeven, partial close, trailing, profit lock, or RR change;
- no session, hour, day, month, or threshold grid;
- exact-MT5 only.

## Runtime Boundary

This decision note is research-only. It does not authorize demo, live, forward, broker-action, chart, preset, account, profile, or runtime changes.

The next implementation must preserve observer-safe/default-off behavior and must not loosen existing broker-action defaults.

## Commit Sequence

1. Commit this decision note and the R2 preregistration.
2. Implement the default-off EA signal.
3. Add the exact-MT5 runner for the two fixed R2 variants.
4. Run exact-MT5 once, write the report, and stop for reviewer review.

No MT5 run is allowed before the preregistration is committed and hashed.
