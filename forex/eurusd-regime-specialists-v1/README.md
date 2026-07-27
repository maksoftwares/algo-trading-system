# EURUSD regime specialists v1

This package tests the Gold-style trajectory on EURUSD: causal market regimes, exclusive specialist ownership, and a portfolio composed only from specialists that survive frozen chronological and cost gates.

Two outcome-locked experiments were run:

1. M30-only seed: stopped before P&L because its opportunity census failed.
2. M15/M30 two-clock ensemble: passed capacity, but every specialist failed admission after exact-cost backtesting.

Final status: `RESEARCH_FAILURE_NOT_DEMO_READY`.

Key reports:

- `EURUSD_TWO_CLOCK_ENSEMBLE_VERDICT_2026_07_27.md`
- `EURUSD_LAST_6_MONTHS_BACKTEST_2026_01_TO_2026_06.md`
- `outputs/two_clock/backtest_results.json`

Run with:

```powershell
uv run --with pandas --with numpy --with pyarrow python run_ensemble.py census
uv run --with pandas --with numpy --with pyarrow python run_ensemble.py backtest
```
