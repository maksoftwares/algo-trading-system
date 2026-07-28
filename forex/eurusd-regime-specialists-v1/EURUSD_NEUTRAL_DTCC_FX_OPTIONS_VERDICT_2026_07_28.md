# EURUSD Neutral DTCC OTC FX-options-flow verdict

Date: 2026-07-28

Decision: `REJECTED_NEUTRAL_DTCC_FX_OPTIONS_V1`

The frozen transaction-level OTC options-flow hypothesis failed development,
pseudo-OOS, final, robustness, and oracle-resemblance gates. It is not
eligible for demo or live use.

## Source and frozen rule

The credential-free DTCC CFTC public-dissemination search supplied executed
EUR/USD vanilla calls and puts. The source contains 674 hash-chained raw
responses covering 2025-07-29 through 2026-06-30.

Only standalone `NEWT/TRAD` records disseminated within 24 hours, with 7-90
day tenor, EUR directional notional, and USD premium were included.
Qualified call and put notional and premium imbalances were each centered on
their preceding 20-active-session median and combined with equal weight.
The composite sign selected one 00:00 UTC Neutral-regime direction.

Execution retained fixed 4-pip risk, 1.5R target, 12-hour timeout, causal
bid/ask prices, 0.7-pip spread floor, 0.1-pip slippage per side, and
stop-first same-bar handling.

## Chronological results

| Window | Trades | Win rate | Payoff | Profit factor | Net R |
|---|---:|---:|---:|---:|---:|
| Development, 2025 Sep-Dec | 27 | 22.22% | 1.439 | 0.411 | -12.68 |
| Pseudo-OOS, 2026 Q1 | 22 | 27.27% | 1.439 | 0.540 | -7.55 |
| Final, 2026 Q2 | 17 | 23.53% | 1.439 | 0.443 | -7.43 |
| Full rule | 66 | 24.24% | 1.439 | 0.460 | -27.65 |

The latest six months contained 39 trades, won 25.64%, returned PF 0.496,
and lost 14.98R. Full-sample maximum drawdown was 27.65R.

## Robustness and oracle resemblance

- Remove the largest 5% of winners: PF 0.345, net -33.55R.
- Add 0.5 pip per round trip: PF 0.376, net -35.90R.
- Exact oracle precision: 24.24%.
- Exact oracle recall: 5.97%.
- Fifteen-minute tolerant precision: 46.97%.

The rule is closed. Its direction must not be reversed after seeing these
results; that would be a new, outcome-selected hypothesis requiring future
data.

## Reproduce

```powershell
uv run --with pandas --with numpy --with pyarrow python download_neutral_dtcc_fx_options.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_dtcc_fx_options.py
```
