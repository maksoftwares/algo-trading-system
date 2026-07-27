# EURUSD 100% win-rate perfect-foresight demonstration

Status: `DIRECT_FUTURE_OUTCOME_LEAKAGE_NOT_TRADABLE`

The pure hindsight ceiling now has the requested 100% historical win rate while retaining exactly four trades per qualifying active day.

| Metric | Perfect-foresight result |
|---|---:|
| Trades | 624 |
| Wins / losses | 624 / 0 |
| Win rate | 100.00% |
| Active trading days | 156 |
| Trades / active day | 4.000 |
| Average realized winner | +1.489R |
| Profit factor | Infinite: no losses |
| Net | +929.25R |
| Maximum drawdown | 0.00R |
| Fixed 0.01-lot P&L | +$1,036.80 |
| Maximum concurrent positions | 4 |

## How the perfect curve was manufactured

The broad EURUSD regime-specialist stream produced 6,035 independently priced candidate opportunities. For each candidate, the oracle:

1. reads its future exit;
2. keeps it only if the 1.50R target will be reached;
3. finds historical dates having at least four such future winners;
4. retains the first four known target winners on each qualifying date;
5. discards every future loss and every additional winner.

Individual fills still include archived bid/ask prices, a 0.70-pip spread floor, 0.10-pip adverse slippage per side, and stop-first ambiguity. Those execution details do not make the result causal: the trade-selection label comes directly from the future exit.

## Why PF and payoff are not 1.5

Profit factor is gross profit divided by gross loss. With zero losses, the denominator is zero, so PF is mathematically infinite.

Average-win / average-loss payoff is undefined for the same reason. The useful displayed quantity is the average realized winner, +1.489R. It sits just below the nominal 1.50R target because execution costs are included.

## Period breakdown

Every period is perfectly fitted because future outcomes are read separately on every date.

| Period | Trades | Active days | Trades / active day | Win rate | Average winner | Net |
|---|---:|---:|---:|---:|---:|---:|
| 2019-2021 | 228 | 57 | 4.0 | 100% | 1.489R | +339.44R |
| 2022-2024 | 256 | 64 | 4.0 | 100% | 1.489R | +381.27R |
| 2025 | 72 | 18 | 4.0 | 100% | 1.491R | +107.32R |
| 2026 H1 | 68 | 17 | 4.0 | 100% | 1.488R | +101.21R |

## Last six completed months

January through June 2026:

- 68 trades on 17 qualifying active days;
- exactly 4.00 trades per active day;
- 68 wins and zero losses;
- 100.00% win rate;
- +1.488R average realized winner;
- infinite PF;
- +101.21R and +$101.43 at fixed 0.01 lot;
- zero closed-trade drawdown;
- maximum four concurrent positions.

## Frequency caveat

The oracle trades four times on its selected dates, but its 156 active dates cover only 7.98% of the 1,954 available weekdays. The full-calendar rate is 0.319 trades per weekday.

## Verdict

This is no longer ordinary parameter overfitting. It is a perfect-foresight label-leakage benchmark. It demonstrates the maximum curve that can be drawn after all future outcomes are known, but it cannot be encoded as a causal EA, tested out of sample, or used for demo/live trading.

Reproduce:

```powershell
uv run --with pandas --with numpy --with pyarrow python run_retrospective_overfit.py
```

Primary artifacts:

- `outputs/retrospective_overfit/RESULT.json`
- `outputs/retrospective_overfit/PERFECT_FORESIGHT_TRADES.csv`
- `outputs/retrospective_overfit/EQUITY_CURVES.csv`
- `outputs/retrospective_overfit/OPPORTUNITY_OUTCOMES.csv`
- `outputs/retrospective_overfit/FOUR_TRADE_DAY_ORACLE_TRADES.csv`
