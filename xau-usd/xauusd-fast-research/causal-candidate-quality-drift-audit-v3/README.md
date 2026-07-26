# Causal Candidate Quality Drift Audit V3

This package replays the frozen Action V3 F2026 policies on their calibration
and test years, then separates feature, score, composition, and within-stratum
outcome changes. It is diagnostic only and has no trading authority.

Run in order:

```powershell
uv run --with-requirements requirements.txt python lock_contract.py
uv run --with-requirements requirements.txt python run_audit.py
uv run --with-requirements requirements.txt python verify.py
uv run --with-requirements requirements.txt pytest -q
```
