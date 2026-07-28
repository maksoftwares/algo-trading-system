# EURUSD Neutral five-session reversal verdict

## Verdict

`REJECTED_NEUTRAL_FIVE_SESSION_REVERSAL_V1`

The hash-locked five-session mean-reversion rule is closed without adding a
return threshold, changing direction, or repairing its 40/60-pip lifecycle.

## Chronological result

| Window | Trades | Win rate | Payoff | PF | Net |
|---|---:|---:|---:|---:|---:|
| 2019-2022 development | 234 | 46.58% | 1.409 | 1.228 | +25.18R |
| 2023 validation | 51 | 49.02% | 1.361 | 1.309 | +7.92R |
| 2024 validation | 41 | 36.59% | 1.153 | 0.665 | -7.72R |
| 2025 pseudo-OOS | 53 | 39.62% | 1.188 | 0.779 | -7.01R |
| 2026 H1 pseudo-OOS | 26 | 38.46% | 1.306 | 0.816 | -2.62R |
| Forward total | 171 | 41.52% | 1.268 | 0.900 | -9.43R |

This is an instructive forward rejection. The rule was profitable in all four
development years and then passed its first untouched year with nearly the
requested shape: 49.02% wins, 1.361 payoff, and PF 1.309. It failed in every
subsequent window.

The requested latest six months contain 26 trades, 38.46% wins, 1.306 payoff,
PF 0.816, and -2.62R. Frequency was not the problem; the realized edge did not
persist.

## Why it failed

Forward win rate remained above 40% overall, but the 72-hour lifecycle produced
many time exits. Average winning R fell to 1.200 while average losing R was
0.947, reducing realized payoff to 1.268 instead of the intended 1.5. At that
payoff, the 41.52% forward win rate was below break-even.

The regime shift is visible after 2023:

- 2023 achieved the target shape and earned +7.92R;
- 2024 win rate fell to 36.59% and payoff to 1.153;
- 2025 and 2026 H1 stayed below 40% wins;
- selecting 2023 alone would be a post-outcome year filter and is prohibited.

## Robustness and oracle resemblance

- extra-half-pip stress: PF 0.879 and -11.57R;
- best 5% of all trades removed: PF 0.758 and -22.91R;
- forward maximum ticket drawdown: 26.06R;
- exact oracle matches: 54 of 171, or 31.58% precision;
- same-side 15-minute matches: 84 of 171, or 49.12% precision.

Oracle resemblance was materially better than most earlier causal rules, but
entry resemblance did not produce a profitable 40/60-pip lifecycle. The
hindsight oracle's 4/6-pip winners cannot validate a different execution path.

## Integrity

The final rule used no magnitude threshold. Its 171 forward timestamps and
directions were fixed from completed closes and a deterministic cooldown before
outcomes. The lock and all pinned sources had zero mismatches before the first
forward pass.

Deterministic result:

`outputs/neutral_five_session_reversal/RESULT.json`

SHA-256:

`594aea49cfe4c1465b0d3b9d96ce442755b9d3079e0621442388380752c2cb62`

Final status remains `RESEARCH_FAILURE_NOT_DEMO_READY`; Regime 1 remains
`CASH`.
