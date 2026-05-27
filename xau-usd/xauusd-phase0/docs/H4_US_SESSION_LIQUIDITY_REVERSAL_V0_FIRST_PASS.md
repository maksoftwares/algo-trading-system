# H4 US Session Liquidity Reversal v0 First Pass

Status: REJECTED_FIRST_PASS

Generated at UTC: 2026-05-27

## Boundary

This was a research-candidate first pass only. It does not approve an EA, does not add any Phase 1 observer, and does not authorize decile, multisymbol, adversarial, paper-mode, or live execution work for this candidate.

## Hypothesis Lock

| Item | Value |
| --- | --- |
| Expert | `h4_us_session_liquidity_reversal_v0` |
| Hypothesis file | `docs/hypothesis_h4_us_session_liquidity_reversal_v0.md` |
| SHA256 | `3746ce113d49c1bb1a17402fcba6bf82a8c01a95c5c07bca642da96f6589826c` |
| Synthetic smoke | PASS |
| Result-producing command | `phase0 run-research-matrix --expert h4_us_session_liquidity_reversal_v0 --hypothesis-file docs/hypothesis_h4_us_session_liquidity_reversal_v0.md` |

## Matrix Summary

| Cell | Broker | Cost | Trades | PF | Return % | Max DD % |
| ---: | --- | --- | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 34 | 1.0840 | 0.5013 | 1.9450 |
| 2 | capital_com | median | 34 | 1.0840 | 0.5013 | 1.9450 |
| 3 | capital_com | p95 | 34 | 1.0751 | 0.4462 | 1.9693 |
| 4 | pepperstone | best_case | 32 | 1.1280 | 0.7913 | 1.8137 |
| 5 | pepperstone | median | 32 | 1.1280 | 0.7913 | 1.8137 |
| 6 | pepperstone | p95 | 32 | 1.1201 | 0.7449 | 1.8300 |
| 7 | dukascopy | best_case | 60 | 1.0472 | 0.4944 | 3.6150 |
| 8 | dukascopy | median | 60 | 1.0380 | 0.3954 | 3.5189 |
| 9 | dukascopy | p95 | 60 | 1.0220 | 0.2284 | 3.5692 |

## Gate Read

| Gate | Result |
| --- | --- |
| PF >= 1.30 in at least 7/9 cells | FAIL: 0/9 cells |
| Minimum 40 trades per cell | FAIL: 6/9 cells below 40 trades |
| Result direction | Weakly positive but far below required PF |
| Next validation | STOP: no deciles, multisymbol, intrabar, or Gate 9 |

## Decision

Reject v0 without tuning.

The candidate produced a mild positive return profile, but the edge was too thin and too low-frequency to survive the locked Phase 0 first-pass gates. This is especially important because the hypothesis was an OHLC-only exhaustion variant; changing thresholds after seeing this result would turn it into tuning, so the correct action is to close v0 and move to either a new versioned hypothesis or a genuinely new data class.
