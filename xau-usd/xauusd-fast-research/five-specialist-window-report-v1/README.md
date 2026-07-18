# Five-Specialist Window Report V1

This package calculates trailing 3-month, 6-month, 1-year, and 2-year results
for the five frozen historical specialist ledgers and their additive combination.

The common evidence cutoff is `2026-07-01T00:00:00Z`. A trade belongs to a
window when its realized exit time is inside `[window_start, cutoff)`.

## P&L basis

- R1 uses exact MT5 closed P&L for its frozen 0.01-lot book.
- R2 through R5 use conservative raw-tick stress P&L converted to a 0.01-lot
  dollar equivalent as `stress_net_r * risk_usd`.
- The additive combined result permits simultaneous specialist positions. It
  is not a shared-risk-engine backtest.
- Drawdown is closed-trade drawdown from realized exits. It is not floating
  equity drawdown.

Run:

```powershell
python build_report.py
```

This report is historical development evidence. It does not authorize training
or execution.
