# One-Trade-Per-Day Native Core V58

Correctness successor to V57. It replaces FIFO-paired R1 exits and P/L with the
frozen native MT5 `position_id` reconciliation, reapplies the V50 exposure rule,
then reruns the unchanged V57 unified add-on governor and historical gates.

Run in order:

```powershell
python lock_contract.py
python run_evaluation.py
pytest -q
```

Research only. No execution authority.
