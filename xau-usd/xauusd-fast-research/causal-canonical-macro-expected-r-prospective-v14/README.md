# Causal Canonical Macro Expected-R Prospective V14

V14 is a read-only forward comparison of the deterministic V60 portfolio
against a frozen Expected-R filter using:

- B1 deterministic candidate and regime facts;
- B2 causal XAUUSD microstructure and cost state from V13;
- B3 completed Dukascopy dollar-index and Treasury-bond state.

The historical B1+B2+B3 diagnostic improved six-month, one-year, two-year,
and all-history net P&L, but underperformed raw V60 in the latest three months.
That mixed result does not authorize deployment. V14 therefore starts at the
fresh `2026-07-27T03:00:00Z` boundary and records research-only scores.

The frozen model was fit on 3,024 resolved causal candidates and uses a pooled
5% veto quantile. Missing, stale, or delayed XAU or macro features always
produce `MODEL_ABSTAIN_RETAIN_ALL`. The lane cannot write EA inputs, place
orders, or alter account risk.

Run one cycle:

```powershell
& ..\balanced-horizon-ml-v5\.venv\Scripts\python.exe run_evaluation.py
```

Run continuously:

```powershell
& ..\balanced-horizon-ml-v5\.venv\Scripts\python.exe run_evaluation.py --watch
```

Verification:

```powershell
& ..\balanced-horizon-ml-v5\.venv\Scripts\python.exe verify.py
```
