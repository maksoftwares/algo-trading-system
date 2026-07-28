# EURUSD Neutral Kraken/Binance multivenue-flow verdict

Date: 2026-07-28

Decision: `REJECTED_NEUTRAL_KRAKEN_MULTIVENUE_FLOW_V1`

## Result

The source-acquisition project succeeded, but the frozen multivenue
direction rule failed.

At each of four first-hour clocks, the strategy equal-weighted:

- reported buy/sell quote-volume imbalance from Kraken's actual EUR/USD
  Trades endpoint; and
- taker-buy/sell quote-volume imbalance from Binance EURUSDT.

Each score used exactly the prior three consecutive, fully completed M5
bars. The sign of the unweighted mean selected one EURUSD side. There was no
fitted weight, threshold, strength filter, agreement requirement, reversal,
clock selection, or abstention.

| Window | Trades | Win rate | Payoff | PF | Net | Conditional side accuracy |
|---|---:|---:|---:|---:|---:|---:|
| 2020-2021 development | 532 | 32.52% | 1.439 | 0.693 | -112.80R | 51.49% |
| 2022-2023 validation | 560 | 31.61% | 1.438 | 0.665 | -131.65R | 49.44% |
| 2024 validation | 248 | 33.47% | 1.439 | 0.724 | -46.70R | 50.92% |
| 2025 pseudo-OOS | 316 | 31.65% | 1.439 | 0.666 | -73.98R | 50.51% |
| 2026 H1 pseudo-OOS | 156 | 29.49% | 1.439 | 0.602 | -44.93R | 51.11% |
| Overall | 1,812 | 31.95% | 1.439 | 0.676 | -410.05R | 50.57% |

Every window failed. Conditional accuracy was effectively a coin flip, and
the latest six months deteriorated rather than confirming an edge.

## Frequency

The mechanical frequency contract passed:

- 453 eligible Neutral dates;
- 1,812 trades;
- exactly four trades on every retained date;
- 100% exact-four execution coverage.

This remains four trades on each Regime-1-owned date, not four trades across
every weekday. Regime 1 owned 39 of 129 active weekdays in 2026 H1.

## Source novelty

Before outcomes:

- Kraken/Binance flow-imbalance correlation was only 0.0603;
- their signs agreed on 51.93% of decisions;
- the frozen multivenue rule predicted LONG 51.77% of the time;
- no score tie occurred.

Kraken therefore contributed genuinely different executed-flow information.
The failure cannot be attributed to simply duplicating the Binance input.

## Fixed-clock diagnostics

Every clock lost:

| Entry UTC | Trades | Win rate | PF | Net |
|---|---:|---:|---:|---:|
| 00:00 | 453 | 31.79% | 0.671 | -104.35R |
| 00:15 | 453 | 30.24% | 0.624 | -121.95R |
| 00:30 | 453 | 34.00% | 0.741 | -79.30R |
| 00:45 | 453 | 31.79% | 0.670 | -104.45R |

These are rejection diagnostics only. No clock may be selected after the
result.

## Same-calendar venue diagnostics

For diagnosis only, the two single-venue signs were recomputed on the exact
same 1,812 retained decisions:

| Diagnostic rule | Win rate | PF | Net | Conditional side accuracy |
|---|---:|---:|---:|---:|
| Kraken sign | 31.13% | 0.650 | -447.48R | 49.26% |
| Binance sign | 32.28% | 0.686 | -395.10R | 51.09% |
| Frozen equal weight | 31.95% | 0.676 | -410.05R | 50.57% |

Both venues and their fixed combination were negative. These counterfactual
diagnostics are not separately preregistered strategies and cannot be used
to choose a winner, weight, or reversal.

## Robustness and oracle resemblance

- Removing the top 5% of winners: PF 0.569 and -544.30R.
- Adding another 0.5 pip per trade: PF 0.551 and -636.55R.
- Daily 0.25R portfolio: PF 0.442, -102.51 portfolio R, and 103.86R maximum
  drawdown.
- Exact oracle precision: 18.93%.
- Same-side 15-minute oracle precision: 40.62%.

Only exact-four frequency passed. All economic, stress, drawdown, and oracle
resemblance gates failed.

## Last six months

From 2026-01-01 through 2026-06-30:

- 156 trades on 39 eligible Neutral dates;
- 46 wins and 110 losses;
- 29.49% win rate;
- 1.439 realized payoff;
- PF 0.602;
- -44.93R;
- 51.11% conditional side accuracy;
- daily portfolio PF 0.343 and -11.23 portfolio R;
- exactly four trades on every eligible Neutral date.

## Source outcome versus strategy outcome

The new source is accepted as reproducible research infrastructure:

- no login or OTP;
- 699 raw public API pages;
- 398,079 EUR/USD trades inside decision-time windows;
- 5,958 populated M5 bars;
- 453 strict all-12-bar dates;
- deterministic manifest and Parquet hashes;
- no missing-bar forward fill.

The strategy is rejected. A materially independent second venue did not
identify the future target-first EURUSD side.

## Verdict

The equal-weight multivenue rule is closed without repair. Retrospectively
selecting Kraken, Binance, a clock, an agreement subset, a stronger venue,
different weights, a threshold, or the inverse would be adaptive
overfitting.

Regime 1 remains `CASH`. Further legitimate progress now requires a new
information class, especially point-in-time macroeconomic release surprises
or a genuinely untouched prospective sample, rather than another
transformation of these two inspected venue histories.

## Reproduce

```powershell
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python download_neutral_kraken_eurusd.py
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_kraken_multivenue_flow.py census
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_neutral_kraken_multivenue_flow.py backtest
```
