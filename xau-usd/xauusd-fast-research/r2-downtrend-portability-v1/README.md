# R2 Downtrend Portability V1

This research-only package ports two frozen MT5 R2 short mechanisms to
continuous Dukascopy bid/ask data from 2010-01 through 2026-06. Signals use
sealed M5 bars; entries and exits use chronological raw ticks.

Run order:

1. `python lock_contract.py`
2. `python run_research.py`

The runner is one-shot. It never contacts a broker, requests paid data, trains
a model, or authorizes execution.
