# COMEX Size-Segment Flow V32

Research-only test of large-versus-small aggressive COMEX flow disagreement as
a causal XAUUSD continuation candidate.

Run from the repository root:

```powershell
uv run --with-requirements xau-usd/xauusd-fast-research/comex-size-segment-flow-v32/requirements.txt -- \
  python xau-usd/xauusd-fast-research/comex-size-segment-flow-v32/prepare_calibration.py

uv run --with-requirements xau-usd/xauusd-fast-research/comex-size-segment-flow-v32/requirements.txt -- \
  python xau-usd/xauusd-fast-research/comex-size-segment-flow-v32/lock_contract.py

uv run --with-requirements xau-usd/xauusd-fast-research/comex-size-segment-flow-v32/requirements.txt -- \
  python xau-usd/xauusd-fast-research/comex-size-segment-flow-v32/run_stage.py --stage development
```

`prepare_calibration.py` cannot read spot outcomes. Later stages cannot run
unless the immutable contract verifies, and the chronological firewall prevents
opening a later stage after an earlier failure.
