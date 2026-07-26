# Capital Multi-Symbol Prospective V1

This package records synchronized, read-only Capital.com ticks from demo account
`1033030`. It supplies a new prospective data foundation for later XAUUSD
regime research; it is not a trading strategy.

The frozen source set is:

- `XAUUSD`
- `XAGUSD`
- `DXY`
- `US500`
- `EURUSD`
- `USDJPY`

Collection begins at `2026-07-27T00:00:00Z`. Files are written under
`D:/AlgoTradingData/prospective/capital-multisymbol-v1`. The collector imports
MetaTrader5 only to read account, symbol, and tick state. It contains no order
API and cannot authorize Python prediction, EA consumption, demo execution, or
live execution.

Run with the repository's Phase 0 Python environment:

```powershell
& xau-usd\xauusd-phase0\.venv\Scripts\python.exe `
  multi-asset\data-foundation\capital-multisymbol-prospective-v1\run_collector.py
```

Use `--once` for a single collection pass and `--preflight` to verify the
account, terminal, symbols, and authority boundary without writing ticks.

