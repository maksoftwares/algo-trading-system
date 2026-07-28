# EURUSD Neutral BLS rolling-surprise carry verdict

## Verdict

`REJECTED_NEUTRAL_BLS_ROLLING_SURPRISE_CARRY_V1`

The exact hash-locked rolling-surprise carry is closed. Its outcome-blind
capacity census passed, but the one permitted backtest failed the win-rate,
profit-factor, chronological stability, both-side, robustness, drawdown, and
oracle-resemblance gates.

The positive four-trade 2026 H1 result is retained but is not activated.

## Outcome-blind capacity

The 267 point-in-time BLS releases yielded 217 directional gaps versus the
median of six previous consecutive initial values. Carrying the most recent
gap for at most 72 hours selected:

| Frozen window | Candidates |
|---|---:|
| 2019-2022 development | 244 |
| 2023 | 72 |
| 2024 | 48 |
| 2025 | 36 |
| 2026 H1 | 4 |
| Total | 404 |

The 404 candidates covered 101 Neutral dates, exactly four clocks on each
selected date. They included 192 LONG and 212 SHORT decisions and all three
families: 164 CPI, 104 PPI, and 136 NFP. Every census gate passed, although
2026 H1 met its four-trade minimum exactly.

## Full-history result

| Window | Trades | Win rate | Payoff | PF | Net |
|---|---:|---:|---:|---:|---:|
| 2019-2022 development | 244 | 31.56% | 1.439 | 0.664 | -57.60R |
| 2023 | 72 | 27.78% | 1.439 | 0.553 | -23.80R |
| 2024 | 48 | 47.92% | 1.439 | 1.324 | +8.30R |
| 2025 | 36 | 19.44% | 1.439 | 0.347 | -19.40R |
| 2026 H1 | 4 | 75.00% | 1.439 | 4.317 | +3.40R |
| Full history | 404 | 32.18% | 1.439 | 0.683 | -89.10R |

The fixed exit delivered the requested payoff shape, but overall win rate was
far below break-even. Development, 2023, and 2025 all lost. Both directions,
all macro families, and all clocks lost over full history.

At the frozen 0.25 portfolio-R allocation per ticket, daily net was -22.275R
and maximum drawdown was 23.575R, exceeding the 20R gate. Fixed 0.01-lot net
was -$35.64.

## Requested last six months

January-June 2026 contains only four trades, all on 12 June 2026:

| Clock UTC | Macro family | Side | Result |
|---|---|---|---:|
| 00:00 | CPI | SHORT | +1.475R |
| 00:15 | CPI | SHORT | +1.475R |
| 00:30 | CPI | SHORT | +1.475R |
| 00:45 | CPI | SHORT | -1.025R |

The numerical summary is 75.00% wins, 1.439 payoff, PF 4.317, +3.40 ticket-R,
+0.85 portfolio-R, and +$1.36 at fixed 0.01 lot.

This is one CPI state on one Neutral date expressed through four overlapping
positions. Its effective independent sample size is one, not four. It cannot
establish six-month profitability or authorize demo trading, particularly
because the same frozen rule lost heavily before and after its isolated
profitable 2024 window.

## Robustness and oracle resemblance

- an additional 0.5-pip round trip reduced full-history PF to 0.557;
- removing the best 5% of winners reduced PF to 0.572;
- LONG PF was 0.737 and SHORT PF was 0.636;
- exact oracle precision was 18.32%;
- same-side oracle precision within 15 minutes was 35.64%.

The simple rolling expectation improved neither full-history profitability nor
oracle resemblance. Changing the six-release baseline, selecting CPI, or
activating only 2024/2026 now would be post-outcome tuning.

## Integrity

Deterministic result:

`outputs/neutral_bls_rolling_surprise_carry/RESULT.json`

SHA-256:

`27613663dafa987c9daba03134138b7a9e438f3be01e59132f6c04e08d9072be`

Final status remains `RESEARCH_FAILURE_NOT_DEMO_READY`; Regime 1 remains
`CASH`.
