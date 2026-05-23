# Symbol Round Sweep Reversal v0 First-Pass Result

Status: `REJECTED_FIRST_PASS`

Generated: 2026-05-23

## Decision

`symbol_round_sweep_reversal_v0` is rejected. It produced enough trades in every matrix cell, but 0/9 cells reached the PF >= 1.30 requirement and several cells exceeded the maximum drawdown threshold.

Do not tune this v0 in place. Any revisit must use a new versioned hypothesis with a new SHA256 registration.

## Hypothesis Lock

| Field | Value |
| --- | --- |
| Hypothesis file | `docs/hypothesis_symbol_round_sweep_reversal_v0.md` |
| Registration report | `outputs/reports/symbol_round_sweep_reversal_v0_research_hypothesis_registration.md` |
| SHA256 | `420149e4e02059fcd677b0d249d979f3d3f91dc06fa47fa87f6449ec552b5019` |
| Research smoke | PASS |

## Matrix Summary

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 685 | 0.785 | -35.89 | 38.74 | 40.58% |
| 2 | capital_com | median | 685 | 0.785 | -35.89 | 38.74 | 40.58% |
| 3 | capital_com | p95 | 685 | 0.727 | -44.10 | 46.47 | 40.58% |
| 4 | pepperstone | best_case | 1,180 | 0.914 | -26.34 | 28.64 | 39.24% |
| 5 | pepperstone | median | 1,180 | 0.914 | -26.34 | 28.64 | 39.24% |
| 6 | pepperstone | p95 | 1,180 | 0.866 | -37.84 | 39.03 | 39.24% |
| 7 | dukascopy | best_case | 1,338 | 1.003 | 1.10 | 25.21 | 41.78% |
| 8 | dukascopy | median | 1,338 | 0.942 | -19.64 | 30.95 | 41.78% |
| 9 | dukascopy | p95 | 1,338 | 0.822 | -48.51 | 50.46 | 41.78% |

## Gate Read

| Gate | Observed | Status |
| --- | --- | --- |
| PF >= 1.30 cells | 0/9 | FAIL |
| Minimum cell trades | 685 | PASS |
| Drawdown discipline | up to 50.46% | FAIL |
| Cost sensitivity | p95 cells weaken materially | FAIL |

## Interpretation

The public-handle sweep/fade idea is not supported by the current v0 rules. The result is useful because it tests the opposite behavior from breakout-retest and rejects it without adding filters.

Next research should continue looking for an independent behavior family, not retune this candidate.
