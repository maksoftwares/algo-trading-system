# Hypothesis: xau_ny_morning_trend_pullback_v0

candidate_id: xau_ny_morning_trend_pullback_v0
candidate_version: v0
mechanic_family: NY-morning funded-impulse pullback continuation
same_family_as_breakout_retest: no
entry_decision_timeframe: H1
execution_timeframe: H1 signal timestamp with M5 simulator sequencing only
expected_median_hold_hours: 2-10
expected_decisions_per_week: 2-3
expected_trades_per_year: 90-140
expected_median_stop_points: 500
expected_cost_R_at_measured_50_75_spread: 0.10
event_clock_id: xau_comex_gold_settlement
market_behavior_thesis: The 08:00-10:00 New York stretch (US data releases plus the COMEX/NYSE opens) sets the day's funded direction in gold; the first orderly counter-directional H1 pause inside that impulse is institutional absorption rather than reversal, and the funded flow tends to resume toward the impulse direction.
participants_or_flow_mechanism: The project's session research measured 2-4x participation and 2x range in the NY morning, with continuation funded by data-driven macro flow, futures opening flow, and benchmark-related dealing; a pullback bar that holds above the impulse origin shows the initiating side absorbing profit-taking without losing the level of initiative.
mechanical_entry_rules: All windows are defined on completed H1 bars whose timestamp_utc equals the bar END converted to America/New_York local time with IANA timezone rules (DST-correct year-round). The morning impulse is the close of the H1 bar with New_York bar-end time 10:00 minus the open of the H1 bar with New_York bar-end time 09:00 on the same date. The setup requires the absolute impulse to be at least 1.00 and at most 6.00 times H1 ATR(14) at the 10:00 bar. The trigger is the first H1 bar with New_York bar-end time 11:00, 12:00, or 13:00 that closes counter to the impulse direction (close below open for an up-impulse; close above open for a down-impulse) while the trigger close remains on the impulse side of the impulse origin (for an up-impulse the trigger close must stay above the 09:00 bar open; mirrored for a down-impulse). Entry is market at the next available simulator quote after the trigger bar completes, in the impulse direction. At most one setup per America/New_York calendar date, bidirectional.
mechanical_exit_rules: Stop-loss or take-profit only, one position at a time, Phase 0 simulator sequencing; no discretionary, time-based, or trailing exits.
stop_model: Stop distance is the maximum of 1.2 times H1 ATR(14) at the trigger bar and 3.75 price units (375 points); placed adverse to the entry direction from the entry price.
target_model: Fixed 1.5R take-profit from entry using the realized stop distance.
risk_model: Fixed-notional, cost-adjusted R-series evaluation through the Phase 0 research matrix.
forbidden_filters: No new session filter, news filter, volatility filter, level filter, direction filter, cost-model cherry-pick, stop change, target change, or rescue rule after results.
falsification_criteria: Reject this version if the locked PHASE0_WAVE2_GATE_SET_V1 selection fails (frequency-aware standard or low-frequency gates, including the carried-over G7 cross-venue floor, G8 modern-era integrity, and G9B realized measured cost), or adversarial review finds a logic mismatch.
ancestry_comparison: breakout_retest (COST_SUSPENDED_CANONICAL) trades M5 level-retest mechanics; this candidate uses no price level, no retest sequence, and no M5 trigger - it trades H1 impulse-absorption structure inside the same funded window, so any pass must be defended as a distinct mechanism at Gate 9. ny_am_pullback_continuation_v0 is REJECTED_FIRST_PASS and is the nearest rejected relative; it predates the measured-cost regime, used different impulse/pullback definitions at lower timeframe scale with tight stops, and its rejection counts as adjacent negative evidence against this lane.
data_window: Full available offline broker windows ending no later than 2025-06-30; Capital.com and Dukascopy PASS full target window; Pepperstone owner-accepted partial 2019-01-02 through 2021-12-31 with DATA_WINDOW_ASYMMETRY_PRESENT.
true_holdout_exclusion: true
expected_failure_modes: Pullback bars that mark genuine reversals on data-shock days, impulse-direction chop on range days where the 1.00 ATR floor admits noise, payoff asymmetry too small to clear costs at 1.5R, or era instability between the pre-2019 and modern regimes.
D2_family_label: xau_ny_morning_trend_pullback_family
author: Claude (independent technical reviewer, Wave-2 second-EA research)
created_utc: 2026-06-10T18:05:00+00:00
sha256_hash: SELF_HASH_EXCLUDED
status: LOCKED

## Event Clock

America/New_York civil time via IANA rules (the `xau_comex_gold_settlement` clock entry documents the NY DST handling used by all NY-anchored windows); the 09:00/10:00/11:00-13:00 bar-end windows track US DST automatically.

## Design Notes Locked Before Any Run

This is the first Wave-2 candidate built from the campaign's strategic finding: every candidate designed outside the funded NY-morning window has failed as a class, while the window itself carries decade-stable participation. G9A pre-check: 500-point expected median stop gives expected cost_R of about 0.10 at the measured 50-point median spread. A failure here is final for v0 under NO_TUNING_RULES.md.

## Classic Template Compliance

Hypothesis date: 2026-06-10
Hypothesis version: v0
Author / owner: Claude (independent technical reviewer) / maksoftwares
Expected trade count per year: 90-140
Expected cost-adjusted PF: 1.15-1.50
Expected losing-month percentage: 35%-55%
Expected worst single month: -6R to -14R
Expected R-multiple distribution: Many failed pullbacks near -1R, frequent 1.5R continuation wins, and no dependence on one outsized winner.
Expected max consecutive zero months: 2

## Mechanical Definition

The complete mechanical rules are the locked `mechanical_entry_rules`, `mechanical_exit_rules`, `stop_model`, and `target_model` fields above: New_York bar-end H1 windows, the 09:00-open-to-10:00-close morning impulse of 1.00 to 6.00 H1 ATR(14), the first counter-directional H1 close in the 11:00-13:00 bar-end window that holds the impulse origin, market entry at the next simulator quote in the impulse direction, a stop of max(1.2 x H1 ATR(14), 375 points), a fixed 1.5R target, and at most one setup per New_York date. Implementation: `src/phase0/strategies/xau_ny_morning_trend_pullback_v0.py` (research registry only; not an approved EA).

## Expected Behavior

Moderate frequency clustered on US data and open days; losses are quick -1R stops when the pullback marks a reversal; wins resolve within the same US session. At least 40 trades per matrix cell is expected on the full windows, with concentration well inside both the absolute and normalized caps because no single day can contribute more than one 1.5R winner.

## Why This Hypothesis Should Exist

The project's session-mechanism research measured a decade-stable 2-4x participation step and 2x range in the NY morning with roughly half the cost per unit of risk, and the 2026-06-10 campaign showed that candidates designed outside this window fail as a class. Absorption pullbacks inside a funded impulse are a different mechanism from any rejected candidate and from breakout_retest's level-retest logic.

## What Would Falsify It

The locked PHASE0_WAVE2_GATE_SET_V1 selection: fewer than 7 of 9 PF cells at 1.30, any cell under 40 trades, concentration breach (absolute caps at high frequency, normalized G4 at low frequency), drawdown or activity breach, p95-to-best PF ratio under 0.50, G7 cross-venue floor under 1.20, G8 modern-era failure, G9B realized cost breach, or adversarial review finding a logic mismatch. A failure is final for v0; no post-result rescue of any kind.
