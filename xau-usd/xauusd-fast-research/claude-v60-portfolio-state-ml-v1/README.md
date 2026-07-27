# Claude V60 Portfolio-State ML V1

Tests whether a model can improve the deployed V60 portfolio by using information
its nine sleeves cannot see. Preregistered before training; see
`PREREGISTRATION.md`.

Historical research only. `ml_runtime_authorized: false` in the V60 config — this
lane authorizes no runtime, EA, demo, live or broker change.

## Frozen Outcome

**CLAUDE_V60_PORTFOLIO_STATE_ML_V1_GATE_FAIL_QUARANTINED_STRONG_SIGNAL_RECORDED**

- The preregistered hypothesis (portfolio state is orthogonal information) is
  **refuted by ablation**: it adds $97 of net and costs 0.79 of net/DD.
- A different result survived: **P&L-regression sizing on market features** takes
  V60 from net/DD 17.05 to **19.94**, net $5,082 to **$6,694 (+32%)**.
- It fails gate 4 (improves in 4 of 6 years, needs 5) and is quarantined.

## The finding worth carrying forward

| score quintile | mean $/trade | win rate |
|---|---|---|
| Q1 | +0.649 | 44.3% |
| Q2 | +0.541 | 41.2% |
| Q5 | +5.672 | 50.7% |

**Q1 and Q2 are near-zero winners, not losers.** A veto removes positive
expectancy, so profit factor rises while net P&L falls — which is exactly what
`v6-causal-ml-veto-v1` measured (PF 1.177 -> 1.221, net $303.59 -> $293.99) and
what four further lanes reproduced.

**The model can identify low-expectancy trades. It cannot identify losing trades.**
Future lanes here should be sizing policies, not filters.

## Also recorded

- **Permutation importance is not incremental value.** The portfolio block held
  27% of importance and three of the top five features, yet contributed nothing
  under ablation. Use the ablation.
- **A data defect that would have biased the model:** `R1_NATIVE_POSITION` records
  no `risk_usd` (444/444 NaN), which silently dropped 35% of the book including
  83% of the most profitable sleeve. Coverage 65.1% -> 100% after the fix.

## Layout

```
PREREGISTRATION.md     written before training; gates fixed in advance
outputs/RESULT.md      gate outcome, ablation, year detail, fragility
src/features.py        market + portfolio-state features, causality assertion
src/walkforward.py     three targets x six policies, annual walk-forward
src/evaluate.py        all four gates on a common scored set
```

Run:

```powershell
& ..\balanced-horizon-ml-v5\.venv\Scripts\python.exe src\features.py
& ..\balanced-horizon-ml-v5\.venv\Scripts\python.exe src\walkforward.py
& ..\balanced-horizon-ml-v5\.venv\Scripts\python.exe src\evaluate.py
```
