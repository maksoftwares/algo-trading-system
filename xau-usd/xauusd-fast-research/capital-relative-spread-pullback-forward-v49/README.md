# Capital Relative-Spread Pullback Forward V49

V49 density-calibrates one quote-level continuation family without outcomes,
locks the selected policy, and evaluates it only on complete Capital demo days
beginning July 21, 2026.

```powershell
uv run --with-requirements requirements.txt python prepare_calibration.py
uv run --with-requirements requirements.txt python lock_contract.py --write
uv run --with-requirements requirements.txt python run_forward_evaluation.py
uv run --with-requirements requirements.txt python -m pytest tests -q
```

No command in this package can place an order.
