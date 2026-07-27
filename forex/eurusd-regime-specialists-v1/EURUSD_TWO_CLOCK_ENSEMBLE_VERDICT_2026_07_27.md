# EURUSD two-clock regime ensemble verdict

Date: 2026-07-27

Decision: `REJECTED_NO_ADMITTED_SPECIALISTS`

## Outcome

Frequency was solved; profitability was not.

The outcome-blind ensemble census passed with 6,035 owned signals, 3.09 signals per Monday-Friday UTC trading day, 59.0% day coverage, and 2,438 / 2,129 / 1,468 signals across the three chronological windows.

After the locked exact-cost backtest, every specialist failed admission:

| Specialist | Trades | PF | Net R | Max DD R | Decision |
| --- | ---: | ---: | ---: | ---: | --- |
| Compression reversion | 1,581 | 0.794 | -163.28 | 166.91 | reject |
| Supportive pullback | 282 | 0.856 | -19.76 | 25.21 | reject |
| Neutral auction | 798 | 1.017 | +5.95 | 27.78 | reject |
| Opposing capitulation | 268 | 0.953 | -5.74 | 22.69 | reject |

Neutral auction was the least weak aggregate owner, but it failed the inherited-evidence window (PF 0.882, -13.48R), top-5%-winner removal (-27.77R), the extra-half-pip stress (-34.47R), and the 20R drawdown cap.

No specialist was admitted, so the governed portfolio correctly has zero trades. This is not a profitable trading system and is not eligible for demo-forward or live use.

## Diagnostic forced combination

For failure attribution only, forcing all rejected owners into one-position routing produced 2,776 trades, PF 0.874, -167.30R, -$131.23 at fixed 0.01 lot, and 182.64R maximum drawdown. This counterfactual is not an admitted portfolio.

## Interpretation

The earlier raw MT5 EURUSD seed had only a thin edge. Enforcing a 0.70-pip minimum retail spread, 0.10-pip slippage per side, causal cross-asset ownership, and stability gates removes it. The result is useful: the frequency problem is no longer the blocker; the entry/exit edge after realistic cost is.

Do not tune hours, thresholds, or regime labels on this outcome. The next EURUSD campaign needs a genuinely different mechanism or execution advantage, not another filter on these long-fade seeds.
