# EURUSD Neutral Asia Growth/Risk Transmission: Development Verdict

Date: 2026-07-28

## Verdict

`N48_NEUTRAL_ASIA_GROWTH_RISK_TRANSMISSION` is rejected in 2022–2023 development.

Status:

`REJECTED_IN_DEVELOPMENT_2024_2026_FORBIDDEN`

The exact 15-minute local-transmission rule did not restore a stable directional edge. No 2024, 2025, or 2026 trade outcome was loaded.

## Outcome-blind capacity

- Total aligned candidates: 87.
- 2022: 19.
- 2023: 25.
- 2024 kept closed: 9.
- 2025 kept closed: 21.
- 2026 H1 kept closed: 13.
- LONG / SHORT: 50 / 37.

All capacity gates passed. The family was intentionally low frequency and had no trades-per-day target.

## Development result

| Window | Trades | Win rate | Payoff | PF | Net | Drawdown |
|---|---:|---:|---:|---:|---:|---:|
| 2022 | 17 | 41.18% | 1.475 | 1.033 | +0.330R | 3.565R |
| 2023 | 24 | 37.50% | 1.467 | 0.880 | -1.822R | 5.627R |
| Combined | 41 | 39.02% | 1.470 | 0.941 | -1.492R | 5.627R |

By side:

| Side | Trades | Win rate | Payoff | PF | Net |
|---|---:|---:|---:|---:|---:|
| LONG | 24 | 41.67% | 1.473 | 1.052 | +0.734R |
| SHORT | 17 | 35.29% | 1.467 | 0.800 | -2.226R |

The payoff ratio remained close to the requested 1.5 because the risk/target design is sound. Profit factor remained below one because the signal could not sustain the required win rate.

## Firewall and execution audit

- Executed development trades: 41 of 44 aligned development candidates.
- Risk-ceiling cash decisions: 3.
- No missing entry bars, noncontiguous stop lookbacks, or overlapping positions.
- EURUSD load ended at `2023-12-29T21:55:00Z`.
- `future_rows_loaded`: false.
- `later_trade_outcomes_loaded`: false.
- Broker action: forbidden.

## Conclusion

The three growth/risk attempts now provide consistent evidence:

1. The mandatory three-session N46 portfolio was profitable in 2022 but failed its evidence floor.
2. The selected Asia-plus-Europe N47 portfolio lost in untouched 2023 confirmation.
3. The single Asia N48 expert with causal EURUSD transmission confirmation remained unprofitable across 2022–2023.

This external-consensus branch should be closed. Opening the sealed last six months after these failures would be selection on future outcomes, not a valid backtest.
