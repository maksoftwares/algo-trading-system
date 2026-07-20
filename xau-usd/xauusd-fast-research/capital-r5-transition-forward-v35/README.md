# Capital R5 Transition Forward V35

Read-only current-feed adapter for the frozen R5 transition specialist.

```powershell
python verify_historical_parity.py
python lock_contract.py
python backfill_macro.py
python run_shadow.py --once
python run_shadow.py --poll-seconds 300
```

The backfiller downloads only free official Dukascopy data. Forward candidates
are recorded without broker action or economic outcome resolution.
