# EURUSD full-calendar perfect-foresight demonstration

Status: `DIRECT_FUTURE_PATH_LEAKAGE_NOT_TRADABLE`

The pure hindsight ceiling now fills every archived EURUSD trading weekday:

| Metric | Full-calendar oracle |
|---|---:|
| Period | 2019-01-02 through 2026-06-30 |
| Archived Monday-Friday dates | 1,954 |
| Active dates | 1,954 |
| Calendar coverage | 100.00% |
| Trades | 7,816 |
| Trades / weekday | 4.000 |
| Wins / losses | 7,816 / 0 |
| Win rate | 100.00% |
| Average realized winner | +1.475R |
| Profit factor | Infinite: no losses |
| Net | +11,528.79R |
| Maximum closed-trade drawdown | 0.00R |
| Fixed 0.01-lot P&L | +$4,610.93 |
| Long / short trades | 3,887 / 3,929 |
| Maximum concurrent positions | 7 |

“Full calendar” means every Monday-Friday date containing archived FX M5 bars. Weekends remain excluded because EURUSD is closed. The raw date span contains 1,955 Monday-Friday dates; 2021-01-01 has no archived bars and is therefore not an active trading day. All other 1,954 weekdays are filled.

## How it was manufactured

The oracle no longer depends on the original sparse RSI/Bollinger specialist signals. For every weekday it:

1. treats every distinct M5 timestamp as a possible entry;
2. evaluates both long and short future paths;
3. uses a 4-pip stop and nominal 1.50R target;
4. looks forward as far as 12 hours;
5. keeps the first four timestamps whose future path reaches the target before the stop;
6. discards every losing path and every unused winner.

No trade is cloned: all four daily entries have distinct timestamps. Archived bid/ask prices, a 0.70-pip minimum spread, 0.10-pip adverse slippage per side, and stop-first same-bar ambiguity remain applied.

Christmas Day 2025 could not supply four 4-pip-risk winners. The oracle retrospectively switched only that date to a 3-pip stop and 4.5-pip target. This is another explicit hindsight choice.

This is future-path leakage, not executable prediction. At each entry the oracle knows both the future direction and whether target or stop occurs first.

## Regime division

Regimes use the latest completed causal cross-asset state at each entry. Trade selection remains noncausal.

| Regime | Trades | Share | Long / short | Active days | Net | 2026 H1 trades |
|---|---:|---:|---:|---:|---:|---:|
| Neutral | 2,615 | 33.46% | 1,321 / 1,294 | 662 | +3,857.15R | 160 |
| Joint compression | 2,577 | 32.97% | 1,295 / 1,282 | 656 | +3,801.22R | 217 |
| USD up | 1,238 | 15.84% | 594 / 644 | 312 | +1,826.05R | 84 |
| USD down | 1,100 | 14.07% | 544 / 556 | 278 | +1,622.52R | 35 |
| Shock | 282 | 3.61% | 133 / 149 | 77 | +415.95R | 20 |
| Missing initial context | 4 | 0.05% | 0 / 4 | 1 | +5.90R | 0 |

The direction mix is nearly balanced, but Neutral plus Joint Compression still contributes 66.43% of trades.

## Period breakdown

Every period is perfect because future paths are read separately on every date.

| Period | Weekdays | Trades | Trades / weekday | Win rate | Average winner | Net |
|---|---:|---:|---:|---:|---:|---:|
| 2019-2021 | 782 | 3,128 | 4.0 | 100% | 1.475R | +4,613.82R |
| 2022-2024 | 782 | 3,128 | 4.0 | 100% | 1.475R | +4,613.95R |
| 2025 | 261 | 1,044 | 4.0 | 100% | 1.475R | +1,539.92R |
| 2026 H1 | 129 | 516 | 4.0 | 100% | 1.475R | +761.10R |

## Last six completed months

January through June 2026:

- all 129 archived weekdays covered;
- exactly 516 trades, or 4.00 per weekday;
- 516 wins and zero losses;
- 100.00% win rate;
- +1.475R average realized winner;
- infinite PF;
- +761.10R and +$304.44 at fixed 0.01 lot;
- zero closed-trade drawdown;
- maximum seven concurrent positions.

## PF and payoff interpretation

With zero losses, profit factor is infinite and average-win / average-loss payoff is undefined. The average realized winner is +1.475R, slightly below the nominal 1.50R target because adverse execution costs are included.

## Verdict

The requested curve exists historically: four distinct winners on every archived weekday with 100% win rate. It exists only because the algorithm reads future M5 paths, chooses the winning direction and timestamp, and deletes all failures. It cannot be converted into a causal EA, validated out of sample, or used for demo/live trading.

Reproduce:

```powershell
uv run --with pandas --with numpy --with pyarrow python run_retrospective_overfit.py
```

Primary artifacts:

- `outputs/retrospective_overfit/RESULT.json`
- `outputs/retrospective_overfit/FULL_CALENDAR_PERFECT_FORESIGHT_TRADES.csv`
- `outputs/retrospective_overfit/FULL_CALENDAR_BY_REGIME.csv`
- `outputs/retrospective_overfit/OPPORTUNITY_OUTCOMES.csv`
