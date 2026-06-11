# Hypothesis: xau_comex_open_drive_continuation_v0

candidate_id: xau_comex_open_drive_continuation_v0
candidate_version: v0
mechanic_family: COMEX/NYSE open-hour participation drive continuation
same_family_as_breakout_retest: no
entry_decision_timeframe: H1
execution_timeframe: H1 signal timestamp with M5 simulator sequencing only
expected_median_hold_hours: 2-12
expected_decisions_per_week: 1-3
expected_trades_per_year: 60-110
expected_median_stop_points: 500
expected_cost_R_at_measured_50_75_spread: 0.10
event_clock_id: xau_comex_gold_settlement
market_behavior_thesis: The hour containing the 09:30 New York COMEX/NYSE cash opens is the single largest scheduled participation step of the gold day; when that hour resolves as a one-sided range-expansion drive (big range, dominant body, close at the directional extreme), the opening flow is initiating rather than rotating, and the move tends to extend during the remaining funded hours.
participants_or_flow_mechanism: Futures opening auctions, equity-open cross-asset flows, and post-8:30-data macro positioning all arrive in the 09:00-10:00 New_York hour; the project's session research shows this participation step is decade-stable (2-4x tick volume) and that winners in this window historically get paid quickly, which is exactly the profile of an initiative drive rather than thin-market noise.
mechanical_entry_rules: All windows are defined on completed H1 bars whose timestamp_utc equals the bar END converted to America/New_York local time with IANA timezone rules (DST-correct year-round). The drive bar is the single H1 bar with New_York bar-end time 10:00 (it contains the 09:30 opens). The trigger requires, at the drive bar: high minus low at least 1.30 times H1 ATR(14); body (absolute close minus open) at least 50 percent of the high-low range; and the close located in the directional 30 percent of the high-low range (top 30 percent for LONG, bottom 30 percent for SHORT). Direction is the drive bar's body direction. Entry is market at the next available simulator quote after the drive bar completes. At most one setup per America/New_York calendar date, bidirectional.
mechanical_exit_rules: Stop-loss or take-profit only, one position at a time, Phase 0 simulator sequencing; no discretionary, time-based, or trailing exits.
stop_model: Stop distance is the maximum of 1.2 times H1 ATR(14) at the drive bar and 3.75 price units (375 points); placed adverse to the entry direction from the entry price.
target_model: Fixed 2.0R take-profit from entry using the realized stop distance; initiative open drives are the strongest-trend subset of the funded window, so the pre-registered payoff is wider than the pullback design.
risk_model: Fixed-notional, cost-adjusted R-series evaluation through the Phase 0 research matrix.
forbidden_filters: No new session filter, news filter, volatility filter, level filter, direction filter, cost-model cherry-pick, stop change, target change, or rescue rule after results.
falsification_criteria: Reject this version if the locked PHASE0_WAVE2_GATE_SET_V1 selection fails (frequency-aware standard or low-frequency gates, including the carried-over G7 cross-venue floor, G8 modern-era integrity, and G9B realized measured cost), or adversarial review finds a logic mismatch.
ancestry_comparison: breakout_retest (COST_SUSPENDED_CANONICAL) requires a price-level break and an M5 retest sequence; this candidate has no level and no retest - it conditions purely on the opening hour's participation signature at H1 scale. opening_drive_failed_continuation_v0 is REJECTED_FIRST_PASS and is the nearest rejected relative; it traded failed-drive logic at a different scale and its rejection counts as adjacent negative evidence. xau_comex_settlement_flow_v0 is FAIL_REJECTED_VERSION_FINAL (2026-06-10) and shares the NY clock but traded the opposite thesis (post-settlement fade outside the funded hours); its failure does not bear on in-window continuation but is disclosed for family accounting.
data_window: Full available offline broker windows ending no later than 2025-06-30; Capital.com and Dukascopy PASS full target window; Pepperstone owner-accepted partial 2019-01-02 through 2021-12-31 with DATA_WINDOW_ASYMMETRY_PRESENT.
true_holdout_exclusion: true
expected_failure_modes: Drive bars that exhaust the move in the opening hour leaving no continuation, false drives on data-shock reversals, low setup frequency in quiet eras pressing against trade-count floors, or 2.0R targets sitting beyond the typical remaining-session range in low-volatility years.
D2_family_label: xau_comex_open_drive_family
author: Claude (independent technical reviewer, Wave-2 second-EA research)
created_utc: 2026-06-10T18:10:00+00:00
sha256_hash: SELF_HASH_EXCLUDED
status: LOCKED

## Event Clock

America/New_York civil time via IANA rules (documented in the `xau_comex_gold_settlement` clock entry); the 10:00 bar-end window tracks US DST automatically.

## Design Notes Locked Before Any Run

G9A pre-check: 500-point expected median stop gives expected cost_R of about 0.10 at the measured 50-point median spread. The drive-bar conditions (range, body, close location) are all measured on the single completed 10:00 bar - there is no lookahead and no intra-bar trigger. A failure here is final for v0 under NO_TUNING_RULES.md.

## Classic Template Compliance

Hypothesis date: 2026-06-10
Hypothesis version: v0
Author / owner: Claude (independent technical reviewer) / maksoftwares
Expected trade count per year: 60-110
Expected cost-adjusted PF: 1.15-1.50
Expected losing-month percentage: 35%-60%
Expected worst single month: -5R to -12R
Expected R-multiple distribution: Frequent -1R failed drives, fewer 2.0R continuation wins carrying the expectancy, and no dependence on one outsized winner.
Expected max consecutive zero months: 3

## Mechanical Definition

The complete mechanical rules are the locked `mechanical_entry_rules`, `mechanical_exit_rules`, `stop_model`, and `target_model` fields above: the single New_York 10:00 bar-end drive bar with range at least 1.30 x H1 ATR(14), body at least 50 percent of range, close in the directional 30 percent, market entry at the next simulator quote in the drive direction, a stop of max(1.2 x H1 ATR(14), 375 points), a fixed 2.0R target, and at most one setup per New_York date. Implementation: `src/phase0/strategies/xau_comex_open_drive_continuation_v0.py` (research registry only; not an approved EA).

## Expected Behavior

Lower frequency than the pullback design; setups cluster on data-plus-open days. Losses are quick failed-drive stops; wins extend through the remaining funded hours. Quiet eras may press against the per-cell trade-count floor, which the gates will judge.

## Why This Hypothesis Should Exist

The 09:00-10:00 New_York hour contains the largest scheduled participation step of the gold day (decade-stable in the project's session research); a one-sided range-expansion close in that hour is the cleanest mechanical signature of initiating institutional flow available on completed H1 bars, and no rejected candidate traded this signature at this scale with cost-aware stops.

## What Would Falsify It

The locked PHASE0_WAVE2_GATE_SET_V1 selection: fewer than 7 of 9 PF cells at 1.30, any cell under 40 trades, concentration breach (absolute caps at high frequency, normalized G4 at low frequency), drawdown or activity breach, p95-to-best PF ratio under 0.50, G7 cross-venue floor under 1.20, G8 modern-era failure, G9B realized cost breach, or adversarial review finding a logic mismatch. A failure is final for v0; no post-result rescue of any kind.
