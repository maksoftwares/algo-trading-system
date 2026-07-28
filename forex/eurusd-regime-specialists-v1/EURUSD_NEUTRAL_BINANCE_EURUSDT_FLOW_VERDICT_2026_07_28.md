# EURUSD Neutral Binance EURUSDT executed-flow verdict

Date: 2026-07-28

Decision: `REJECTED_NEUTRAL_BINANCE_EURUSDT_FLOW_V1`

## Result

A login-free, checksum-pinned source was acquired successfully, but its
frozen directional rule failed.

The strategy used the sign of buyer-initiated versus seller-initiated
EURUSDT quote volume over the three fully completed M5 bars before each
EURUSD entry. It had no fitted model, flow-strength threshold, clock
selection, or outcome-based abstention.

| Window | Trades | Win rate | Payoff | PF | Net | Conditional side accuracy |
|---|---:|---:|---:|---:|---:|---:|
| 2020-2021 development | 740 | 32.70% | 1.439 | 0.699 | -153.50R | 51.16% |
| 2022-2023 validation | 596 | 32.05% | 1.420 | 0.669 | -139.10R | 50.00% |
| 2024 validation | 264 | 35.61% | 1.439 | 0.796 | -35.60R | 54.65% |
| 2025 pseudo-OOS | 320 | 31.25% | 1.439 | 0.654 | -78.08R | 50.00% |
| 2026 H1 pseudo-OOS | 156 | 26.28% | 1.438 | 0.513 | -57.48R | 45.56% |
| Overall | 2,076 | 32.18% | 1.433 | 0.680 | -463.75R | 50.72% |

Every window failed. Conditional side accuracy was effectively a coin flip
over full history and deteriorated in the most recent six months.

## Frequency

The rule passed the mechanical frequency contract:

- 519 eligible Neutral dates;
- exactly four trades on all 519 dates;
- 2,076 total trades;
- 100% exact-four coverage.

As in the previous first-hour campaigns, this is four trades per
Regime-1-owned date, not four trades across all weekdays. In 2026 H1, Regime
1 owned 39 of 129 active weekdays.

## Clock diagnostics

All four fixed clocks were negative:

| Entry UTC | Trades | Win rate | PF | Net |
|---|---:|---:|---:|---:|
| 00:00 | 519 | 33.53% | 0.722 | -98.85R |
| 00:15 | 519 | 32.56% | 0.691 | -111.43R |
| 00:30 | 519 | 30.83% | 0.641 | -132.23R |
| 00:45 | 519 | 31.79% | 0.667 | -121.25R |

These are rejection diagnostics only. No clock is selected after outcomes.

## Robustness

- Removing the top 5% of winners: PF 0.574 and -617.15R.
- Adding another 0.5 pip per trade: PF 0.555 and -723.25R.
- Daily 0.25R portfolio: PF 0.473, -115.94 portfolio R, and 116.66R
  maximum drawdown.
- Exact oracle precision: 19.51%.
- Same-side 15-minute oracle precision: 40.27%.

The predicted LONG rate was 48.17%, so the failure was not caused by a
persistent long or short bias.

## Last six months

From 2026-01-01 through 2026-06-30:

- 156 trades;
- 41 wins and 115 losses;
- 26.28% win rate;
- 1.438 realized payoff;
- PF 0.513;
- -57.48R;
- 45.56% conditional side accuracy;
- daily portfolio PF 0.288 and -14.37 portfolio R;
- exactly four trades on all 39 eligible Neutral dates.

## Source outcome versus strategy outcome

The source-acquisition project succeeded:

- 78 official monthly archives;
- all official SHA-256 checksums passed;
- 682,290 normalized five-minute rows;
- correct normalization of 60 millisecond and 18 microsecond archives;
- no forward filling across 462 missing intervals;
- a reproducible downloader, parser, manifest, and source audit.

The strategy project failed. Executed EURUSDT taker flow did not identify
the EURUSD target-first side at the required horizon.

## Verdict

The fixed 15-minute flow-sign rule is closed without reversal, thresholding,
or subgroup selection. Reversing it after this result would not be
legitimate and would not solve the full-history problem anyway: direct
conditional accuracy was 50.72%, so its inverse would be approximately
49.28%.

The source remains useful infrastructure for future preregistered research,
but this exact rule is not eligible for demo or live use.

## Reproduce

```powershell
uv run --with pandas --with numpy --with pyarrow python download_neutral_binance_eurusdt.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_binance_eurusdt_flow.py census
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_binance_eurusdt_flow.py backtest
```
