# XAUUSD High-Frequency Expansion V1

Research-only candidate expansion and ranking campaign.

The campaign keeps the frozen five-specialist Core unchanged. It converts three
high-coverage MT5 mechanical signal streams into timestamped candidate events,
joins only information available at decision time from the verified Dukascopy
bid/ask cache, creates conservative action labels, and searches a fixed set of
ranking policies behind chronological firewalls.

Run:

```powershell
uv run --with-requirements requirements.txt python build_dataset.py
uv run --with-requirements requirements.txt python run_search.py
uv run --with-requirements requirements.txt pytest -q
```

No output from this directory authorizes Python prediction, EA attachment, demo
trading, live trading, or broker action.
