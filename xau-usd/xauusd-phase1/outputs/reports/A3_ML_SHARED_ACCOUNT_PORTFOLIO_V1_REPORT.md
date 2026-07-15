# A3 ML Shared-Account Portfolio V1

Classification: `SHARED_ACCOUNT_RESEARCH_FAIL`

Unguarded: 1056 trades, 0.419/trading day, stress PF 2.369, stress net $12523.49.
Measured closed-trade drawdown: $868.47.
Conservative component-sum upper boundary: $2003.38.
Minimum starting equity for that boundary to equal 15%: $13355.87.
$1,000 control simulation: 48 accepted, 1008 blocked, emergency halt `2017-03-03T07:04:00Z`.

## Gates

- `stress_profit_factor`: PASS
- `severe_cost_profit_factor`: PASS
- `minimum_frequency`: FAIL
- `six_month_stability`: PASS
- `conservative_drawdown`: FAIL
- `top10_winners_removed`: PASS
- `untouched_holdout`: FAIL
- `no_emergency_halt`: FAIL

Exact shared mark-to-market equity drawdown is unavailable from closed-trade ledgers. No demo or live action is authorized.
