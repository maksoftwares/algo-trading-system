# V8 Auxiliary Veto V18

V18 is an offline historical experiment. It tests one frozen
`V8_RETEST_HEALTH` bottom-tail veto using V15's causal nonlinear auxiliary
score. All other B123 decisions are immutable, and missing evidence preserves
B123.

Run only after preregistration:

```powershell
python lock_contract.py
python run_evaluation.py
python verify.py
```

No runtime or trading authority is granted.
