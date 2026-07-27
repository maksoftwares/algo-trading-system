# EURUSD Regime 1 Neutral causal verdict

Date: 2026-07-27

Decision: `NO_CAUSAL_NEUTRAL_EXPERT_ADMITTED`

## Objective

Approximate the 2,615 Regime 1 Neutral hindsight-oracle trades using only information available at the decision timestamp, while preserving approximately 1.50R payoff and rejecting outcome-dependent parameter repair.

The oracle is a comparison benchmark only. It never generates a causal signal, feature, training label, model threshold, or execution decision.

## Causal campaigns tested

| Campaign | Evaluation scope | Trades | Win rate | Payoff | PF | Net |
|---|---|---:|---:|---:|---:|---:|
| Four fixed rule families, forced combination | 2019–2026 H1 | 4,348 | 31.21% | 1.424 | 0.646 | -1,092.88R |
| Regularized EURUSD bar classifier | 2023–2026 H1 walk-forward | 1,019 | 32.97% | 1.438 | 0.707 | -206.15R |
| Regularized EURUSD + GBPUSD/USDJPY classifier | 2023–2026 H1 walk-forward | 1,042 | 33.40% | 1.441 | 0.722 | -198.08R |
| Constrained nonlinear cross-pair classifier | 2023–2026 H1 walk-forward | 22 | 13.64% | 1.439 | 0.227 | -15.05R |
| Raw EURUSD tick-microstructure classifier, fixed 4-pip risk | 2023–2026 H1 walk-forward | 103 | 35.92% | 1.439 | 0.807 | -13.08R |
| Raw tick-microstructure classifier, volatility-scaled risk | 2023–2026 H1 walk-forward | 779 | 35.30% | 1.449 | 0.791 | -106.94R |

None passed its locked development gate. Consequently, none is an admitted strategy or eligible for demo/live use.

## Fixed-rule family result

| Family | Trades | Win rate | Payoff | PF | Net |
|---|---:|---:|---:|---:|---:|
| Rolling one-hour sweep fade | 3,186 | 31.98% | 1.430 | 0.672 | -730.83R |
| Asia-range sweep fade | 352 | 29.26% | 1.436 | 0.594 | -103.88R |
| EMA-anchor reversion | 3,566 | 32.00% | 1.433 | 0.674 | -809.50R |
| Micro-breakout continuation | 2,498 | 27.98% | 1.430 | 0.556 | -824.95R |

The forced one-position combination matched 715 oracle trades within the same direction, UTC date, and 60-minute tolerance. That is 16.44% precision and 27.34% oracle recall, with a five-minute median timing difference. Timing similarity did not produce economic edge.

## Walk-forward controls

The learned campaigns used:

- completed M5 features and cross-asset state lagged to the latest available observation no later than completion-hour minus one hour;
- exact-timestamp completed GBPUSD/USDJPY M5 bars where applicable;
- source-hashed raw EURUSD ticks aggregated only through signal completion;
- no forward fill for missing tick or cross-pair buckets;
- future target/stop paths only as historical supervised labels;
- a purge requiring every training label exit strictly before its inference refit;
- model fitting on 2019–2020;
- threshold selection only on 2021–2022;
- annual frozen-threshold refits for 2023, 2024, 2025, and 2026;
- exact bid/ask execution, 0.70-pip minimum spread, 0.10-pip adverse slippage per side, and stop-first ambiguous bars.

Every campaign was preregistered and SHA-256 locked before its own outcome pass. All archive history had been inspected in earlier research, so these controls reduce adaptive overfitting but cannot turn the archive into pristine out-of-sample evidence.

## Best causal boundary

The closest isolated result was the fixed-risk tick model in 2023:

- 63 trades;
- 42.86% wins;
- 1.439 payoff;
- PF 1.079;
- +2.92R.

It did not persist:

| Window | Trades | Win rate | PF | Net |
|---|---:|---:|---:|---:|
| 2023 | 63 | 42.86% | 1.079 | +2.92R |
| 2024 | 16 | 12.50% | 0.206 | -11.40R |
| 2025 | 14 | 35.71% | 0.799 | -1.85R |
| 2026 H1 | 10 | 30.00% | 0.617 | -2.75R |

The volatility-scaled lifecycle increased usable frequency but remained negative in every forward window:

| Window | Trades | Win rate | Payoff | PF | Net |
|---|---:|---:|---:|---:|---:|
| 2023 | 264 | 36.74% | 1.452 | 0.844 | -26.52R |
| 2024 | 178 | 33.15% | 1.462 | 0.725 | -33.23R |
| 2025 | 235 | 37.02% | 1.441 | 0.847 | -22.82R |
| 2026 H1 | 102 | 31.37% | 1.437 | 0.657 | -24.38R |

## Frozen July prospective diagnostic

The rejected volatility-scaled model was subsequently frozen at its
development-selected 0.375 threshold before bulk acquisition of July
EURUSD, GBPUSD, and USDJPY ticks. A single refit used only labels completed
before 2026-07-01, followed by untouched inference through
2026-07-27 02:59 UTC.

| Trades | Win rate | Payoff | PF | Net | Frequency |
|---:|---:|---:|---:|---:|---:|
| 19 | 31.58% | 1.459 | 0.673 | -4.317R | 1.00/active weekday |

The preregistered evidence gate requires at least 100 completed trades and
60 calendar days; the available slice has 19 trades and 27 days. It
therefore remains an accumulating, non-promotional diagnostic. Its metric
gate also failed, and it does not rescue the historical model.

## Interpretation

At a realized payoff near 1.44, break-even requires approximately 41% wins. The best stable causal variants remained around 33–35%. The 100%-winning Neutral oracle does not reveal a learnable process: it scans both future directions, keeps early target-first paths, and deletes every failure.

The evidence does not support claiming that Regime 1 has been solved. Further retrospective threshold, hour, feature, or model search on this archive would increase overfitting rather than improve causal evidence.

## Next legitimate evidence

Progress now requires at least one source not adaptively exhausted here:

1. a prospectively collected, untouched EURUSD tick period;
2. event-time macroeconomic surprise data known at release;
3. genuine executed-flow or multi-venue order-book imbalance rather than quoted Dukascopy volume;
4. an explicit relaxation of the requested frequency/payoff objective.

Until then, Regime 1 remains `CASH`.

## Reproduce

```powershell
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_causal.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_walkforward.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_crosspair.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_crosspair_nonlinear.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_tick_microstructure.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_tick_volatility.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_prospective.py
```
