# Hypothesis: xau_comex_settlement_flow_v0

candidate_id: xau_comex_settlement_flow_v0
candidate_version: v0
mechanic_family: COMEX settlement-window position-squaring fade
same_family_as_breakout_retest: no
entry_decision_timeframe: H1
execution_timeframe: H1 signal timestamp with M5 simulator sequencing only
expected_median_hold_hours: 2-12
expected_decisions_per_week: 1-3
expected_trades_per_year: 40-110
expected_median_stop_points: 420
expected_cost_R_at_measured_50_75_spread: 0.12
event_clock_id: xau_comex_gold_settlement
market_behavior_thesis: The CME gold settlement period ending 13:30 America/New_York closes the deepest liquidity window of the gold day; a strong directional impulse that runs into settlement is partly settlement-related position-squaring and benchmark-chasing flow, and once that flow expires the thinner post-settlement market tends to retrace part of the impulse rather than extend it.
participants_or_flow_mechanism: Futures position-squaring into the settlement print, options hedging pinned to the settlement reference, and index/benchmark flows all complete at the settlement boundary; the project's own session research shows post-peak hours revert to a thin inventory market, so an impulse whose marginal buyer was the settlement process loses its sponsor exactly at the boundary.
mechanical_entry_rules: All windows are defined on completed H1 bars whose timestamp_utc equals the bar END converted to America/New_York local time with IANA timezone rules (DST-correct year-round). The settlement bar is the single completed H1 bar with New_York bar-end time 14:00 on the trade date (it contains the 13:30 settlement boundary). The pre-settlement impulse is the settlement bar close minus the open of the completed H1 bar with New_York bar-end time 10:00 on the same date. The trigger requires the absolute impulse to be at least 1.50 and at most 5.00 times H1 ATR(14) at the settlement bar. The entry direction is opposite to the impulse sign (fade). Entry is market at the next available simulator quote after the settlement bar completes. At most one setup per America/New_York calendar date, bidirectional.
mechanical_exit_rules: Stop-loss or take-profit only, one position at a time, Phase 0 simulator sequencing; no discretionary, time-based, or trailing exits.
stop_model: Stop distance is the maximum of 1.2 times H1 ATR(14) at the settlement bar and 3.75 price units (375 points); placed adverse to the entry direction from the entry price (on the impulse side).
target_model: Fixed 1.2R take-profit from entry using the realized stop distance; the reversion leg is expected to retrace only part of the impulse, so the pre-registered payoff is deliberately smaller than the continuation designs.
risk_model: Fixed-notional, cost-adjusted R-series evaluation through the Phase 0 research matrix.
forbidden_filters: No new session filter, news filter, volatility filter, level filter, direction filter, cost-model cherry-pick, stop change, target change, or rescue rule after results.
falsification_criteria: Reject this version if locked PHASE0_LOWFREQ_GATE_SET_V1 gates fail, fewer than 7 of 9 PF cells reach 1.30, any cell has fewer than 40 trades, concentration fails under normalized G4, the G7 cross-venue floor fails, the G8 modern-era slice fails, G9B realized measured cost fails, D2 fails if required, or adversarial review finds a logic mismatch.
ancestry_comparison: h4_us_session_liquidity_reversal_v0 and h1_friday_position_squaring_reversion_v0 are REJECTED_FIRST_PASS and are the nearest rejected US-session and position-squaring relatives; neither was anchored to the settlement clock and both used different impulse definitions and stop scales. Their rejections are treated as adjacent negative evidence against US-afternoon reversion designs; this is a new settlement-anchored H1 fade with wide ATR-floored stops, a new name, and a final-verdict version, not a tune of either rejected file.
data_window: Full available offline broker windows ending no later than 2025-06-30; Capital.com and Dukascopy PASS full target window; Pepperstone owner-accepted partial 2019-01-02 through 2021-12-31 with DATA_WINDOW_ASYMMETRY_PRESENT.
true_holdout_exclusion: true
expected_failure_modes: Genuine macro trend days where the impulse keeps extending after settlement (counter-trend losses), the fade winning only in the era already known to be mean-reverting, impulse-frequency scarcity pressing against the 40-trade cell floor in quiet eras, or asymmetric behavior between up-impulses and down-impulses that the bidirectional rule cannot express.
D2_family_label: xau_comex_settlement_flow_family
author: Claude (independent technical reviewer, second-EA research campaign)
created_utc: 2026-06-10T13:15:00+00:00
sha256_hash: SELF_HASH_EXCLUDED
status: LOCKED

## Event Clock

`xau_comex_gold_settlement` (config/event_clocks.yaml): CME gold settlement period ends 13:30 America/New_York, converted per settlement date with IANA timezone rules; windows track US civil time automatically across DST changes. Source: https://cmegroupclientsite.atlassian.net/wiki/display/EPICSANDBOX/Daily%2BSettlement%2BTime%2BDetails

## Design Notes Locked Before Any Run

The fade direction (not drift) is pre-registered from the mechanism: the project's session research (EVENING_EDGE_SESSION_MECHANISM_RESEARCH_2026_06_10.md) measured that gold's off-peak hours behave as a thin, mean-reverting inventory market, and that participation collapses after the US morning window; the settlement boundary is the structural end of that funded window. If the fade fails, the failure is final for v0; a drift variant would be a separate new hypothesis with its own mechanism argument, registered before any run, and the fade rejection counts as evidence against the whole settlement lane. G9A pre-check: 420-point expected median stop gives expected cost_R of about 0.12 at the measured 50-point median spread.
