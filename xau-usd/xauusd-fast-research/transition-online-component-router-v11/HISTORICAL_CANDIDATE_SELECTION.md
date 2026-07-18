# Transition V11 Historical Candidate Selection

Selected attempt: `27135`

Mechanic: `TRAILING_DRAWDOWN_GATE`

Frozen parameters:

```json
{
  "cold_start": "HALF",
  "lookback_days": 180,
  "minimum_history": 5,
  "threshold": 2.0,
  "weak_multiplier": 0.25
}
```

The candidate is the first row under the preregistered shortlist ordering: economic
pass, gate count, minimum-era PF, total PF, trade count, and attempt number.

- Trades: 330.
- Stress net: +14.241947 R.
- Stress PF: 1.288909.
- Minimum-era PF: 1.205331.
- Minimum-era average: +0.029390 R.
- Closed-trade drawdown: 3.821299 R.
- Net after removing five largest winners: +4.411986 R.
- Daily p-value: 0.043630.
- Benjamini-Hochberg q-value across 1,000 policies: 0.271266.

This is a historical discovery candidate. It is not FDR-supported, independently
replicated, prospectively confirmed, training-authorized, or execution-authorized.
