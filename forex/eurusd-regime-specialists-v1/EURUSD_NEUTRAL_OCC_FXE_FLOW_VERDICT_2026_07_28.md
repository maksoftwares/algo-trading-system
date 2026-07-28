# EURUSD Neutral OCC FXE Customer Flow Verdict

Date: 2026-07-28

Decision: `REJECTED_NEUTRAL_OCC_FXE_FLOW_V1`

This experiment used the official, login-free OCC daily volume query for FXE
customer options. The fixed full rule failed chronological admission and is
not eligible for demo or live use.

Source documentation:
<https://www.theocc.com/market-data/market-data-reports/other-market-data-info/batch-processing/volume-query-batch-processing>

## Frozen signal

- Trade only the 00:00 UTC Neutral-regime anchor.
- At each decision, use only the previous OCC business day's customer-account
  FXE call and put volumes.
- Compute `log1p(call volume) - log1p(put volume)` and subtract its preceding
  20-session median, excluding the current observation.
- Require total FXE customer option volume to be at least its preceding
  20-session median.
- Go long when normalized imbalance is positive and short when it is negative.
- Use fixed 4-pip risk, 1.5R target, 12-hour timeout, causal bid/ask execution,
  0.7-pip spread floor, and 0.1-pip slippage per side.

The outcome-blind census contained 78 trades: 41 long and 37 short.

## Chronological results

| Window | Trades | Win rate | Payoff ratio | Profit factor | Net R | Gate |
|---|---:|---:|---:|---:|---:|---|
| Development | 24 | 37.50% | 1.439 | 0.863 | -2.10 | Fail |
| Validation, 2025 Q2-Q3 | 18 | 55.56% | 1.439 | 1.799 | +6.55 | Fail |
| Pseudo-OOS, 2025 Q4-2026 Q1 | 28 | 25.00% | 1.439 | 0.480 | -11.20 | Fail |
| Final, 2026 Q2 | 8 | 50.00% | 1.439 | 1.439 | +1.80 | Pass |
| Full rule | 78 | 38.46% | 1.439 | 0.899 | -4.95 | Fail |

The profitable final quarter is only eight trades and cannot be selected after
observing the other windows. Full-sample maximum drawdown was 15.43R and
frequency was 0.16 trades per weekday.

## Trailing audit

| Window | Trades | Win rate | Profit factor | Net R |
|---|---:|---:|---:|---:|
| Latest 3 months | 8 | 50.00% | 1.439 | +1.80 |
| Latest 6 months | 21 | 38.10% | 0.886 | -1.53 |
| Latest 12 months | 44 | 34.09% | 0.744 | -7.60 |

Robustness remained negative: removing the largest 5% of winners produced PF
0.779 and -10.85R; adding 0.5 pip per round trip produced PF 0.734 and
-14.70R. Exact hindsight-oracle precision was 38.46%, recall was 5.24%, and
15-minute tolerant precision was 55.13%.

The exact rule is closed. Selecting its profitable subperiods, thresholds, or
direction after seeing these results would be subgroup overfitting.

## Reproduce

```powershell
powershell -ExecutionPolicy Bypass -File download_occ_fxe_flow_raw.ps1
uv run --with pandas --with numpy --with pyarrow python download_neutral_occ_fxe_flow.py
uv run --with pandas --with numpy --with pyarrow python run_neutral_occ_fxe_flow.py
```
