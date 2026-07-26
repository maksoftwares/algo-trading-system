# Causal Specialist Winner/Loser Diagnostic V1

This package investigates whether any entry-time measurement consistently
separates stressed winning and losing candidates inside each canonical
specialist family.

It uses the locked 3,752-row Step 3 dataset and its purged expanding
walk-forward assignments. The analysis:

- keeps specialists separate;
- matches winners and losers within family, direction, calendar year, UTC
  session, stop mode, and target mode;
- measures full-history effects only as exploratory descriptions;
- learns every walk-forward feature direction from the fit partition only;
- reports thin or unstable evidence as insufficient;
- never changes MT5, the deterministic demo portfolio, risk controls, or ML
  runtime authority.

Historical outcomes were already exposed before this package was created.
Therefore, a reported lead is a feature-discovery hypothesis, not promotion
evidence. It must survive a separately frozen prospective test.

Run:

```powershell
uv run --with-requirements requirements.txt python lock_contract.py
uv run --with-requirements requirements.txt python run_analysis.py
uv run --with-requirements requirements.txt python verify.py
uv run --with-requirements requirements.txt python -m pytest -q
```
