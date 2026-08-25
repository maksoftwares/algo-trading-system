# V60 Dynamic Capacity Twin Prospective V19

V19 is a strictly read-only prospective portfolio twin. It resolves every
eligible post-boundary XAUUSD candidate from completed Capital.com raw-tick
files, then independently replays deployed V60 and frozen Dynamic V6. Its main
purpose is to measure replacement-capacity trades that the executed-trade V6
observer cannot see.

It never imports MetaTrader5 and cannot send, modify, or close orders. A pass is
review evidence only and never authorizes deployment.

## Rebuild and verify

Use the V60 runtime Python environment or install `requirements.txt`, then run:

```powershell
python -m pytest -q
python lock_contract.py
python run_evaluation.py
```

The contract must be locked before `2026-08-26T00:00:00Z`. Runtime evidence is
written under `D:/AlgoTradingData/prospective/v60-dynamic-capacity-twin-v19`.
For supervised collection, use `run_evaluation.py --poll-seconds 3600`.

Do not regenerate the lock after the boundary. Any code or dependency change
requires a new version and a new prospective boundary.
