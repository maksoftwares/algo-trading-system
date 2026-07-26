# Causal Candidate Quality Action Models V4

Offline, research-only replay of the frozen Action V3 model methodology using
the corrected Expanded Causal Dataset V4.

This package changes only the two corrected prior-event-density features. It
produces a direct V4-versus-V3 comparison after evaluation and grants no MT5,
Python serving, ML shadow, demo, live, sizing, or broker authority.

```powershell
uv run --with-requirements requirements.txt python lock_contract.py
uv run --with-requirements requirements.txt python run_evaluation.py
uv run --with-requirements requirements.txt python verify.py
uv run --with-requirements requirements.txt pytest -q
```
