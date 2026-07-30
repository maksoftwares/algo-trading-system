# EURUSD RSI health-gate historical transfer result

Date: 2026-07-30

Status: **HISTORICAL_TRANSFER_REJECTED**

Demo-order authorization: **false**

## Decision

The exact RSI reconstruction passed cross-broker parity and reproduced the
recent profitable state, but the unchanged 30-trade/PF-1.05 health gate lost
money before mid-2022. The gate is a recent-regime mechanism, not a durable
full-history edge.

## Reconstruction parity

| Check | Result | Frozen requirement | Pass |
|---|---:|---:|---:|
| Broker RSI entries | 633 | 633 | Yes |
| Dukascopy raw trades | 661 | 317-950 | Yes |
| Raw count ratio | 1.044 | 0.50-1.50 | Yes |
| Broker entries with qualifying Dukascopy signal within 15 minutes | 83.25% | at least 60% | Yes |

The parity result matters: the historical rejection is not explained by a
failed reconstruction. The independently aggregated bid/ask archive produced
almost the same raw trade count and covered most broker entry times.

## Earlier 2017-2024 transfer

| Scope | Trades | Trades/weekday | Win rate | Payoff | PF | Stressed PF | Net R |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full earlier transfer | 992 | 0.507 | 55.24% | 0.781 | 0.964 | 0.855 | -16.25 |
| 2017-2019 | 334 | 0.427 | 53.59% | 0.781 | 0.902 | 0.799 | -15.33 |
| 2020-2022H1 | 396 | 0.607 | 54.29% | 0.781 | 0.928 | 0.823 | -13.19 |
| 2022H2-2024H1 | 262 | 0.503 | 58.78% | 0.780 | 1.112 | 0.987 | +12.27 |

The full earlier result also failed concentration, month consistency, and
drawdown gates:

- best-5%-removed PF: 0.875;
- positive active-month share: 36.62%;
- maximum closed-trade drawdown: 38.16R;
- earlier latest-12-month PF: 0.896.

## Recent cross-broker window

The same reconstructed rule remained attractive only in the recent window:

| Scope | Trades | Trades/weekday | Win rate | PF | Stressed PF | Best-5%-removed PF | Net R |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2024H2-2026H1 | 409 | 0.784 | 62.35% | 1.284 | 1.132 | 1.178 | +44.56 |

This confirms regime drift rather than implementation error. The gate begins
working around the same period in which it was discovered. It cannot be
promoted from that inspected window.

No lookback, threshold, hour, indicator, stop, target, side, or cost repair is
permitted for this exact transfer.

## Implication for the frequency goal

The recent rule could supply enough trades to bring the portfolio close to
0.85 trades/weekday, but it adds zero historically admitted capacity because
its earlier transfer failed. It remains eligible only as a disarmed
prospective experiment.

## Reproducibility

```powershell
uv run --offline --with pandas --with numpy --with pyarrow python run_rsi_health_gate_historical_transfer.py
```

Hashes:

- Frozen config:
  `3c13093d34668cd28240b4b9b5cd85fcfbfbf6a280ba795fdd37adf215deb8e0`
- Market source:
  `8281d96ccbc3488f98586894fe58f6988eaa5376601a0bfaec874fd9f08f1f45`
- EA source:
  `0dd10b6d12b48598f891619f56c5bbab3a289dd8ecc9fef111ab45c6b5cdfcdd`
- `RESULT.json`:
  `2d5a80fd1cf1dab5edab7236d4f8a59acb8fad242528010314b5a42118b2db9c`
- `RESULT.md`:
  `5951ce71b15ffbe78d22bab3c0a4cb697264c18896b243c049b66470a20e580a`
- `GATED_TRADES.csv`:
  `9f1f5a15562cef8f4b745cabe3997c0b35f0229f76c40bac46e9905808a6e1c8`
- `RAW_TRADES_WITH_GATE.csv`:
  `5f5e903e5345331d7af87f865ecb6b6785c20f9f67b05b31a20c3bc53d302535`
