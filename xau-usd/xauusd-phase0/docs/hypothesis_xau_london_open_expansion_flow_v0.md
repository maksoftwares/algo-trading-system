# Hypothesis: xau_london_open_expansion_flow_v0

candidate_id: xau_london_open_expansion_flow_v0
candidate_version: v0
mechanic_family: London-open structural flow expansion continuation
same_family_as_breakout_retest: no
entry_decision_timeframe: H1
execution_timeframe: H1 signal timestamp with M5 simulator sequencing only
expected_median_hold_hours: 4-24
expected_decisions_per_week: 1-4
expected_trades_per_year: 60-170
expected_median_stop_points: 420
expected_cost_R_at_measured_50_75_spread: 0.12
event_clock_id: xau_london_open
market_behavior_thesis: The overnight Asia inventory range is repriced when European institutional liquidity arrives at the London open; a decisive completed-H1 expansion out of a contained Asia range can carry follow-through when positioning into the open is one-sided.
participants_or_flow_mechanism: European banks, refiners, and macro desks arriving at 08:00 Europe/London concentrate the first genuine two-way institutional liquidity of the day; initiative flow that breaks the overnight range at this clock is funded by real participation rather than thin Asia inventory shuffling.
mechanical_entry_rules: All windows are defined on completed H1 bars whose timestamp_utc equals the bar END converted to Europe/London local time with IANA timezone rules (DST-correct year-round). Asia reference range is the highest high and lowest low of the completed H1 bars whose London bar-end times are 01:00 through 08:00 inclusive on the trade date. Range sanity requires the Asia range width to be at least 0.75 and at most 4.0 times H1 ATR(14) at the last Asia bar. The trigger is the first completed H1 bar with London bar-end time 09:00, 10:00, or 11:00 that closes at least 0.15 times H1 ATR(14) beyond the Asia high (LONG) or below the Asia low (SHORT), closes directionally (bullish for LONG, bearish for SHORT), closes in the directional 40 percent of its high-low range, and has body at least 35 percent of its high-low range. Entry is market at the next available simulator quote after the trigger bar completes. At most one setup per Europe/London calendar date, first trigger wins, bidirectional.
mechanical_exit_rules: Stop-loss or take-profit only, one position at a time, Phase 0 simulator sequencing; no discretionary, time-based, or trailing exits.
stop_model: Stop distance is the maximum of 1.2 times H1 ATR(14) at the trigger bar and 3.75 price units (375 points); placed adverse to the entry direction from the entry price.
target_model: Fixed 1.5R take-profit from entry using the realized stop distance.
risk_model: Fixed-notional, cost-adjusted R-series evaluation through the Phase 0 research matrix.
forbidden_filters: No new session filter, news filter, volatility filter, level filter, direction filter, cost-model cherry-pick, stop change, target change, or rescue rule after results.
falsification_criteria: Reject this version if locked PHASE0_LOWFREQ_GATE_SET_V1 gates fail, fewer than 7 of 9 PF cells reach 1.30, any cell has fewer than 40 trades, concentration fails under normalized G4, the G7 cross-venue floor fails, the G8 modern-era slice fails, G9B realized measured cost fails, D2 fails if required, or adversarial review finds a logic mismatch.
ancestry_comparison: asia_range_london_breakout_v0 is REJECTED_FIRST_PASS (failed 9-cell matrix Gate 1; M5 entries, tight M5-ATR stops, UTC-fixed session windows). This is a new design from the same flow event with H1 decision bars, wide ATR-floored stops of at least 375 points, and DST-correct Europe/London event timing. The prior rejection is treated as evidence against this lane, not as a baseline to rescue; this is a new name and a final-verdict version, not a tune of the rejected file.
data_window: Full available offline broker windows ending no later than 2025-06-30; Capital.com and Dukascopy PASS full target window; Pepperstone owner-accepted partial 2019-01-02 through 2021-12-31 with DATA_WINDOW_ASYMMETRY_PRESENT.
true_holdout_exclusion: true
expected_failure_modes: London-open stop runs that reverse into the NY session, range-definition fragility on UK/US DST divergence weeks, contained-range scarcity in high-volatility eras cutting frequency, or concentration of PnL in a few trend days.
D2_family_label: xau_london_open_expansion_family
author: Claude (independent technical reviewer, second-EA research campaign)
created_utc: 2026-06-10T13:05:00+00:00
sha256_hash: SELF_HASH_EXCLUDED
status: LOCKED

## Event Clock

`xau_london_open` (config/event_clocks.yaml): 08:00 Europe/London institutional arrival, converted per trade date with IANA timezone rules. Europe/London is UTC+0 in winter (GMT) and UTC+1 in British Summer Time, so all windows in this hypothesis track UK civil time automatically across DST changes.

## Why This Design Is Not The Rejected Ancestor

The rejected `asia_range_london_breakout_v0` triggered on M5 candles with stops of roughly 0.25 times M5 ATR(14) beyond the trigger candle (typically far below 250 points), making it structurally cost-fragile at the measured 50/75-point spreads and exposed to M5 noise. This candidate decides on completed H1 bars, floors the stop at 375 points (G9A pre-check: 420-point expected median stop gives expected cost_R of about 0.12 at the measured 50-point median spread), and defines every session window in Europe/London local time rather than fixed UTC. A failure here is final for v0 under NO_TUNING_RULES.md.
