# HistData XAUUSD Independent-Feed Audit V47

V47 audits one free HistData XAU/USD tick month against the locked Dukascopy M5
foundation. It decides whether the source is valid and sufficiently non-duplicate
to support a later, separately preregistered cross-venue experiment.

Run:

```powershell
uv run --with-requirements requirements.txt python lock_contract.py --verify
uv run --with-requirements requirements.txt python run_audit.py
uv run --with-requirements requirements.txt python -m pytest tests -q
```

This package has no execution authority and contains no strategy outcomes.
