# Phase 2 Trend-Guarded Fix Observer

Status: `READY_FOR_OBSERVER_REVIEW`
Created: 2026-06-12
Reviewer verdict: `APPROVE_WITH_CHANGES_RESOLVED`

## Boundary

This is a repo-side observer copy only. It does not replace, edit, stop, restart, attach, or deploy any existing MT5 EA.

The new EA source is:

```text
xau-usd/xauusd-phase1/mt5/Experts/Phase2TrendGuardedFixObserver.mq5
```

It is telemetry-only:

```text
InpDryRunOnly=true
broker_action_allowed=false
no order placement
no live capital
no canonical Phase 2 approval
```

## Purpose

Review #8 found that the weak/repair XAUUSD lanes were allowed to short gold from fragile local M5 candle evidence while the higher-timeframe trend was rising. This observer measures the proposed fix without changing the running demo EAs.

The fix under observation is:

```text
Block XAUUSD SHORT would-signals when M15 EMA20 slope and H1 EMA20 slope are both rising.
Block XAUUSD LONG would-signals when M15 EMA20 slope and H1 EMA20 slope are both falling.
Log D1 bias, M15 slope, H1 slope, trend-veto decision, and fixed shadow decision.
```

Review #9 requested two evidence-quality changes before relying on the observer data:

```text
1. Use deterministic Dubai time from UTC + configured offset, not host local time.
2. Cache EMA indicator handles and log slope-unavailable rows explicitly.
```

Both are implemented in schema `trend_guarded_fix_policy_20260612_v2`.

## Observer Presets

Observer-only presets are prepared for XAUUSD:

```text
Phase2TrendGuardedFixObserver.breakout_retest_xauusd.set
Phase2TrendGuardedFixObserver.swing_breakout_retest_v0_xauusd.set
Phase2TrendGuardedFixObserver.symbol_normalized_round_retest_v0_xauusd.set
Phase2TrendGuardedFixObserver.round_number_retest_v0_xauusd.set
Phase2TrendGuardedFixObserver.session_extreme_retest_v0_xauusd.set
```

The first two are controls. The last three are the weak/repair targets.

## New Evidence Fields

The observer signal log adds:

```text
timestamp_dubai
legacy_shadow_action
legacy_shadow_reason
d1_bias
d1_bias_status
m15_ema20_slope_points
m15_ema20_slope_status
h1_ema20_slope_points
h1_ema20_slope_status
atr14_m5_points
estimated_cost_r
m15_ema20_distance_points
trend_veto_action
trend_veto_reason
fixed_shadow_action
fixed_shadow_reason
```

Use `fixed_shadow_action` as the candidate repair decision. Use `legacy_shadow_action` only as a comparison to the earlier broad shadow-blocking policy.

Rows with `m15_ema20_slope_status != OK` or `h1_ema20_slope_status != OK` are evidence-quality rows, not rule verdict rows. Exclude them from promotion metrics.

## Friday-Evening Review Question

For Friday evening observation, review:

```text
How many weak-EA XAUUSD SHORT would-signals were blocked by BLOCK_XAUUSD_SHORT_UPTREND_M15_H1?
How many kept signals would have aligned with M15/H1 trend?
Did the fixed observer reduce bad shorts without deleting all trade flow?
Were the controls affected in a way that would harm breakout_retest or swing_breakout_retest_v0?
```

Friday evening is only a pipeline smoke test. Promotion rule remains shadow-first: one full fresh forward week, replay/matched-actual outcomes, and explicit owner/reviewer approval are required before any runtime guard/router or broker-action change.
