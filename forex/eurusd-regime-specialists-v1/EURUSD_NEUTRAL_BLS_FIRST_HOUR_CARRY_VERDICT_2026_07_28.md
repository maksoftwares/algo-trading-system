# EURUSD Neutral BLS first-hour macro carry verdict

## Verdict

`REJECTED_NEUTRAL_BLS_FIRST_HOUR_CARRY_V1`

The exact hash-locked macro-carry rule is closed. Its candidate census passed
before P&L, then the one permitted frozen backtest failed the win-rate, profit
factor, chronological stability, robustness, drawdown, and oracle-resemblance
gates.

No macro direction, release age, family, clock, year, stop, or target is
changed after seeing this result.

## Outcome-blind capacity

The 267 archived first-published BLS releases yielded 244 directional
same-family acceleration states. Carrying only the most recent state known
strictly before entry, for at most 72 hours, selected:

| Frozen window | Candidates |
|---|---:|
| 2019-2022 development | 272 |
| 2023 | 64 |
| 2024 | 44 |
| 2025 | 48 |
| 2026 H1 | 20 |
| Total | 448 |

The 448 candidates covered 112 Neutral dates, exactly four clocks per selected
date. They included 200 LONG and 248 SHORT decisions, and all three macro
families: 168 CPI, 128 PPI, and 152 NFP. Every frozen census gate passed.

## Full-history result

The fixed four-pip stop, six-pip target, 0.7-pip minimum spread, and 0.1-pip
slippage per side produced:

| Window | Trades | Win rate | Payoff | PF | Net |
|---|---:|---:|---:|---:|---:|
| 2019-2022 development | 272 | 34.56% | 1.439 | 0.760 | -43.80R |
| 2023 | 64 | 25.00% | 1.439 | 0.480 | -25.60R |
| 2024 | 44 | 43.18% | 1.439 | 1.094 | +2.40R |
| 2025 | 48 | 25.00% | 1.439 | 0.480 | -19.20R |
| 2026 H1 | 20 | 20.00% | 1.439 | 0.360 | -10.50R |
| Full history | 448 | 32.37% | 1.439 | 0.689 | -96.70R |

The target produced the requested payoff shape, but the 32.37% hit rate was
far below the roughly 41% cost-aware break-even level. Only 2024 was
profitable. Activating that year, removing shorts, or reversing the macro
direction now would be post-outcome selection.

At the frozen 0.25 portfolio-R allocation per ticket, the four-clock daily
portfolio lost 24.175R and reached a 24.175R maximum drawdown. At the separate
fixed 0.01-lot reporting scale, full-history net was -$38.68.

## Requested last six months

January-June 2026 contained 20 trades on five selected Neutral dates:

- wins: 4;
- losses: 16;
- win rate: 20.00%;
- realized payoff: 1.439;
- profit factor: 0.360;
- net: -10.50 ticket-R, equal to -2.625 portfolio-R;
- fixed 0.01-lot research result: -$4.20.

January returned PF 0.720 and -2.30R. April and June each had four losses,
PF 0, and -4.10R. February, March, and May had no qualifying macro-carry date.
This is neither profitable nor a sufficient basis for demo activation.

## Robustness and oracle resemblance

- adding another 0.5 pip round trip reduced PF to 0.562 and net to -152.70R;
- removing the best 5% of winners reduced PF to 0.579;
- LONG PF was 0.863 and SHORT PF was 0.566;
- all three macro families and all four clocks lost overall;
- exact oracle precision was 18.75%;
- same-side oracle precision within 15 minutes was 34.82%.

The latest initial-release acceleration state therefore does not approximate
the Neutral hindsight oracle at the first-hour clocks. It is a valid causal
input but not a viable specialist in this form.

## Integrity

Deterministic result:

`outputs/neutral_bls_first_hour_carry/RESULT.json`

SHA-256:

`6d171c348f2100c0896fecf20e56c7b8761d6cdb7caaa943046fd08444b1349c`

Final status remains `RESEARCH_FAILURE_NOT_DEMO_READY`; Regime 1 remains
`CASH`.
