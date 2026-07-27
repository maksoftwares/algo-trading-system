# EURUSD asymmetric-payoff verdict

Date: 2026-07-27

Decision: `REJECTED_TARGET_GEOMETRY_RECENT_ONLY`

## Requested target

The experiment defined “around 50% win rate” as 45–55% and “profit ratio around 1.5” as realized average winning R divided by average losing R from 1.35–1.75. Profit factor was measured separately and required to be at least 1.30.

The only strategy change was a 1.50R target and a 12-hour maximum holding period. The previously frozen EURUSD entries, regimes, stops, costs, and routing remained unchanged.

## Full-history forced diagnostic

| Trades | Win rate | Realized payoff | PF | Net R | Max DD R |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2,622 | 38.75% | 1.428 | 0.904 | -152.33 | 193.57 |

The exit achieved the requested payoff geometry, but the entry set did not win often enough. Every specialist failed chronological admission, so the governed portfolio correctly has zero trades.

| Specialist | Trades | Win rate | Payoff | PF | Net R |
| --- | ---: | ---: | ---: | ---: | ---: |
| Compression reversion | 1,516 | 35.88% | 1.445 | 0.809 | -185.82 |
| Supportive pullback | 265 | 40.38% | 1.480 | 1.002 | +0.35 |
| Neutral auction | 752 | 42.42% | 1.397 | 1.029 | +12.22 |
| Opposing capitulation | 264 | 41.29% | 1.436 | 1.010 | +1.47 |

## Latest six months

The forced all-owner stream from January through June 2026 was materially better but remains adaptive diagnostic evidence:

| Trades | Trades/day | Win rate | Realized payoff | PF | Net R | Fixed 0.01-lot P&L | Max DD R |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 195 | 1.512 | 44.62% | 1.454 | 1.171 | +18.11 | +$29.56 | 9.24 |

| Month | Trades | Win rate | Payoff | PF | Net R |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-01 | 26 | 50.00% | 1.430 | 1.430 | +5.38 |
| 2026-02 | 31 | 45.16% | 1.388 | 1.143 | +2.47 |
| 2026-03 | 39 | 43.59% | 1.505 | 1.163 | +3.56 |
| 2026-04 | 30 | 40.00% | 1.406 | 0.937 | -1.12 |
| 2026-05 | 34 | 44.12% | 1.529 | 1.207 | +3.69 |
| 2026-06 | 35 | 45.71% | 1.453 | 1.224 | +4.14 |

## Interpretation

The requested payoff ratio is feasible: the fixed 1.50R target realizes roughly 1.43–1.45 after costs and time exits. The unresolved problem is signal accuracy. The long-fade substrate produces only 38.75% wins over full history; recent 44.62% is close to the requested band but cannot override the historical failures or PF below 1.30.

The sparse broker-real-tick H4 chop control remains the only prior EURUSD evidence near both requested quality targets (53.23% win rate and PF 1.45), but 62 trades over two years is far below the frequency requirement.

Do not tune the 1.50R target or select only the recent neutral/opposing owners. The next valid research unit must be a genuinely different entry mechanism capable of increasing accuracy while retaining this frozen payoff geometry.
