# EURUSD H4 chop controlled demo verification

Status: **CONTROLLED_SHADOW_DEMO_ARTIFACT_READY**

The hardened EA compiled with zero errors and zero warnings. Its broker
Strategy Tester run exactly reproduced all 62 prior trade rows and aggregate
metrics from July 2024 through June 2026.

| Window | Trades | Win rate | Payoff | PF | Fixed 0.01-lot P&L |
|---|---:|---:|---:|---:|---:|
| Full broker window | 62 | 53.2% | 1.271 | 1.447 | $+22.85 |
| Latest 12 months | 33 | 54.5% | 1.397 | 1.676 | $+17.09 |
| Latest 6 months | 17 | 58.8% | 1.213 | 1.732 | $+9.83 |

Broker-reported maximum balance drawdown was $11.00 (0.11%) and maximum
equity drawdown was $14.82 (0.15%) on a $10,000 test deposit.

## Latest 12 calendar months

| Month | Trades | Win rate | Payoff | PF | Fixed 0.01-lot P&L |
|---|---:|---:|---:|---:|---:|
| 2025-07 | 3 | 66.7% | 14.275 | 28.550 | $+5.51 |
| 2025-08 | 3 | 66.7% | 1.019 | 2.038 | $+2.43 |
| 2025-09 | 3 | 33.3% | 1.351 | 0.675 | $-1.00 |
| 2025-10 | 4 | 50.0% | 1.705 | 1.705 | $+2.06 |
| 2025-11 | 0 | 0.0% | 0.000 | 0.000 | $+0.00 |
| 2025-12 | 3 | 33.3% | 0.949 | 0.474 | $-1.74 |
| 2026-01 | 2 | 50.0% | 1.219 | 1.219 | $+0.32 |
| 2026-02 | 3 | 33.3% | 1.973 | 0.987 | $-0.04 |
| 2026-03 | 7 | 42.9% | 1.354 | 1.016 | $+0.14 |
| 2026-04 | 0 | 0.0% | 0.000 | 0.000 | $+0.00 |
| 2026-05 | 3 | 100.0% | 0.000 | infinite | $+6.17 |
| 2026-06 | 2 | 100.0% | 0.000 | infinite | $+3.24 |

## Decision

The compiled artifact and disarmed shadow preset are ready for controlled demo
observation. The ordering preset intentionally remains a template: the owner
must enter the exact demo account and server allowlist. No live account is
supported. Sparse frequency and inspected-history bias prevent any claim of a
production-ready trading edge.
