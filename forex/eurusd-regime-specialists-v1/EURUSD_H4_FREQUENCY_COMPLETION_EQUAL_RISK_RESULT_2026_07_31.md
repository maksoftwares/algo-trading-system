# EURUSD H4 frequency-completion equal-risk backtest result

Status: **BACKTEST FREQUENCY AND EDGE GATES PASSED**

The exact portfolio contains the passing H4/M15 confirmation core, four fixed
M15 follow-through experts, and the locked M30 first-break family. The rejected
v1 ledger's 2,532 trades are checksum-pinned. V2 changes no timestamp, side,
exit, ordering, regime, or expert; every trade receives the same 0.15R risk,
equivalent to 0.015 lot at the 0.1-lot reference.

## Full result

All 20 frozen gates passed.

| Metric | Result |
|---|---:|
| Trades / FX days | 2,532 / 2,476 |
| Average trades per FX day | 1.023 |
| Active FX days | 663 (26.78%) |
| Trades per active day | 3.819 |
| Win rate | 47.24% |
| Realized payoff | 1.360 |
| Profit factor | 1.218 |
| PF after another 0.5 pip | 1.162 |
| PF after another 1.0 pip | 1.109 |
| Best-5%-removed PF | 1.020 |
| Positive active months | 55.86% |
| Maximum closed-trade drawdown | 10.741R |
| Maximum simultaneous positions | 9 |
| Maximum concurrent initial risk | 1.350R |
| Trade-bootstrap PF 5th percentile | 1.090 |
| Calendar-bootstrap PF 5th percentile | 1.074 |
| Trade-bootstrap probability PF <= 1 | 0.20% |
| Calendar-bootstrap probability PF <= 1 | 0.475% |

## Chronological stability and dollars

The dollar column uses the executable 0.015-lot-per-trade policy.

| Window | Trades | Win rate | Payoff | PF | Net R | P&L | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2017-2019 | 813 | 46.49% | 1.410 | 1.225 | +14.078 | +$249.59 | 10.741R |
| 2020-2022 H1 | 721 | 47.30% | 1.327 | 1.191 | +10.498 | +$240.00 | 5.312R |
| 2022 H2-2024 H1 | 536 | 45.71% | 1.313 | 1.105 | +4.472 | +$58.12 | 4.128R |
| 2024 H2-2026 H1 | 462 | 50.22% | 1.385 | 1.397 | +12.881 | +$246.31 | 4.305R |
| Latest 12 months | 266 | 52.63% | 1.435 | 1.594 | +10.696 | +$224.10 | 4.305R |
| Latest 6 months | 111 | 57.66% | 1.357 | 1.848 | +5.671 | +$106.48 | 1.813R |
| **Full 2017-2026** | **2,532** | **47.24%** | **1.360** | **1.218** | **+41.929** | **+$794.01** | **10.741R** |

## Latest six months

| Month | Trades | Win rate | PF | 0.015-lot P&L |
|---|---:|---:|---:|---:|
| 2026-01 | 18 | 50.00% | 1.973 | +$13.74 |
| 2026-02 | 19 | 36.84% | 0.720 | -$6.09 |
| 2026-03 | 25 | 52.00% | 1.230 | +$19.91 |
| 2026-04 | 14 | 28.57% | 0.569 | -$14.53 |
| 2026-05 | 21 | 85.71% | 11.272 | +$55.53 |
| 2026-06 | 14 | 92.86% | 13.783 | +$37.91 |
| **Total** | **111** | **57.66%** | **1.848** | **+$106.48** |

## Interpretation

The required average-frequency backtest outcome is achieved without weakening
the prior edge gates. Frequency is clustered rather than evenly distributed:
the system averages 1.023 trades per FX day because it places about 3.82 trades
on its 663 active days, while 73.22% of FX days remain cash.

This is adaptive historical research, not pristine unseen evidence. It is the
backtest candidate to transfer to MT5 parity testing; it does not yet authorize
demo or live orders.

## Reproduction

```powershell
uv run --offline --with pandas --with numpy --with pyarrow python run_h4_frequency_completion_equal_risk.py
```
