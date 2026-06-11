# Hypothesis: d1_momentum_h4_pullback_v1_fullhist

candidate_id: d1_momentum_h4_pullback_v1_fullhist
candidate_version: v1_fullhist
mechanic_family: D1 directional momentum with H4 trend pullback continuation
same_family_as_breakout_retest: no
entry_decision_timeframe: H4
execution_timeframe: H4 signal timestamp with M5 simulator sequencing only
expected_median_hold_hours: 24-72
expected_decisions_per_week: 0-2
expected_trades_per_year: 25-95
expected_median_stop_points: 450
expected_cost_R_at_measured_50_75_spread: 0.08
market_behavior_thesis: Daily XAUUSD directional momentum can persist after a completed H4 pullback re-accepts trend direction.
participants_or_flow_mechanism: Multi-session macro and positioning flow can continue after H4 pullback liquidity is absorbed.
mechanical_entry_rules: Preserve d1_momentum_h4_pullback_v0 byte-identical mechanics where implementation permits: D1 EMA20/EMA50 trend state, five-day D1 momentum threshold, H4 EMA20-zone pullback candle quality, one setup per ISO week, and first available execution bar after the completed H4 signal.
mechanical_exit_rules: Preserve d1_momentum_h4_pullback_v0 exit mechanics: one-position-at-a-time Phase 0 simulator sequencing, fixed 2.0R target, and no discretionary exits.
stop_model: Preserve d1_momentum_h4_pullback_v0 stop construction: stop beyond the H4 pullback candle extreme by 0.25 times H4 ATR(14).
target_model: Fixed 2.0R target inherited from d1_momentum_h4_pullback_v0.
risk_model: Fixed-notional, cost-adjusted R-series evaluation through the Phase 0 research matrix.
forbidden_filters: No new session filter, news filter, volatility filter, level filter, direction filter, cost-model cherry-pick, stop change, target change, or rescue rule after results.
falsification_criteria: Reject this version if locked low-frequency gates fail, fewer than 7 of 9 PF cells reach 1.30, any cell has fewer than 40 trades, concentration fails under G4, G9B measured-cost feasibility fails, D2 fails if required, or adversarial review finds a logic mismatch.
data_window: Full available offline broker windows ending no later than 2025-06-30; Capital.com and Dukascopy PASS full target window; Pepperstone owner-accepted partial 2019-01-02 through 2021-12-31 with DATA_WINDOW_ASYMMETRY_PRESENT.
true_holdout_exclusion: true
expected_failure_modes: Dukascopy underperformance, trend exhaustion, choppy H4 pullbacks, concentration in a few multi-day winners, or Pepperstone-window asymmetry.
D2_family_label: d1_momentum_h4_pullback_family
author: Codex
created_utc: 2026-06-10T10:30:00+00:00
sha256_hash: SELF_HASH_EXCLUDED
status: LOCKED

## Source Integrity

Source v0 hypothesis SHA256: `076b9b78412f9b272b0821e8abe82b64ce706815efca17a573a52767e0ee36bd`

Source v0 strategy SHA256: `61710b735d93ff018487322d20a607e88db209393e8f64a3583543f6f44b92ce`

This v1 claim is a full-history retest claim for the same rule mechanics. It does not add filters or parameter changes.
