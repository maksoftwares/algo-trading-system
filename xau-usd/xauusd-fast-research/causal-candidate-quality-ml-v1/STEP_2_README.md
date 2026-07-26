# Causal Candidate Quality ML V1 - Step 2

`run_step_2_audit.py` performs the authorized metadata-only source and candidate
audit. It reads only explicit identity, lineage, action, and timestamp columns;
economic outcome columns are blocked. It writes the seven required audit reports
and a metadata-only canonical candidate registry under `outputs/step_2`.

Run with an environment containing pandas and PyArrow:

```powershell
python run_step_2_audit.py
python -m unittest discover -s tests -v
```

Step 2 does not build counterfactual labels, materialize model features, fit a
model, change the V59/V60 demo runtime, or authorize ML execution.
