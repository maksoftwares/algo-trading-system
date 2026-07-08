# A1 XAU Regime Router V1 Exact-MT5 Preregistration

Generated: 2026-07-08

## Purpose

Implement the first small regime router from the reviewer direction. This pass tests the architecture, not a new optimized strategy:

- `R0 SHOCK`: no trade.
- `R1 UPTREND`: long specialist may trade.
- `R2 DOWNTREND`: short specialist may trade.
- `R3 COMPRESSION`: no trade for now.
- `R4 CHOP`: no trade.

The goal is to prove whether the existing long and short specialists behave better when armed only in their assigned regime.

This is research-only. It does not authorize demo/live trading.

## Router Definition

All decisions use completed bars only.

Priority cascade:

1. `SHOCK`
   - H1 completed-bar true range `>= 3.0 * H1 ATR14`, or
   - D1 ATR14 percentile `>= 95` over trailing 60 completed D1 bars.
2. `UPTREND`
   - D1 close above EMA20 above EMA50,
   - EMA20 and EMA50 rising versus 5 completed D1 bars ago,
   - condition persists for 2 completed D1 bars,
   - H4 EMA20 above EMA50 and rising confirms.
3. `DOWNTREND`
   - D1 close below EMA20 below EMA50,
   - EMA20 and EMA50 falling versus 5 completed D1 bars ago,
   - condition persists for 2 completed D1 bars,
   - H4 EMA20 below EMA50 and falling confirms.
4. `COMPRESSION`
   - D1 ATR percentile `<= 30`,
   - recent D1 box width average `<= 1.0 * D1 median range`.
5. `CHOP`
   - everything else.

## Exact-MT5 Component Runs

Run exactly two routed components:

1. `router_v1_r1_long_box2_prevhealth`
   - Existing H4/D1 box2 long specialist.
   - Existing previous-month health gate remains enabled.
   - Router mode: long allowed only in `R1 UPTREND`.

2. `router_v1_r2_short_v4_structural`
   - Existing V4 downside impulse/retest short specialist.
   - Existing structural/H1/H4 short filters remain enabled.
   - Router mode: short allowed only in `R2 DOWNTREND`.

## Recomposition Diagnostics

Report exactly these portfolios:

- `router_long_short_no_freq`: routed long + routed short only.
- `router_long_short_with_freq_observer`: routed long + routed short + existing `freq_step3_frontier` rows from the current best chart-context blend.

The frequency layer is diagnostic only. It cannot make the router pass unless its own in-regime edge is later proven.

## Acceptance Labels

Use `ROUTER_V1_ARCHITECTURE_REVIEW_CANDIDATE` only if:

- routed long has positive net,
- routed short has positive net or at least improves Q2-2026 protection,
- `router_long_short_no_freq` has positive full-window net,
- `router_long_short_no_freq` has positive Q2-2026 net or no Q2 exposure,
- max closed DD is not worse than the current best blend's `$958.86`.

Use `ROUTER_V1_SHADOW_ONLY` if the router proves useful but still needs frequency/future specialists.

Use `ROUTER_V1_NO_SURVIVOR` if routed components lose full-window or Q2 protection gets worse.

## Forbidden

- No hour/session/day/month masks.
- No new thresholds after seeing results.
- No RR tuning.
- No new source added besides the two routed components and diagnostic existing frequency rows.
- No demo claim.

