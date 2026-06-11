# Hypothesis: xau_real_yield_regime_d1_trend_v0

candidate_id: xau_real_yield_regime_d1_trend_v0
candidate_version: v0
Hypothesis date: 2026-06-10
Hypothesis version: v0
Author / owner: Claude (independent technical reviewer) / maksoftwares
Expected trade count per year: 60-130
Expected cost-adjusted PF: 1.15-1.50
Expected losing-month percentage: 35%-55%
Expected worst single month: -6R to -14R
Expected R-multiple distribution: Many -1R initiative failures, steady 2.0R macro-aligned trend wins, no dependence on one outsized winner.
Expected max consecutive zero months: 3
expected_median_stop_points: 600
expected_cost_R_at_measured_50_75_spread: 0.08

## Mechanical Definition

All H1 windows use completed bars whose timestamp_utc equals the bar END converted to America/New_York local time with IANA timezone rules. Daily trend state comes from completed XAUUSD D1 bars only (last bar ending at or before the start of the New_York trade date): LONG-state when D1 EMA20 is above D1 EMA50, SHORT-state when below. Real-yield regime comes from the macro_proxy frame (FRED DFII10, `real_yield_10y`): using the last observation at or before the start of the New_York trade date, the regime is the sign of the change over the prior 20 observations - falling real yields permit LONG only, rising permit SHORT only; zero change permits nothing. A setup exists only when trend state and yield regime agree. The trigger is the first H1 bar with New_York bar-end time 10:00, 11:00, or 12:00 that closes in the agreed direction, closes beyond the previous H1 bar's high (LONG) or below its low (SHORT), and has body at least 35 percent of its high-low range. Entry is market at the next available simulator quote. Stop distance is the maximum of 1.5 times H1 ATR(14) at the trigger bar and 3.75 price units (375 points). Target is a fixed 2.0R. Stop or target exits only, one position at a time, at most one setup per New_York date. Implementation: `src/phase0/strategies/xau_real_yield_regime_d1_trend_v0.py` (research registry only; not an approved EA).

## Expected Behavior

Lower frequency than the unconditioned trend design (the regime gate removes roughly half of trend days); losing clusters in months where gold decouples from real yields; per-cell samples should clear 40 comfortably on the full windows. Gate selection follows locked `docs/PHASE0_WAVE2_GATE_SET_V1.md` (frequency-aware; this file is registered as a later wave referencing that gate set), on the locked full per-broker windows with Pepperstone owner-accepted partial and true holdout untouched.

## Why This Hypothesis Should Exist

Gold is a zero-yield real asset whose discount-rate channel to 10-year real yields is one of the most documented macro relationships in the literature. The 2026-06-10 locked runs measured (a) weak unconditional decade momentum (PF 1.05-1.28) and (b) an unconditioned NY-window initiative entry at PF ~1.0; the claim under test is that requiring the standing gold trend to be CONFIRMED by the real-yield trend isolates the macro-funded subset of trend days from positioning noise. No rejected candidate combined daily trend, real-yield confirmation, and funded-window execution; the nearest rejected relatives are h4_real_yield_proxy_momentum_v0 and the h1_real_yield shock designs (REJECTED_FIRST_PASS - shock-response mechanics at intraday scale, disclosed as adjacent negative evidence), plus xau_d1_trend_ny_window_continuation_v0 (FAIL_REJECTED_VERSION_FINAL 2026-06-10 - the unconditioned ancestor of the entry leg; this is a NEW design whose added mechanism is the macro confirmation, not a parameter change to that version).

## What Would Falsify It

The locked PHASE0_WAVE2_GATE_SET_V1 selection: fewer than 7 of 9 PF cells at 1.30, any cell under 40 trades, concentration breach (absolute caps at high frequency, normalized G4 at low frequency), drawdown or activity breach, p95-to-best PF ratio under 0.50, G7 cross-venue floor under 1.20, G8 modern-era failure, G9B realized cost breach, or adversarial review finding a logic mismatch. A failure is final for v0 under NO_TUNING_RULES.md; no post-result rescue of any kind.

status: LOCKED
