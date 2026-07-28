# EURUSD Neutral Coinbase stablecoin-flow verdict

## Verdict

`REJECTED_NEUTRAL_COINBASE_STABLECOIN_FLOW_V1`

The login-free source acquisition succeeded, but the frozen signed-volume
agreement rule lost in development and every chronological validation
window. It is closed without a product reversal, magnitude threshold, clock
filter, return confirmation, or subgroup repair.

## Rule tested

At each 00:00, 00:15, 00:30, and 00:45 UTC Neutral decision:

1. require three consecutive completed positive-volume M5 candles at both
   Coinbase `USDC-EUR` and `USDT-EUR`;
2. calculate each product's volume-weighted candle direction;
3. invert stablecoin/EUR direction into EURUSD terms;
4. trade the agreed sign;
5. stay in CASH on disagreement or missing data.

There was no magnitude threshold, product weight, model, clock selection, or
daily quota. The existing executable bid/ask 4-pip-stop, 6-pip-target,
12-hour-hold contract remained unchanged.

## Frequency

| Window | Source dates | Trades | Traded dates | Cash-only dates | Trades/source date |
|---|---:|---:|---:|---:|---:|
| 2022-2023 development | 149 | 166 | 83 | 66 | 1.114 |
| 2024 validation | 66 | 169 | 65 | 1 | 2.561 |
| 2025 pseudo-OOS | 80 | 194 | 76 | 4 | 2.425 |
| 2026 H1 / last six months | 39 | 85 | 36 | 3 | 2.179 |
| Overall | 334 | 614 | 260 | 74 | 1.838 |

Frequency was not an admission gate. Candidate counts and side balance were
frozen before P&L.

## Backtest

| Window | Trades | Win rate | Payoff | PF | Net R | Conditional side accuracy |
|---|---:|---:|---:|---:|---:|---:|
| 2022-2023 development | 166 | 37.95% | 1.439 | 0.880 | -12.65 | 57.27% |
| 2024 validation | 169 | 26.04% | 1.439 | 0.507 | -63.23 | 38.94% |
| 2025 pseudo-OOS | 194 | 37.11% | 1.439 | 0.849 | -18.85 | 56.25% |
| 2026 H1 / last six months | 85 | 29.41% | 1.440 | 0.600 | -24.60 | 49.02% |
| Overall | 614 | 33.22% | 1.439 | 0.716 | -119.33 | 50.75% |

Overall daily portfolio PF was 0.568 with -29.83 portfolio R and 32.42
portfolio R maximum drawdown. Every ticket and daily window was below
break-even.

## Robustness and oracle resemblance

| Check | Result |
|---|---:|
| Extra 0.5-pip round-trip PF | 0.584 |
| Extra 0.5-pip round-trip net | -196.08R |
| Best 5% of winners removed PF | 0.607 |
| Best 5% of winners removed net | -165.08R |
| Exact oracle precision | 18.89% |
| Same-side 15-minute precision | 43.65% |

No overall, robustness, oracle, drawdown, recent-period, or every-window gate
passed. The frequency-relaxation gate passed by construction.

## Interpretation

The new volume observations did not solve the direction problem. Conditional
side accuracy was promising in development and 2025, but collapsed in 2024
and was below chance in 2026 H1. With only 33.22% realized winners, the rule
remained far below the roughly 41% break-even rate implied by its 1.439
payoff.

The source is retained because it is public, reproducible, and materially
different in volume pressure from the earlier sources. Its exact
three-candle sign-agreement use is exhausted. Selecting only the favorable
years, clocks, products, magnitudes, or an inverted 2024 subgroup would be
retrospective overfitting.

## Integrity and reproduction

- Source manifest SHA-256:
  `37b2dc54439a91dedc42919a7a80604b48fdffe6a7345397ca2b404828490090`
- Source Parquet SHA-256:
  `d2f978e185534417a2f3f237983a9f97b90084b3d174b114e2f9df105130268a`
- Result SHA-256:
  `8b88dd0cf28dc50dde962c3c3d0b0789419b054307bdbd1b0a8b3643a2510a21`

```powershell
uv run --with pandas --with numpy --with pyarrow python download_neutral_coinbase_stablecoin_eur.py rebuild
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_coinbase_stablecoin_flow.py census
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_coinbase_stablecoin_flow.py backtest
```
