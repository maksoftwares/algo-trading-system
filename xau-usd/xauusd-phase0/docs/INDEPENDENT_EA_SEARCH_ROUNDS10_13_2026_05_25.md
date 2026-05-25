# Independent EA Search Rounds 10-13

Generated: 2026-05-25

## Starting Point

Rounds 8 and 9 rejected the M15 two-bar impulse family. The next search batch moved to slower-timeframe state, deterministic AI-style state memory, and intermarket XAG/FX behavior while keeping active Phase 1 runtime untouched.

## Tested Lanes

| Round | Candidate | Core Idea | Result |
| ---: | --- | --- | --- |
| 10 | `d1_w1_momentum_h4_pullback_v0` | D1/W1 trend state with H4 pullback execution | Rejected: 3/9 PF cells >= 1.30, all Dukascopy |
| 11 | `h4_walk_forward_knn_momentum_state_v0` | Auditable H4 nearest-neighbor state memory | Rejected: 0/9 PF cells >= 1.30 |
| 12 | `xau_xag_fx_composite_reversion_v0` | XAU/XAG value dislocation with FX proxy confirmation | Rejected: 0/9 PF cells >= 1.30 |
| 13 | `xag_lead_xau_followthrough_v0` | XAG impulse leadership forecasting XAU continuation | Rejected: 0/9 PF cells >= 1.30 |

## Outcome

No new independent EA was found in this batch.

The best lead was `d1_w1_momentum_h4_pullback_v0`, which passed sample size, drawdown, activity, and cost-sensitivity gates, but its PF strength was isolated to the Dukascopy 2022-2024 cells and concentration failed.

The AI-style lane was implemented safely as deterministic walk-forward KNN, but the result did not pass. The intermarket composite and lead-lag lanes both produced enough trades and cleared operational gates, but neither showed PF survival.

## Process Boundary

Do not tune any rejected v0 in place. Any revisit needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

This batch does not alter active Phase 1 soak, Phase 2 readiness, approved expert status, dry-run permission, or trade permissions.
