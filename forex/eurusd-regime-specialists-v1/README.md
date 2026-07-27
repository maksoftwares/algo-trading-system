# EURUSD regime specialists v1

This package tests the Gold-style trajectory on EURUSD: causal market regimes, exclusive specialist ownership, and a portfolio composed only from specialists that survive frozen chronological and cost gates.

Outcome-locked causal experiments and one intentionally contaminated control were run:

1. M30-only seed: stopped before P&L because its opportunity census failed.
2. M15/M30 two-clock ensemble: passed capacity, but every specialist failed admission after exact-cost backtesting.
3. A 1.50R/12-hour asymmetric exit: realized payoff reached 1.428 overall and 1.454 in the latest six months, but full-history win rate was only 38.75% and PF was 0.904.
4. M15 exhaustion plus M5 structure confirmation: capacity passed at 2.10 signals/day, but full-history win rate fell to 37.15% and PF to 0.841. The price-confirmation family is closed.
5. DXY-confirmed London and New York session handoffs: capacity passed at 0.254 signals/weekday, but full-history win rate was 33.87% and PF was 0.744. The cross-asset continuation family is closed.
6. Gold-style retrospective selection: the dense perfect-foresight oracle reached exactly 4.00 trades on every one of 1,954 archived weekdays (7,816 trades) with 100% wins by scanning future long/short paths from M5 entries. Its average winner was 1.475R and PF is infinite because every loss was deleted. This is direct path leakage, not a strategy.
7. Regime 1 Neutral causal reconstruction: four rule families, regularized bar models, synchronized GBPUSD/USDJPY features, constrained nonlinear models, raw EURUSD tick microstructure, and volatility-scaled risk were preregistered and tested chronologically. None qualified development or passed the forward gates. The best isolated year was tick microstructure in 2023 at PF 1.079; it collapsed afterward. Regime 1 remains cash.
8. Frozen July prospective diagnostic: the rejected volatility-scaled tick model was locked before bulk July acquisition and run without retuning. It produced 19 trades, 31.58% wins, 1.459 payoff, PF 0.673, and -4.317R. Both the 100-trade/60-day sample gate and the metric gate failed, so the result cannot admit or rescue the model.
9. Direct causal oracle imitation: a purged five-minute classifier learned meaningful entry resemblance (23.03% exact precision and 27.52% recall), but this was mostly the oracle's midnight scan artifact. Its 1,246 chronological trades won 31.54%, returned PF 0.654, and lost 306.20R. Every forward year failed.
10. Synchronous DXY/Treasury oracle imitation: 18 completed M5 cross-asset features raised exact-match precision only to 24.76% while recall fell to 15.15%. Its 638 chronological trades won 30.56%, returned PF 0.633, and lost 166.43R. Every forward year failed, so this quoted-cross-asset extension is closed.

Final status: `RESEARCH_FAILURE_NOT_DEMO_READY`.

Key reports:

- `EURUSD_TWO_CLOCK_ENSEMBLE_VERDICT_2026_07_27.md`
- `EURUSD_LAST_6_MONTHS_BACKTEST_2026_01_TO_2026_06.md`
- `EURUSD_ASYMMETRIC_PAYOFF_VERDICT_2026_07_27.md`
- `EURUSD_CONFIRMED_REVERSAL_VERDICT_2026_07_27.md`
- `EURUSD_CROSSASSET_HANDOFF_VERDICT_2026_07_27.md`
- `EURUSD_RETROSPECTIVE_OVERFIT_DEMONSTRATION_2026_07_27.md`
- `EURUSD_REGIME_1_NEUTRAL_CAUSAL_VERDICT_2026_07_27.md`
- `EURUSD_NEUTRAL_PROSPECTIVE_JULY_RESULT_2026_07_27.md`
- `EURUSD_NEUTRAL_ORACLE_IMITATION_VERDICT_2026_07_27.md`
- `EURUSD_NEUTRAL_SYNCHRONOUS_CROSSASSET_VERDICT_2026_07_27.md`
- `outputs/two_clock/backtest_results.json`
- `outputs/asymmetric_payoff/RESULT.json`
- `outputs/confirmed_reversal/RESULT.json`
- `outputs/crossasset_handoff/RESULT.json`
- `outputs/retrospective_overfit/RESULT.json`
- `outputs/neutral_causal/RESULT.json`
- `outputs/neutral_walkforward/RESULT.json`
- `outputs/neutral_crosspair/RESULT.json`
- `outputs/neutral_crosspair_nonlinear/RESULT.json`
- `outputs/neutral_tick_microstructure/RESULT.json`
- `outputs/neutral_tick_volatility/RESULT.json`
- `outputs/neutral_prospective_july/RESULT.json`
- `outputs/neutral_oracle_imitation/RESULT.json`
- `outputs/neutral_synchronous_crossasset/RESULT.json`

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
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_causal.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_walkforward.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_crosspair.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_crosspair_nonlinear.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_tick_microstructure.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_tick_volatility.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_prospective.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_oracle_imitation.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_synchronous_crossasset.py
```
