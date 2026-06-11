# Hypothesis: h4_inside_bar_d1_momentum_breakout_v1_fullhist

candidate_id: h4_inside_bar_d1_momentum_breakout_v1_fullhist
candidate_version: v1_fullhist
mechanic_family: H4 inside-bar breakout with D1 momentum gating
same_family_as_breakout_retest: no
entry_decision_timeframe: H4
execution_timeframe: H4 signal timestamp with M5 simulator sequencing only
expected_median_hold_hours: 12-72
expected_decisions_per_week: 0-2
expected_trades_per_year: 20-120
expected_median_stop_points: 375
expected_cost_R_at_measured_50_75_spread: 0.10
market_behavior_thesis: H4 inside-bar contraction can resolve in the direction of D1 momentum and continue far enough to overcome measured costs.
participants_or_flow_mechanism: Gold liquidity can compress inside prior H4 ranges before trend-aligned institutional flow expands price.
mechanical_entry_rules: Preserve h4_inside_bar_d1_momentum_breakout_v0 byte-identical mechanics where implementation permits: H4 inside-bar quality, D1 five-day momentum state, H4 breakout within three completed bars, breakout candle body/location quality, one setup per inside bar and direction, and first available execution bar after the completed H4 breakout.
mechanical_exit_rules: Preserve h4_inside_bar_d1_momentum_breakout_v0 exit mechanics: one-position-at-a-time Phase 0 simulator sequencing, fixed 1.5R target, and no discretionary exits.
stop_model: Preserve h4_inside_bar_d1_momentum_breakout_v0 stop construction: stop at the inside-bar extreme or 0.75 H4 ATR from entry, whichever is farther.
target_model: Fixed 1.5R target inherited from h4_inside_bar_d1_momentum_breakout_v0.
risk_model: Fixed-notional, cost-adjusted R-series evaluation through the Phase 0 research matrix.
forbidden_filters: No new session filter, news filter, retest filter, level filter, direction filter, cost-model cherry-pick, stop change, target change, or rescue rule after results.
falsification_criteria: Reject this version if locked low-frequency gates fail, fewer than 7 of 9 PF cells reach 1.30, any cell has fewer than 40 trades, concentration fails under G4, G9B measured-cost feasibility fails, D2 fails if required, or adversarial review finds a logic mismatch.
data_window: Full available offline broker windows ending no later than 2025-06-30; Capital.com and Dukascopy PASS full target window; Pepperstone owner-accepted partial 2019-01-02 through 2021-12-31 with DATA_WINDOW_ASYMMETRY_PRESENT.
true_holdout_exclusion: true
expected_failure_modes: False breakouts, venue-specific weakness, late trend exhaustion, concentration in a few breakout periods, or Pepperstone-window asymmetry.
D2_family_label: h4_inside_bar_d1_momentum_breakout_family
author: Codex
created_utc: 2026-06-10T10:30:00+00:00
sha256_hash: SELF_HASH_EXCLUDED
status: LOCKED

## Source Integrity

Source v0 hypothesis SHA256: `93fd61822f0b4a0dc15699de3b46b9735cdd0bba64db08b16389094188144e0f`

Source v0 strategy SHA256: `0810a7ac958eb1e4742d00fce1e1608b1872b56e39483da519a5b04a8bee1640`

This v1 claim is a full-history retest claim for the same rule mechanics. It does not add filters or parameter changes.
