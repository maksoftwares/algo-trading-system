# EURUSD RSI health-gate observer parity result

Status: **parity passed; prospective shadow only**.

Demo-order authorization: **false**.

The compiled zero-order observer replayed 632 virtual entries. Of 630 broker
reference entries in the same MT5 window, 629 matched the observer at the exact
minute (99.84% broker coverage).

| Sleeve | Trades | Win rate | Payoff | PF | Net pips |
|---|---:|---:|---:|---:|---:|
| Raw virtual book | 632 | 57.91% | 0.893 | 1.229 | 652.5 |
| Health-admitted | 344 | 63.37% | 0.937 | 1.622 | 830.7 |

The admitted sleeve remains profitable after 0.5 pip extra round-trip stress
(PF 1.471) and after removing its best 5% of winners (PF 1.322).

This does not cure the core readiness problem. The first 12 months produced
723.7 of 830.7 admitted net pips, while the second 12 months produced only
107.0. The gate admitted no trades from August through December 2025. That
instability is why historical parity cannot authorize demo orders and why fresh
prospective observation is required.
