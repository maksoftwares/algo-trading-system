# XAUUSD Independent Specialists V1

Bounded, research-only discovery of mechanically distinct XAUUSD specialists on
the verified 2016-07 through 2026-06 Dukascopy Bid/Ask feature cache.

The campaign is frozen in `config/independent_specialists_v1.json`. Run it with:

```powershell
uv run --with pandas --with numpy --with pyarrow --with pytest python run_research.py
```

The campaign cannot authorize Python predictions, EA consumption, demo orders, or
live trading. Retrospective survivors require exact-tick parity and prospective
forward-shadow evidence.
