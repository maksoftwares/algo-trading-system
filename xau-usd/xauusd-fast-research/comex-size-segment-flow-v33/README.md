# COMEX Size-Segment Flow V33

Outcome-blind candidate-density repair for the V32 large-versus-small COMEX
aggressor-flow hypothesis. V33 reuses the hashed V32 causal and economic engine;
it changes only the registered frequency grid before outcomes.

```powershell
uv run --with-requirements xau-usd/xauusd-fast-research/comex-size-segment-flow-v33/requirements.txt -- \
  python xau-usd/xauusd-fast-research/comex-size-segment-flow-v33/prepare_calibration.py

uv run --with-requirements xau-usd/xauusd-fast-research/comex-size-segment-flow-v33/requirements.txt -- \
  python xau-usd/xauusd-fast-research/comex-size-segment-flow-v33/lock_contract.py

uv run --with-requirements xau-usd/xauusd-fast-research/comex-size-segment-flow-v33/requirements.txt -- \
  python xau-usd/xauusd-fast-research/comex-size-segment-flow-v33/run_stage.py --stage development
```

