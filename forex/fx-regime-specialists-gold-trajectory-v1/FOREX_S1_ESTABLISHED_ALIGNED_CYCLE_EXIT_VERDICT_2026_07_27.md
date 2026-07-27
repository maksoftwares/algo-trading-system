# S1 Established-Aligned Next-Cycle Exit Verdict — 2026-07-27

Status: `REJECTED_STANDALONE`

Boundary: offline research only. The sole change was the hash-locked next-active-06:00 UTC lifecycle exit.

## Full-History Result

- Trades: 70
- PF: 2.2545
- Net: 23.2532R
- Expectancy: 0.3322R
- Win rate: 67.14%
- Maximum drawdown: 3.0041R
- Executed-trade change versus frozen S1: +0

| Window | Trades | PF | Net R | Expectancy R | Max DD R |
| --- | ---: | ---: | ---: | ---: | ---: |
| design | 19 | 4.2283 | 9.9059 | 0.5214 | 1.7295 |
| validation | 27 | 2.1305 | 8.7565 | 0.3243 | 3.0041 |
| adaptive_exam | 24 | 1.5945 | 4.5908 | 0.1913 | 2.0100 |

- Top-5%-winner removal net: 19.2598R.
- Additional 0.5-pip round-trip stress net: 22.2353R.

## Admission Failures

- design: 19 trades < 30
- validation: 27 trades < 30
- adaptive_exam: 24 trades < 30

The lifecycle hypothesis is closed because it did not increase the sample. No further exit tuning is authorized by this result.

The result remains historical development evidence even if every gate passes.
