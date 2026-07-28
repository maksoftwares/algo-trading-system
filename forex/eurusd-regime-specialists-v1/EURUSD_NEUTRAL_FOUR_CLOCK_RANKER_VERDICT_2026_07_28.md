# EURUSD Neutral four-clock paired ranker verdict

Date: 2026-07-28

Decision: `REJECTED_NEUTRAL_FOUR_CLOCK_PAIRED_RANKER_V1`

## What changed

This campaign addressed a structural limitation in the earlier oracle
imitation model.

The earlier model treated LONG and SHORT as independent rare-event rows,
selected a probability threshold on development data, and averaged only
1.37 trades per weekday. The new model:

- paired LONG and SHORT at the identical timestamp;
- trained directly on each 16-feature LONG-minus-SHORT contrast;
- learned only from historical timestamps where exactly one target-first
  side existed;
- used strict paired label-time purging before every inference window;
- used fixed L2 logistic regression without feature, threshold, clock, or
  hyperparameter selection;
- forced one causal side at 00:00, 00:15, 00:30, and 00:45 UTC;
- retained every no-winner timestamp at inference.

The complete rule, source hashes, causal census, admission gates, code, and
tests were SHA-256 locked before the first fit and outcome pass.

## Frequency

The frequency contract passed exactly:

- 433 eligible Neutral evaluation dates;
- 1,732 trades;
- four trades on every eligible date;
- 100% exact-four execution coverage.

The strategy traded only 1.21 times per all active weekdays in the latest
six months because Regime 1 owned 39 of 129 weekdays. It nevertheless
executed four times on every one of those 39 Neutral days.

## Chronological result

| Window | Trades | Win rate | Payoff | PF | Net | Conditional side accuracy |
|---|---:|---:|---:|---:|---:|---:|
| 2021-2022 development holdout | 696 | 32.90% | 1.439 | 0.706 | -140.90R | 51.81% |
| 2023 validation | 296 | 34.80% | 1.399 | 0.747 | -51.55R | 53.93% |
| 2024 validation | 264 | 35.23% | 1.439 | 0.783 | -38.10R | 54.07% |
| 2025 pseudo-OOS | 320 | 32.81% | 1.439 | 0.703 | -65.58R | 52.50% |
| 2026 H1 pseudo-OOS | 156 | 29.49% | 1.438 | 0.601 | -44.98R | 51.11% |
| Overall | 1,732 | 33.26% | 1.432 | 0.714 | -341.10R | 52.60% |

Every window failed. Conditional side accuracy measures the chosen direction
only on timestamps where exactly one 1.5R target-first side was available.
The model improved on a 50% coin flip by only 2.60 percentage points
overall. The frozen requirement was 70%, approximately the level needed to
lift unconditional win rate into the requested range while still trading
the no-winner timestamps.

The predicted LONG rate was 49.13%, so failure was not caused by a persistent
one-side bias.

## Fixed-clock diagnostics

All four preregistered clocks were negative:

| Clock UTC | Trades | Win rate | PF | Net |
|---|---:|---:|---:|---:|
| 00:00 | 433 | 35.33% | 0.781 | -63.18R |
| 00:15 | 433 | 30.95% | 0.641 | -110.78R |
| 00:30 | 433 | 33.49% | 0.724 | -81.58R |
| 00:45 | 433 | 33.26% | 0.713 | -85.58R |

These are rejection diagnostics only. No clock may be selected or removed
after viewing its result.

## Model stability

The leading paired coefficients were reasonably stable after 2023:

- EURUSD H1 directional gap was consistently negative;
- asymmetric room was consistently positive;
- DXY directional gap was consistently positive;
- one-bar return and Treasury gap appeared repeatedly.

Coefficient stability did not translate to usable directional accuracy.
This is important: regularization and chronological refitting behaved as
intended, but the available features did not contain enough side
information.

## Robustness and oracle resemblance

- Removing the top 5% of winners: PF 0.606 and -469.43R.
- Adding another 0.5 pip per trade: PF 0.582 and -557.60R.
- Daily 0.25R portfolio: PF 0.500, -85.28 portfolio R, and 85.28R maximum
  drawdown.
- Exact oracle precision and recall: approximately 21.0%.
- Same-side 15-minute oracle precision and recall: approximately 40.4%.

The direct paired formulation raised PF from 0.654 for the prior independent
oracle-imitation classifier to 0.714. That is a real but insufficient
improvement. It remained far below break-even and failed every admission
gate except frequency.

## Last six months

From 2026-01-01 through 2026-06-30:

- 156 trades on 39 eligible Neutral days;
- 46 wins and 110 losses;
- 29.49% win rate;
- 1.438 realized payoff;
- PF 0.601;
- -44.98R;
- 51.11% conditional side accuracy;
- daily portfolio PF 0.325 and -11.24 portfolio R.

## Verdict

The paired-ranking route is closed without repair. It is causal at
inference, strictly purged, regularized, and frequency-complete, but it does
not approach the hindsight oracle's winning-side selection.

The evidence now covers both ways to formulate the supervised problem:

1. independent rare-event membership probabilities; and
2. direct paired LONG-versus-SHORT ranking.

Neither extracted stable direction from the available completed EURUSD,
DXY, Treasury, and tick-microstructure features. Retuning clocks, labels,
features, `C`, probability thresholds, or excluding no-winner rows after
these results would be adaptive overfitting.

## Reproduce

```powershell
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_four_clock_ranker.py census
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_four_clock_ranker.py backtest
```
