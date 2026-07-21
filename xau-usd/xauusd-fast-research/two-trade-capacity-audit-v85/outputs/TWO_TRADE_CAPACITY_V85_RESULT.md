# V85 Two-Trade Capacity Audit Result

Decision: `V85_EXISTING_RESERVOIR_INSUFFICIENT_FOR_TWO_PER_DAY`

| Window | Current/day | Rejected | Upper/day | Upper shortfall | Capacity |
|---|---:|---:|---:|---:|---|
| development_2 | 1.142 | 72 | 1.280 | 375 | False |
| confirmation | 1.690 | 86 | 2.019 | 0 | True |
| final | 1.395 | 71 | 1.667 | 87 | False |

The upper bound counts every distinct broker-executable V57 candidate and ignores overlap, risk, drawdown, and economics.
It cannot authorize admitting a rejected trade. V59/V60 remain byte-identical.
