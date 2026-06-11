# Hypothesis: xau_d1_trend_ny_window_continuation_v0

candidate_id: xau_d1_trend_ny_window_continuation_v0
candidate_version: v0
mechanic_family: Daily-trend continuation gated to the funded NY-morning window with H1 initiative confirmation
same_family_as_breakout_retest: no
entry_decision_timeframe: H1
execution_timeframe: H1 signal timestamp with M5 simulator sequencing only
expected_median_hold_hours: 3-18
expected_decisions_per_week: 2-4
expected_trades_per_year: 120-200
expected_median_stop_points: 600
expected_cost_R_at_measured_50_75_spread: 0.08
event_clock_id: xau_comex_gold_settlement
market_behavior_thesis: Gold's multi-day directional state persists weakly across the decade, but its per-trade economics are only attractive when the entry coincides with funded participation; taking daily-trend risk exclusively when the NY-morning window confirms with an initiative H1 bar combines the two independently measured effects - weak decade-scale momentum and a 2x-range, half-cost execution window.
participants_or_flow_mechanism: Macro and positioning flows that drive multi-day gold trends are executed predominantly during US hours (COMEX depth, data releases, benchmark fixes); an H1 bar in the NY morning that closes beyond the prior bar's extreme in the direction of the daily trend is the funded flow re-expressing the standing trend rather than off-session drift.
mechanical_entry_rules: All windows are defined on completed H1 bars whose timestamp_utc equals the bar END converted to America/New_York local time with IANA timezone rules (DST-correct year-round). The daily trend state is computed from completed D1 bars only, using the last D1 bar whose bar end is at or before the start of the trade's New_York calendar date: LONG-only state when D1 EMA20 is above D1 EMA50, SHORT-only state when below, no setup when equal or unavailable. The trigger is the first H1 bar with New_York bar-end time 10:00, 11:00, or 12:00 that closes in the trend direction, closes beyond the previous H1 bar's high (LONG) or below its low (SHORT), and has body at least 35 percent of its high-low range. Entry is market at the next available simulator quote after the trigger bar completes, in the trend direction. At most one setup per America/New_York calendar date.
mechanical_exit_rules: Stop-loss or take-profit only, one position at a time, Phase 0 simulator sequencing; no discretionary, time-based, or trailing exits.
stop_model: Stop distance is the maximum of 1.5 times H1 ATR(14) at the trigger bar and 3.75 price units (375 points); placed adverse to the entry direction from the entry price.
target_model: Fixed 2.0R take-profit from entry using the realized stop distance.
risk_model: Fixed-notional, cost-adjusted R-series evaluation through the Phase 0 research matrix.
forbidden_filters: No new session filter, news filter, volatility filter, level filter, additional direction filter, cost-model cherry-pick, stop change, target change, or rescue rule after results.
falsification_criteria: Reject this version if the locked PHASE0_WAVE2_GATE_SET_V1 selection fails (frequency-aware standard or low-frequency gates, including the carried-over G7 cross-venue floor, G8 modern-era integrity, and G9B realized measured cost), or adversarial review finds a logic mismatch.
ancestry_comparison: d1_momentum_h4_pullback_v1_fullhist, w1_d1_momentum_continuation_v1_fullhist, and h4_inside_bar_d1_momentum_breakout_v1_fullhist are FAIL_REJECTED_VERSION_FINAL (2026-06-10, locked full-window runs); they share the daily-trend ingredient but used H4/D1 pattern entries with no participation timing, and their failures count as evidence against naked decade-scale momentum. This is a NEW design, not a rescue: the entry mechanism (H1 initiative bar inside the NY-morning window), stop scale, target, and frequency profile are all different, and the mechanism argument is the measured funded-window economics, which none of the rejected versions used. breakout_retest is mechanically separate (no level, no retest, no M5 trigger here).
data_window: Full available offline broker windows ending no later than 2025-06-30; Capital.com and Dukascopy PASS full target window; Pepperstone owner-accepted partial 2019-01-02 through 2021-12-31 with DATA_WINDOW_ASYMMETRY_PRESENT.
true_holdout_exclusion: true
expected_failure_modes: Trend-state whipsaw in transition months, initiative bars that mark morning exhaustion rather than continuation, EMA-state lag entering major reversals, payoff shortfall at 2.0R in compressed-volatility years, or the same venue disagreement that split Capital.com and Pepperstone on 2019-2021.
D2_family_label: xau_d1_trend_ny_window_family
author: Claude (independent technical reviewer, Wave-2 second-EA research)
created_utc: 2026-06-10T18:15:00+00:00
sha256_hash: SELF_HASH_EXCLUDED
status: LOCKED

## Event Clock

America/New_York civil time via IANA rules (documented in the `xau_comex_gold_settlement` clock entry); the 10:00-12:00 bar-end windows track US DST automatically.

## Design Notes Locked Before Any Run

This candidate operationalizes the campaign's closing recommendation: combine the decade's weak-but-real daily momentum with the funded window where per-unit-risk costs halve and ranges double. G9A pre-check: 600-point expected median stop gives expected cost_R of about 0.08 at the measured 50-point median spread. A failure here is final for v0 under NO_TUNING_RULES.md.

## Classic Template Compliance

Hypothesis date: 2026-06-10
Hypothesis version: v0
Author / owner: Claude (independent technical reviewer) / maksoftwares
Expected trade count per year: 120-200
Expected cost-adjusted PF: 1.15-1.45
Expected losing-month percentage: 35%-55%
Expected worst single month: -8R to -16R
Expected R-multiple distribution: Many -1R initiative failures in chop, steady 2.0R trend-day wins, and no dependence on one outsized winner.
Expected max consecutive zero months: 2

## Mechanical Definition

The complete mechanical rules are the locked `mechanical_entry_rules`, `mechanical_exit_rules`, `stop_model`, and `target_model` fields above: D1 EMA20-versus-EMA50 trend state from completed daily bars only, the first New_York 10:00-12:00 bar-end H1 bar closing in the trend direction beyond the prior bar's extreme with body at least 35 percent, market entry at the next simulator quote, a stop of max(1.5 x H1 ATR(14), 375 points), a fixed 2.0R target, and at most one setup per New_York date. Implementation: `src/phase0/strategies/xau_d1_trend_ny_window_continuation_v0.py` (research registry only; not an approved EA).

## Expected Behavior

The highest-frequency Wave-2 design; long stretches of one-sided exposure during persistent trends, with losing clusters in trend-transition months. Per-cell samples on the full windows should comfortably exceed the trade-count floor, likely placing this candidate in the high-frequency gate branch with absolute concentration caps binding.

## Why This Hypothesis Should Exist

The 2026-06-10 locked runs measured weak-but-persistent decade-scale daily momentum (full-window PF 1.06-1.28 across the rejected pattern family) that died at the 1.30 bar mainly through off-session execution economics; the session research independently measured that the NY-morning window doubles range and halves cost per unit of risk. Expressing the same standing flow only when it is funded is a genuinely different design from any rejected version, with a mechanism argument neither ingredient had alone.

## What Would Falsify It

The locked PHASE0_WAVE2_GATE_SET_V1 selection: fewer than 7 of 9 PF cells at 1.30, any cell under 40 trades, concentration breach (absolute caps at high frequency, normalized G4 at low frequency), drawdown or activity breach, p95-to-best PF ratio under 0.50, G7 cross-venue floor under 1.20, G8 modern-era failure, G9B realized cost breach, or adversarial review finding a logic mismatch. A failure is final for v0; no post-result rescue of any kind.
