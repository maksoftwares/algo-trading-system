# EURUSD Neutral selective target-probability verdict

## Verdict

`REJECTED_PRE_EVALUATION_NO_TARGET_PROBABILITY_SIGNALS`

The frozen causal model selected zero trades. No selected trade outcome or
oracle match was evaluated, because none of the 1,280 chronological
evaluation decisions reached the predeclared 45% target-first probability
hurdle.

The model therefore remains in CASH. Its threshold will not be lowered after
the screen merely to create activity.

## Model screened

One shared side-stacked L2 logistic model estimated LONG and SHORT
target-first probabilities from twelve decision-time features:

- eight side-aligned price, room, DXY, and quote-change fields;
- Kraken and Binance flow imbalance aligned to the candidate side;
- the absolute Kraken and Binance imbalance magnitudes.

The fit used `C=0.1`, no class balancing, no feature search, no interaction,
no clock feature, and no probability recalibration. At each evaluation-window
start, training used only side labels whose entries and exits were strictly
earlier than the cutoff.

The higher of the LONG and SHORT probabilities was eligible only when it was
at least 0.45. Exact ties mapped to LONG; sub-threshold decisions mapped to
CASH.

## Pre-evaluation screen

| Window | Source decisions | Selected | Probability median | P95 | Maximum |
|---|---:|---:|---:|---:|---:|
| 2022-2023 | 560 | 0 | 34.70% | 38.93% | 43.18% |
| 2024 | 248 | 0 | 33.91% | 37.48% | 40.87% |
| 2025 | 316 | 0 | 34.45% | 38.36% | 42.92% |
| 2026 H1 / last six months | 156 | 0 | 34.25% | 37.66% | 40.02% |
| Overall | 1,280 | 0 | 34.39% | 38.40% | 43.18% |

The overall 99th percentile was only 40.47%. All 320 source-complete
evaluation dates were cash-only.

## Why this is informative

With a realized win/loss profile near +1.475R / -1.025R, break-even requires
about 41% wins before an additional safety margin. The unbalanced probability
model learned a base target-first rate near 31.6%-31.9% and found no
decision-time feature combination strong enough to justify the 45% hurdle.

The 2026 H1 ceiling fell below even the approximate break-even probability.
This agrees with the separately evaluated agreement filter's severe
last-six-month loss without reusing that filter's P&L to change the model.

Lowering the probability threshold now would be threshold selection after
seeing the score distribution and would deliberately admit estimates with
insufficient economic margin. That path is closed.

## Integrity

- Trade outcomes routed: no.
- Oracle evaluated: no.
- Threshold changed after screen: no.
- Full selection-census SHA-256:
  `62d0fe950d86f7642a6f89eb5c605471c17288c73257a5948c0b342d1b22341f`.
- Result SHA-256:
  `64ab90d02cb69e5645723b2fa5bb196237752e2b616b3ce68ee791250be7cb28`.

## Reproduce

```powershell
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_selective_target_probability.py census
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_selective_target_probability.py backtest
```
