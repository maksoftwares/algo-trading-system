# EURUSD RSI chronological regime result

Date: 2026-07-30

Status: **HISTORICAL_VALIDATION_REJECTED**

Demo-order authorization: **false**

## Decision

Chronological regime selection does not validate the high-frequency RSI
construction. Three causal regimes passed every first-year gate, but they
reversed in the locked second year.

No trailing-PF grid was used. `NEUTRAL`, `JOINT_COMPRESSION`, and `SHOCK` were
admitted using only 2024-07-01 through 2025-06-30. The selection was then
applied unchanged to 2025-07-01 through 2026-06-30.

## Locked last-12-month result

| Metric | Result |
|---|---:|
| Selected RSI trades | 289 |
| Protected M15 trades | 61 |
| Combined trades | 350 |
| Trades per weekday | 1.3410 |
| Weekday coverage | 54.02% |
| Win rate | 51.43% |
| Payoff | 0.9509 |
| Profit factor | 1.0069 |
| PF after +0.5 pip | 0.9237 |
| Best-5%-removed PF | 0.7296 |
| Net P&L | $1.39 |

The RSI component itself lost $20.31; protected M15 added $21.70 and prevented
the combined result from becoming negative.

Validation by selected regime:

| Regime | Trades | PF | Stressed PF | Net P&L |
|---|---:|---:|---:|---:|
| Neutral | 69 | 0.7552 | 0.6770 | -$8.89 |
| Joint Compression | 126 | 1.0231 | 0.9034 | +$1.16 |
| Shock | 94 | 0.8020 | 0.7374 | -$12.58 |

Frequency was abundant but clustered: 350 trades occurred on only 141 of 261
weekdays, with up to three simultaneous positions and seven same-entry
overlaps. Payoff also missed the 1.25 portfolio floor.

This proves that the attractive full two-year RSI result was not a stable
regime transfer. It was dominated by the first-year development performance
and retrospective trailing-PF selection. It must not be deployed.

## Reproducibility

Run:

```powershell
uv run --offline --with pandas --with numpy --with pyarrow python run_rsi_regime_chronological_selector.py
```

Implementation hashes:

- config:
  `030734fc1053c9712c368b1fc15a489212b048df24a2386107763e5a5bfd7a6b`
- source:
  `1a3e8490b978fc5b9b07374bb67d4e1356041cfa11d38490c80c7229018e84f6`

Output hashes:

- `DEVELOPMENT_REGIMES.csv`:
  `c8cf051c8b3d60584800c72301c0b4ec9c56977ceb1446de082f5eec3589debb`
- `LOCKED_VALIDATION_COMBINED_TRADES.csv`:
  `ad82898e49287af35566762031868132b1f741c636c686e0872109d03f8c1aef`
- `MONTHLY.csv`:
  `b3633e8c425f00f8eff4ecdff059577eb3d2d3db3d8d70c018e1026d6d05bdac`
- `RESULT.json`:
  `28f003362b471386dbb45274a2fea3d4dcc8a493a69fc9c71a403e2a3dda7893`
- `RESULT.md`:
  `c6128249e72dd722af0e86e0396dec1494326ac2ee0081b9bef45c5c4e9e757d`
