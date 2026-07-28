# EURUSD Neutral Growth/Risk Consensus: Development Verdict

Date: 2026-07-28

## Verdict

`N46_NEUTRAL_GROWTH_RISK_CONSENSUS` is **rejected under its frozen contract**.

The strategy was profitable in the only opened outcome window, but it executed 68 trades against a preregistered minimum of 80. The trade-count gate is an evidence floor, not a daily-frequency target. It cannot be relaxed after seeing the result.

Status recorded by the runner:

`REJECTED_IN_DEVELOPMENT_2023_2026_FORBIDDEN`

No 2023, 2024, 2025, or 2026 EURUSD outcome was loaded.

## Outcome-blind census

- Neutral dates in the parent contract: 642.
- Expected decision points at three fixed clocks: 1,926.
- Causal complete external-market points: 993.
- Unanimous growth/risk candidates: 410.
- Candidate dates: 261.
- LONG candidates: 223.
- SHORT candidates: 187.
- 2022 development candidates: 104.
- 2023 confirmation candidates kept closed: 106.
- 2024–2026 H1 forward candidates kept closed: 200.

All census gates passed.

The generated field `neutral_dates_in_source_windows` is descriptively mislabeled: its value of 642 is the count of all parent Neutral dates used to construct expected clocks, including pre-2022 dates outside source coverage. The 924 missing source rows explicitly absorb the pre-2022 period. This label does not enter any gate or trade.

## Frozen 2022 development result

| Metric | Result |
|---|---:|
| Trades | 68 |
| Wins / losses | 31 / 37 |
| Win rate | 45.59% |
| Realized payoff ratio | 1.434 |
| Profit factor | 1.202 |
| Net | +7.547R |
| Expectancy | +0.111R/trade |
| Maximum drawdown | 7.401R |

The result was positive on both sides:

| Side | Trades | Win rate | Payoff | PF | Net |
|---|---:|---:|---:|---:|---:|
| LONG | 38 | 42.11% | 1.471 | 1.070 | +1.556R |
| SHORT | 30 | 50.00% | 1.395 | 1.395 | +5.991R |

## Session-specialist diagnosis

| Expert | Trades | Win rate | Payoff | PF | Net |
|---|---:|---:|---:|---:|---:|
| Asia 03:00 | 35 | 45.71% | 1.468 | 1.236 | +4.544R |
| Europe 09:00 | 19 | 52.63% | 1.476 | 1.640 | +5.812R |
| US 15:00 | 14 | 35.71% | 1.246 | 0.692 | -2.809R |

Asia plus Europe, viewed explicitly as in-sample development evidence, produced:

- 54 trades;
- 48.15% win rate;
- 1.471 realized payoff ratio;
- 1.366 profit factor;
- +10.356R;
- 6.122R maximum drawdown.

This decomposition does not rescue N46: the frozen N46 contract made all three experts mandatory and prohibited post-outcome expert selection. It can only motivate a separately named, explicitly adaptive successor that is locked before opening 2023.

## Execution and firewall audit

- 36 of 104 candidates were cash because the frozen structural risk exceeded the 20-pip ceiling.
- No candidate was lost to an open position, missing entry bar, or noncontiguous stop lookback.
- EURUSD parquet was loaded with a timestamp filter ending `2022-12-31T23:59:59Z`.
- The final loaded EURUSD M5 timestamp was `2022-12-30T21:55:00Z`.
- `future_rows_loaded` is false.
- Broker action remains forbidden.

## Interpretation

The mechanism is materially more promising than the rejected London-fix family: it achieved the desired neighborhood of roughly 50% wins, 1.5 payoff, and PF above 1.0 with costs. It is not yet validated. The next legitimate test is a new two-specialist portfolio that treats 2022 as development and uses untouched 2023 as confirmation.
