# XAUUSD M30 Chop Dukascopy Portability V1

Research-only cross-venue replay of the frozen
`CHOP_RANGE_ROTATION_CONTINUATION_V1 / M30` specialist from commit `50bf9b5d`.
The signal and regime mechanics are imported unchanged from `chop-v1`; only the
market-data adapter and conservative cost evidence are new.

```powershell
uv run --with pandas --with numpy --with pyarrow --with pytest python -m pytest -q
uv run --with pandas --with numpy --with pyarrow python run_portability.py
```

No retrospective result authorizes Python prediction, EA consumption, demo, or
live execution.
