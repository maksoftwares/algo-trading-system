# A3 ML Six-Iteration Final Qualification V1

Classification: `SIX_ITERATION_RESEARCH_COMPLETE_NO_DEPLOYABLE_SYSTEM`

## Bottom Line

The R1/R2 historical foundation is profitable: 1056 trades, stress net $12523.49, stress PF 2.369.
It is not deployable under this campaign: frequency is 0.419/day, no new specialist or ML policy survived, and shared-account risk/holdout gates failed.
Measured closed-trade drawdown is $868.47; the conservative component-sum upper boundary is $2003.38.

## Monte Carlo

| Starting capital | Ruin probability | P(DD >= 15%) | Median max DD | P95 max DD | Median ending equity |
|---:|---:|---:|---:|---:|---:|
| $1000.00 | 2.22% | 87.65% | 30.17% | 80.87% | $12046.47 |
| $13355.87 | 0.00% | 0.30% | 5.61% | 9.82% | $24485.65 |

## Gates

- `minimum_frequency`: FAIL
- `monte_carlo_drawdown`: FAIL
- `monte_carlo_risk_of_ruin`: FAIL
- `stress_profit_factor`: PASS
- `six_month_stability`: PASS
- `external_specialist_survivor`: FAIL
- `ml_ranker_survivor`: FAIL
- `shared_portfolio_pass`: FAIL
- `untouched_holdout`: FAIL

## Decision

The six research iterations are complete. Python demo prediction, EA consumption, demo trading, and live trading remain unauthorized.
