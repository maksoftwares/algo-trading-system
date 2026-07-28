# EURUSD Neutral flow-augmented paired-ranker verdict

Date: 2026-07-28

Decision: `REJECTED_NEUTRAL_FLOW_AUGMENTED_PAIRED_RANKER_V1`

## What was tested

This campaign tested the remaining preregistered fitted use of the official
Binance EURUSDT executed-flow archive.

The model retained the previously frozen 16 LONG-minus-SHORT decision-time
contrasts and added exactly two direction-bearing variables from the three
fully completed EURUSDT M5 bars before each entry:

- taker-buy quote-volume imbalance;
- EURUSDT return.

The model was fixed L2 logistic regression with `C=0.1`, balanced classes,
and a 0.5 direction threshold. There was no feature selection, interaction
search, flow-strength threshold, clock selection, calibration, reversal, or
abstention.

Training used only one-winner pairs. Both entry time and the maximum of the
LONG and SHORT label-known times had to be strictly earlier than each
evaluation-window start. No-winner points remained mandatory at inference.
The full specification, outcome-blind census, code, tests, and source hashes
were locked before the outcome-bearing run.

## Frequency and chronology

The 2020-2021 source period was training-only. Evaluation covered 2022
through June 2026:

- 334 eligible Neutral dates;
- 1,336 forced evaluation trades;
- exactly four trades on every eligible date;
- 100% exact-four execution coverage.

| Window | Training one-winner pairs | Trades | Win rate | Payoff | PF | Net | Conditional side accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2022-2023 validation | 473 | 596 | 32.21% | 1.420 | 0.675 | -136.55R | 50.26% |
| 2024 validation | 855 | 264 | 31.82% | 1.439 | 0.672 | -60.60R | 48.84% |
| 2025 pseudo-OOS | 1,027 | 320 | 33.13% | 1.439 | 0.713 | -63.08R | 53.00% |
| 2026 H1 pseudo-OOS | 1,227 | 156 | 32.69% | 1.438 | 0.698 | -32.48R | 56.67% |
| Overall | — | 1,336 | 32.41% | 1.430 | 0.686 | -292.70R | 51.30% |

Every chronological window failed. The required conditional side accuracy
was 70%; the full evaluation result was only 1.30 percentage points above a
coin flip. The predicted LONG rate was 52.69%, so one-side bias does not
explain the failure.

## Fixed-clock diagnostics

Every clock lost:

| Entry UTC | Trades | Win rate | PF | Net |
|---|---:|---:|---:|---:|
| 00:00 | 334 | 34.43% | 0.749 | -56.70R |
| 00:15 | 334 | 29.64% | 0.601 | -96.80R |
| 00:30 | 334 | 32.63% | 0.696 | -70.10R |
| 00:45 | 334 | 32.93% | 0.701 | -69.10R |

These are rejection diagnostics. No clock may be retained or removed after
viewing the result.

## Executed-flow stability

The standardized taker-imbalance coefficient changed sign between the first
and later refits: -0.002 in 2022-2023, then +0.008, +0.044, and +0.035. The
return coefficient was also tiny in the first refit and negative thereafter:
-0.002, -0.025, -0.027, and -0.028.

Neither flow variable developed a large, stable linear contribution. The
latest window improved relative to the standalone flow-sign rule, but that
local improvement did not establish a profitable or stable side-selection
edge.

## Robustness and oracle resemblance

- Removing the top 5% of winners: PF 0.580 and -391.53R.
- Adding another 0.5 pip per trade: PF 0.560 and -459.70R.
- Daily 0.25R portfolio: PF 0.459, -73.18 portfolio R, and 73.40R maximum
  drawdown.
- Exact oracle precision: 20.66%.
- Same-side 15-minute oracle precision: 39.07%.

Only the mechanical frequency gate passed. All economic, resemblance,
stress, and drawdown gates failed.

## Last six months

From 2026-01-01 through 2026-06-30:

- 156 trades on 39 eligible Neutral dates;
- 51 wins and 105 losses;
- 32.69% win rate;
- 1.438 realized payoff;
- PF 0.698;
- -32.48R;
- 56.67% conditional side accuracy;
- daily portfolio PF 0.438 and -8.12 portfolio R;
- exactly four trades on every eligible Neutral date.

This was better than the standalone flow sign over the same period
(PF 0.513 and -57.48R), but remained far below break-even and failed all
frozen admission requirements.

## Verdict

The flow-augmented ranker is closed without repair. It is causal at
inference, chronologically purged, frequency-complete, and based on genuine
executed flow, but it still cannot select the Regime 1 future-winning side.

The Binance archive has now been tested in both predeclared forms:

1. a deterministic taker-flow sign; and
2. a strict linear conditional augmentation of the paired side ranker.

Further horizon, strength, interaction, feature, clock, model, or threshold
search on the same inspected history would be adaptive overfitting. The
source pipeline remains reproducible infrastructure, but no EURUSD expert
from it is admitted.

## Reproduce

```powershell
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_flow_augmented_ranker.py census
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_flow_augmented_ranker.py backtest
```
