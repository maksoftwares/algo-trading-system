# Hypothesis: w1_d1_momentum_continuation_v1_fullhist

candidate_id: w1_d1_momentum_continuation_v1_fullhist
candidate_version: v1_fullhist
mechanic_family: W1/D1 directional momentum continuation
same_family_as_breakout_retest: no
entry_decision_timeframe: D1
execution_timeframe: D1 signal timestamp with M5 simulator sequencing only
expected_median_hold_hours: 24-120
expected_decisions_per_week: 0-1
expected_trades_per_year: 15-80
expected_median_stop_points: 600
expected_cost_R_at_measured_50_75_spread: 0.06
market_behavior_thesis: Strong 20-day gold momentum with a completed D1 continuation candle can persist across multiple sessions.
participants_or_flow_mechanism: Multi-week macro repricing, risk allocation, and positioning flow can create slower D1 continuation behavior.
mechanical_entry_rules: Preserve w1_d1_momentum_continuation_v0 byte-identical mechanics where implementation permits: 20-day D1 momentum threshold, five-day confirmation, D1 candle body/range/location quality, one setup per ISO week, and first available execution bar after the completed D1 signal.
mechanical_exit_rules: Preserve w1_d1_momentum_continuation_v0 exit mechanics: one-position-at-a-time Phase 0 simulator sequencing, fixed 1.5R target, and no discretionary exits.
stop_model: Preserve w1_d1_momentum_continuation_v0 stop construction: stop beyond the D1 signal candle extreme by 0.20 times D1 ATR(14).
target_model: Fixed 1.5R target inherited from w1_d1_momentum_continuation_v0.
risk_model: Fixed-notional, cost-adjusted R-series evaluation through the Phase 0 research matrix.
forbidden_filters: No new session filter, news filter, volatility filter, level filter, direction filter, cost-model cherry-pick, stop change, target change, or rescue rule after results.
falsification_criteria: Reject this version if locked low-frequency gates fail, fewer than 7 of 9 PF cells reach 1.30, any cell has fewer than 40 trades, concentration fails under G4, G9B measured-cost feasibility fails, D2 fails if required, or adversarial review finds a logic mismatch.
data_window: Full available offline broker windows ending no later than 2025-06-30; Capital.com and Dukascopy PASS full target window; Pepperstone owner-accepted partial 2019-01-02 through 2021-12-31 with DATA_WINDOW_ASYMMETRY_PRESENT.
true_holdout_exclusion: true
expected_failure_modes: Long-gold drift dominance, one-year trend dominance, Dukascopy underperformance, low trade count, concentration, or Pepperstone-window asymmetry.
D2_family_label: w1_d1_momentum_continuation_family
author: Codex
created_utc: 2026-06-10T10:30:00+00:00
sha256_hash: SELF_HASH_EXCLUDED
status: LOCKED

## Source Integrity

Source v0 hypothesis SHA256: `a1f62130384e9b1adb6f156cfb6ff64771556dce55f75575f7a44d5bde4df459`

Source v0 strategy SHA256: `3064645a67ee043d8a72a5103712b2054c6452739f566e87702e9962036af355`

This v1 claim is a full-history retest claim for the same rule mechanics. It does not add filters or parameter changes.
