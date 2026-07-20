# Capital R4 Chop Forward V34

Read-only Capital quote adapter for the frozen V26 R4 chop specialist.

## Verify and lock

```powershell
python verify_historical_parity.py
python lock_contract.py
```

## Run

```powershell
python run_shadow.py --once
python run_shadow.py --poll-seconds 60
```

Runtime files are written below
`C:/MT5PortableProspectiveCollector/MQL5/Files/r4_chop_shadow_v34`.
The process emits candidates only; it has no broker-action path.
