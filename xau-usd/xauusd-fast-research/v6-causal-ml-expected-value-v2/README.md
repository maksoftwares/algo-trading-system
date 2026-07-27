# V6 Causal ML Expected Value V2

V2 tests the specific failure diagnosed in the quarantined V1 classifier:
binary win/loss labels ignore payoff magnitude and can reject large winners.

This lane reuses V1's source-hashed causal features and 117,267-row training
corpus. A shallow histogram gradient-boosted regressor predicts a robust utility
target clipped to `[-1.25R, +3R]`. For each target year, it trains only on
outcomes closed at least 48 hours before that year. A frozen economic rule keeps
trades with predicted utility above zero.

Historical research only. No Python, EA, demo, live, or broker execution is
authorized.

## Frozen Outcome

V2 **failed and is quarantined**:

- 29 of 277 nominations were selected and 24 were accepted beside V60;
- V2 V6 stress P&L was -$161.25 with PF 0.593;
- mean annual target AUC was 0.521;
- mean annual rank correlation was 0.034;
- only two of five years had positive rank correlation;
- V60 plus V2 fell to $5,297.14 stress net, PF 1.602, and $320.42 closed
  drawdown versus unchanged V60 at $5,458.39, PF 1.649, and $298.06.

The result rejects payoff-size regression with this feature set. The separate
V1 binary veto remains the better ML benchmark and must not be altered by V2.

Run:

```powershell
python run_experiment.py
python -m pytest -q
```
