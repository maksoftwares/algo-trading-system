# EURUSD Regime 1 Neutral synchronous cross-asset verdict

Date: 2026-07-27

Decision: `REJECTED_NEUTRAL_SYNCHRONOUS_CROSSASSET_V1`

## Question tested

Can synchronized, completed five-minute DXY and US Treasury quote behavior
separate the future-winning direction inside the Neutral oracle's candidate
cluster better than the prior causal oracle-imitation model?

This was a single controlled extension of the locked oracle-imitation
campaign. Candidate generation, oracle labels, execution, development
periods, threshold-selection rule, walk-forward windows, and admission
gates were inherited unchanged. The only model-input change was the
addition of 18 preregistered cross-asset features.

## Source and causality audit

- Source: Dukascopy `DOLLARIDXUSD` and `USTBONDTRUSD` CFD bid/ask ticks
  aggregated to synchronized M5 bars.
- Historical source: 525,099 rows from 2019-01-02 01:00 UTC through
  2026-06-30 23:55 UTC.
- Historical SHA-256:
  `3982a3bb56741a5c5139f0381696d4ec4f50d7b1be7588a0efa2664bbf51ffa4`.
- The source row timestamp is the M5 bar start. A row joined at the EURUSD
  signal timestamp becomes usable only at the shared five-minute
  completion timestamp.
- Both symbols had to exist at the exact timestamp. Missing values were
  dropped; none were forward-filled.
- A separately produced continuation overlapped 266 rows with maximum
  absolute feature error of 0.0.
- The source is quoted CFD price, spread, and tick-count behavior. It is not
  exchange order flow or executed-volume imbalance.

The usable joined dataset contained 168,196 long/short rows at 84,098
timestamps, with 1,247 exact oracle-positive rows. The model had 50 total
features: the prior 32 causal features plus 18 new synchronized features.

## Frozen design

- L2 logistic regression, `C=0.10`, balanced classes, fixed random seed;
- model fit on 2019-2020;
- threshold selection on 2021-2022;
- maximum exact-match F1, then 15-minute F1, then net R;
- strict 12-hour label purge before every refit;
- expanding annual refits for 2023, 2024, 2025, and 2026 H1;
- no oracle membership or future path information at inference;
- online threshold acceptance with no future daily ranking;
- at most four concurrent positions and four entries per UTC day;
- fixed 4-pip risk, 1.50R target, 12-hour maximum hold, exact bid/ask
  execution costs, and stop-first treatment of ambiguous bars.

The preregistration and frozen configuration were SHA-256 locked before
the outcome pass. The selected development threshold was 0.90. It produced
490 trades in 2021-2022, 26.33% exact precision, 18.70% exact recall, and
36.33% same-side precision within 15 minutes. Its economics were already
negative: PF 0.660 and -116.65R. No parameter was repaired.

## Chronological result

| Window | Trades | Win rate | Payoff | PF | Net | Exact precision | Exact recall | 15m precision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 199 | 29.65% | 1.439 | 0.606 | -56.48R | 26.13% | 17.33% | 38.19% |
| 2024 | 193 | 31.09% | 1.439 | 0.649 | -47.83R | 25.39% | 18.63% | 37.31% |
| 2025 | 156 | 34.62% | 1.439 | 0.762 | -24.88R | 26.28% | 12.81% | 37.82% |
| 2026 H1 | 90 | 24.44% | 1.439 | 0.466 | -37.25R | 17.78% | 10.00% | 30.00% |
| Overall | 638 | 30.56% | 1.439 | 0.633 | -166.43R | 24.76% | 15.15% | 36.68% |

Every chronological economic window failed. Overall expectancy was
-0.261R per trade, maximum drawdown was 166.43R, and frequency was 0.700
trades per archived weekday. The extra half-pip round-trip stress result
was -246.18R. At the frozen 0.25 portfolio-R allocation, net performance
was -41.61 portfolio-R.

The behavioral-imitation gate passed, but that did not admit the model
because the win-rate, PF, expectancy, stress, and annual economic gates
failed.

## Comparison with the prior causal imitation model

| Campaign | Trades | Exact precision | Exact recall | PF | Net |
|---|---:|---:|---:|---:|---:|
| Prior oracle-imitation baseline | 1,246 | 23.03% | 27.52% | 0.654 | -306.20R |
| Synchronous DXY/Treasury extension | 638 | 24.76% | 15.15% | 0.633 | -166.43R |

Synchronized cross-asset inputs increased exact precision by only 1.73
percentage points, reduced recall substantially, and lowered PF by 0.0209.
The smaller absolute loss came from taking fewer trades, not from positive
expectancy.

## Failure anatomy

| Predicted group | Trades | Wins | Win rate | PF | Net |
|---|---:|---:|---:|---:|---:|
| Exact oracle members | 158 | 158 | 100.00% | Undefined: no losses | +233.08R |
| Nonmembers accepted by the model | 480 | 37 | 7.71% | 0.120 | -399.50R |

Exact oracle members win by construction because their future target-first
path is already known in the historical label. The causal model still
accepted roughly three false positives for every exact match, and those
false positives destroyed the apparent oracle-like gains.

The development model's largest standardized coefficient remained
`hour_cos` at 7.82, followed by `hour_sin` at -1.10. The strongest new
feature was DXY tick-count ratio at -0.56. The explicitly directional
`aligned_joint_pressure_1` coefficient was only 0.0035 and
`dxy_bond_support_agreement_1` was -0.0345. The model therefore continued
to learn the oracle's midnight scan artifact more strongly than
cross-asset direction.

## Verdict

The synchronized DXY/Treasury source does not solve Regime 1. It makes the
entry set look slightly more like the hindsight oracle but does not provide
the missing causal direction information. The campaign is rejected and
cannot be used for demo or live trading.

Post-outcome threshold changes, hour exclusions, coefficient filtering, or
screening the observed nonmembers would be retrospective overfitting. This
specific M5 quoted-cross-asset extension is closed without retuning.

A legitimate next campaign needs genuinely different information, such as
point-in-time macroeconomic consensus surprises or multi-venue executed
flow/order-book imbalance, and must be locked before inspecting its
chronological outcomes. Until such evidence passes, Regime 1 remains
`CASH`.

## Reproduce

```powershell
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_synchronous_crossasset.py
```
