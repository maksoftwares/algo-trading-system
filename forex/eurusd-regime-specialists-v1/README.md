# EURUSD regime specialists v1

This package tests the Gold-style trajectory on EURUSD: causal market regimes, exclusive specialist ownership, and a portfolio composed only from specialists that survive frozen chronological and cost gates.

Five outcome-locked experiments and one intentionally contaminated control were run:

1. M30-only seed: stopped before P&L because its opportunity census failed.
2. M15/M30 two-clock ensemble: passed capacity, but every specialist failed admission after exact-cost backtesting.
3. A 1.50R/12-hour asymmetric exit: realized payoff reached 1.428 overall and 1.454 in the latest six months, but full-history win rate was only 38.75% and PF was 0.904.
4. M15 exhaustion plus M5 structure confirmation: capacity passed at 2.10 signals/day, but full-history win rate fell to 37.15% and PF to 0.841. The price-confirmation family is closed.
5. DXY-confirmed London and New York session handoffs: capacity passed at 0.254 signals/weekday, but full-history win rate was 33.87% and PF was 0.744. The cross-asset continuation family is closed.
6. Gold-style retrospective selection: the dense perfect-foresight oracle reached exactly 4.00 trades on every one of 1,954 archived weekdays (7,816 trades) with 100% wins by scanning future long/short paths from M5 entries. Its average winner was 1.475R and PF is infinite because every loss was deleted. This is direct path leakage, not a strategy.

Final status: `RESEARCH_FAILURE_NOT_DEMO_READY`.

Key reports:

- `EURUSD_TWO_CLOCK_ENSEMBLE_VERDICT_2026_07_27.md`
- `EURUSD_LAST_6_MONTHS_BACKTEST_2026_01_TO_2026_06.md`
- `EURUSD_ASYMMETRIC_PAYOFF_VERDICT_2026_07_27.md`
- `EURUSD_CONFIRMED_REVERSAL_VERDICT_2026_07_27.md`
- `EURUSD_CROSSASSET_HANDOFF_VERDICT_2026_07_27.md`
- `EURUSD_RETROSPECTIVE_OVERFIT_DEMONSTRATION_2026_07_27.md`
- `outputs/two_clock/backtest_results.json`
- `outputs/asymmetric_payoff/RESULT.json`
- `outputs/confirmed_reversal/RESULT.json`
- `outputs/crossasset_handoff/RESULT.json`
- `outputs/retrospective_overfit/RESULT.json`

Run with:

```powershell
uv run --with pandas --with numpy --with pyarrow python run_ensemble.py census
uv run --with pandas --with numpy --with pyarrow python run_ensemble.py backtest
uv run --with pandas --with numpy --with pyarrow python run_asymmetric.py
uv run --with pandas --with numpy --with pyarrow python run_confirmed_reversal.py census
uv run --with pandas --with numpy --with pyarrow python run_confirmed_reversal.py backtest
uv run --with pandas --with numpy --with pyarrow python run_crossasset_handoff.py census
uv run --with pandas --with numpy --with pyarrow python run_crossasset_handoff.py backtest
uv run --with pandas --with numpy --with pyarrow python run_retrospective_overfit.py
```
