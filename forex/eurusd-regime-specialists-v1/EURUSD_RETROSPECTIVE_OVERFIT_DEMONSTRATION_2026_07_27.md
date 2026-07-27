# EURUSD four-trade active-day overfit demonstration

Status: `INTENTIONALLY_OVERFIT_DIAGNOSTIC_NOT_TRADABLE`

The requested historical shape can be manufactured:

| Metric | Retrospective result |
|---|---:|
| Trades | 496 |
| Active trading days | 124 |
| Trades / active day | 4.000 |
| Win rate | 49.60% |
| Realized payoff ratio | 1.467 |
| Profit factor | 1.444 |
| Net | +107.22R |
| Maximum drawdown | 18.47R |
| Fixed 0.01-lot P&L | +$136.69 |
| Maximum concurrent positions | 4 |

This closely matches the requested combination of approximately four trades per active day, 50% wins, and a 1.5 payoff/PF shape.

## How the overfit was created

The broad regime-specialist stream produced 6,035 independently priced opportunities. The analysis inspected a retrospective density ladder: days containing exactly one opportunity, exactly two, and so on through twelve.

The selected oracle keeps every trade only on UTC dates later observed to contain exactly four total opportunities. That bucket happened to produce the requested historical statistics.

This is impossible to trade causally. When the first or second opportunity arrives, the system cannot know whether the completed day will contain exactly four opportunities. It learns that only after the final opportunity—or after the day has ended. The rule therefore uses future information even though each individual fill and exit uses realistic archived bid/ask prices.

## Density ladder inspected after outcomes

| Final opportunities on day | Trades | Active days | Trades / active day | Win rate | Payoff | PF |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 230 | 230 | 1.0 | 73.48% | 1.475 | 4.085 |
| 2 | 378 | 189 | 2.0 | 64.02% | 1.520 | 2.705 |
| 3 | 405 | 135 | 3.0 | 59.26% | 1.473 | 2.142 |
| **4** | **496** | **124** | **4.0** | **49.60%** | **1.467** | **1.444** |
| 5 | 515 | 103 | 5.0 | 39.22% | 1.490 | 0.962 |
| 6 | 456 | 76 | 6.0 | 44.30% | 1.470 | 1.169 |
| 7 | 357 | 51 | 7.0 | 39.78% | 1.416 | 0.935 |
| 8 | 424 | 53 | 8.0 | 32.31% | 1.372 | 0.655 |

The smooth relationship itself is suspicious: quiet days look exceptionally profitable and dense signal days lose. Choosing the four-opportunity bucket after inspecting this ladder is selection contamination, just like selecting Gold's favorable historical hours after observing them.

## Period breakdown

None of these periods is untouched because the density bucket was selected after inspecting the complete history.

| Period | Trades | Active days | Trades / active day | Win rate | Payoff | PF | Net |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2019-2021 | 188 | 47 | 4.0 | 46.81% | 1.424 | 1.253 | +24.73R |
| 2022-2024 | 188 | 47 | 4.0 | 44.68% | 1.533 | 1.238 | +23.83R |
| 2025 | 68 | 17 | 4.0 | 69.12% | 1.464 | 3.277 | +45.90R |
| 2026 H1 | 52 | 13 | 4.0 | 51.92% | 1.424 | 1.537 | +12.76R |

## Last six completed months

January through June 2026 contains 52 trades on 13 selected days:

- 4.00 trades per active day;
- 51.92% win rate;
- 1.424 realized payoff;
- PF 1.537;
- +12.76R and +$11.95 at fixed 0.01 lot;
- 7.14R maximum drawdown;
- maximum four concurrent positions.

## Frequency caveat

The result has four trades on days selected by the oracle, but it does not trade on every Forex weekday. Its 124 active dates cover only 6.35% of the 1,954 available weekdays; the full-calendar rate is 0.254 trades per weekday.

## Verdict

This demonstrates that EURUSD history can be made to look like the requested system. It is not an executable EA: its central gate requires the future completed-day signal count. It must never be presented as out-of-sample, demo-ready, or evidence of future profitability.

Reproduce:

```powershell
uv run --with pandas --with numpy --with pyarrow python run_retrospective_overfit.py
```

Primary artifacts:

- `outputs/retrospective_overfit/RESULT.json`
- `outputs/retrospective_overfit/DENSITY_LADDER.csv`
- `outputs/retrospective_overfit/FOUR_TRADE_DAY_ORACLE_TRADES.csv`
- `outputs/retrospective_overfit/EQUITY_CURVES.csv`
- `outputs/retrospective_overfit/OPPORTUNITY_OUTCOMES.csv`
