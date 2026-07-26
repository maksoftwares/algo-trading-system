# Causal Candidate Quality ML V1

This package freezes Step 1 of the next XAUUSD ML phase. It defines the first
research question, evidence boundaries, permitted data roles, model budget, and
pass/fail gates before a candidate inventory, counterfactual labels, features, or
model outcomes are opened.

Step 1 does not build a dataset or train a model. It does not change the active
V59/V60 demo portfolio. Run `python lock_contract.py` to create or verify the
immutable rule lock, then run `python -m unittest discover -s tests -v`.

The next allowed stage is a metadata-only data and candidate inventory. Any
economic label generation or model fitting before that inventory is reviewed
violates this contract.
