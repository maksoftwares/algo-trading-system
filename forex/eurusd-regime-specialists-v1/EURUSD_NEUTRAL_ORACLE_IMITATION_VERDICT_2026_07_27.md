# EURUSD Regime 1 Neutral oracle-imitation verdict

Date: 2026-07-27

Decision: `REJECTED_NEUTRAL_ORACLE_IMITATION_V1`

## Question tested

Can a causal, shallow model learn enough of the Neutral hindsight oracle's
entry timing and direction to reproduce both its behavior and profitable
1.50R execution in later chronological windows?

Historical oracle membership was used only as a purged supervised label.
Oracle rows and future candidate scores were forbidden at inference.

## Frozen design

- 250,860 long/short candidate rows at completed five-minute timestamps;
- 125,430 causal timestamps in non-shock, non-compressed Neutral state;
- 2,563 candidate rows exactly matching one of 2,615 Neutral oracle trades;
- 32 completed-bar, cross-asset, time-cycle, and EURUSD tick features;
- L2 logistic regression with balanced classes;
- 2019-2020 model fit and 2021-2022 threshold selection;
- annual expanding-window refits for 2023, 2024, 2025, and 2026 H1;
- a strict 12-hour label purge;
- online threshold acceptance with no future daily ranking;
- at most four concurrent positions and four entries per UTC day;
- fixed 4-pip risk, 1.50R target, 12-hour hold, exact bid/ask costs,
  stop-first ambiguous bars, and 0.25 portfolio-R per position.

The development-selected threshold was 0.85. It passed the frozen imitation
qualification with 21.41% exact precision and 28.55% exact recall, but its
development-selection economics were already negative: PF 0.692 and
-200.00R. No parameter was repaired.

## Chronological result

| Window | Trades | Win rate | Payoff | PF | Net | Exact precision | Exact recall | 15m precision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 378 | 30.69% | 1.380 | 0.611 | -108.98R | 21.43% | 27.00% | 29.10% |
| 2024 | 320 | 34.06% | 1.439 | 0.743 | -55.50R | 26.56% | 32.32% | 36.25% |
| 2025 | 353 | 32.01% | 1.439 | 0.678 | -79.30R | 22.66% | 25.00% | 30.88% |
| 2026 H1 | 195 | 28.21% | 1.439 | 0.565 | -62.43R | 21.03% | 25.63% | 28.21% |
| Overall | 1,246 | 31.54% | 1.420 | 0.654 | -306.20R | 23.03% | 27.52% | 31.30% |

Frequency was 1.366 trades per archived weekday. The extra half-pip stress
result was -461.95R. At the frozen 0.25 portfolio-R allocation, the result
was -76.55 portfolio-R.

Every chronological economic window failed.

## What the model actually learned

The behavioral imitation gate passed, but the economic gate failed
decisively:

| Predicted group | Trades | Wins | Win rate | Net |
|---|---:|---:|---:|---:|
| Exact oracle members | 287 | 287 | 100.00% | +423.35R |
| Nonmembers accepted by the model | 959 | 106 | 11.05% | -729.55R |

The exact matches win by construction because oracle membership means that
the future target was already known. The causal model could not distinguish
them from the much larger set of nearby failures with adequate precision.

The development model's dominant standardized coefficient was `hour_cos`
at 11.94; the next largest time coefficient was `hour_sin` at 1.41. This
matches the audited oracle construction: 2,482 of 2,615 Neutral oracle
trades occur during 00:00-00:59 UTC because the oracle scans each date from
midnight and retains the first four future winners. The classifier learned
this timing artifact. It did not learn the unavailable future direction.

## Verdict

This campaign came materially closer to the oracle's recorded entries than
the earlier causal families, but entry resemblance was not an economic
edge. A strategy needs approximately 41%-42% wins at this realized payoff;
the model remained between 28% and 34% in every forward window.

The campaign is rejected and cannot be used for demo or live trading.
Retuning its threshold for precision, excluding losing hours, or filtering
the inspected nonmembers would be post-outcome overfitting.

Further progress requires a new causal information source capable of
separating direction within the midnight candidate cluster, such as
timestamped macro surprises or genuine multi-venue order-flow imbalance,
followed by a separately locked future holdout. Until that evidence exists,
Regime 1 remains `CASH`.

## Reproduce

```powershell
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_oracle_imitation.py
```
