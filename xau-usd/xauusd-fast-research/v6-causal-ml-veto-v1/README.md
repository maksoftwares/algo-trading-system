# V6 Causal ML Veto V1

This offline research lane tests whether machine learning can veto weak trades
from the frozen V6 candidate stream without generating trades or changing V60.

The classifier trains on 117,267 broad confirmed-impulse candidates. For each
target year from 2022 through 2026:

1. training outcomes must close before the preceding calibration year, with a
   48-hour purge;
2. the previous calendar year supplies only the prediction-score distribution;
3. the fixed rule retains the top 60% of scores;
4. the model scores that year's already-frozen V6 nominations;
5. selected trades are rerouted beside immutable V60.

All history through 2026-06-30 remains development evidence. This lane cannot
authorize Python, EA, demo, live, or broker execution.

## Frozen Outcome

V1 **failed the full historical gate and is quarantined**, but showed partial
ranking value:

- accepted trades fell from 213 raw V6 trades to 177 ML-filtered trades;
- stress net stayed nearly flat: $303.59 raw versus $293.99 with ML;
- V6 PF improved from 1.177 to 1.221;
- V6 win rate improved from 34.7% to 37.9%;
- V6 closed drawdown fell from $298.34 to $199.12;
- mean annual target AUC was only 0.543;
- the final window weakened and the combined portfolio still worsened V60 PF,
  drawdown, floating drawdown, and conservative add-on limits.

This classifier must not be deployed or tuned in place. Its useful lesson is
that a binary win label ignores payoff magnitude; that hypothesis belongs in a
separate preregistered expected-value experiment.

Run:

```powershell
python run_experiment.py
python -m pytest -q
```
