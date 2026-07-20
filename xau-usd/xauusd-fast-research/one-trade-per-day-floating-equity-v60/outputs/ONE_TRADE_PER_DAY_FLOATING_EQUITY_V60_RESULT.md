# One-Trade-Per-Day Floating Equity V60 Result

Decision: `V60_WHOLE_ACCOUNT_FLOATING_EQUITY_GATE_PASS`

Reconstructed trades: **2194 / 2194**
Maximum concurrent positions: **10**
Maximum concurrent add-ons: **2**

| Scenario | Raw floating DD | Buffered DD | Peak UTC | Trough UTC |
|---|---:|---:|---|---|
| Locked P&L | 329.64 | 412.06 | 2024-07-17T14:00:00+00:00 | 2024-09-10T14:10:00+00:00 |
| R1 +$0.30 fee stress | 335.34 | 419.18 | 2024-07-17T14:00:00+00:00 | 2024-09-10T14:10:00+00:00 |

Locked raw-DD limit: **$359.81**; buffered hard limit: **$449.77**.

| Window | Base floating DD | Fee-stress floating DD |
|---|---:|---:|
| reverse | 32.87 | 32.87 |
| development_1 | 148.32 | 148.32 |
| development_2 | 282.93 | 298.34 |
| confirmation | 329.64 | 335.34 |
| final | 256.90 | 258.70 |

Failed checks: `[]`

Historical research only. MT5 portfolio parity and sealed prospective shadow evidence remain required.
