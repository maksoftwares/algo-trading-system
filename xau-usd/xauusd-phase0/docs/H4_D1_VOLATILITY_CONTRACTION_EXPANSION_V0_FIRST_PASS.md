# H4/D1 Volatility Contraction Expansion v0 First Pass

Generated: 2026-06-02
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h4_d1_volatility_contraction_expansion_v0` without tuning.

This was a fresh Phase 0R lower-cost candidate, not a same-family breakout-retest variant. It was SHA256-locked before implementation, passed the measured-cost structural precheck, passed synthetic smoke, and produced enough trades in all 9 real-data matrix cells. It still failed the core edge gate: 0/9 cells reached PF >= 1.30, and the Dukascopy broker window was negative across all cost cases.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Single Trade | Top 5 | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 111 | 45.05% | 1.2453 | 7.04% | 2.40% | 3 | 11.87% | 57.81% | FAIL |
| 2 | capital_com | median | 111 | 45.05% | 1.2453 | 7.04% | 2.40% | 3 | 11.87% | 57.81% | FAIL |
| 3 | capital_com | p95 | 111 | 45.05% | 1.2370 | 6.79% | 2.48% | 3 | 12.10% | 57.87% | FAIL |
| 4 | pepperstone | best_case | 75 | 42.67% | 1.2090 | 3.86% | 2.97% | 3 | 21.41% | 104.12% | FAIL |
| 5 | pepperstone | median | 75 | 42.67% | 1.2090 | 3.86% | 2.97% | 3 | 21.41% | 104.12% | FAIL |
| 6 | pepperstone | p95 | 75 | 42.67% | 1.2030 | 3.76% | 2.99% | 3 | 21.92% | 106.67% | FAIL |
| 7 | dukascopy | best_case | 165 | 31.52% | 0.7288 | -12.91% | 14.67% | 3 | 100.00% | 100.00% | FAIL |
| 8 | dukascopy | median | 165 | 31.52% | 0.7199 | -13.19% | 14.69% | 3 | 100.00% | 100.00% | FAIL |
| 9 | dukascopy | p95 | 165 | 31.52% | 0.6991 | -14.05% | 15.31% | 3 | 100.00% | 100.00% | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 0/9 | >= 7/9 | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total matrix trades | 1053 | Informational | PASS |
| Max zero-trade months | 3 | <= 3 | PASS |
| Max drawdown | 15.31% | <= 30.00% | PASS |
| Worst total return | -14.05% | >= -25.00% | PASS |
| Largest single trade contribution | Up to 100.00% | <= 10.00% | FAIL |
| Top-5 trade contribution | Up to 106.67% | <= 40.00% | FAIL |
| Cost structure | P95 cost_R precheck 0.1875R | <= 0.3000R | PASS |

## Interpretation

The candidate did meet the lower-cost/wider-stop objective structurally. The failure is not because it was too tight or too sparse. It simply did not produce enough persistent edge across brokers and time windows. The positive Capital.com and Pepperstone pockets stayed below the PF threshold, while Dukascopy was materially negative.

## Next Action

Do not proceed to deciles, multisymbol validation, intrabar review, adversarial review, EA coding, or demo observation for this version.

Do not tune `h4_d1_volatility_contraction_expansion_v0` in place. Any future revisit needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

The next Phase 0R search should continue toward lower-cost, wider-stop, independent mechanics. Given repeated OHLC-only H4/D1 failures, the highest-value next lane remains a higher-quality data class such as primary futures participation, order-flow, or licensed options-skew/CVOL evidence.
