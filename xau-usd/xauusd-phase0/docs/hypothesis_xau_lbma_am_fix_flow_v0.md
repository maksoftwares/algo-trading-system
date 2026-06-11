# Hypothesis: xau_lbma_am_fix_flow_v0

candidate_id: xau_lbma_am_fix_flow_v0
candidate_version: v0
mechanic_family: LBMA AM auction post-fix imbalance continuation
same_family_as_breakout_retest: no
entry_decision_timeframe: H1
execution_timeframe: H1 signal timestamp with M5 simulator sequencing only
expected_median_hold_hours: 4-24
expected_decisions_per_week: 1-3
expected_trades_per_year: 40-120
expected_median_stop_points: 420
expected_cost_R_at_measured_50_75_spread: 0.12
event_clock_id: xau_lbma_am_fix
market_behavior_thesis: The LBMA Gold Price AM auction at 10:30 Europe/London concentrates real producer, refiner, and client benchmark flow into one clearing event; when the auction hour resolves decisively outside the pre-auction range, the unfilled imbalance can leave a short-horizon directional residue.
participants_or_flow_mechanism: Miners, central banks, ETFs, and commercial hedgers transact at the LBMA benchmark; auction-clearing imbalances that exceed the pre-fix range express real positioning demand rather than technical noise, and dealers hedging benchmark fills can extend the move after the auction completes.
mechanical_entry_rules: All windows are defined on completed H1 bars whose timestamp_utc equals the bar END converted to Europe/London local time with IANA timezone rules (DST-correct year-round). The pre-fix reference range is the highest high and lowest low of the completed H1 bars whose London bar-end times are 07:00, 08:00, 09:00, and 10:00 on the trade date. Range sanity requires the pre-fix range width to be at least 0.50 and at most 3.50 times H1 ATR(14) at the 10:00 bar. The fix bar is the single completed H1 bar with London bar-end time 11:00 (it contains the 10:30 auction). The trigger requires the fix bar to close at least 0.15 times H1 ATR(14) above the pre-fix high (LONG) or below the pre-fix low (SHORT), close directionally, close in the directional 40 percent of its high-low range, and have body at least 35 percent of its high-low range. Entry is market at the next available simulator quote after the fix bar completes. At most one setup per Europe/London calendar date, bidirectional.
mechanical_exit_rules: Stop-loss or take-profit only, one position at a time, Phase 0 simulator sequencing; no discretionary, time-based, or trailing exits.
stop_model: Stop distance is the maximum of 1.2 times H1 ATR(14) at the fix bar and 3.75 price units (375 points); placed adverse to the entry direction from the entry price.
target_model: Fixed 1.5R take-profit from entry using the realized stop distance.
risk_model: Fixed-notional, cost-adjusted R-series evaluation through the Phase 0 research matrix.
forbidden_filters: No new session filter, news filter, volatility filter, level filter, direction filter, cost-model cherry-pick, stop change, target change, or rescue rule after results.
falsification_criteria: Reject this version if locked PHASE0_LOWFREQ_GATE_SET_V1 gates fail, fewer than 7 of 9 PF cells reach 1.30, any cell has fewer than 40 trades, concentration fails under normalized G4, the G7 cross-venue floor fails, the G8 modern-era slice fails, G9B realized measured cost fails, D2 fails if required, or adversarial review finds a logic mismatch.
ancestry_comparison: london_fix_continuation_v0 is REJECTED_FIRST_PASS (failed 9-cell matrix Gate 1); it targeted the 15:00 Europe/London afternoon fix proxy with M5 entries, a 30-minute M5 pre-fix range, and tight M5-ATR stops. This candidate targets the 10:30 AM auction (a different clearing event) at H1 scale with a 4-hour pre-fix range and wide ATR-floored stops of at least 375 points. The adjacent rejection is treated as evidence against fix-family designs in general; this is a new name and a final-verdict version, not a tune of the rejected file. This hypothesis also sits inside the demo book's losing Afternoon bucket on purpose: the test is whether a mechanism-anchored design finds structure where generic patterns found none.
data_window: Full available offline broker windows ending no later than 2025-06-30; Capital.com and Dukascopy PASS full target window; Pepperstone owner-accepted partial 2019-01-02 through 2021-12-31 with DATA_WINDOW_ASYMMETRY_PRESENT.
true_holdout_exclusion: true
expected_failure_modes: Auction flow fully absorbed inside the fix hour leaving no residue, post-fix reversal toward the NY open, pre-fix range fragility on UK DST transition weeks, low setup frequency in quiet eras pressing against the 40-trade cell floor, or PnL concentration on a few macro days.
D2_family_label: xau_lbma_am_fix_flow_family
author: Claude (independent technical reviewer, second-EA research campaign)
created_utc: 2026-06-10T13:10:00+00:00
sha256_hash: SELF_HASH_EXCLUDED
status: LOCKED

## Event Clock

`xau_lbma_am_fix` (config/event_clocks.yaml): LBMA Gold Price AM auction at 10:30 Europe/London, converted per auction date with IANA timezone rules; windows track UK civil time automatically across DST changes. Source: https://www.lbma.org.uk/prices-and-data/precious-metal-prices

## Why This Design Is Not The Rejected Ancestor

The rejected `london_fix_continuation_v0` keyed off the 15:00 London PM-fix proxy, formed its range from six M5 bars, triggered on M5 candles, and used stops near one M5 ATR(14) - structurally cost-fragile at measured 50/75-point spreads. This candidate keys off the AM auction, decides once per day on a single completed H1 bar, uses a 4-hour H1 reference range, and floors the stop at 375 points (G9A pre-check: 420-point expected median stop gives expected cost_R of about 0.12 at the measured 50-point median spread). A failure here is final for v0 under NO_TUNING_RULES.md.
