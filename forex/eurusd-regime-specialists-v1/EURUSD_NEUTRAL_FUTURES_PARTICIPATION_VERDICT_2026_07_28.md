# EURUSD Neutral Futures Participation Verdict

Date: 2026-07-28

Decision: `REJECTED_NEUTRAL_FUTURES_PARTICIPATION_V1`

The frozen, causal exchange-participation hypothesis failed development,
every forward year, the latest six months, and both robustness tests. It is
not eligible for demo or live use.

## Frozen signal

- Trade only the 00:00 UTC Neutral-regime anchor.
- Use only the prior completed daily sessions of continuous Euro FX futures
  (`6E=F`) and the Invesco DB US Dollar Index Bullish Fund (`UUP`).
- Require the sign of the Euro FX session return to agree with the inverse
  sign of the UUP session return.
- Require the geometric mean of both volume ratios, each measured against its
  preceding 20-session median, to be at least 1.0.
- Enter in the agreed direction with fixed 4-pip risk, 1.5R target, 12-hour
  timeout, causal bid/ask execution, 0.7-pip spread floor, and 0.1-pip
  slippage per side.

The outcome-blind census contained 227 trades: 105 long and 122 short.

## Chronological results

| Window | Trades | Win rate | Payoff ratio | Profit factor | Net R |
|---|---:|---:|---:|---:|---:|
| Development, 2019-2022 | 135 | 37.78% | 1.439 | 0.874 | -10.88 |
| 2023 | 22 | 18.18% | 1.439 | 0.319 | -12.58 |
| 2024 | 21 | 23.81% | 1.439 | 0.450 | -9.03 |
| 2025 | 31 | 29.03% | 1.439 | 0.589 | -9.28 |
| 2026 H1 / latest six months | 18 | 16.67% | 1.439 | 0.288 | -10.95 |
| Full sample | 227 | 31.72% | 1.439 | 0.668 | -52.70 |

Full-sample maximum drawdown was 55.18R. The latest-six-month frequency was
0.14 trades per weekday.

## Robustness and oracle resemblance

- Remove the largest 5% of winners: PF 0.557, net -70.40R.
- Add 0.5 pip per round trip: PF 0.545, net -81.08R.
- Exact hindsight-oracle precision: 22.83%.
- Exact hindsight-oracle recall: 2.01%.
- Fifteen-minute tolerant precision: 39.13%.

The rule is rejected before any repair or reversal. A contrarian version is
not a preregistered strategy and must not be inferred from this loss.

## Reproduce

```powershell
uv run --with pandas --with numpy --with pyarrow python download_neutral_futures_participation.py
uv run --with pandas --with numpy --with pyarrow python run_neutral_futures_participation.py
```
