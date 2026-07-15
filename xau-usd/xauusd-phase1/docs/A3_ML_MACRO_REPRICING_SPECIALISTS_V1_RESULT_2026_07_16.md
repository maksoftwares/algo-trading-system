# A3 ML Macro Repricing Specialists V1 Result

## Decision

Iteration 2 produced no train-family survivor. Validation, internal test, and exam outcomes remained closed.

## Train evidence

| Family | Trades | Baseline PF | Stress PF | Average stress R | Decision |
|---|---:|---:|---:|---:|---|
| Real-yield shock | 32 | 1.158 | 0.977 | -0.0136 | Reject: insufficient sample |
| Yield/USD agreement | 42 | 0.542 | 0.459 | -0.4321 | Reject |
| Inflation repricing | 52 | 0.450 | 0.382 | -0.5231 | Reject |

The real-yield shock was the only family near economic neutrality, but it missed the frozen 80-trade minimum and remained negative after stress costs. It is not a usable strategy.

## Integrity decision

Do not lower the threshold or open validation based on these outcomes. A future real-yield experiment would require a new mechanism and preregistration.

No demo, live, EA, or broker action is authorized.
