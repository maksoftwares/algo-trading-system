# EURUSD Neutral Rates/Dollar MT5 Audit

Status: `REJECTED_RETROSPECTIVE_NEUTRAL_RATES_DOLLAR_MT5`

## Outcome

This existing H4 short strategy is **not** a viable Neutral expert. Its canonical Neutral subset is superficially profitable, but it is too small, does not match the requested payoff profile, weakens under timezone robustness, and failed in 2025.

| Scope | Trades | Win rate | Payoff | PF | Net USD |
|---|---:|---:|---:|---:|---:|
| Primary Neutral | 12 | 66.67% | 0.731 | 1.461 | 11.84 |
| Primary Neutral +0.5 pip | 12 | 66.67% | 0.717 | 1.434 | 11.24 |
| Primary Neutral, top 5% winners removed | 11 | 63.64% | 0.643 | 1.126 | 3.23 |
| Offset 2 Neutral | 9 | 55.56% | 0.913 | 1.142 | 3.64 |
| Offset 3 Neutral | 9 | 55.56% | 0.913 | 1.142 | 3.64 |

## Chronology

| Window | Trades | Win rate | Payoff | PF | Net USD |
|---|---:|---:|---:|---:|---:|
| 2022 | 5 | 80.00% | 3.059 | 12.234 | 17.75 |
| 2023 | 3 | 66.67% | 0.756 | 1.512 | 3.25 |
| 2024 | 1 | 100.00% | N/A | N/A | 2.87 |
| 2025 | 2 | 0.00% | N/A | 0.000 | -17.75 |
| 2026_H1 | 1 | 100.00% | N/A | N/A | 5.72 |
| DEVELOPMENT_2022_2023 | 8 | 75.00% | 1.216 | 3.648 | 21.00 |
| RECENT_2024_2026_H1 | 4 | 50.00% | 0.484 | 0.484 | -9.16 |
| LATEST_SIX_MONTHS | 1 | 100.00% | N/A | N/A | 5.72 |

## Full primary regime attribution

| Regime | Trades | Win rate | Payoff | PF | Net USD |
|---|---:|---:|---:|---:|---:|
| JOINT_COMPRESSION | 46 | 41.30% | 1.317 | 0.927 | -6.04 |
| NEUTRAL | 12 | 66.67% | 0.731 | 1.461 | 11.84 |
| SHOCK | 14 | 64.29% | 3.376 | 6.076 | 32.74 |
| USD_UP | 19 | 36.84% | 1.121 | 0.654 | -19.58 |

## Oracle resemblance

During the common 2024-07 through 2026-06 window, only `3` causal Neutral candidate trades existed versus `600` oracle trades. Exact same-side matches: `0`; within 15 minutes: `0`. The oracle was used only after execution for diagnosis.

## Why rejected

- Only 12 canonical Neutral trades exist; the latest six months contain one trade.
- The canonical 66.7% win rate and 0.73 realized payoff do not match the requested approximately 50% / 1.5 profile.
- Neutral PF falls from 1.46 at offset 0 to 1.14 at offsets 2/3.
- Removing the top 5% of winners lowers canonical Neutral PF to 1.13.
- The 2025 Neutral slice lost USD 17.75, while the latest-six-month result is a single winning trade.
- The reports predate this audit, so no slice can be represented as pristine chronological out-of-sample evidence.

## Integrity boundary

- All three MT5 reports reconcile exactly to their deal ledgers when swap is included.
- Offset 0 was declared primary; offsets 2 and 3 are robustness checks, not alternatives selected by outcome.
- Causal regime ownership uses the state from the prior completed hour.
- No thresholds, target, regime definition, or time window were retuned.
- No broker, demo, or live action occurred.
- The strong Shock-regime diagnostic is out of scope and was not substituted for Neutral.
