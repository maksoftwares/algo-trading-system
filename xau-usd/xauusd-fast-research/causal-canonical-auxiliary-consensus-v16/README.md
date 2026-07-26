# Auxiliary Consensus V16

V16 tests whether the larger auxiliary causal dataset is useful as independent
confirmation of the locked B1+B2+B3 veto, rather than as raw inputs to another
canonical model.

A candidate is vetoed only when:

1. the locked B1+B2+B3 policy rejects it; and
2. at least two of the three auxiliary models place it in their calibrated
   bottom tail.

The lane is historical research only. It does not modify V14, V15, MT5, the
demo EAs, or any runtime authorization.

Run:

```powershell
python lock_contract.py
python run_evaluation.py
python verify.py
python -m pytest -q
```
