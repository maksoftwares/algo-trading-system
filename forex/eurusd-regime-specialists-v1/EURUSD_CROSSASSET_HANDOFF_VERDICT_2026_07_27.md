# EURUSD cross-asset session-handoff verdict

Decision: `REJECTED_CLOSE_CROSSASSET_SESSION_HANDOFF`

The frozen cross-asset experiment passed its outcome-blind opportunity census, but failed the exact-cost profitability and stability gates. Neither specialist was admitted, so the governed portfolio has no trades.

## Capacity census

| Measure | Result |
|---|---:|
| Eligible signals | 497 |
| Signals per weekday | 0.254 |
| Weekday coverage | 22.16% |
| Historical / inherited / adaptive signals | 158 / 201 / 138 |
| London / New York signals | 306 / 191 |
| Long / short signals | 219 / 278 |
| Capacity gate | PASS |

## Full-history exact-cost results

| Diagnostic | Trades | Win rate | Realized payoff | PF | Net R | Max DD |
|---|---:|---:|---:|---:|---:|---:|
| London handoff | 306 | 33.01% | 1.461 | 0.720 | -58.37R | 63.27R |
| New York handoff | 191 | 35.08% | 1.441 | 0.778 | -27.57R | 32.98R |
| Forced combined diagnostic | 496 | 33.87% | 1.452 | 0.744 | -84.92R | 92.97R |

The New York specialist's PF was 0.625 / 0.959 / 0.695 across the three chronological windows. The London specialist's PF was 0.782 / 0.780 / 0.575. Neither showed a profitable window sequence, and both failed the 45-55% win-rate requirement by a wide margin.

## Latest six completed months

Window: 2026-01-01 through 2026-06-30.

The forced all-specialist diagnostic produced 41 trades, a 36.59% win rate, a 1.466 realized payoff ratio, PF 0.846, -4.06R, and a 7.68R maximum drawdown. At fixed 0.01-lot sizing the result was -$2.71.

## Interpretation

The 1.50R lifecycle continues to deliver the requested payoff shape, but the entries do not supply the roughly 41% break-even win rate after costs, let alone the requested approximately 50%. Independent DXY confirmation and session-range resolution did not increase precision; they reduced frequency while retaining the same low-accuracy problem.

No DXY lookback, session, breakout buffer, stop, or target was retuned after opening outcomes. This mechanism is closed rather than optimized on the observed losses. A subsequent experiment must change the information source or prediction horizon, not add another filter to the same price-continuation thesis.

Artifacts:

- `outputs/crossasset_handoff/CENSUS.json`
- `outputs/crossasset_handoff/RESULT.json`
- `outputs/crossasset_handoff/SIGNALS.parquet`
- specialist and combined diagnostic trade ledgers in `outputs/crossasset_handoff/`
