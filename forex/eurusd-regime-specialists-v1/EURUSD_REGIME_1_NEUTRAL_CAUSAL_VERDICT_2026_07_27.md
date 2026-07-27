# EURUSD Regime 1 Neutral causal verdict

Date: 2026-07-27

Decision: `NO_CAUSAL_NEUTRAL_EXPERT_ADMITTED`

## Objective

Approximate the 2,615 Regime 1 Neutral hindsight-oracle trades using only information available at the decision timestamp, while preserving approximately 1.50R payoff and rejecting outcome-dependent parameter repair.

The oracle is a comparison benchmark only in the first six campaigns. A
separately locked seventh campaign uses historical oracle membership as a
purged supervised label, but forbids oracle rows at inference. An eighth
controlled campaign adds synchronized completed DXY and Treasury M5
features to that model. The oracle never generates a causal feature or
execution decision.

## Causal campaigns tested

| Campaign | Evaluation scope | Trades | Win rate | Payoff | PF | Net |
|---|---|---:|---:|---:|---:|---:|
| Four fixed rule families, forced combination | 2019–2026 H1 | 4,348 | 31.21% | 1.424 | 0.646 | -1,092.88R |
| Regularized EURUSD bar classifier | 2023–2026 H1 walk-forward | 1,019 | 32.97% | 1.438 | 0.707 | -206.15R |
| Regularized EURUSD + GBPUSD/USDJPY classifier | 2023–2026 H1 walk-forward | 1,042 | 33.40% | 1.441 | 0.722 | -198.08R |
| Constrained nonlinear cross-pair classifier | 2023–2026 H1 walk-forward | 22 | 13.64% | 1.439 | 0.227 | -15.05R |
| Raw EURUSD tick-microstructure classifier, fixed 4-pip risk | 2023–2026 H1 walk-forward | 103 | 35.92% | 1.439 | 0.807 | -13.08R |
| Raw tick-microstructure classifier, volatility-scaled risk | 2023–2026 H1 walk-forward | 779 | 35.30% | 1.449 | 0.791 | -106.94R |
| Purged direct Neutral-oracle imitation classifier | 2023–2026 H1 walk-forward | 1,246 | 31.54% | 1.420 | 0.654 | -306.20R |
| Synchronous DXY/Treasury oracle-imitation extension | 2023–2026 H1 walk-forward | 638 | 30.56% | 1.439 | 0.633 | -166.43R |

None passed all locked chronological admission gates. Consequently, none is
an admitted strategy or eligible for demo/live use.

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

## Direct oracle-imitation boundary

A separately locked classifier was trained on exact historical Neutral
oracle membership rather than generic target-first outcomes. It used causal
five-minute bar, cross-asset, time-cycle, and tick features, a 12-hour label
purge, 2019-2022 development, and annual expanding refits for 2023-2026 H1.

The model achieved 23.03% exact-match precision, 27.52% exact recall, and
31.30% same-side precision within 15 minutes across the forward windows.
This passed its behavioral-imitation gate. Economics nevertheless failed in
every window: 1,246 trades, 31.54% wins, 1.420 payoff, PF 0.654, and
-306.20R.

All 287 exact oracle matches won, while the 959 accepted nonmembers won only
11.05% and lost -729.55R. The dominant coefficient was the UTC time cycle,
reflecting that 2,482 of 2,615 Neutral oracle rows occur in the first UTC
hour because the hindsight generator scans from midnight. The model learned
that construction artifact but could not identify the future-winning
direction.

## Synchronous cross-asset boundary

A final controlled extension added 18 exact-timestamp, completed M5
DOLLARIDXUSD and USTBONDTRUSD features to the direct imitation model.
Source rows required both symbols and were never forward-filled. The
525,099-row source was hash-pinned, and 266 independently produced overlap
rows reproduced with maximum absolute error 0.0.

The extension achieved 24.76% exact precision and 36.68% same-side
precision within 15 minutes, but only 15.15% exact recall. Economics failed
in every window: 638 trades, 30.56% wins, 1.439 payoff, PF 0.633, and
-166.43R. Compared with the prior imitation baseline, exact precision rose
only 1.73 percentage points while PF fell by 0.0209.

All 158 exact oracle members won +233.08R, while the 480 accepted
nonmembers won only 7.71% and lost -399.50R. The UTC time-cycle coefficient
remained dominant; the explicit DXY/Treasury joint-direction coefficient
was essentially zero. Synchronized quoted cross-asset behavior did not
provide the missing causal direction.

## Interpretation

At a realized payoff near 1.44, break-even requires approximately 41% wins. The best stable causal variants remained around 33–35%. The 100%-winning Neutral oracle does not reveal a learnable process: it scans both future directions, keeps early target-first paths, and deletes every failure.

The evidence does not support claiming that Regime 1 has been solved. Further retrospective threshold, hour, feature, or model search on this archive would increase overfitting rather than improve causal evidence.

## Next legitimate evidence

Progress now requires at least one source not adaptively exhausted here:

1. a prospectively collected, untouched EURUSD tick period;
2. event-time macroeconomic surprise data known at release;
3. genuine executed-flow or multi-venue order-book imbalance rather than
   quoted Dukascopy volume; synchronized DXY/Treasury quoted M5 behavior has
   now also failed;
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
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_oracle_imitation.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_synchronous_crossasset.py
```
